from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Enrichit les films Kinepolis avec les données TMDb (posters HD, trailers, notes)."

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Re-enrichit tous les films, même ceux déjà enrichis.',
        )
        parser.add_argument(
            '--sync-genres',
            action='store_true',
            help='Synchronise d\'abord les genres TMDb.',
        )

    def handle(self, *args, **options):
        from apps.films.services.tmdb_service import TMDbService

        try:
            service = TMDbService()
        except ValueError as e:
            self.stderr.write(self.style.ERROR(str(e)))
            return

        if options['sync_genres']:
            self.stdout.write("Synchronisation des genres TMDb...")
            count = service.sync_genres()
            self.stdout.write(self.style.SUCCESS(f"  {count} genres ajoutés."))

        force = options['force']
        self.stdout.write(
            f"Enrichissement TMDb ({'tous les films' if force else 'films sans tmdb_id'})..."
        )

        result = service.enrich_all(force=force)

        self.stdout.write(
            self.style.SUCCESS(
                f"\nTermine: {result['enriched']} enrichis, "
                f"{result['failed']} echoues sur {result['total']} films."
            )
        )
