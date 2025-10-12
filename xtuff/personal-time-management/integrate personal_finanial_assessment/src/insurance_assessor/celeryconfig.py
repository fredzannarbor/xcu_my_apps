# celeryconfig.py
broker_url = 'redis://localhost:6379/0'  # Redis broker URL (default port)
result_backend = 'redis://localhost:6379/1'  # Backend for storing results
task_serializer = 'json'
accept_content = ['json']
result_serializer = 'json'
timezone = 'UTC'  # Adjust to your timezone if needed, e.g., 'America/New_York'

from celery.schedules import crontab

beat_schedule = {
    'periodic-check-first-day-of-month': {
        'task': 'tasks.periodic_check',
        'schedule': crontab(hour=8, minute=0, day_of_month=1),  # Run on the 1st day of every month at 8:00 AM
    },
    'monthly-coverage-check-first-day-of-month': {
        'task': 'tasks.monthly_coverage_check',
        'schedule': crontab(hour=9, minute=0, day_of_month=1),  # Run on the 1st day of every month at 9:00 AM
    },
}