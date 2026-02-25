from celery.schedules import crontab
from . import tasks

app = 'notifications'

# Настройка периодических задач
CELERYBEAT_SCHEDULE = {
    # Проверка начала пар каждую минуту
    'check-class-start': {
        'task': 'notifications.tasks.send_class_start_notifications',
        'schedule': crontab(minute='*'),  # Каждую минуту
    },
    # Проверка конца пар каждую минуту  
    'check-class-end': {
        'task': 'notifications.tasks.send_class_end_notifications',
        'schedule': crontab(minute='*'),  # Каждую минуту
    },
    # Проверка опозданий каждые 5 минут
    'check-late-students': {
        'task': 'notifications.tasks.check_late_students',
        'schedule': crontab(minute='*/5'),  # Каждые 5 минут
    },
}
