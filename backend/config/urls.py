import threading
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response


def health_check(request):
    return JsonResponse({"status": "ok", "version": "1.0.0"})


@api_view(['POST'])
@permission_classes([IsAdminUser])
def admin_sync_kinepolis(request):
    def run():
        try:
            from apps.films.services.kinepolis_service import KinepolisService
            KinepolisService().sync_all()
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"[admin_sync] {e}")

    threading.Thread(target=run, daemon=True).start()
    return Response({"status": "started"})


@api_view(['POST'])
@permission_classes([IsAdminUser])
def admin_fix_mojibake(request):
    """Corrige en arrière-plan les titres/synopses Mojibake déjà en base."""
    def run():
        try:
            from apps.films.models import Film
            from apps.films.services.kinepolis_service import _fix_mojibake
            import logging
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
            logging.getLogger(__name__).info(f"[fix_mojibake] {fixed} films corrigés")
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"[fix_mojibake] {e}")

    threading.Thread(target=run, daemon=True).start()
    return Response({"status": "started"})


@api_view(['POST'])
@permission_classes([IsAdminUser])
def admin_sync_kinepolis_data(request):
    """Reçoit les données Kinepolis scrapées localement et les sync dans la DB Railway."""
    data = request.data
    if not data or 'current_movies' not in data:
        return Response({"error": "Données invalides"}, status=400)

    def run():
        try:
            from apps.films.services.kinepolis_service import KinepolisService
            result = KinepolisService().sync_all(data=data)
            import logging
            logging.getLogger(__name__).info(f"[admin_sync_data] {result}")
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"[admin_sync_data] {e}")

    threading.Thread(target=run, daemon=True).start()
    return Response({"status": "started"})


@api_view(['POST'])
@permission_classes([IsAdminUser])
def admin_merge_genres(request):
    """Fusionne les genres Kinepolis en double avec leurs équivalents TMDb."""
    def run():
        import logging
        log = logging.getLogger(__name__)
        try:
            from apps.films.models import Genre
            from apps.users.models import UserProfile

            # canonical name → liste de variantes à fusionner (comparaison insensible à la casse)
            MERGES = {
                "Science-Fiction": ["sciencefiction", "science-fiction", "science fiction"],
                "Aventure": ["aventures"],
                "Animation": ["dessin animé", "dessin anime"],
                "Romance": ["romantique"],
            }

            canonical_genres = {g.name: g for g in Genre.objects.all()}

            for canonical_name, variants in MERGES.items():
                new = canonical_genres.get(canonical_name)
                if not new:
                    log.info(f"[merge_genres] Genre canonique {canonical_name!r} introuvable, skip")
                    continue

                # Fusionner les genres DB qui correspondent à une variante
                for old in Genre.objects.all():
                    if old.name == canonical_name:
                        continue
                    if old.name.lower().replace(" ", "").replace("-", "") in [v.replace(" ", "").replace("-", "") for v in variants]:
                        try:
                            for film in old.film_set.all():
                                film.genres.add(new)
                                film.genres.remove(old)
                            old.delete()
                            log.info(f"[merge_genres] Genre DB {old.name!r} → {canonical_name!r} OK")
                        except Exception as e:
                            log.error(f"[merge_genres] Erreur genre DB {old.name!r}: {e}")

                # Nettoyer genre_preferences dans tous les profils
                for profile in UserProfile.objects.all():
                    prefs = profile.genre_preferences or {}
                    changed = False
                    for key in list(prefs.keys()):
                        if key == canonical_name:
                            continue
                        normalized = key.lower().replace(" ", "").replace("-", "")
                        if normalized in [v.replace(" ", "").replace("-", "") for v in variants]:
                            old_val = prefs.pop(key)
                            prefs[canonical_name] = max(prefs.get(canonical_name, 0), old_val)
                            changed = True
                            log.info(f"[merge_genres] Profil {profile.id}: {key!r} → {canonical_name!r}")
                    if changed:
                        profile.genre_preferences = prefs
                        profile.save(update_fields=['genre_preferences'])

            log.info("[merge_genres] Terminé")

            log.info("[merge_genres] Terminé")
        except Exception as e:
            logging.getLogger(__name__).error(f"[merge_genres] {e}")

    threading.Thread(target=run, daemon=True).start()
    return Response({"status": "started"})


