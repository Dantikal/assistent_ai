from django.contrib import admin
from .models import StudentGroup, Student, Teacher, Subject, ClassSchedule, Attendance


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


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['user', 'group', 'telegram_chat_id', 'created_at']
    list_filter = ['group', 'created_at']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'group__name']
    ordering = ['user__last_name', 'user__first_name']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('user', 'group')
        }),
        ('Контакты', {
            'fields': ('telegram_chat_id',)
        }),
    )


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ['get_full_name', 'email', 'phone']
    search_fields = ['last_name', 'first_name', 'patronymic', 'email']
    ordering = ['last_name', 'first_name']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('last_name', 'first_name', 'patronymic')
        }),
        ('Контакты', {
            'fields': ('email', 'phone')
        }),
    )


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'teacher', 'description']
    list_filter = ['teacher']
    search_fields = ['name', 'description']
    ordering = ['name']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'teacher')
        }),
        ('Описание', {
            'fields': ('description',)
        }),
    )


@admin.register(ClassSchedule)
class ClassScheduleAdmin(admin.ModelAdmin):
    list_display = ['subject', 'group', 'get_day_of_week_display', 'start_time', 'end_time', 'room', 'is_active']
    list_filter = ['day_of_week', 'group', 'subject', 'is_active']
    search_fields = ['subject__name', 'group__name', 'room']
    ordering = ['day_of_week', 'start_time']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('subject', 'group', 'day_of_week', 'start_time', 'end_time', 'room')
        }),
        ('Статус', {
            'fields': ('is_active',)
        }),
    )


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['student', 'schedule', 'date', 'is_present', 'created_at']
    list_filter = ['date', 'is_present', 'schedule__group']
    search_fields = ['student__user__username', 'schedule__subject__name']
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('student', 'schedule', 'date', 'is_present')
        }),
    )
