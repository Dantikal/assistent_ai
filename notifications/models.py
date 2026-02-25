from django.db import models
from django.contrib.auth.models import User
from schedule.models import Student, ClassSchedule, StudentGroup


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('class_reminder', 'Напоминание о паре'),
        ('schedule_change', 'Изменение расписания'),
        ('emergency', 'Срочное уведомление'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    message = models.TextField()
    is_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.student.user.username} - {self.get_notification_type_display()}"


class TelegramMessage(models.Model):
    chat_id = models.CharField(max_length=50)
    message_text = models.TextField()
    is_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    def __str__(self):
        return f"Message to {self.chat_id} - {'Sent' if self.is_sent else 'Pending'}"


class NotificationTemplate(models.Model):
    name = models.CharField(max_length=100, unique=True)
    template_text = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class NotificationSettings(models.Model):
    """Настройки уведомлений"""
    enable_notifications = models.BooleanField(default=True, verbose_name="Включить уведомления")
    notification_before_minutes = models.IntegerField(
        default=10, 
        verbose_name="Уведомлять за N минут до пары",
        help_text="За сколько минут до начала пары отправлять уведомление"
    )
    late_threshold_minutes = models.IntegerField(
        default=5,
        verbose_name="Порог опоздания (минуты)",
        help_text="Если студент не пришел через N минут после начала пары, считать опозданием"
    )
    
    class Meta:
        verbose_name = "Настройки уведомлений"
        verbose_name_plural = "Настройки уведомлений"
    
    def __str__(self):
        return f"Настройки уведомлений"


class SentNotification(models.Model):
    """Отправленные уведомления"""
    NOTIFICATION_TYPES = [
        ('class_start', 'Начало пары'),
        ('class_end', 'Конец пары'),
        ('late_student', 'Опоздание студента'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, verbose_name="Студент")
    schedule = models.ForeignKey(ClassSchedule, on_delete=models.CASCADE, verbose_name="Расписание")
    notification_type = models.CharField(
        max_length=20, 
        choices=NOTIFICATION_TYPES,
        verbose_name="Тип уведомления"
    )
    sent_at = models.DateTimeField(auto_now_add=True, verbose_name="Отправлено")
    message_text = models.TextField(verbose_name="Текст сообщения")
    
    class Meta:
        verbose_name = "Отправленное уведомление"
        verbose_name_plural = "Отправленные уведомления"
        ordering = ['-sent_at']
    
    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.get_notification_type_display()}"


class LateNotification(models.Model):
    """Уведомления об опозданиях"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, verbose_name="Студент")
    schedule = models.ForeignKey(ClassSchedule, on_delete=models.CASCADE, verbose_name="Расписание")
    late_at = models.DateTimeField(auto_now_add=True, verbose_name="Время опоздания")
    notified = models.BooleanField(default=False, verbose_name="Уведомлено")
    
    class Meta:
        verbose_name = "Опоздание"
        verbose_name_plural = "Опоздания"
        ordering = ['-late_at']
        unique_together = ['student', 'schedule', 'late_at']
    
    def __str__(self):
        return f"{self.student.user.get_full_name()} опоздал на {self.schedule.subject.name}"
