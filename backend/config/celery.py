import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('cinematch')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Tâches périodiques
app.conf.beat_schedule = {
    'sync-kinepolis-every-5h': {
        'task': 'apps.films.tasks.sync_kinepolis_all',
        'schedule': 18000.0,  # Toutes les 5h
        'options': {'expires': 3600},
    },
    'enrich-tmdb-daily': {
        'task': 'apps.films.tasks.enrich_tmdb_films',
        'schedule': 86400.0,  # Quotidien (24h)
        'options': {'expires': 3600},
    },
    'cleanup-seances-daily': {
        'task': 'apps.films.tasks.cleanup_old_seances',
        'schedule': 86400.0,  # Quotidien (24h)
        'options': {'expires': 3600},
    },
}
