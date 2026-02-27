from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.db.models import Sum
from django.urls import path
from django.urls import reverse
from django.shortcuts import redirect
from .models import (
    KnowledgeCard, AIConversation, StudyProgress, QuestionCategory, UserProfile, Rank, 
    SubjectScore, TaskCategory, TaskTracker, StudentNote, PointsAdjustment
)


class CustomAdminSite(admin.AdminSite):
    """Кастомная админ-панель с дополнительными ссылками"""
    
    def get_urls(self):
        from ai_assistant.admin_urls import urlpatterns as admin_panel_urls
        urls = super().get_urls()
        custom_urls = [
            path('points-management/', self.admin_view(lambda request: redirect('admin_panel:points_management')), name='points_management_redirect'),
        ]
        return custom_urls + urls
    
    def index(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['points_management_url'] = reverse('admin_panel:points_management')
        return super().index(request, extra_context)


@admin.register(PointsAdjustment)
class PointsAdjustmentAdmin(admin.ModelAdmin):
    """Админка для истории изменений очков"""
    list_display = ['user', 'points_change_colored', 'reason', 'created_at', 'created_by']
    list_filter = ['created_at', 'created_by']
    search_fields = ['user__username', 'reason']
    readonly_fields = ['created_at', 'created_by']
    
    def points_change_colored(self, obj):
        """Цветное отображение изменения очков"""
        if obj.points_change > 0:
            color = 'green'
            sign = '+'
        else:
            color = 'red'
            sign = ''
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}{}</span>',
            color, sign, obj.points_change
        )
    points_change_colored.short_description = 'Изменение очков'
    
    def save_model(self, request, obj, form, change):
        """Автоматически устанавливаем кто изменил очки"""
        if not change:  # Только при создании
            obj.created_by = request.user
            
            # Обновляем общие очки пользователя
            user_profile, created = UserProfile.objects.get_or_create(
                user=obj.user,
                defaults={'points': 0}
            )
            user_profile.points = max(0, user_profile.points + obj.points_change)
            user_profile.save()
        
        super().save_model(request, obj, form, change)


class PointsAdjustmentInline(admin.TabularInline):
    """Inline для истории изменений очков"""
    model = PointsAdjustment
    fk_name = 'user'
    extra = 0
    fields = ['points_change_colored', 'reason', 'created_at', 'created_by']
    readonly_fields = ['points_change_colored', 'created_at', 'created_by']
    
    def points_change_colored(self, obj):
        if obj.points_change > 0:
            color = 'green'
            sign = '+'
        else:
            color = 'red'
            sign = ''
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}{}</span>',
            color, sign, obj.points_change
        )
    points_change_colored.short_description = 'Изменение'


# Расширенная админка для пользователя
class CustomUserAdmin(UserAdmin):
    """Кастомная админка для пользователей с управлением очками"""
    inlines = [PointsAdjustmentInline]
    list_display = ['username', 'email', 'first_name', 'last_name', 'total_points', 'is_staff']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    list_filter = ['is_staff', 'is_superuser', 'is_active']
    
    def total_points(self, obj):
        """Общие очки пользователя"""
        try:
            profile = obj.userprofile
            return format_html(
                '<span style="font-weight: bold; color: #667eea;">{} очков</span>',
                profile.points
            )
        except UserProfile.DoesNotExist:
            return format_html('<span style="color: red;">0 очков</span>')
    total_points.short_description = 'Общие очки'
    
    def get_queryset(self, request):
        """Оптимизация запросов"""
        return super().get_queryset(request).select_related('userprofile')


@admin.register(StudentNote)
class StudentNoteAdmin(admin.ModelAdmin):
    """Админка для заметок студентов"""
    list_display = ['title', 'user', 'priority_colored', 'category', 'is_completed', 'created_at']
    list_filter = ['priority', 'category', 'is_completed', 'created_at']
    search_fields = ['title', 'content', 'user__username', 'tags']
    readonly_fields = ['created_at', 'updated_at']
    
    def priority_colored(self, obj):
        """Цветное отображение приоритета"""
        colors = {
            'low': 'gray',
            'medium': 'blue', 
            'high': 'orange',
            'urgent': 'red'
        }
        color = colors.get(obj.priority, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_priority_display()
        )
    priority_colored.short_description = 'Приоритет'


@admin.register(Rank)
class RankAdmin(admin.ModelAdmin):
    list_display = ('level', 'emoji', 'name', 'min_points', 'max_points', 'color')
    list_filter = ('color',)
    search_fields = ('name',)
    fieldsets = (
        ('Основная информация', {
            'fields': ('level', 'name', 'emoji', 'color')
        }),
        ('Диапазон очков', {
            'fields': ('min_points', 'max_points')
        }),
        ('Описание', {
            'fields': ('description',)
        }),
    )
    ordering = ('level',)


