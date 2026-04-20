import logging
import time

import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

CACHE_TTL = 86400  # 24h
IMAGE_SIZE_POSTER = 'w500'
IMAGE_SIZE_BACKDROP = 'w1280'


class TMDbService:
    """
    Service d'enrichissement des films Kinepolis via l'API TMDb.
    Stratégie : cherche d'abord via IMDb code, puis via titre.
    """

    RATE_LIMIT_DELAY = 0.28  # ~40 req/10s

    def __init__(self):
        self.api_key = settings.TMDB_API_KEY
        if not self.api_key:
            raise ValueError("TMDB_API_KEY non configurée dans .env")
        self.base_url = settings.TMDB_BASE_URL
        self.image_base_url = settings.TMDB_IMAGE_BASE_URL
        self.session = requests.Session()
        self.session.params = {'api_key': self.api_key, 'language': 'fr-BE'}

    # ------------------------------------------------------------------
    # HTTP helpers
    # ------------------------------------------------------------------

    def _get(self, endpoint, extra_params=None, cache_key=None):
        if cache_key:
            cached = cache.get(cache_key)
            if cached is not None:
                return cached

        time.sleep(self.RATE_LIMIT_DELAY)
        try:
            resp = self.session.get(
                f"{self.base_url}{endpoint}",
                params=extra_params or {},
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            if cache_key:
                cache.set(cache_key, data, CACHE_TTL)
            return data
        except requests.RequestException as e:
            logger.error(f"[TMDb] Erreur {endpoint}: {e}")
            return None

    # ------------------------------------------------------------------
    # Lookup methods
    # ------------------------------------------------------------------

    def find_by_imdb(self, imdb_code: str):
        """Cherche un film TMDb via son code IMDb (ex: 'tt1234567')."""
        cache_key = f'tmdb_find_imdb_{imdb_code}'
        data = self._get(
            f'/find/{imdb_code}',
            extra_params={'external_source': 'imdb_id'},
            cache_key=cache_key,
        )
        if data and data.get('movie_results'):
            return data['movie_results'][0]
        return None

    def search_by_title(self, title: str, year=None):
        """Cherche un film TMDb par titre (retourne le premier résultat)."""
        params = {'query': title}
        if year:
            params['year'] = year
        cache_key = f'tmdb_search_{title}_{year}'
        data = self._get('/search/movie', extra_params=params, cache_key=cache_key)
        if data and data.get('results'):
            return data['results'][0]
        return None

    def get_details(self, tmdb_id: int):
        """Récupère les détails complets + videos d'un film TMDb."""
        cache_key = f'tmdb_details_{tmdb_id}'
        return self._get(
            f'/movie/{tmdb_id}',
            extra_params={'append_to_response': 'videos'},
            cache_key=cache_key,
        )

    # ------------------------------------------------------------------
    # Image URL helpers
    # ------------------------------------------------------------------

    def _build_image_url(self, path: str, size: str) -> str:
        if not path:
            return ''
        base = self.image_base_url.rstrip('/')
        # Replace any size suffix with the desired one
        import re
        base = re.sub(r'/w\d+$|/original$', f'/{size}', base)
        return f"{base}{path}"

    def make_poster_url(self, path: str) -> str:
        return self._build_image_url(path, IMAGE_SIZE_POSTER)

    def make_backdrop_url(self, path: str) -> str:
        return self._build_image_url(path, IMAGE_SIZE_BACKDROP)

    # ------------------------------------------------------------------
    # Trailer extraction
    # ------------------------------------------------------------------

    def _extract_trailer_key(self, details: dict) -> str:
        videos = details.get('videos', {}).get('results', [])
        # Prefer FR trailer, then any language
        for lang in ('fr', None):
            for v in videos:
                if v.get('type') == 'Trailer' and v.get('site') == 'YouTube':
                    if lang is None or v.get('iso_639_1') == lang:
                        return v['key']
        return ''

    # ------------------------------------------------------------------
    # Genre sync
    # ------------------------------------------------------------------

    def sync_genres(self) -> int:
        """Synchronise les genres TMDb vers la base de données."""
        from apps.films.models import Genre

        data = self._get('/genre/movie/list', cache_key='tmdb_genres_list')
        if not data:
            return 0
        count = 0
        for g in data.get('genres', []):
            # Lookup par nom (les genres Kinepolis ont tmdb_id=NULL)
            obj, created = Genre.objects.get_or_create(name=g['name'])
            if obj.tmdb_id != g['id']:
                obj.tmdb_id = g['id']
                obj.save(update_fields=['tmdb_id'])
            if created:
                count += 1
        logger.info(f"[TMDb] Genres: {count} nouveaux synchronises")
        return count

    # ------------------------------------------------------------------
    # Film enrichment
    # ------------------------------------------------------------------

    def enrich_film(self, film) -> bool:
        """
        Enrichit un film Kinepolis avec les données TMDb.
        Retourne True si le film a été enrichi avec succès.
        """
        from apps.films.models import Genre

        # 1. Find TMDb entry — utilise le tmdb_id existant si disponible
        tmdb_data = None
        tmdb_id = film.tmdb_id

        if not tmdb_id:
            if film.imdb_code:
                tmdb_data = self.find_by_imdb(film.imdb_code)
            if not tmdb_data:
                year = film.release_date.year if film.release_date else None
                tmdb_data = self.search_by_title(film.title, year=year)
            if not tmdb_data:
                logger.debug(f"[TMDb] Film non trouve: {film.title}")
                return False
            tmdb_id = tmdb_data.get('id')
            if not tmdb_id:
                return False

        # 2. Get full details (with videos)
        details = self.get_details(tmdb_id)
        if not details:
            return False

        # 3. Build update dict
        poster_path = details.get('poster_path') or tmdb_data.get('poster_path', '')
        backdrop_path = details.get('backdrop_path') or tmdb_data.get('backdrop_path', '')
        vote_average = details.get('vote_average') or tmdb_data.get('vote_average')

        # Si un autre film a déjà ce tmdb_id, on n'écrase pas la clé unique
        from apps.films.models import Film as FilmModel
        tmdb_id_already_used = FilmModel.objects.filter(
            tmdb_id=tmdb_id
        ).exclude(pk=film.pk).exists()

        updates = {
            'trailer_youtube_key': self._extract_trailer_key(details),
        }
        if not tmdb_id_already_used:
            updates['tmdb_id'] = tmdb_id

        if poster_path:
            updates['poster_url'] = self.make_poster_url(poster_path)
        if backdrop_path:
            updates['backdrop_url'] = self.make_backdrop_url(backdrop_path)
        if vote_average:
            updates['tmdb_rating'] = round(float(vote_average), 1)

        # Fill synopsis if missing
        if not film.synopsis and details.get('overview'):
            updates['synopsis'] = details['overview']

        for field, value in updates.items():
            setattr(film, field, value)
        film.save(update_fields=list(updates.keys()))

        # 4. Sync genres
        tmdb_genre_ids = [g['id'] for g in details.get('genres', [])]
        if tmdb_genre_ids:
            genres = Genre.objects.filter(tmdb_id__in=tmdb_genre_ids)
            if genres.exists():
                film.genres.set(genres)

        logger.debug(f"[TMDb] Enrichi: {film.title} (tmdb_id={tmdb_id})")
        return True

    # ------------------------------------------------------------------
    # Bulk enrichment
    # ------------------------------------------------------------------

    def enrich_all(self, force: bool = False) -> dict:
        """
        Enrichit tous les films qui n'ont pas encore de tmdb_id.
        Si force=True, re-enrichit tous les films.
        """
        from apps.films.models import Film

        if force:
            qs = Film.objects.all()
        else:
            # Films sans tmdb_id OU avec tmdb_id mais sans poster (poster perdu lors d'un sync)
            from django.db.models import Q
            qs = Film.objects.filter(Q(tmdb_id__isnull=True) | Q(poster_url=''))
        total = qs.count()
        enriched = 0
        failed = 0

        logger.info(f"[TMDb] Enrichissement de {total} films (force={force})")

        for film in qs.iterator():
            try:
                if self.enrich_film(film):
                    enriched += 1
                else:
                    failed += 1
            except Exception as e:
                logger.warning(f"[TMDb] Erreur pour '{film.title}': {e}")
                failed += 1

        logger.info(
            f"[TMDb] Enrichissement termine: {enriched} reussis, "
            f"{failed} echoues sur {total}"
        )
        return {'total': total, 'enriched': enriched, 'failed': failed}
