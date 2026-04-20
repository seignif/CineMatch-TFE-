"""US-035 : Recommandations de films personnalisées."""
from collections import defaultdict

MOOD_GENRE_BOOST = {
    'rire':       ['Comédie', 'Animation', 'Famille'],
    'reflechir':  ['Drame', 'Documentaire', 'Histoire'],
    'emu':        ['Drame', 'Romance', 'Animation'],
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

        genre_prefs  = profile.genre_preferences or {}
        mood         = profile.mood or ''
        mood_genres  = MOOD_GENRE_BOOST.get(mood, [])

        # Genres des films signature → poids supplémentaire
        signature_films   = list(profile.films_signature.prefetch_related('genres').all())
        signature_ids     = {f.id for f in signature_films}
        signature_genre_weights: dict[str, float] = defaultdict(float)
        signature_genre_to_film: dict[str, str]   = {}
        for sig_film in signature_films:
            for genre in sig_film.genres.all():
                signature_genre_weights[genre.name] += 10
                if genre.name not in signature_genre_to_film:
                    signature_genre_to_film[genre.name] = sig_film.title

        films = (
            Film.objects
            .exclude(kinepolis_id__startswith='tmdb_')
            .filter(poster_url__gt='', is_future=False)
            .exclude(id__in=signature_ids)
            .prefetch_related('genres')
        )

        scored = []

        for film in films:
            score   = 0.0
            reasons = []
            film_genre_names = [g.name for g in film.genres.all()]

            # 1. Genres préférés
            for genre_name in film_genre_names:
                pref = genre_prefs.get(genre_name, 0)
                if pref > 0:
                    score += pref * 5
                    if pref >= 7 and len(reasons) < 2 and f"Vous adorez {genre_name}" not in reasons:
                        reasons.append(f"Vous adorez {genre_name}")

            # 2. Similarité avec films signature
            matched_sig = None
            for genre_name in film_genre_names:
                w = signature_genre_weights.get(genre_name, 0)
                if w > 0:
                    score += w
                    if not matched_sig and genre_name in signature_genre_to_film:
                        matched_sig = signature_genre_to_film[genre_name]
            if matched_sig:
                reasons.insert(0, f"Similaire à {matched_sig}")

            # 3. Mood du moment
            for genre_name in film_genre_names:
                if genre_name in mood_genres:
                    score += 20
                    if 'Correspond à votre mood' not in reasons and len(reasons) < 2:
                        reasons.append('Correspond à votre mood')
                    break

            # 4. Note TMDb
            if film.tmdb_rating:
                score += float(film.tmdb_rating) * 3

            if score > 0:
                scored.append((film, score, reasons[:2]))

        scored.sort(key=lambda x: x[1], reverse=True)
        return [
            {'film': f, 'score': round(s, 1), 'reasons': r or ['Populaire en ce moment']}
            for f, s, r in scored[:limit]
        ]