@admin.register(KnowledgeCard)
class KnowledgeCardAdmin(admin.ModelAdmin):
    list_display = ('title', 'subject', 'difficulty_level', 'is_active', 'created_at')
    list_filter = ('subject', 'difficulty_level', 'is_active', 'created_at')
    search_fields = ('title', 'main_definition', 'simple_explanation')
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'subject', 'difficulty_level', 'is_active')
        }),
        ('Содержание', {
            'fields': ('main_definition', 'simple_explanation', 'examples', 'analogies')
        }),
        ('Дополнительно', {
            'fields': ('key_concepts', 'common_mistakes'),
            'classes': ('collapse',)
        }),
    )


@admin.register(AIConversation)
class AIConversationAdmin(admin.ModelAdmin):
    list_display = ['user', 'short_question', 'created_at']
    search_fields = ['user__username', 'student_question']  # Исправлено на student_question
    readonly_fields = ['created_at']

    def short_question(self, obj):
        # Исправлено с question на student_question
        return obj.student_question[:50] + '...' if len(obj.student_question) > 50 else obj.student_question
    short_question.short_description = 'Вопрос'  # Добавим понятное название для колонки

@admin.register(StudyProgress)
class StudyProgressAdmin(admin.ModelAdmin):
    list_display = ['user', 'knowledge_card', 'mastery_level', 'last_accessed', 'access_count']
    list_filter = ['mastery_level', 'last_accessed']
    search_fields = ['user__username', 'knowledge_card__title']


@admin.register(SubjectScore)
class SubjectScoreAdmin(admin.ModelAdmin):
    list_display = ['user_profile', 'subject', 'points', 'correct_answers', 'wrong_answers', 'updated_at']
    list_filter = ['subject', 'updated_at']
    search_fields = ['user_profile__user__username', 'subject__name']


@admin.register(TaskCategory)
class TaskCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'color', 'icon', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Внешний вид', {
            'fields': ('color', 'icon')
        }),
        ('Системная информация', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(TaskTracker)
class TaskTrackerAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'category', 'is_completed', 'points', 'deadline', 'created_at']
    list_filter = ['is_completed', 'category', 'created_at', 'deadline']
    search_fields = ['title', 'description', 'user__username', 'category__name']
    readonly_fields = ['created_at', 'completed_at']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('user', 'category', 'title', 'description')
        }),
        ('Статус и баллы', {
            'fields': ('is_completed', 'points')
        }),
        ('Время', {
            'fields': ('deadline', 'created_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    
    def user(self, obj):
        return obj.user_profile.user.username
    user.short_description = 'Пользователь'


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_rank_display', 'points', 'correct_answers', 'wrong_answers', 'accuracy')
    list_filter = ('points',)
    search_fields = ('user__username',)
    fieldsets = (
        ('Информация о пользователе', {
            'fields': ('user', 'avatar')
        }),
        ('Очки и статистика', {
            'fields': ('points', 'correct_answers', 'wrong_answers'),
            'description': 'Можно менять очки студента - ранг обновится автоматически'
        }),
        ('Текущий ранг', {
            'fields': ('current_rank_display', 'progress_display'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('current_rank_display', 'progress_display')

    def get_rank_display(self, obj):
        """Отобразить ранг в списке"""
        return obj.get_rank_name()
    get_rank_display.short_description = 'Ранг'

    def accuracy(self, obj):
        """Показать точность ответов"""
        return f"{obj.get_accuracy_percentage()}%"
    accuracy.short_description = 'Точность'

    def current_rank_display(self, obj):
        """Отобразить информацию о текущем ранге"""
        rank = obj.get_rank()
        if rank:
            next_rank = obj.get_next_rank()
            if next_rank:
                points_to_next = obj.get_points_to_next_rank()
                return f"{rank.emoji} {rank.name} | Очков до {next_rank.name}: {points_to_next}"
            else:
                return f"{rank.emoji} {rank.name} (Максимальный ранг!)"
        return "Без ранга"
    current_rank_display.short_description = 'Информация о ранге'

    def progress_display(self, obj):
        """Отобразить прогресс к следующему рангу"""
        progress = obj.get_progress_percentage()
        next_rank = obj.get_next_rank()
        if next_rank:
            return f"{progress}% к {next_rank.name}"
        return "100% - максимальный ранг"
    progress_display.short_description = 'Прогресс'


# Заменяем стандартную админку User на нашу
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
