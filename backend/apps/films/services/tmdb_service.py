import requests
import time
import logging
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

CACHE_TTL = 86400  # 24h


class TMDbService:
    """Service d'accès à l'API The Movie Database."""

    BASE_URL = settings.TMDB_BASE_URL
    IMAGE_BASE_URL = settings.TMDB_IMAGE_BASE_URL
    RATE_LIMIT_DELAY = 0.25  # 40 req/10s → 1 req/0.25s

    def __init__(self):
        self.api_key = settings.TMDB_API_KEY
        if not self.api_key:
            raise ValueError("TMDB_API_KEY non configurée dans .env")
        self.session = requests.Session()
        self.session.params = {'api_key': self.api_key, 'language': 'fr-BE'}

    def _get(self, endpoint, params=None, cache_key=None, cache_ttl=CACHE_TTL):
        if cache_key:
            cached = cache.get(cache_key)
            if cached:
                return cached

        time.sleep(self.RATE_LIMIT_DELAY)
        url = f"{self.BASE_URL}{endpoint}"
        try:
            resp = self.session.get(url, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            if cache_key:
                cache.set(cache_key, data, cache_ttl)
            return data
        except requests.RequestException as e:
            logger.error(f"TMDb API error [{endpoint}]: {e}")
            return None

    def get_now_playing(self, region='BE', page=1):
        """Films actuellement en salle en Belgique."""
        cache_key = f'tmdb_now_playing_{region}_p{page}'
        return self._get(
            '/movie/now_playing',
            params={'region': region, 'page': page},
            cache_key=cache_key,
        )

    def get_movie_details(self, tmdb_id):
        """Détails complets d'un film (avec videos)."""
        cache_key = f'tmdb_movie_{tmdb_id}'
        return self._get(
            f'/movie/{tmdb_id}',
            params={'append_to_response': 'videos,credits'},
            cache_key=cache_key,
        )

    def get_genres(self):
        """Liste des genres TMDb."""
        cache_key = 'tmdb_genres'
        return self._get('/genre/movie/list', cache_key=cache_key, cache_ttl=604800)  # 7j

    def sync_now_playing_movies(self, region='BE'):
        """Synchronise les films en salle depuis TMDb."""
        from apps.films.models import Film, Genre

        logger.info(f"[TMDb] Synchronisation films en salle (region={region})")
        synced_count = 0

        # Sync genres d'abord
        genres_data = self.get_genres()
        if genres_data:
            for g in genres_data.get('genres', []):
                Genre.objects.update_or_create(
                    tmdb_id=g['id'],
                    defaults={'nom': g['name']},
                )

        # Récupérer toutes les pages de films
        page = 1
        while True:
            data = self.get_now_playing(region=region, page=page)
            if not data or not data.get('results'):
                break

            for movie_data in data['results']:
                film = self._upsert_film(movie_data)
                if film:
                    synced_count += 1

            if page >= data.get('total_pages', 1) or page >= 5:  # max 5 pages
                break
            page += 1

        # Marquer les films qui ne sont plus en salle
        tmdb_ids_now_playing = self._get_all_now_playing_ids(region)
        Film.objects.exclude(tmdb_id__in=tmdb_ids_now_playing).update(is_now_playing=False)

        logger.info(f"[TMDb] {synced_count} films synchronisés")
        return synced_count

    def _upsert_film(self, movie_data):
        """Crée ou met à jour un film depuis les données TMDb."""
        from apps.films.models import Film, Genre

        tmdb_id = movie_data.get('id')
        if not tmdb_id:
            return None

        # Récupérer la clé YouTube du trailer
        trailer_key = ''
        details = self.get_movie_details(tmdb_id)
        if details:
            videos = details.get('videos', {}).get('results', [])
            trailers = [v for v in videos if v.get('type') == 'Trailer' and v.get('site') == 'YouTube']
            if trailers:
                trailer_key = trailers[0]['key']

        poster_path = movie_data.get('poster_path', '')
        backdrop_path = movie_data.get('backdrop_path', '')

        film, _ = Film.objects.update_or_create(
            tmdb_id=tmdb_id,
            defaults={
                'titre': movie_data.get('title', ''),
                'titre_original': movie_data.get('original_title', ''),
                'synopsis': movie_data.get('overview', ''),
                'poster': f"{self.IMAGE_BASE_URL}{poster_path}" if poster_path else '',
                'backdrop': f"{self.IMAGE_BASE_URL}{backdrop_path}" if backdrop_path else '',
                'trailer_youtube_key': trailer_key,
                'duree': details.get('runtime') if details else None,
                'date_sortie': movie_data.get('release_date') or None,
                'note': movie_data.get('vote_average'),
                'vote_count': movie_data.get('vote_count', 0),
                'is_now_playing': True,
            },
        )

        # Genres
        genre_ids = movie_data.get('genre_ids', [])
        genres = Genre.objects.filter(tmdb_id__in=genre_ids)
        film.genres.set(genres)

        return film

    def _get_all_now_playing_ids(self, region='BE'):
        ids = []
        page = 1
        while page <= 10:
            data = self.get_now_playing(region=region, page=page)
            if not data or not data.get('results'):
                break
            ids.extend([m['id'] for m in data['results']])
            if page >= data.get('total_pages', 1):
                break
            page += 1
        return ids
