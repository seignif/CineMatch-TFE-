import math
import logging

logger = logging.getLogger(__name__)

MOOD_LABELS = {
    'rire': 'Envie de rire',
    'reflechir': 'Besoin de réfléchir',
    'emu': "Envie d'être ému",
    'adrenaline': "Besoin d'adrénaline",
}


class MatchingAlgorithm:
    """
    Score de compatibilité = 40% genres + 30% films + 20% ville + 10% mood
    """

    def calculate_compatibility(self, user1, user2) -> tuple[int, list[str]]:
        try:
            profile1 = user1.profile
            profile2 = user2.profile
        except Exception:
            return 0, ["Profils incomplets"]

        genre_score = self._genre_similarity(
            profile1.genre_preferences or {},
            profile2.genre_preferences or {},
        )
        film_score = self._film_similarity(
            list(profile1.films_signature.all()),
            list(profile2.films_signature.all()),
        )
        city_score = self._city_similarity(user1, user2)
        mood_score = self._mood_similarity(profile1.mood, profile2.mood)

        total = (
            genre_score * 0.40
            + film_score * 0.30
            + city_score * 0.20
            + mood_score * 0.10
        )

        reasons = self._generate_reasons(user1, user2, genre_score, film_score, mood_score)
        return int(total), reasons

    def _genre_similarity(self, prefs1: dict, prefs2: dict) -> float:
        """Cosine similarity entre les vecteurs de préférences de genres."""
        if not prefs1 or not prefs2:
            return 0.0

        all_genres = set(prefs1.keys()) | set(prefs2.keys())
        dot = sum(prefs1.get(g, 0) * prefs2.get(g, 0) for g in all_genres)
        norm1 = math.sqrt(sum(v ** 2 for v in prefs1.values()))
        norm2 = math.sqrt(sum(v ** 2 for v in prefs2.values()))

        if norm1 == 0 or norm2 == 0:
            return 0.0
        return (dot / (norm1 * norm2)) * 100

    def _film_similarity(self, films1: list, films2: list) -> float:
        """Jaccard similarity sur les films signature."""
        set1 = {f.kinepolis_id for f in films1 if f.kinepolis_id}
        set2 = {f.kinepolis_id for f in films2 if f.kinepolis_id}

        if not set1 or not set2:
            return 0.0
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        return (intersection / union) * 100 if union else 0.0

    def _city_similarity(self, user1, user2) -> float:
        """100 si même ville, 50 si les deux ont une ville différente, 25 sinon."""
        c1 = (user1.city or '').strip().lower()
        c2 = (user2.city or '').strip().lower()
        if c1 and c2:
            return 100.0 if c1 == c2 else 50.0
        return 25.0

    def _mood_similarity(self, mood1: str, mood2: str) -> float:
        if not mood1 or not mood2:
            return 50.0
        return 100.0 if mood1 == mood2 else 0.0

    def _generate_reasons(self, user1, user2, genre_score, film_score, mood_score) -> list[str]:
        reasons = []
        p1 = user1.profile
        p2 = user2.profile

        if genre_score >= 70:
            prefs1 = p1.genre_preferences or {}
            prefs2 = p2.genre_preferences or {}
            common = [g for g in prefs1 if g in prefs2]
            if common:
                reasons.append(f"Genres en commun : {', '.join(common[:3])}")

        if film_score >= 30:
            films1 = {f.title for f in p1.films_signature.all()}
            films2 = {f.title for f in p2.films_signature.all()}
            common_films = list(films1 & films2)[:2]
            if common_films:
                reasons.append(f"Films en commun : {', '.join(common_films)}")

        if mood_score == 100 and p1.mood:
            label = MOOD_LABELS.get(p1.mood, p1.mood)
            reasons.append(f"Même envie du moment : {label}")

        c1 = (user1.city or '').strip()
        c2 = (user2.city or '').strip()
        if c1 and c1.lower() == (c2 or '').lower():
            reasons.append(f"Même ville : {c1}")

        if not reasons:
            reasons.append("Profils complémentaires")

        return reasons
