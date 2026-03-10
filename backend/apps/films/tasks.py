import logging

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def sync_tmdb_films(self):
    """
    Synchronise les films en salle depuis TMDb.
    Planifier : 1x/jour à 4h du matin.
    """
    logger.info("[Celery] Début sync TMDb films")
    try:
        from apps.films.services.tmdb_service import TMDbService
        count = TMDbService().sync_now_playing_movies(region='BE')
        logger.info(f"[Celery] {count} films synchronisés depuis TMDb")
        return count
    except Exception as exc:
        logger.error(f"[Celery] Erreur sync TMDb: {exc}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def sync_movieglu_cinemas(self):
    """
    Synchronise les cinémas belges depuis MovieGlu.
    Planifier : 1x/semaine (dimanche 3h du matin).
    Budget : ~4 requêtes/mois.
    """
    logger.info("[Celery] Début sync cinémas MovieGlu")
    try:
        from apps.films.services.movieglu_service import MovieGluService
        count = MovieGluService().sync_belgian_cinemas()
        logger.info(f"[Celery] {count} cinémas synchronisés depuis MovieGlu")
        return count
    except Exception as exc:
        logger.error(f"[Celery] Erreur sync cinémas MovieGlu: {exc}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def sync_movieglu_showtimes(self):
    """
    Synchronise les séances depuis MovieGlu.
    Planifier : 1x/jour à 5h du matin.
    Budget : ~20 cinémas × 30 jours = 600 requêtes/mois.
    """
    logger.info("[Celery] Début sync séances MovieGlu")
    try:
        from apps.films.services.movieglu_service import MovieGluService
        count = MovieGluService().sync_showtimes_for_all_cinemas(days=7)
        logger.info(f"[Celery] {count} séances synchronisées depuis MovieGlu")
        return count
    except Exception as exc:
        logger.error(f"[Celery] Erreur sync séances MovieGlu: {exc}")
        raise self.retry(exc=exc)


@shared_task
def cleanup_old_showtimes():
    """
    Supprime les séances passées.
    Planifier : 1x/jour à 6h du matin.
    """
    from apps.films.models import Seance
    count, _ = Seance.objects.filter(date_heure__lt=timezone.now()).delete()
    logger.info(f"[Celery] Cleanup: {count} séances passées supprimées")
    return count
