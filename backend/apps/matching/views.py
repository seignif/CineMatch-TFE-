import logging
from django.db.models import Q
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.models import User
from .algorithm import MatchingAlgorithm
from .ai_service import MatchingAIService
from .models import Swipe, Match, PlannedOuting, Review, Group, GroupMember, GroupMessage, FilmVote
from .serializers import (
    CandidateSerializer, MatchSerializer, SwipeSerializer,
    PlannedOutingSerializer, ReviewSerializer,
    GroupSerializer, GroupMessageSerializer, FilmVoteSerializer,
)

logger = logging.getLogger(__name__)
algorithm = MatchingAlgorithm()
ai_service = MatchingAIService()


class CandidatesView(APIView):
    """GET /api/matching/candidates/ — Liste de candidats potentiels avec leur score."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # Exclure : soi-même, utilisateurs déjà swipés
        already_swiped = Swipe.objects.filter(from_user=user).values_list('to_user_id', flat=True)
        matched_ids = Match.objects.filter(
            Q(user1=user) | Q(user2=user)
        ).values_list('user1_id', 'user2_id')
        matched_flat = {uid for pair in matched_ids for uid in pair if uid != user.id}

        exclude_ids = set(already_swiped) | matched_flat | {user.id}

        # Utilisateurs qui ont superliké l'utilisateur courant (sans qu'il ait encore swipé)
        superliked_me_ids = set(
            Swipe.objects.filter(to_user=user, action='superlike')
            .exclude(from_user_id__in=exclude_ids)
            .values_list('from_user_id', flat=True)
        )

        candidates = (
            User.objects.exclude(id__in=exclude_ids)
            .select_related('profile')
            .prefetch_related('profile__films_signature')
            [:50]
        )

        results = []
        for candidate in candidates:
            score, reasons = algorithm.calculate_compatibility(user, candidate)
            results.append({
                'candidate': candidate,
                'score': score,
                'reasons': reasons,
                'superliked_me': candidate.id in superliked_me_ids,
            })

        # Superlikes d'abord, puis par score décroissant
        results.sort(key=lambda x: (x['superliked_me'], x['score']), reverse=True)
        results = results[:20]

        serialized = []
        for item in results:
            c = item['candidate']
            c.score = item['score']
            c.reasons = item['reasons']
            c.superliked_me = item['superliked_me']
            serialized.append(CandidateSerializer(c, context={'request': request}).data)

        return Response(serialized)


class SwipeView(APIView):
    """POST /api/matching/swipe/ — Enregistre un swipe et crée un match si mutual."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SwipeSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        from_user = request.user
        to_user_id = serializer.validated_data['to_user_id']
        action = serializer.validated_data['action']

        if to_user_id == from_user.id:
            return Response({'detail': 'Vous ne pouvez pas vous swiper vous-même.'}, status=400)

        try:
            to_user = User.objects.select_related('profile').prefetch_related('profile__films_signature').get(id=to_user_id)
        except User.DoesNotExist:
            return Response({'detail': 'Utilisateur introuvable.'}, status=404)

        swipe, created = Swipe.objects.get_or_create(
            from_user=from_user,
            to_user=to_user,
            defaults={'action': action},
        )
        if not created:
            swipe.action = action
            swipe.save(update_fields=['action'])

        # Vérifier si match mutuel
        match_obj = None
        is_new_match = False

        if action in ('like', 'superlike'):
            reverse = Swipe.objects.filter(
                from_user=to_user, to_user=from_user, action__in=['like', 'superlike']
            ).first()

            if reverse:
                # Assurer un ordre déterministe pour user1/user2
                u1, u2 = (from_user, to_user) if from_user.id < to_user.id else (to_user, from_user)
                match_obj, is_new_match = Match.objects.get_or_create(user1=u1, user2=u2)

                if is_new_match:
                    score, reasons = algorithm.calculate_compatibility(u1, u2)
                    ai_reasons, ai_message = ai_service.generate_match_content(u1, u2, score, reasons)
                    match_obj.score_compatibilite = score
                    match_obj.raisons_compatibilite = reasons
                    match_obj.ai_generated_reasons = ai_reasons
                    match_obj.ai_match_message = ai_message
                    match_obj.save()

        response_data = {'action': action, 'match': None}
        if is_new_match and match_obj:
            response_data['match'] = MatchSerializer(match_obj, context={'request': request}).data

        return Response(response_data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class MatchListView(APIView):
    """GET /api/matching/matches/ — Tous les matchs de l'utilisateur connecté."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        matches = (
            Match.objects.filter(Q(user1=user) | Q(user2=user), status='active')
            .select_related('user1__profile', 'user2__profile')
            .order_by('-created_at')
        )
        return Response(MatchSerializer(matches, many=True, context={'request': request}).data)


class MatchDetailView(APIView):
    """GET /api/matching/matches/<id>/ — Détail d'un match."""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        user = request.user
        try:
            match = Match.objects.select_related(
                'user1__profile', 'user2__profile'
            ).get(Q(user1=user) | Q(user2=user), pk=pk)
        except Match.DoesNotExist:
            return Response({'detail': 'Match introuvable.'}, status=404)
        return Response(MatchSerializer(match, context={'request': request}).data)


# ---------------------------------------------------------------------------
# Sorties planifiées (US-029 à US-033)
# ---------------------------------------------------------------------------

def _outing_qs(user):
    """Queryset de base : sorties où l'utilisateur est participant."""
    return (
        PlannedOuting.objects
        .filter(Q(proposer=user) | Q(match__user1=user) | Q(match__user2=user))
        .select_related(
            'seance__film', 'seance__cinema',
            'proposer__profile',
            'match__user1__profile', 'match__user2__profile',
        )
        .distinct()
    )


class OutingListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/matching/outings/  — mes sorties
    POST /api/matching/outings/  — proposer une sortie à un match
    """
    permission_classes = [IsAuthenticated]
    serializer_class = PlannedOutingSerializer

    def get_queryset(self):
        return _outing_qs(self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        from rest_framework.exceptions import ValidationError
        from apps.films.models import Seance

        user = self.request.user
        match_id = self.request.data.get('match')
        seance_id = self.request.data.get('seance_id')

        match = Match.objects.filter(
            id=match_id, status='active'
        ).filter(Q(user1=user) | Q(user2=user)).first()
        if not match:
            raise ValidationError({'match': 'Match introuvable ou non autorisé.'})

        seance = Seance.objects.filter(id=seance_id).first() if seance_id else None

        serializer.save(proposer=user, match=match, seance=seance, status='proposed')


class OutingDetailView(generics.RetrieveAPIView):
    """GET /api/matching/outings/<id>/"""
    permission_classes = [IsAuthenticated]
    serializer_class = PlannedOutingSerializer

    def get_queryset(self):
        return _outing_qs(self.request.user)


class OutingConfirmView(APIView):
    """
    PUT /api/matching/outings/<id>/confirm/
    Body: {"action": "confirm"} ou {"action": "refuse"}
    Seul le partenaire (non-proposer) peut confirmer/refuser.
    """
    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        user = request.user
        action = request.data.get('action')

        if action not in ('confirm', 'refuse'):
            return Response(
                {'error': 'Action invalide : confirm ou refuse.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        outing = _outing_qs(user).filter(id=pk, status='proposed').first()
        if not outing:
            return Response(
                {'error': 'Sortie introuvable ou déjà traitée.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if outing.proposer == user:
            return Response(
                {'error': 'Vous ne pouvez pas confirmer votre propre proposition.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        outing.status = 'confirmed' if action == 'confirm' else 'cancelled'
        outing.save(update_fields=['status', 'updated_at'])

        msg = 'Sortie confirmée !' if action == 'confirm' else 'Sortie refusée.'
        return Response({
            'message': msg,
            'outing': PlannedOutingSerializer(outing, context={'request': request}).data,
        })


class OutingCancelView(APIView):
    """PUT /api/matching/outings/<id>/cancel/ — n'importe quel participant peut annuler."""
    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        user = request.user
        outing = _outing_qs(user).filter(
            id=pk, status__in=['proposed', 'confirmed']
        ).first()

        if not outing:
            return Response(
                {'error': 'Sortie introuvable ou déjà terminée.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        outing.status = 'cancelled'
        outing.save(update_fields=['status', 'updated_at'])

        return Response({
            'message': 'Sortie annulée.',
            'outing': PlannedOutingSerializer(outing, context={'request': request}).data,
        })


class OutingMarkBookedView(APIView):
    """PUT /api/matching/outings/<id>/booked/ — marquer billet réservé (US-032)."""
    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        user = request.user
        outing = _outing_qs(user).filter(id=pk, status='confirmed').first()

        if not outing:
            return Response(
                {'error': 'Sortie introuvable ou non confirmée.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if outing.proposer == user:
            outing.proposer_booked = True
        else:
            outing.partner_booked = True
        outing.save(update_fields=['proposer_booked', 'partner_booked', 'updated_at'])

        both = outing.proposer_booked and outing.partner_booked
        return Response({
            'message': 'Super ! Vous avez tous les deux réservé !' if both else 'Billet marqué comme réservé !',
            'both_booked': both,
            'outing': PlannedOutingSerializer(outing, context={'request': request}).data,
        })


class UpcomingOutingsView(generics.ListAPIView):
    """GET /api/matching/outings/upcoming/ — sorties confirmées à venir (US-033 badges)."""
    permission_classes = [IsAuthenticated]
    serializer_class = PlannedOutingSerializer

    def get_queryset(self):
        return _outing_qs(self.request.user).filter(
            status='confirmed',
            seance__showtime__gt=timezone.now(),
        ).order_by('seance__showtime')


class OutingCompleteView(APIView):
    """PUT /api/matching/outings/<id>/complete/ — marquer la sortie comme terminée."""
    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        user = request.user
        outing = _outing_qs(user).filter(id=pk, status='confirmed').first()

        if not outing:
            return Response(
                {'error': 'Sortie introuvable ou non confirmée.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        outing.status = 'completed'
        outing.save(update_fields=['status', 'updated_at'])
        return Response({
            'message': 'Sortie marquée comme terminée.',
            'outing': PlannedOutingSerializer(outing, context={'request': request}).data,
        })


class ReviewCreateView(APIView):
    """POST /api/matching/outings/<id>/review/ — laisser un avis post-sortie (US-038)."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        from apps.users.badge_service import BadgeService

        user = request.user
        outing = _outing_qs(user).filter(
            id=pk, status__in=['completed', 'confirmed']
        ).first()

        if not outing:
            return Response(
                {'error': 'Sortie introuvable.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Identifier le partenaire par rapport à l'utilisateur courant
        match = outing.match
        partner = match.user2 if match.user1 == user else match.user1
        if partner == user:
            return Response({'error': 'Invalide.'}, status=400)

        # Vérifier qu'il n'y a pas déjà un avis de cet utilisateur
        if Review.objects.filter(outing=outing, reviewer=user).exists():
            return Response({'error': 'Vous avez déjà laissé un avis pour cette sortie.'}, status=400)

        serializer = ReviewSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        review = serializer.save(
            outing=outing,
            reviewer=user,
            reviewed=partner,
        )

        # Passer en completed si ce n'est pas déjà le cas
        if outing.status != 'completed':
            outing.status = 'completed'
            outing.save(update_fields=['status', 'updated_at'])

        # Vérifier et attribuer les badges
        new_badges = BadgeService.check_and_award_badges(user)

        return Response({
            'review': ReviewSerializer(review).data,
            'new_badges': new_badges,
        }, status=status.HTTP_201_CREATED)


# ---------------------------------------------------------------------------
# Groupes (US-041 / US-042 / US-043)
# ---------------------------------------------------------------------------

class GroupListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = GroupSerializer

    def get_queryset(self):
        user = self.request.user
        return Group.objects.filter(
            groupmember__user=user,
            groupmember__status='accepted',
        ).prefetch_related(
            'groupmember_set__user__profile',
            'messages',
            'votes__film',
        ).distinct()

    def create(self, request, *args, **kwargs):
        user = request.user
        name = request.data.get('name', '').strip()
        member_ids = request.data.get('member_ids', [])

        if not member_ids:
            return Response({'error': 'Invitez au moins une personne.'}, status=status.HTTP_400_BAD_REQUEST)
        if len(member_ids) > 7:
            return Response({'error': 'Maximum 7 invités par groupe.'}, status=status.HTTP_400_BAD_REQUEST)

        # Vérifier que les invités sont des matchs actifs du créateur
        valid_ids = []
        for mid in member_ids:
            is_match = Match.objects.filter(
                Q(user1=user, user2_id=mid) | Q(user1_id=mid, user2=user),
                status='active',
            ).exists()
            if is_match:
                valid_ids.append(mid)

        if not valid_ids:
            return Response({'error': 'Aucun des invités n\'est un de vos matchs.'}, status=status.HTTP_400_BAD_REQUEST)

        group = Group.objects.create(
            name=name or f"Groupe de {user.first_name}",
            creator=user,
        )

        # Créateur → accepté directement (admin)
        GroupMember.objects.create(
            group=group, user=user, role='admin', status='accepted',
            responded_at=timezone.now(),
        )

        # Invités → statut pending
        for mid in valid_ids:
            try:
                invitee = User.objects.get(id=mid)
                GroupMember.objects.create(
                    group=group, user=invitee, role='member',
                    status='pending', invited_by=user,
                )
            except User.DoesNotExist:
                pass

        GroupMessage.objects.create(
            group=group, sender=user,
            content=f"{user.first_name} a créé le groupe.",
            is_system=True,
        )

        serializer = GroupSerializer(group, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class GroupInvitationsView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = GroupSerializer

    def get_queryset(self):
        return Group.objects.filter(
            groupmember__user=self.request.user,
            groupmember__status='pending',
        ).prefetch_related('groupmember_set__user__profile')


class GroupRespondInvitationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        user = request.user
        action = request.data.get('action')

        if action not in ('accept', 'decline'):
            return Response({'error': "Action invalide : 'accept' ou 'decline'."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            membership = GroupMember.objects.get(group_id=pk, user=user, status='pending')
        except GroupMember.DoesNotExist:
            return Response({'error': 'Invitation introuvable ou déjà traitée.'}, status=status.HTTP_404_NOT_FOUND)

        membership.responded_at = timezone.now()

        if action == 'accept':
            membership.status = 'accepted'
            membership.save()
            GroupMessage.objects.create(
                group=membership.group, sender=user,
                content=f"{user.first_name} a rejoint le groupe ! 🎉",
                is_system=True,
            )
            serializer = GroupSerializer(membership.group, context={'request': request})
            return Response({'message': 'Invitation acceptée !', 'group': serializer.data})
        else:
            membership.status = 'declined'
            membership.save()
            return Response({'message': 'Invitation refusée.'})


class GroupDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = GroupSerializer
    http_method_names = ['get', 'patch', 'head', 'options']

    def get_queryset(self):
        return Group.objects.filter(groupmember__user=self.request.user).prefetch_related(
            'groupmember_set__user__profile', 'messages', 'votes__film',
        )

    def perform_update(self, serializer):
        if self.get_object().creator != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Seul le créateur peut modifier le groupe.")
        serializer.save()


class GroupLeaveView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        user = request.user
        try:
            membership = GroupMember.objects.get(group_id=pk, user=user, status='accepted')
        except GroupMember.DoesNotExist:
            return Response({'error': 'Vous n\'êtes pas membre de ce groupe.'}, status=status.HTTP_404_NOT_FOUND)

        group = membership.group
        GroupMessage.objects.create(
            group=group, sender=user,
            content=f"{user.first_name} a quitté le groupe.",
            is_system=True,
        )
        membership.delete()

        if group.groupmember_set.filter(status='accepted').count() == 0:
            group.status = 'archived'
            group.save()

        return Response({'message': 'Vous avez quitté le groupe.'})


class GroupInviteMembersView(APIView):
    """POST /api/matching/groups/<pk>/invite/ — l'admin invite de nouveaux membres."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        user = request.user
        try:
            membership = GroupMember.objects.get(group_id=pk, user=user, status='accepted', role='admin')
        except GroupMember.DoesNotExist:
            return Response({'error': 'Réservé à l\'admin du groupe.'}, status=status.HTTP_403_FORBIDDEN)

        group = membership.group
        member_ids = request.data.get('member_ids', [])
        if not member_ids:
            return Response({'error': 'Sélectionnez au moins une personne.'}, status=status.HTTP_400_BAD_REQUEST)

        existing_ids = set(group.groupmember_set.values_list('user_id', flat=True))
        invited = []

        for mid in member_ids:
            if mid in existing_ids:
                continue
            is_match = Match.objects.filter(
                Q(user1=user, user2_id=mid) | Q(user1_id=mid, user2=user),
                status='active',
            ).exists()
            if not is_match:
                continue
            try:
                invitee = User.objects.get(id=mid)
                GroupMember.objects.create(
                    group=group, user=invitee, role='member',
                    status='pending', invited_by=user,
                )
                invited.append(invitee.first_name)
            except User.DoesNotExist:
                pass

        if not invited:
            return Response({'error': 'Aucune invitation envoyée (déjà membres ou non-matchs).'}, status=status.HTTP_400_BAD_REQUEST)

        GroupMessage.objects.create(
            group=group, sender=user,
            content=f"{user.first_name} a invité {', '.join(invited)}.",
            is_system=True,
        )
        return Response({'message': f'{len(invited)} invitation(s) envoyée(s).', 'invited': invited})


class GroupMessagesView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = GroupMessageSerializer

    def get_queryset(self):
        user = self.request.user
        group_id = self.kwargs['pk']
        if not GroupMember.objects.filter(group_id=group_id, user=user, status='accepted').exists():
            return GroupMessage.objects.none()
        return GroupMessage.objects.filter(group_id=group_id).select_related('sender').order_by('created_at')


class FilmVoteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        user = request.user
        if not GroupMember.objects.filter(group_id=pk, user=user, status='accepted').exists():
            return Response({'error': 'Vous devez être membre actif pour voter.'}, status=status.HTTP_403_FORBIDDEN)

        film_id = request.data.get('film_id')
        vote_value = request.data.get('vote')
        if vote_value not in ('up', 'down'):
            return Response({'error': "Vote invalide : 'up' ou 'down'."}, status=status.HTTP_400_BAD_REQUEST)

        from apps.films.models import Film
        try:
            film = Film.objects.get(id=film_id)
        except Film.DoesNotExist:
            return Response({'error': 'Film introuvable.'}, status=status.HTTP_404_NOT_FOUND)

        group = Group.objects.get(id=pk)
        existing = FilmVote.objects.filter(group=group, film=film, voter=user).first()

        # Toggle : même vote → on le retire
        if existing and existing.vote == vote_value:
            existing.delete()
            removed = True
            film_vote = None
        else:
            film_vote, _ = FilmVote.objects.update_or_create(
                group=group, film=film, voter=user,
                defaults={'vote': vote_value},
            )
            removed = False

        active_count = group.groupmember_set.filter(status='accepted').count()
        up_votes = FilmVote.objects.filter(group=group, film=film, vote='up').count()
        down_votes = FilmVote.objects.filter(group=group, film=film, vote='down').count()

        film_chosen = False
        if not removed and up_votes == active_count and active_count > 0:
            already_chosen = group.chosen_film_id == film.id
            group.chosen_film = film
            group.save()
            film_chosen = True
            if not already_chosen:
                GroupMessage.objects.create(
                    group=group, sender=user,
                    content=f"Film choisi : {film.title} ! 🎬",
                    is_system=True,
                )

        return Response({
            'vote': FilmVoteSerializer(film_vote).data if film_vote else None,
            'removed': removed,
            'film_chosen': film_chosen,
            'votes_for_film': {'up': up_votes, 'down': down_votes, 'total_active_members': active_count},
        }, status=status.HTTP_200_OK)


class GroupChooseFilmView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        user = request.user
        try:
            group = Group.objects.get(id=pk, creator=user)
        except Group.DoesNotExist:
            return Response({'error': 'Seul le créateur peut forcer le choix.'}, status=status.HTTP_403_FORBIDDEN)

        from apps.films.models import Film
        try:
            film = Film.objects.get(id=request.data.get('film_id'))
        except Film.DoesNotExist:
            return Response({'error': 'Film introuvable.'}, status=status.HTTP_404_NOT_FOUND)

        group.chosen_film = film
        group.save()
        GroupMessage.objects.create(
            group=group, sender=user,
            content=f"{user.first_name} a choisi le film : {film.title} 🎬",
            is_system=True,
        )

        serializer = GroupSerializer(group, context={'request': request})
        return Response({'message': f"Film choisi : {film.title} !", 'group': serializer.data})
