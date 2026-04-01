import logging
from django.db.models import Q
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.models import User
from .algorithm import MatchingAlgorithm
from .ai_service import MatchingAIService
from .models import Swipe, Match
from .serializers import CandidateSerializer, MatchSerializer, SwipeSerializer

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
