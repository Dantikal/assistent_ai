import telegram
from celery import shared_task
from django.conf import settings
from django.utils import timezone
from datetime import timedelta, datetime, time as datetime_time
from schedule.models import ClassSchedule, Student
from .models import Notification, TelegramMessage, NotificationSettings, SentNotification, LateNotification


@shared_task
def send_class_start_notifications():
    """Отправка уведомлений о начале пар"""
    now = timezone.now()
    current_day = now.weekday() + 1  # Конвертация в формат модели (1-7)
    current_time = now.time()
    
    # Получаем настройки уведомлений
    try:
        settings_obj = NotificationSettings.objects.first()
        if not settings_obj or not settings_obj.enable_notifications:
            return "Уведомления отключены"
        
        notification_before = settings_obj.notification_before_minutes
        late_threshold = settings_obj.late_threshold_minutes
    except:
        notification_before = 10  # Значение по умолчанию
        late_threshold = 5
    
    # Найти все пары, которые начинаются сейчас
    schedules = ClassSchedule.objects.filter(
        day_of_week=current_day,
        start_time=current_time,
        is_active=True
    )
    
    for schedule in schedules:
        students = Student.objects.filter(group=schedule.group)
        
        for student in students:
            if student.telegram_chat_id:
                # Формируем сообщение о начале пары
                message = f"🔔 НАЧАЛО ПАРЫ!\n\n" \
                         f"👤 Студент: {student.user.get_full_name()}\n" \
                         f"📚 Предмет: {schedule.subject.name}\n" \
                         f"👨‍🏫 Преподаватель: {schedule.subject.teacher.get_full_name()}\n" \
                         f"🕐 Время: {schedule.start_time} - {schedule.end_time}\n" \
                         f"📍 Аудитория: {schedule.room}\n" \
                         f"👥 Группа: {schedule.group.name}\n\n" \
                         f"⏰ Пара началась! Не опаздывайте!"
                
                send_telegram_message.delay(student.telegram_chat_id, message)
                
                # Сохраняем уведомление
                SentNotification.objects.create(
                    student=student,
                    schedule=schedule,
                    notification_type='class_start',
                    message_text=message
                )
    
    return f"Отправлено уведомлений о начале пар: {schedules.count()}"


@shared_task
def send_class_end_notifications():
    """Отправка уведомлений о конце пар"""
    now = timezone.now()
    current_day = now.weekday() + 1
    current_time = now.time()
    
    # Найти все пары, которые заканчиваются сейчас
    schedules = ClassSchedule.objects.filter(
        day_of_week=current_day,
        end_time=current_time,
        is_active=True
    )
    
    for schedule in schedules:
        students = Student.objects.filter(group=schedule.group)
        
        for student in students:
            if student.telegram_chat_id:
                message = f"🔔 КОНЕЦ ПАРЫ!\n\n" \
                         f"📚 Предмет: {schedule.subject.name}\n" \
                         f"👨‍🏫 Преподаватель: {schedule.subject.teacher.get_full_name()}\n" \
                         f"🕐 Время: {schedule.start_time} - {schedule.end_time}\n" \
                         f"📍 Аудитория: {schedule.room}\n\n" \
                         f"✅ Пара завершена! Отдыхайте!"
                
                send_telegram_message.delay(student.telegram_chat_id, message)
                
                # Сохраняем уведомление
                SentNotification.objects.create(
                    student=student,
                    schedule=schedule,
                    notification_type='class_end',
                    message_text=message
                )
    
    return f"Отправлено уведомлений о конце пар: {schedules.count()}"


@shared_task
def check_late_students():
    """Проверка опоздавших студентов"""
    now = timezone.now()
    current_day = now.weekday() + 1
    
    # Получаем настройки
    try:
        settings_obj = NotificationSettings.objects.first()
        if not settings_obj or not settings_obj.enable_notifications:
            return "Уведомления отключены"
        
        late_threshold = settings_obj.late_threshold_minutes
    except:
        late_threshold = 5  # Значение по умолчанию
    
    # Время, когда нужно проверять опоздания (начало пары + порог)
    check_time = (now - timedelta(minutes=late_threshold)).time()
    
    # Найти пары, которые начались порог минут назад
    schedules = ClassSchedule.objects.filter(
        day_of_week=current_day,
        start_time=check_time,
        is_active=True
    )
    
    for schedule in schedules:
        students = Student.objects.filter(group=schedule.group)
        
        for student in students:
            # Проверяем, не было ли уже уведомление об опоздании
            existing_late = LateNotification.objects.filter(
                student=student,
                schedule=schedule,
                late_at__date=now.date()
            ).exists()
            
            if not existing_late and student.telegram_chat_id:
                # Создаем запись об опоздании
                late_notification = LateNotification.objects.create(
                    student=student,
                    schedule=schedule
                )
                
                # Формируем сообщение об опоздании
                message = f"⚠️ ОПОЗДАНИЕ!\n\n" \
                         f"👤 Студент: {student.user.get_full_name()}\n" \
                         f"📚 Предмет: {schedule.subject.name}\n" \
                         f"👨‍🏫 Преподаватель: {schedule.subject.teacher.get_full_name()}\n" \
                         f"🕐 Начало пары: {schedule.start_time}\n" \
                         f"📍 Аудитория: {schedule.room}\n" \
                         f"👥 Группа: {schedule.group.name}\n\n" \
                         f"⏰ Студент опоздал на {late_threshold} минут!"
                
                send_telegram_message.delay(student.telegram_chat_id, message)
                
                # Отмечаем как уведомленное
                late_notification.notified = True
                late_notification.save()
                
                # Сохраняем уведомление
                SentNotification.objects.create(
                    student=student,
                    schedule=schedule,
                    notification_type='late_student',
                    message_text=message
                )
    
    return f"Проверено опозданий для {schedules.count()} пар"


@shared_task
def send_class_reminder():
    """Отправка уведомлений о предстоящих парах (старая функция для совместимости)"""
    return send_class_start_notifications()


@shared_task
def send_telegram_message(chat_id, message_text):
    """Отправка сообщения в Telegram"""
    try:
        bot = telegram.Bot(token=settings.TELEGRAM_BOT_TOKEN)
        bot.send_message(chat_id=chat_id, text=message_text)
        
        # Сохранить успешную отправку
        TelegramMessage.objects.create(
            chat_id=chat_id,
            message_text=message_text,
            is_sent=True,
            sent_at=timezone.now()
        )
        return True
    except Exception as e:
        # Сохранить ошибку
        TelegramMessage.objects.create(
            chat_id=chat_id,
            message_text=message_text,
            is_sent=False,
            error_message=str(e)
        )
        return False


@shared_task
def check_schedule_changes():
    """Проверка изменений в расписании и отправка уведомлений"""
    # Здесь можно добавить логику для отслеживания изменений
    pass
