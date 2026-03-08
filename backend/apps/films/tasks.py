import logging
from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def sync_all_belgian_data(self):
    """
    Tâche principale : synchronise films, cinémas et séances belges.
    Exécutée quotidiennement par Celery Beat.
    """
    logger.info("[Celery] Début synchronisation données belges")

    try:
        from apps.films.services.tmdb_service import TMDbService
        from apps.films.services.allocine_service import AllocineService
        from apps.films.models import Seance

        # 1. Synchroniser les films TMDb
        tmdb_service = TMDbService()
        films_count = tmdb_service.sync_now_playing_movies(region='BE')
        logger.info(f"[Celery] {films_count} films synchronisés depuis TMDb")

        # 2. Synchroniser les cinémas (seulement si nécessaire)
        allocine_service = AllocineService()
        if _should_sync_cinemas():
            cinemas_count = allocine_service.sync_all_belgian_cinemas()
            logger.info(f"[Celery] {cinemas_count} cinémas synchronisés depuis AlloCiné")

        # 3. Synchroniser les séances (7 prochains jours)
        seances_count = allocine_service.sync_showtimes_for_all_cinemas(days=7)
        logger.info(f"[Celery] {seances_count} séances synchronisées")

        # 4. Supprimer les séances passées
        deleted_count, _ = Seance.objects.filter(date_heure__lt=timezone.now()).delete()
        logger.info(f"[Celery] {deleted_count} séances passées supprimées")

        logger.info("[Celery] Synchronisation terminée avec succès")
        return {
            'films': films_count,
            'seances': seances_count,
            'deleted_seances': deleted_count,
        }

    except Exception as exc:
        logger.error(f"[Celery] Erreur synchronisation: {exc}")
        raise self.retry(exc=exc)


def _should_sync_cinemas() -> bool:
    """Synchronise les cinémas seulement une fois par semaine."""
    from apps.films.models import Cinema
    from django.utils import timezone
    from datetime import timedelta

    oldest_sync = Cinema.objects.filter(
        last_sync__isnull=False
    ).order_by('last_sync').values_list('last_sync', flat=True).first()

    if not oldest_sync:
        return True

    return timezone.now() - oldest_sync > timedelta(days=7)


@shared_task
def cleanup_expired_seances():
    """Nettoyage des séances passées (peut être lancé séparément)."""
    from apps.films.models import Seance
    count, _ = Seance.objects.filter(date_heure__lt=timezone.now()).delete()
    logger.info(f"[Celery] Cleanup: {count} séances supprimées")
    return count
