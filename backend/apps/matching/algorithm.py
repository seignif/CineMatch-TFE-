"""
Algorithme de matching CineMatch — Sprint 7
Score = 35% genres + 25% films + 15% mood + 15% distance géo + 10% VF/VO
"""
import math
import logging
from datetime import date

logger = logging.getLogger(__name__)

MOOD_LABELS = {
    'rire': 'Envie de rire',
    'reflechir': 'Besoin de réfléchir',
    'emu': "Envie d'être ému",
    'adrenaline': "Besoin d'adrénaline",
}


class MatchingAlgorithm:

    def calculate_compatibility(self, user1, user2) -> tuple[int, list[str]]:
        try:
            p1 = user1.profile
            p2 = user2.profile
        except Exception:
            return 0, ["Profils incomplets"]

        genre_score = self._genre_similarity(
            p1.genre_preferences or {}, p2.genre_preferences or {}
        )
        film_score = self._film_similarity(
            list(p1.films_signature.all()), list(p2.films_signature.all())
        )
        mood_score = self._mood_similarity(p1.mood, p2.mood)
        dist_score = self._distance_score(user1, user2)
        lang_score = self._language_score(p1, p2)

        total = int(
            genre_score * 0.35
            + film_score * 0.25
            + mood_score * 0.15
            + dist_score * 0.15
            + lang_score * 0.10
        )

        reasons = self._generate_reasons(
            user1, user2, genre_score, film_score, mood_score, dist_score, lang_score
        )
        return min(total, 100), reasons

    # ------------------------------------------------------------------
    # Scores individuels
    # ------------------------------------------------------------------

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
        return (len(set1 & set2) / len(set1 | set2)) * 100

    def _mood_similarity(self, mood1: str, mood2: str) -> float:
        if not mood1 or not mood2:
            return 50.0
        if mood1 == mood2:
            return 100.0
        compatible = {
            'rire': ['adrenaline'],
            'reflechir': ['emu'],
            'emu': ['reflechir'],
            'adrenaline': ['rire'],
        }
        return 30.0 if mood2 in compatible.get(mood1, []) else 0.0

    def _distance_score(self, user1, user2) -> float:
        """
        Haversine si lat/lng disponibles, sinon fallback ville.
        0km→100 / 0-5km→90 / 5-15km→70 / 15-30km→40 / 30-50km→20 / +50km→0
        """
        try:
            p1, p2 = user1.profile, user2.profile

            if all([p1.latitude, p1.longitude, p2.latitude, p2.longitude]):
                dist = self._haversine(
                    float(p1.latitude), float(p1.longitude),
                    float(p2.latitude), float(p2.longitude),
                )
                if dist == 0:
                    return 100.0
                if dist <= 5:
                    return 90.0
                if dist <= 15:
                    return 70.0
                if dist <= 30:
                    return 40.0
                if dist <= 50:
                    return 20.0
                return 0.0

            # Fallback : ville
            c1 = (user1.city or '').strip().lower()
            c2 = (user2.city or '').strip().lower()
            if not c1 or not c2:
                return 50.0
            return 100.0 if c1 == c2 else 20.0

        except Exception:
            return 50.0

    def get_distance_km(self, user1, user2) -> float | None:
        """Retourne la distance en km entre deux utilisateurs, ou None si indisponible."""
        try:
            p1, p2 = user1.profile, user2.profile
            if all([p1.latitude, p1.longitude, p2.latitude, p2.longitude]):
                return round(self._haversine(
                    float(p1.latitude), float(p1.longitude),
                    float(p2.latitude), float(p2.longitude),
                ), 1)
        except Exception:
            pass
        return None

    def _haversine(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Distance en km entre deux coordonnées GPS."""
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat / 2) ** 2
             + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
             * math.sin(dlon / 2) ** 2)
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    def _language_score(self, profile1, profile2) -> float:
        """
        Même préférence (VF/VF ou VO/VO) → 100
        Un des deux = both → 60
        Opposés (VF vs VO) → 20
        """
        lang1 = getattr(profile1, 'language_preference', 'both') or 'both'
        lang2 = getattr(profile2, 'language_preference', 'both') or 'both'
        if lang1 == lang2:
            return 100.0 if lang1 != 'both' else 60.0
        if lang1 == 'both' or lang2 == 'both':
            return 60.0
        return 20.0

    # ------------------------------------------------------------------
    # Raisons lisibles
    # ------------------------------------------------------------------

    def _generate_reasons(self, user1, user2,
                          genre_score, film_score, mood_score,
                          dist_score, lang_score) -> list[str]:
        reasons = []
        p1 = user1.profile
        p2 = user2.profile

        if genre_score >= 70:
            prefs1 = p1.genre_preferences or {}
            prefs2 = p2.genre_preferences or {}
            common = [g for g in prefs1 if g in prefs2 and prefs1[g] >= 7 and prefs2[g] >= 7]
            if common:
                reasons.append(f"Genres en commun : {', '.join(common[:3])}")

        if film_score >= 30:
            films1 = {f.title for f in p1.films_signature.all()}
            films2 = {f.title for f in p2.films_signature.all()}
            common_films = list(films1 & films2)[:2]
            if common_films:
                reasons.append(f"Films en commun : {', '.join(common_films)}")

        if mood_score == 100 and p1.mood:
            reasons.append(f"Même envie du moment : {MOOD_LABELS.get(p1.mood, p1.mood)}")

        if dist_score >= 90:
            reasons.append("Très proches géographiquement")
        elif dist_score >= 70:
            reasons.append("Même secteur géographique")
        elif dist_score == 100:
            c1 = (user1.city or '').strip()
            reasons.append(f"Même ville : {c1}")

        if lang_score == 100:
            labels = {'vf': 'VF', 'vo': 'VO'}
            lang = getattr(p1, 'language_preference', 'both')
            if lang in labels:
                reasons.append(f"Même préférence de langue : {labels[lang]}")

        return reasons or ["Profils complémentaires"]

    # ------------------------------------------------------------------
    # Alias de rétrocompatibilité (tests existants)
    # ------------------------------------------------------------------

    def calculate_genre_similarity(self, prefs1: dict, prefs2: dict) -> float:
        return self._genre_similarity(prefs1, prefs2)

    def calculate_film_similarity(self, films1: list, films2: list) -> float:
        return self._film_similarity(films1, films2)

    def calculate_availability_overlap(self, user1, user2) -> float:
        return 50.0

    def generate_compatibility_reasons(self, user1, user2, genre_score, film_score, mood_score) -> list[str]:
        return self._generate_reasons(user1, user2, genre_score, film_score, mood_score, 50, 60)
