import json
import logging
import os
import subprocess
import sys

from django.core.cache import cache
from django.utils.dateparse import parse_datetime

logger = logging.getLogger(__name__)

_SCRAPER_SCRIPT = os.path.join(os.path.dirname(__file__), "_kinepolis_scraper.py")

CDN_BASE = "https://cdn.kinepolis.be"
BOOKING_BASE = "https://kinepolis.be/fr/direct-vista-redirect"


class KinepolisService:
    KINEPOLIS_URL = "https://kinepolis.be/fr/"
    CACHE_KEY = "kinepolis_drupal_data"
    CACHE_TTL = 60 * 60 * 3  # 3 heures

    # ------------------------------------------------------------------
    # Fetch
    # ------------------------------------------------------------------

    def fetch_data(self):
        """Récupère Drupal.settings.variables depuis kinepolis.be (cache Redis 3h)."""
        cached = cache.get(self.CACHE_KEY)
        if cached:
            logger.info("[Kinepolis] Donnees chargees depuis le cache Redis")
            return cached

        logger.info("[Kinepolis] Scraping kinepolis.be...")
        data = self._scrape()
        cache.set(self.CACHE_KEY, data, self.CACHE_TTL)
        logger.info("[Kinepolis] Donnees mises en cache Redis pour 3h")
        return data

    def _scrape(self):
        # Run Playwright in a separate process to avoid asyncio/Windows conflicts
        # on Python 3.13 (NotImplementedError: _make_subprocess_transport).
        result = subprocess.run(
            [sys.executable, _SCRAPER_SCRIPT],
            capture_output=True,
            timeout=120,
        )
        if result.returncode != 0:
            logger.error(f"[Kinepolis] Scraper failed:\n{result.stderr.decode('utf-8', errors='replace')}")
            raise RuntimeError(
                f"Kinepolis scraper exited with code {result.returncode}: "
                f"{result.stderr.decode('utf-8', errors='replace')}"
            )
        return json.loads(result.stdout.decode('utf-8'))

    # ------------------------------------------------------------------
    # Sync cinemas
    # ------------------------------------------------------------------

    def sync_cinemas(self, data=None):
        """Upsert Cinema depuis data['complexes']."""
        from apps.films.models import Cinema

        if data is None:
            data = self.fetch_data()

        count = 0
        for cx in data.get("complexes", []):
            Cinema.objects.update_or_create(
                kinepolis_id=cx["id"],
                defaults={
                    "name": cx["name"],
                    "country": cx.get("country", "BE"),
                    "language": cx.get("defaultLanguage", "FR"),
                    "is_active": cx.get("isActive", True) and not cx.get("inMaintenance", False),
                },
            )
            count += 1

        logger.info(f"[Kinepolis] {count} cinemas synchronises")
        return count

    # ------------------------------------------------------------------
    # Sync films + sessions
    # ------------------------------------------------------------------

    def sync_films_and_sessions(self, data=None):
        """Upsert Films et Seances depuis current_movies et future_movies."""
        if data is None:
            data = self.fetch_data()

        cdn_base = data.get("movieservice_image_url", CDN_BASE).rstrip("/")

        # Dédupliquer les films (current + future)
        all_films = {}
        for section in ("current_movies", "future_movies"):
            for film_data in data.get(section, {}).get("films", []):
                all_films[film_data["id"]] = film_data

        films_count = sum(self._sync_film(fd, cdn_base) for fd in all_films.values())

        # Retirer les films qui ne sont plus dans le feed Kinepolis
        from apps.films.models import Film
        retired = Film.objects.exclude(
            kinepolis_id__startswith='tmdb_'
        ).exclude(
            kinepolis_id__in=set(all_films.keys())
        ).update(is_future=True)
        if retired:
            logger.info(f"[Kinepolis] {retired} films retires de l'affiche (plus dans le feed)")

        # Sessions (current + future)
        all_sessions = []
        for section in ("current_movies", "future_movies"):
            all_sessions.extend(data.get(section, {}).get("sessions", []))

        sessions_count = sum(self._sync_session(sd) for sd in all_sessions)

        logger.info(f"[Kinepolis] {films_count} films, {sessions_count} seances synchronises")
        return films_count, sessions_count

    def _sync_film(self, film_data, cdn_base):
        from apps.films.models import Film, Genre

        film_id = film_data["id"]

        # Images
        poster_url = ""
        backdrop_url = ""
        for img in film_data.get("images", []):
            media_type = img.get("mediaType", "")
            if media_type == "Poster Graphic" and not poster_url:
                poster_url = cdn_base + img["url"]
            elif media_type == "Backdrop" and not backdrop_url:
                backdrop_url = cdn_base + img["url"]

        # Date de sortie (naive → aware)
        release_date = None
        raw_date = film_data.get("releaseDate")
        if raw_date:
            from django.utils import timezone as tz
            dt = parse_datetime(raw_date)
            if dt is not None and tz.is_naive(dt):
                dt = tz.make_aware(dt)
            release_date = dt

        existing = Film.objects.filter(kinepolis_id=film_id).only('poster_url', 'backdrop_url').first()
        # Ne pas ecraser les posters/backdrops deja enrichis par TMDb
        final_poster = poster_url if not (existing and existing.poster_url) else existing.poster_url
        final_backdrop = backdrop_url if not (existing and existing.backdrop_url) else existing.backdrop_url

        film, _ = Film.objects.update_or_create(
            kinepolis_id=film_id,
            defaults={
                "corporate_id": film_data.get("corporateId"),
                "imdb_code": film_data.get("imdbCode", ""),
                "title": film_data.get("title") or film_data.get("name", ""),
                "synopsis": film_data.get("synopsis", ""),
                "short_synopsis": film_data.get("shortSynopsis", ""),
                "duration": film_data.get("duration"),
                "release_date": release_date,
                "language": film_data.get("language", "FR"),
                "audio_language": film_data.get("audioLanguage", ""),
                "is_future": film_data.get("showAsFutureRelease", False),
                "poster_url": final_poster,
                "backdrop_url": final_backdrop,
            },
        )

        # Genres
        for genre_data in film_data.get("genres", []):
            genre, _ = Genre.objects.get_or_create(
                name=genre_data["name"],
                defaults={"tmdb_id": None},
            )
            film.genres.add(genre)

        return 1

    def _sync_session(self, session_data):
        from apps.films.models import Cinema, Film, Seance

        session_id = session_data["id"]
        film_kinepolis_id = session_data["film"]["id"]
        complex_id = session_data["complexOperator"]

        try:
            film = Film.objects.get(kinepolis_id=film_kinepolis_id)
            cinema = Cinema.objects.get(kinepolis_id=complex_id)
        except (Film.DoesNotExist, Cinema.DoesNotExist):
            logger.debug(f"[Kinepolis] Session {session_id} ignoree (film/cinema inconnu)")
            return 0

        showtime = parse_datetime(session_data["showtime"])

        vista_id = session_data.get("vistaSessionId")
        booking_url = f"{BOOKING_BASE}/{vista_id}/0/{complex_id}/0" if vista_id else ""

        Seance.objects.update_or_create(
            kinepolis_session_id=session_id,
            defaults={
                "film": film,
                "cinema": cinema,
                "showtime": showtime,
                "language": session_data.get("language", "FR"),
                "hall": session_data.get("hall"),
                "vista_session_id": vista_id,
                "is_sold_out": session_data.get("isSoldOut", False),
                "has_cosy_seating": session_data.get("hasCosySeating", False),
                "booking_url": booking_url,
                "raw_attributes": (session_data.get("rawSessionAttributes") or "")[:100],
            },
        )
        return 1

    # ------------------------------------------------------------------
    # Sync all
    # ------------------------------------------------------------------

    def sync_all(self):
        """Synchronise cinémas, films et séances en une seule passe."""
        data = self.fetch_data()
        cinemas_count = self.sync_cinemas(data)
        films_count, sessions_count = self.sync_films_and_sessions(data)
        return {
            "cinemas": cinemas_count,
            "films": films_count,
            "sessions": sessions_count,
        }
