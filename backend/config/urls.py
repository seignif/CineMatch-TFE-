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
    path('api/admin/enrich-tmdb/', admin_enrich_tmdb, name='admin-enrich-tmdb'),
    path('api/', include('api.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
