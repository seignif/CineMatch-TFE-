import logging

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def sync_kinepolis_all(self):
    """
    Synchronise cinémas, films et séances depuis kinepolis.be.
    Exécutée toutes les 3h par Celery Beat.
    """
    logger.info("[Celery] Debut synchronisation Kinepolis")
    try:
        from apps.films.services.kinepolis_service import KinepolisService

        result = KinepolisService().sync_all()
        logger.info(
            f"[Celery] Synchronisation terminee — "
            f"{result['cinemas']} cinemas, "
            f"{result['films']} films, "
            f"{result['sessions']} seances"
        )
        return result

    except Exception as exc:
        logger.error(f"[Celery] Erreur synchronisation Kinepolis: {exc}")
        raise self.retry(exc=exc)


@shared_task
def cleanup_old_seances():
    """Supprime les séances passées. Exécutée quotidiennement à 6h."""
    from apps.films.models import Seance

    count, _ = Seance.objects.filter(showtime__lt=timezone.now()).delete()
    logger.info(f"[Celery] Cleanup: {count} seances passees supprimees")
    return count