@api_view(['POST'])
@permission_classes([IsAdminUser])
def admin_fix_genre_prefs(request):
    """Corrige directement les clés erronées dans genre_preferences de tous les profils."""
    def run():
        import logging
        log = logging.getLogger(__name__)
        try:
            from apps.users.models import UserProfile

            # Mapping exact : ancienne clé → nouvelle clé canonique
            KEY_MAP = {
                "Science-fiction": "Science-Fiction",
                "Sciencefiction": "Science-Fiction",
                "science-fiction": "Science-Fiction",
                "sciencefiction": "Science-Fiction",
                "Aventures": "Aventure",
                "Romantique": "Romance",
                "Dessin animé": "Animation",
                "Dessin anime": "Animation",
            }

            fixed = 0
            for profile in UserProfile.objects.all():
                prefs = profile.genre_preferences or {}
                changed = False
                for old_key, new_key in KEY_MAP.items():
                    if old_key in prefs and old_key != new_key:
                        val = prefs.pop(old_key)
                        prefs[new_key] = max(prefs.get(new_key, 0), val)
                        changed = True
                        log.info(f"[fix_genre_prefs] Profil {profile.id}: {old_key!r} → {new_key!r}")
                if changed:
                    profile.genre_preferences = prefs
                    profile.save(update_fields=['genre_preferences'])
                    fixed += 1

            log.info(f"[fix_genre_prefs] {fixed} profils corrigés")
        except Exception as e:
            logging.getLogger(__name__).error(f"[fix_genre_prefs] {e}")

    threading.Thread(target=run, daemon=True).start()
    return Response({"status": "started"})


@api_view(['POST'])
@permission_classes([IsAdminUser])
def admin_delete_duplicate_genres(request):
    """Supprime les genres en double en les remplaçant par leur équivalent canonique."""
    def run():
        import logging
        log = logging.getLogger(__name__)
        try:
            from apps.films.models import Genre, Film

            DUPLICATES = {
                "Science-fiction": "Science-Fiction",
                "Sciencefiction": "Science-Fiction",
                "Aventures": "Aventure",
                "Romantique": "Romance",
                "Dessin animé": "Animation",
            }

            for old_name, canonical_name in DUPLICATES.items():
                old = Genre.objects.filter(name=old_name).first()
                canonical = Genre.objects.filter(name=canonical_name).first()
                if not old:
                    log.info(f"[del_genres] {old_name!r} introuvable, skip")
                    continue
                if not canonical:
                    log.info(f"[del_genres] Canonique {canonical_name!r} introuvable pour {old_name!r}, skip")
                    continue
                # Réassigner les films via queryset direct
                films_with_old = Film.objects.filter(genres=old)
                for film in films_with_old:
                    film.genres.add(canonical)
                    film.genres.remove(old)
                count = films_with_old.count()
                old.delete()
                log.info(f"[del_genres] Supprimé {old_name!r} ({count} films migrés vers {canonical_name!r})")

            log.info("[del_genres] Terminé")
        except Exception as e:
            logging.getLogger(__name__).error(f"[del_genres] ERREUR: {e}")

    threading.Thread(target=run, daemon=True).start()
    return Response({"status": "started"})


@api_view(['POST'])
@permission_classes([IsAdminUser])
def admin_enrich_tmdb(request):
    """Lance l'enrichissement TMDb en arrière-plan."""
    def run():
        try:
            from apps.films.services.tmdb_service import TMDbService
            import logging
            svc = TMDbService()
            svc.sync_genres()
            result = svc.enrich_all()
            logging.getLogger(__name__).info(f"[enrich_tmdb] {result}")
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"[enrich_tmdb] {e}")

    threading.Thread(target=run, daemon=True).start()
    return Response({"status": "started"})


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/health/', health_check, name='health-check'),
    path('api/admin/sync-kinepolis/', admin_sync_kinepolis, name='admin-sync-kinepolis'),
    path('api/admin/sync-kinepolis-data/', admin_sync_kinepolis_data, name='admin-sync-kinepolis-data'),
    path('api/admin/fix-mojibake/', admin_fix_mojibake, name='admin-fix-mojibake'),
    path('api/admin/merge-genres/', admin_merge_genres, name='admin-merge-genres'),
    path('api/admin/fix-genre-prefs/', admin_fix_genre_prefs, name='admin-fix-genre-prefs'),
    path('api/admin/delete-duplicate-genres/', admin_delete_duplicate_genres, name='admin-delete-duplicate-genres'),
    path('api/admin/enrich-tmdb/', admin_enrich_tmdb, name='admin-enrich-tmdb'),
    path('api/', include('api.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
