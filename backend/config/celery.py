import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('cinematch')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Tâches périodiques
app.conf.beat_schedule = {
    'sync-belgian-data-daily': {
        'task': 'apps.films.tasks.sync_all_belgian_data',
        'schedule': 18000.0,  # Toutes les 5h (en secondes)
        'options': {'expires': 3600},
    },
}
