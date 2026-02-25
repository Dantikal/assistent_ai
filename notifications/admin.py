from django.contrib import admin
from .models import (
    Notification, TelegramMessage, NotificationTemplate,
    NotificationSettings, SentNotification, LateNotification
)


@admin.register(NotificationSettings)
class NotificationSettingsAdmin(admin.ModelAdmin):
    """Настройки уведомлений"""
    list_display = ['enable_notifications', 'notification_before_minutes', 'late_threshold_minutes']
    fieldsets = (
        ('Основные настройки', {
            'fields': ('enable_notifications',)
        }),
        ('Время уведомлений', {
            'fields': ('notification_before_minutes', 'late_threshold_minutes'),
            'description': 'Настройки времени для отправки уведомлений'
        }),
    )
    
    def has_add_permission(self, request):
        # Разрешаем только одну запись настроек
        return not self.model.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(SentNotification)
class SentNotificationAdmin(admin.ModelAdmin):
    """Отправленные уведомления"""
    list_display = ['student', 'schedule', 'notification_type', 'sent_at']
    list_filter = ['notification_type', 'sent_at', 'schedule__group']
    search_fields = ['student__user__username', 'student__user__first_name', 'schedule__subject__name']
    date_hierarchy = 'sent_at'
    readonly_fields = ['student', 'schedule', 'notification_type', 'sent_at', 'message_text']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(LateNotification)
class LateNotificationAdmin(admin.ModelAdmin):
    """Опоздания студентов"""
    list_display = ['student', 'schedule', 'late_at', 'notified']
    list_filter = ['notified', 'late_at', 'schedule__group']
    search_fields = ['student__user__username', 'student__user__first_name', 'schedule__subject__name']
    date_hierarchy = 'late_at'
    readonly_fields = ['student', 'schedule', 'late_at']
    
    actions = ['mark_as_notified']
    
    def mark_as_notified(self, request, queryset):
        """Отметить выбранные опоздания как уведомленные"""
        queryset.update(notified=True)
        self.message_user(request, f"Отмечено {queryset.count()} опозданий как уведомленные")
    mark_as_notified.short_description = "Отметить как уведомленные"


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Базовые уведомления"""
    list_display = ['student', 'notification_type', 'is_sent', 'created_at']
    list_filter = ['notification_type', 'is_sent', 'created_at']
    search_fields = ['student__user__username', 'message']
    date_hierarchy = 'created_at'


@admin.register(TelegramMessage)
class TelegramMessageAdmin(admin.ModelAdmin):
    """Telegram сообщения"""
    list_display = ['chat_id', 'is_sent', 'created_at']
    list_filter = ['is_sent', 'created_at']
    search_fields = ['chat_id', 'message_text']
    date_hierarchy = 'created_at'
    readonly_fields = ['chat_id', 'message_text', 'created_at', 'sent_at', 'error_message']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    """Шаблоны уведомлений"""
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'template_text']
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'template_text')
        }),
        ('Статус', {
            'fields': ('is_active',)
        }),
    )
