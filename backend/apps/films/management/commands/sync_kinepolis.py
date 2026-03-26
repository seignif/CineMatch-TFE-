"""
Commande Django pour synchroniser les données Kinepolis.

Usage :
    python manage.py sync_kinepolis
    python manage.py sync_kinepolis --force   # ignore le cache Redis
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Synchronise cinemas, films et seances depuis kinepolis.be"

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Ignore le cache Redis et force un nouveau scraping',
        )

    def handle(self, *args, **options):
        from apps.films.services.kinepolis_service import KinepolisService

        service = KinepolisService()

        if options['force']:
            from django.core.cache import cache
            cache.delete(service.CACHE_KEY)
            self.stdout.write(self.style.WARNING("  Cache Redis efface — scraping force"))

        self.stdout.write(self.style.MIGRATE_HEADING("\n=== Synchronisation Kinepolis ==="))

        try:
            result = service.sync_all()
            self.stdout.write(self.style.SUCCESS(
                f"  [OK] {result['cinemas']} cinemas synchronises"
            ))
            self.stdout.write(self.style.SUCCESS(
                f"  [OK] {result['films']} films synchronises"
            ))
            self.stdout.write(self.style.SUCCESS(
                f"  [OK] {result['sessions']} seances synchronisees"
            ))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  [FAIL] Erreur : {e}"))
            raise
