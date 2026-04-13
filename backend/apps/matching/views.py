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
from .models import Swipe, Match, PlannedOuting
from .serializers import (
    CandidateSerializer, MatchSerializer, SwipeSerializer,
    PlannedOutingSerializer,
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

        candidates = (
            User.objects.exclude(id__in=exclude_ids)
            .select_related('profile')
            .prefetch_related('profile__films_signature')
            [:20]
        )

        results = []
        for candidate in candidates:
            score, reasons = algorithm.calculate_compatibility(user, candidate)
            results.append({
                'candidate': candidate,
                'score': score,
                'reasons': reasons,
            })

        results.sort(key=lambda x: x['score'], reverse=True)

        serialized = []
        for item in results:
            c = item['candidate']
            c.score = item['score']
            c.reasons = item['reasons']
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
