from celery import Celery
from celery.schedules import crontab

app = Celery('general_assessor_beat')
app.conf.beat_schedule = {
    'check_status_every_10_minutes': {
        'task': 'ga_tasks.check_status',
        'schedule': 600.0,
    },
}

app.conf.timezone = 'UTC'
