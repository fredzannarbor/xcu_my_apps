from celery import Celery

app = Celery('general_assessor',
             broker='redis://localhost:6379/0',
             backend='redis://localhost:6379/0')

app.conf.beat_schedule = {
    'check_status_every_10_minutes': {
        'task': 'ga_tasks.check_status',
        'schedule': 600.0,
    },
}

app.conf.timezone = 'UTC'
