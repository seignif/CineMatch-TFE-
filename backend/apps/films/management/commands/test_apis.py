"""
Commande Django pour tester la connexion aux APIs externes.

Usage :
    python manage.py test_apis
    python manage.py test_apis --tmdb-only
    python manage.py test_apis --movieglu-only
"""
from datetime import datetime

import requests
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Teste la connexion aux APIs TMDb et MovieGlu"

    def add_arguments(self, parser):
        parser.add_argument('--tmdb-only', action='store_true', help='Tester uniquement TMDb')
        parser.add_argument('--movieglu-only', action='store_true', help='Tester uniquement MovieGlu')

    def handle(self, *args, **options):
        tmdb_only = options['tmdb_only']
        movieglu_only = options['movieglu_only']

        if not movieglu_only:
            self._test_tmdb()

        if not tmdb_only:
            self._test_movieglu()

    # ------------------------------------------------------------------
    # TMDb
    # ------------------------------------------------------------------

    def _test_tmdb(self):
        self.stdout.write(self.style.MIGRATE_HEADING("\n=== Test API TMDb ==="))

        api_key = getattr(settings, 'TMDB_API_KEY', '')
        if not api_key:
            self.stdout.write(self.style.ERROR("  [FAIL] TMDB_API_KEY manquant dans .env"))
            return

        url = f"{settings.TMDB_BASE_URL}/movie/now_playing"
        params = {'api_key': api_key, 'language': 'fr-BE', 'region': 'BE', 'page': 1}

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            total = data.get('total_results', 0)
            films = data.get('results', [])

            self.stdout.write(self.style.SUCCESS(f"  [OK] Connexion OK (HTTP {response.status_code})"))
            self.stdout.write(f"  [OK] {total} films en salle en Belgique")
            if films:
                self.stdout.write(f"  [OK] Exemple : '{films[0].get('title')}' (TMDb ID: {films[0].get('id')})")

            # Rate limits
            self.stdout.write(self.style.WARNING("  Rate limits : 1 000 req/jour · 40 req/10s"))

        except requests.exceptions.ConnectionError:
            self.stdout.write(self.style.ERROR("  [FAIL] Impossible de joindre api.themoviedb.org"))
        except requests.exceptions.HTTPError as e:
            self.stdout.write(self.style.ERROR(f"  [FAIL] Erreur HTTP {e.response.status_code} — clé API invalide ?"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  [FAIL] Erreur : {e}"))

    # ------------------------------------------------------------------
    # MovieGlu
    # ------------------------------------------------------------------

    def _test_movieglu(self):
        self.stdout.write(self.style.MIGRATE_HEADING("\n=== Test API MovieGlu ==="))

        api_key = getattr(settings, 'MOVIEGLU_API_KEY', '')
        authorization = getattr(settings, 'MOVIEGLU_AUTHORIZATION', '')

        if not api_key or not authorization:
            self.stdout.write(self.style.ERROR("  [FAIL] MOVIEGLU_API_KEY ou MOVIEGLU_AUTHORIZATION manquant dans .env"))
            return

        headers = {
            'client': settings.MOVIEGLU_CLIENT,
            'x-api-key': api_key,
            'authorization': authorization,
            'territory': settings.MOVIEGLU_TERRITORY,
            'api-version': settings.MOVIEGLU_API_VERSION,
            'geolocation': '50.8503;4.3517',  # Bruxelles
            'device-datetime': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.000Z'),
        }

        url = f"{settings.MOVIEGLU_BASE_URL}cinemasNearby/"
        params = {'n': 10}

        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()

            # 204 = credentials OK mais aucun résultat (sandbox sans données locales)
            if response.status_code == 204 or not response.text:
                self.stdout.write(self.style.SUCCESS(f"  [OK] Connexion OK (HTTP {response.status_code})"))
                self.stdout.write(self.style.WARNING(
                    "  [INFO] Aucun cinema retourne (territoire XX = sandbox, donnees limitees)"
                ))
                self.stdout.write(self.style.WARNING("  Rate limits : 10 000 req/mois (sandbox)"))
                return

            data = response.json()
            cinemas = data.get('cinemas', [])

            self.stdout.write(self.style.SUCCESS(f"  [OK] Connexion OK (HTTP {response.status_code})"))
            self.stdout.write(f"  [OK] {len(cinemas)} cinemas retournes (territoire: {settings.MOVIEGLU_TERRITORY})")
            if cinemas:
                c = cinemas[0]
                self.stdout.write(
                    f"  [OK] Exemple : '{c.get('cinema_name')}' "
                    f"(ID: {c.get('cinema_id')}, {c.get('city', '')})"
                )

            self.stdout.write(self.style.WARNING("  Rate limits : 10 000 req/mois (sandbox)"))

        except requests.exceptions.ConnectionError:
            self.stdout.write(self.style.ERROR("  [FAIL] Impossible de joindre api-gate2.movieglu.com"))
        except requests.exceptions.HTTPError as e:
            self.stdout.write(self.style.ERROR(
                f"  [FAIL] Erreur HTTP {e.response.status_code} - credentials invalides ?\n"
                f"    Reponse : {e.response.text[:200]}"
            ))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  [FAIL] Erreur : {e}"))

        self.stdout.write("")
