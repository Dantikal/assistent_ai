from django.contrib import admin
from .models import StudentGroup, GroupSchedule, GroupScheduleItem
from schedule.models import Student, ClassSchedule


@admin.register(StudentGroup)
class StudentGroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'course', 'faculty', 'is_active', 'created_at']
    list_filter = ['faculty', 'course', 'is_active']
    search_fields = ['name', 'description', 'faculty']
    ordering = ['name', 'course']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'description', 'faculty', 'course')
        }),
        ('Статус', {
            'fields': ('is_active',)
        }),
    )


@admin.register(GroupSchedule)
class GroupScheduleAdmin(admin.ModelAdmin):
    list_display = ['name', 'group', 'is_default', 'created_by', 'created_at']
    list_filter = ['group', 'is_default']
    search_fields = ['name', 'description']
    ordering = ['name']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'description', 'group', 'is_default')
        }),
        ('Метаданные', {
            'fields': ('created_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(GroupScheduleItem)
class GroupScheduleItemAdmin(admin.ModelAdmin):
    list_display = ['template', 'subject', 'day_of_week', 'start_time', 'end_time', 'room']
    list_filter = ['template', 'day_of_week']
    search_fields = ['template__name', 'subject__name', 'room']
    ordering = ['template', 'day_of_week', 'start_time']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('template', 'subject', 'day_of_week', 'start_time', 'end_time', 'room')
        }),
        ('Дополнительно', {
            'fields': ('break_time',),
            'classes': ('collapse',)
        }),
    )


class StudentInline(admin.TabularInline):
    model = Student
    extra = 0
    fields = ['user', 'telegram_chat_id', 'created_at']


# Расширяем админку для StudentGroup с возможностью управления студентами
class StudentGroupAdminExtended(StudentGroupAdmin):
    inlines = [StudentInline]
