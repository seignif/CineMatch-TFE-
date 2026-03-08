import math
import logging

logger = logging.getLogger(__name__)


class MatchingAlgorithm:
    """
    Score de compatibilité = 40% genres + 30% films + 20% dispo + 10% mood
    """

    def calculate_compatibility(self, user1, user2) -> tuple[int, list[str]]:
        genre_score = self.calculate_genre_similarity(
            user1.profile.genre_preferences,
            user2.profile.genre_preferences,
        )
        film_score = self.calculate_film_similarity(
            user1.profile.films_signature.all(),
            user2.profile.films_signature.all(),
        )
        availability_score = self.calculate_availability_overlap(user1, user2)
        mood_score = 100 if user1.profile.mood == user2.profile.mood else 0

        total = (
            genre_score * 0.40
            + film_score * 0.30
            + availability_score * 0.20
            + mood_score * 0.10
        )

        reasons = self.generate_compatibility_reasons(user1, user2, genre_score, film_score, mood_score)
        return int(total), reasons

    def calculate_genre_similarity(self, prefs1: dict, prefs2: dict) -> float:
        """Cosine similarity entre les vecteurs de préférences de genres."""
        if not prefs1 or not prefs2:
            return 0.0

        all_genres = set(prefs1.keys()) | set(prefs2.keys())
        if not all_genres:
            return 0.0

        dot_product = sum(prefs1.get(g, 0) * prefs2.get(g, 0) for g in all_genres)
        norm1 = math.sqrt(sum(v ** 2 for v in prefs1.values()))
        norm2 = math.sqrt(sum(v ** 2 for v in prefs2.values()))

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return (dot_product / (norm1 * norm2)) * 100

    def calculate_film_similarity(self, films1, films2) -> float:
        """Jaccard similarity sur les films signature."""
        set1 = {f.tmdb_id for f in films1}
        set2 = {f.tmdb_id for f in films2}

        if not set1 or not set2:
            return 0.0

        intersection = len(set1 & set2)
        union = len(set1 | set2)

        return (intersection / union) * 100 if union > 0 else 0.0

    def calculate_availability_overlap(self, user1, user2) -> float:
        """Placeholder : retourne 50 par défaut (à implémenter avec un modèle Availability)."""
        return 50.0

    def generate_compatibility_reasons(
        self, user1, user2, genre_score: float, film_score: float, mood_score: float
    ) -> list[str]:
        reasons = []

        if genre_score >= 70:
            # Trouver les genres communs les plus appréciés
            prefs1 = user1.profile.genre_preferences
            prefs2 = user2.profile.genre_preferences
            common_genres = [
                g for g in prefs1 if g in prefs2 and prefs1[g] >= 6 and prefs2[g] >= 6
            ]
            if common_genres:
                genre_str = ', '.join(common_genres[:3])
                reasons.append(f"Vous adorez tous les deux : {genre_str}")

        if film_score >= 30:
            films1 = set(f.titre for f in user1.profile.films_signature.all())
            films2 = set(f.titre for f in user2.profile.films_signature.all())
            common_films = list(films1 & films2)[:2]
            if common_films:
                reasons.append(f"Films en commun : {', '.join(common_films)}")

        if mood_score == 100 and user1.profile.mood:
            reasons.append(f"Même envie du moment : {user1.profile.mood}")

        if not reasons:
            reasons.append("Profils complémentaires")

        return reasons
