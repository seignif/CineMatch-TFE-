import logging
import time
from datetime import datetime, timedelta

import requests
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)


class MovieGluService:
    """
    Service pour interagir avec l'API MovieGlu (sandbox TFE).

    Endpoints utilisés :
        GET cinemasNearby/      → cinémas proches d'une position
        GET cinemaShowTimes/    → séances d'un cinéma pour une date
        GET filmShowTimes/      → séances d'un film spécifique

    Headers requis : client, x-api-key, authorization, territory,
                     api-version, geolocation, device-datetime
    Quota : 10 000 requêtes/mois (sandbox)
    """

    def __init__(self):
        self.base_url = settings.MOVIEGLU_BASE_URL
        self.client = settings.MOVIEGLU_CLIENT
        self.api_key = settings.MOVIEGLU_API_KEY
        self.authorization = settings.MOVIEGLU_AUTHORIZATION
        self.territory = settings.MOVIEGLU_TERRITORY
        self.api_version = settings.MOVIEGLU_API_VERSION

    # ------------------------------------------------------------------
    # Headers
    # ------------------------------------------------------------------

    def _get_headers(self, latitude=None, longitude=None):
        """Génère les headers requis pour chaque requête MovieGlu."""
        headers = {
            'client': self.client,
            'x-api-key': self.api_key,
            'authorization': self.authorization,
            'territory': self.territory,
            'api-version': self.api_version,
            'device-datetime': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.000Z'),
        }
        if latitude is not None and longitude is not None:
            headers['geolocation'] = f'{latitude};{longitude}'
        return headers

    # ------------------------------------------------------------------
    # API calls
    # ------------------------------------------------------------------

    def get_cinemas_nearby(self, latitude, longitude, n=50):
        """
        Récupère les cinémas proches d'une position géographique.
        Cache 24 heures (les cinémas changent rarement).
        """
        cache_key = f'movieglu_cinemas_{latitude}_{longitude}_{n}'
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            response = requests.get(
                f'{self.base_url}cinemasNearby/',
                headers=self._get_headers(latitude, longitude),
                params={'n': n},
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
            cache.set(cache_key, data, 60 * 60 * 24)
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"[MovieGlu] cinemasNearby error: {e}")
            return None

    def get_cinema_showtimes(self, cinema_id, date=None):
        """
        Récupère toutes les séances d'un cinéma pour une date donnée.
        Cache 6 heures.
        date format : 'YYYYMMDD'
        """
        if date is None:
            date = datetime.now().strftime('%Y%m%d')

        cache_key = f'movieglu_showtimes_{cinema_id}_{date}'
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            response = requests.get(
                f'{self.base_url}cinemaShowTimes/',
                headers=self._get_headers(),
                params={'cinema_id': cinema_id, 'date': date},
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
            cache.set(cache_key, data, 60 * 60 * 6)
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"[MovieGlu] cinemaShowTimes error (cinema={cinema_id}, date={date}): {e}")
            return None

    # ------------------------------------------------------------------
    # Synchronisation
    # ------------------------------------------------------------------

    def sync_belgian_cinemas(self):
        """
        Synchronise les cinémas belges via cinemasNearby depuis Bruxelles.
        Appeler 1x/semaine maximum.
        Retourne le nombre de cinémas synchronisés.
        """
        from apps.films.models import Cinema

        # Centre de la Belgique (Bruxelles)
        data = self.get_cinemas_nearby(50.8503, 4.3517, n=100)

        if not data or 'cinemas' not in data:
            logger.error("[MovieGlu] Aucun cinéma retourné par l'API")
            return 0

        synced = 0
        for cinema_data in data['cinemas']:
            try:
                Cinema.objects.update_or_create(
                    movieglu_id=str(cinema_data['cinema_id']),
                    defaults={
                        'name': cinema_data.get('cinema_name', ''),
                        'address': cinema_data.get('address', ''),
                        'city': cinema_data.get('city', ''),
                        'postal_code': cinema_data.get('postcode', ''),
                        'country': 'BE',
                        'latitude': cinema_data.get('lat'),
                        'longitude': cinema_data.get('lng'),
                        'phone': cinema_data.get('telephone', ''),
                        'website': cinema_data.get('booking_url', ''),
                        'is_active': True,
                        'last_sync': timezone.now(),
                    },
                )
                synced += 1
                logger.debug(f"[MovieGlu] Cinéma: {cinema_data.get('cinema_name')} ({cinema_data.get('cinema_id')})")
            except Exception as e:
                logger.error(f"[MovieGlu] Erreur sync cinéma {cinema_data.get('cinema_id')}: {e}")

        logger.info(f"[MovieGlu] {synced} cinémas synchronisés")
        return synced

    def sync_showtimes_for_cinema(self, cinema, days=7):
        """
        Synchronise les séances d'un cinéma pour les N prochains jours.
        Retourne le nombre de séances créées/mises à jour.
        """
        from apps.films.models import Seance
        from apps.films.services.matching_service import match_movieglu_to_tmdb

        synced = 0

        for day_offset in range(days):
            date_str = (datetime.now() + timedelta(days=day_offset)).strftime('%Y%m%d')
            data = self.get_cinema_showtimes(cinema.movieglu_id, date_str)

            if not data or 'films' not in data:
                continue

            for film_data in data['films']:
                tmdb_film = match_movieglu_to_tmdb(film_data)
                if not tmdb_film:
                    logger.debug(f"[MovieGlu] Non matché: '{film_data.get('film_name')}'")
                    continue

                for showtime in film_data.get('showings', []):
                    try:
                        # Parsing flexible du format datetime MovieGlu
                        time_str = showtime.get('time', '')
                        try:
                            dt = datetime.strptime(time_str, '%Y-%m-%dT%H:%M:%S')
                        except ValueError:
                            dt = datetime.strptime(time_str, '%H:%M')
                            base_date = datetime.strptime(date_str, '%Y%m%d')
                            dt = base_date.replace(hour=dt.hour, minute=dt.minute)

                        Seance.objects.update_or_create(
                            film=tmdb_film,
                            cinema=cinema,
                            date_heure=timezone.make_aware(dt),
                            version=showtime.get('language', 'VF'),
                            format=showtime.get('display_name', '2D')[:10],
                            defaults={
                                'booking_url': showtime.get('booking_link', ''),
                            },
                        )
                        synced += 1
                    except Exception as e:
                        logger.error(f"[MovieGlu] Erreur création séance: {e}")

        cinema.last_sync = timezone.now()
        cinema.save(update_fields=['last_sync'])

        logger.info(f"[MovieGlu] {synced} séances synchronisées pour {cinema.name}")
        return synced

    def sync_showtimes_for_all_cinemas(self, days=7):
        """
        Synchronise les séances de tous les cinémas actifs.
        Limite à 20 cinémas pour respecter le quota API (600 req/mois).
        """
        from apps.films.models import Cinema

        cinemas = Cinema.objects.filter(is_active=True, country='BE')[:20]
        total = 0

        for cinema in cinemas:
            total += self.sync_showtimes_for_cinema(cinema, days)
            time.sleep(1)  # Rate limiting

        logger.info(f"[MovieGlu] Total: {total} séances synchronisées ({cinemas.count()} cinémas)")
        return total
