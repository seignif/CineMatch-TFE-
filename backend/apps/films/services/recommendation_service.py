"""US-035 : Recommandations de films personnalisées."""
from collections import defaultdict
from django.utils import timezone

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

        # Normaliser les clés en minuscules pour éviter les mismatches de casse
        raw_prefs    = profile.genre_preferences or {}
        genre_prefs  = {k.lower(): v for k, v in raw_prefs.items()}
        mood         = profile.mood or ''
        mood_genres  = [g.lower() for g in MOOD_GENRE_BOOST.get(mood, [])]

        # Genres des films signature → poids supplémentaire
        signature_films   = list(profile.films_signature.prefetch_related('genres').all())
        signature_ids     = {f.id for f in signature_films}
        # Précomputer les genres de chaque film signature (déjà prefetch → pas de requête)
        signature_film_genres: dict[int, set[str]] = {
            sig.id: {g.name for g in sig.genres.all()}
            for sig in signature_films
        }
        signature_genre_weights: dict[str, float] = defaultdict(float)
        for genres in signature_film_genres.values():
            for genre_name in genres:
                signature_genre_weights[genre_name] += 10

        films = (
            Film.objects
            .exclude(kinepolis_id__startswith='tmdb_')
            .filter(
                poster_url__gt='',
                is_future=False,
                seances__showtime__gte=timezone.now(),  # uniquement films avec séances à venir
            )
            .exclude(id__in=signature_ids)
            .prefetch_related('genres')
            .distinct()
        )

        scored = []

        for film in films:
            score   = 0.0
            reasons = []
            film_genre_names = [g.name for g in film.genres.all()]

            # 1. Genres préférés (comparaison insensible à la casse)
            for genre_name in film_genre_names:
                pref = genre_prefs.get(genre_name.lower(), 0)
                if pref > 0:
                    score += pref * 5
                    if pref >= 7 and len(reasons) < 2 and f"Vous adorez {genre_name}" not in reasons:
                        reasons.append(f"Vous adorez {genre_name}")

            # 2. Similarité avec films signature
            film_genre_set = set(film_genre_names)
            best_sig_title: str | None = None
            best_sig_overlap = 0
            for sig_film in signature_films:
                overlap = film_genre_set & signature_film_genres[sig_film.id]
                if overlap:
                    score += len(overlap) * 10
                    if len(overlap) > best_sig_overlap:
                        best_sig_overlap = len(overlap)
                        best_sig_title = sig_film.title
            if best_sig_title:
                reasons.insert(0, f"Similaire à {best_sig_title}")

            # 3. Mood du moment (insensible à la casse)
            for genre_name in film_genre_names:
                if genre_name.lower() in mood_genres:
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

        # Dédupliquer : une seule version par film (même corporate_id)
        seen_corporate: set[int] = set()
        deduped = []
        for film, score, reasons in scored:
            if film.corporate_id and film.corporate_id in seen_corporate:
                continue
            if film.corporate_id:
                seen_corporate.add(film.corporate_id)
            deduped.append((film, score, reasons))
            if len(deduped) >= limit:
                break

        return [
            {'film': f, 'score': round(s, 1), 'reasons': r or ['Populaire en ce moment']}
            for f, s, r in deduped
        ]
