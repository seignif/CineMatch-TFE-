from django.core.management.base import BaseCommand
from apps.films.models import Film
from apps.films.services.kinepolis_service import _fix_mojibake


class Command(BaseCommand):
    help = "Corrige les titres/synopses encodés en double (Mojibake Latin-1/UTF-8)"

    def handle(self, *args, **options):
        fixed = 0
        for film in Film.objects.all():
            new_title = _fix_mojibake(film.title)
            new_synopsis = _fix_mojibake(film.synopsis)
            new_short = _fix_mojibake(film.short_synopsis)

            if new_title != film.title or new_synopsis != film.synopsis or new_short != film.short_synopsis:
                film.title = new_title
                film.synopsis = new_synopsis
                film.short_synopsis = new_short
                film.save(update_fields=['title', 'synopsis', 'short_synopsis'])
                fixed += 1

        self.stdout.write(self.style.SUCCESS(f"{fixed} films corrigés."))
