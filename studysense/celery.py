import os
from celery import Celery
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'studysense.settings')

app = Celery('studysense')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Загружаем расписание периодических задач
app.conf.beat_schedule = {
    # Проверка начала пар каждую минуту
    'check-class-start': {
        'task': 'notifications.tasks.send_class_start_notifications',
        'schedule': 60.0,  # Каждые 60 секунд
    },
    # Проверка конца пар каждую минуту  
    'check-class-end': {
        'task': 'notifications.tasks.send_class_end_notifications',
        'schedule': 60.0,  # Каждые 60 секунд
    },
    # Проверка опозданий каждые 5 минут
    'check-late-students': {
        'task': 'notifications.tasks.check_late_students',
        'schedule': 300.0,  # Каждые 300 секунд (5 минут)
    },
}
