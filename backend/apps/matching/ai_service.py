import logging
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

MOOD_LABELS = {
    'rire': 'Envie de rire',
    'reflechir': 'Besoin de réfléchir',
    'emu': "Envie d'être ému",
    'adrenaline': "Besoin d'adrénaline",
}


class MatchingAIService:
    """
    Génère des raisons de compatibilité personnalisées via l'API Claude.
    Résultats mis en cache 24h dans Redis pour minimiser les appels API.
    """

    CACHE_TTL = 86400  # 24h

    def generate_match_content(self, user1, user2, score: int, algorithmic_reasons: list) -> tuple:
        cache_key = f"ai_match_{min(user1.id, user2.id)}_{max(user1.id, user2.id)}"
        cached = cache.get(cache_key)
        if cached:
            return cached['reasons'], cached['message']

        try:
            result = self._call_claude(user1, user2, score, algorithmic_reasons)
            cache.set(cache_key, result, self.CACHE_TTL)
            return result['reasons'], result['message']
        except Exception as e:
            logger.warning(f"Claude API error for match {user1.id}/{user2.id}: {e}")
            return algorithmic_reasons, self._fallback_message(user1, score)

    def _call_claude(self, user1, user2, score: int, reasons: list) -> dict:
        import anthropic

        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        prompt = self._build_prompt(user1, user2, score, reasons)

        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}],
        )

        text = message.content[0].text.strip()
        return self._parse_response(text, reasons)

    def _build_prompt(self, user1, user2, score: int, reasons: list) -> str:
        p1 = user1.profile
        p2 = user2.profile

        genres1 = list((p1.genre_preferences or {}).keys())[:5]
        genres2 = list((p2.genre_preferences or {}).keys())[:5]
        mood1 = MOOD_LABELS.get(p1.mood or '', '')
        mood2 = MOOD_LABELS.get(p2.mood or '', '')
        city1 = user1.city or 'non précisée'
        city2 = user2.city or 'non précisée'

        return (
            "Tu es un assistant pour CineMatch, une app de rencontres pour cinéphiles belges.\n"
            "Génère du contenu de compatibilité entre deux utilisateurs.\n\n"
            f"Utilisateur A : prénom {user1.first_name}, ville {city1}, "
            f"humeur: {mood1 or 'non précisée'}, genres préférés: {', '.join(genres1) or 'non précisés'}\n"
            f"Utilisateur B : prénom {user2.first_name}, ville {city2}, "
            f"humeur: {mood2 or 'non précisée'}, genres préférés: {', '.join(genres2) or 'non précisés'}\n\n"
            f"Score de compatibilité algorithmique : {score}/100\n"
            f"Raisons calculées : {', '.join(reasons)}\n\n"
            "Génère EXACTEMENT ce format JSON (pas de markdown, juste le JSON) :\n"
            '{\n'
            '  "reasons": ["raison courte 1", "raison courte 2", "raison courte 3"],\n'
            f'  "message": "Un message chaleureux de 1-2 phrases pour encourager {user1.first_name} à rencontrer {user2.first_name} au cinéma."\n'
            '}\n\n'
            "Les raisons doivent être spécifiques aux goûts communs et en français."
        )

    def _parse_response(self, text: str, fallback_reasons: list) -> dict:
        import json
        import re

        try:
            data = json.loads(text)
            return {
                'reasons': data.get('reasons', fallback_reasons)[:4],
                'message': data.get('message', ''),
            }
        except json.JSONDecodeError:
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group())
                    return {
                        'reasons': data.get('reasons', fallback_reasons)[:4],
                        'message': data.get('message', ''),
                    }
                except json.JSONDecodeError:
                    pass
            return {'reasons': fallback_reasons, 'message': ''}

    def _fallback_message(self, user, score: int) -> str:
        if score >= 80:
            return f"Excellente compatibilité ! Vous semblez avoir beaucoup en commun, {user.first_name}."
        if score >= 60:
            return f"Bonne compatibilité, {user.first_name} ! Ça vaut le coup de se rencontrer."
        return f"Pourquoi ne pas tenter l'expérience, {user.first_name} ?"
