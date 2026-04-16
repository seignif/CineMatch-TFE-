"""US-035 : Recommandations de films personnalisées."""

MOOD_GENRE_BOOST = {
    'rire': ['Comédie', 'Animation', 'Famille'],
    'reflechir': ['Drame', 'Documentaire', 'Histoire'],
    'emu': ['Drame', 'Romance', 'Animation'],
    'adrenaline': ['Action', 'Thriller', 'Horreur', 'Science-fiction'],
}


class RecommendationService:

    def get_recommendations(self, user, limit: int = 5) -> list:
        from apps.films.models import Film

        try:
            profile = user.profile
        except Exception:
            return list(Film.objects.exclude(
                kinepolis_id__startswith='tmdb_'
            ).filter(poster_url__gt='').order_by('-tmdb_rating')[:limit])

        genre_prefs = profile.genre_preferences or {}
        mood = profile.mood or ''
        signature_ids = set(profile.films_signature.values_list('id', flat=True))

        films = (
            Film.objects
            .exclude(kinepolis_id__startswith='tmdb_')
            .filter(poster_url__gt='')
            .exclude(id__in=signature_ids)
            .prefetch_related('genres')
        )

        mood_genres = MOOD_GENRE_BOOST.get(mood, [])
        scored = []

        for film in films:
            score = 0.0
            reasons = []
            film_genre_names = [g.name for g in film.genres.all()]

            for genre_name in film_genre_names:
                pref = genre_prefs.get(genre_name, 0)
                if pref > 0:
                    score += pref * 5
                    if pref >= 7 and f"Vous adorez {genre_name}" not in reasons:
                        reasons.append(f"Vous adorez {genre_name}")

            for genre_name in film_genre_names:
                if genre_name in mood_genres:
                    score += 20
                    if 'Parfait pour votre mood du moment' not in reasons:
                        reasons.append('Parfait pour votre mood du moment')
                    break

            if film.tmdb_rating:
                score += float(film.tmdb_rating) * 3

            if score > 0:
                scored.append((film, score, reasons[:2]))

        scored.sort(key=lambda x: x[1], reverse=True)
        return [
            {'film': f, 'score': round(s, 1), 'reasons': r}
            for f, s, r in scored[:limit]
        ]
