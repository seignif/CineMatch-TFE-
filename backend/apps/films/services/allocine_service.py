import logging
from django.utils import timezone

logger = logging.getLogger(__name__)


class AllocineService:
    """Service d'accès aux données AlloCiné via allocine-seances."""

    BELGIAN_CITIES = [
        'Bruxelles', 'Liège', 'Charleroi', 'Namur', 'Mons',
        'Bruges', 'Gand', 'Anvers', 'Louvain', 'Hasselt',
        'Waterloo', 'Braine-l\'Alleud', 'Ottignies', 'Wavre',
    ]

    def sync_all_belgian_cinemas(self):
        """Synchronise tous les cinémas belges depuis AlloCiné."""
        try:
            from allocine_seances import AllocineScraper
        except ImportError:
            logger.error("[AlloCiné] Package allocine-seances non installé")
            return 0

        from apps.films.models import Cinema

        synced = 0
        scraper = AllocineScraper()

        try:
            cinemas_data = scraper.get_cinemas(country='BE')
            for cinema_data in cinemas_data:
                Cinema.objects.update_or_create(
                    allocine_id=cinema_data.get('id', ''),
                    defaults={
                        'name': cinema_data.get('name', ''),
                        'address': cinema_data.get('address', ''),
                        'city': cinema_data.get('city', ''),
                        'postal_code': cinema_data.get('postal_code', ''),
                        'latitude': cinema_data.get('lat'),
                        'longitude': cinema_data.get('lng'),
                        'website': cinema_data.get('website', ''),
                        'is_active': True,
                        'last_sync': timezone.now(),
                    },
                )
                synced += 1
        except Exception as e:
            logger.error(f"[AlloCiné] Erreur sync cinémas: {e}")

        logger.info(f"[AlloCiné] {synced} cinémas synchronisés")
        return synced

    def sync_showtimes_for_all_cinemas(self, days=7):
        """Synchronise les séances pour tous les cinémas actifs."""
        try:
            from allocine_seances import AllocineScraper
        except ImportError:
            logger.error("[AlloCiné] Package allocine-seances non installé")
            return 0

        from apps.films.models import Cinema, Film, Seance
        from apps.films.services.matching_service import fuzzy_match_title

        scraper = AllocineScraper()
        synced_total = 0
        cinemas = Cinema.objects.filter(is_active=True)

        for cinema in cinemas:
            try:
                showtimes = scraper.get_showtimes(cinema_id=cinema.allocine_id, days=days)
                for showtime in showtimes:
                    # Fuzzy match du titre avec nos films TMDb
                    titre_allocine = showtime.get('movie_title', '')
                    film = self._find_matching_film(titre_allocine)

                    if not film:
                        logger.debug(f"[AlloCiné] Film non trouvé: {titre_allocine}")
                        continue

                    Seance.objects.update_or_create(
                        film=film,
                        cinema=cinema,
                        date_heure=showtime.get('datetime'),
                        version=showtime.get('version', 'VF')[:4],
                        format=showtime.get('format', '2D')[:10],
                        defaults={
                            'booking_url': showtime.get('booking_url', ''),
                        },
                    )
                    synced_total += 1

                cinema.last_sync = timezone.now()
                cinema.save(update_fields=['last_sync'])

            except Exception as e:
                logger.error(f"[AlloCiné] Erreur sync {cinema.name}: {e}")

        logger.info(f"[AlloCiné] {synced_total} séances synchronisées")
        return synced_total

    def _find_matching_film(self, allocine_title):
        """Trouve le Film correspondant au titre AlloCiné via fuzzy matching."""
        from apps.films.models import Film
        from apps.films.services.matching_service import fuzzy_match_title

        films = Film.objects.filter(is_now_playing=True)
        best_film = None
        best_ratio = 0

        for film in films:
            matched, ratio = fuzzy_match_title(film.titre, allocine_title)
            if matched and ratio > best_ratio:
                best_ratio = ratio
                best_film = film
            # Essayer aussi avec le titre original
            if film.titre_original:
                matched_orig, ratio_orig = fuzzy_match_title(film.titre_original, allocine_title)
                if matched_orig and ratio_orig > best_ratio:
                    best_ratio = ratio_orig
                    best_film = film

        return best_film
