import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('cinematch')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Tâches périodiques
app.conf.beat_schedule = {
    # Kinepolis scraping à 4h00 UTC (6h00 Belgique)
    'sync-kinepolis-daily': {
        'task': 'apps.films.tasks.sync_kinepolis_all',
        'schedule': crontab(hour=4, minute=0),
        'options': {'expires': 3600},
    },
    # TMDb enrichissement à 5h00 UTC — après Kinepolis
    'enrich-tmdb-daily': {
        'task': 'apps.films.tasks.enrich_tmdb_films',
        'schedule': crontab(hour=5, minute=0),
        'options': {'expires': 3600},
    },
    # Nettoyage séances expirées à 3h00 UTC
    'cleanup-seances-daily': {
        'task': 'apps.films.tasks.cleanup_old_seances',
        'schedule': crontab(hour=3, minute=0),
        'options': {'expires': 3600},
    },
}
