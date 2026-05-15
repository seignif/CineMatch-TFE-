from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Enrichit les films Kinepolis avec les données TMDb (posters HD, trailers, acteurs)."

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true',
                            help='Re-enrichit tous les films, même ceux déjà enrichis.')
        parser.add_argument('--sync-genres', action='store_true',
                            help='Synchronise d\'abord les genres TMDb.')
        parser.add_argument('--film-id', type=int,
                            help='Enrichit un seul film par son id Django.')
        parser.add_argument('--credits-only', action='store_true',
                            help='Enrichit uniquement les acteurs/équipe (films sans cast).')

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

        if options['credits_only']:
            self.stdout.write("Enrichissement credits uniquement (films sans cast)...")
            result = service.enrich_credits_only()
            self.stdout.write(self.style.SUCCESS(
                f"Termine: {result['enriched']} enrichis, "
                f"{result['failed']} echoues sur {result['total']} films."
            ))
            return

        if options['film_id']:
            from apps.films.models import Film
            try:
                film = Film.objects.get(pk=options['film_id'])
            except Film.DoesNotExist:
                self.stderr.write(self.style.ERROR(f"Film id={options['film_id']} introuvable."))
                return
            ok = service.enrich_film(film)
            if ok:
                self.stdout.write(self.style.SUCCESS(f"Film '{film.title}' enrichi."))
            else:
                self.stdout.write(self.style.WARNING(f"Film '{film.title}' non trouvé sur TMDb."))
            return

        force = options['force']
        self.stdout.write(
            f"Enrichissement TMDb ({'tous les films' if force else 'films sans données'})..."
        )
        result = service.enrich_all(force=force)
        self.stdout.write(self.style.SUCCESS(
            f"Termine: {result['enriched']} enrichis, "
            f"{result['failed']} echoues sur {result['total']} films."
        ))
