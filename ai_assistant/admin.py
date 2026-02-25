from django.contrib import admin
from .models import KnowledgeCard, AIConversation, StudyProgress, QuestionCategory, UserProfile, Rank, SubjectScore


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
        ('Метаданные', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)


@admin.register(AIConversation)
class AIConversationAdmin(admin.ModelAdmin):
    list_display = ('user', 'student_question_short', 'created_at')
    list_filter = ('user', 'created_at')
    search_fields = ('student_question', 'ai_response')
    readonly_fields = ('created_at',)

    def student_question_short(self, obj):
        return obj.student_question[:50] + "..." if len(obj.student_question) > 50 else obj.student_question
    student_question_short.short_description = 'Вопрос'


@admin.register(StudyProgress)
class StudyProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'knowledge_card', 'mastery_level', 'access_count', 'last_accessed')
    list_filter = ('mastery_level', 'user', 'knowledge_card__subject')
    search_fields = ('user__username', 'knowledge_card__title')
    readonly_fields = ('last_accessed',)


@admin.register(QuestionCategory)
class QuestionCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'subject')
    list_filter = ('subject',)
    search_fields = ('name', 'description')


@admin.register(SubjectScore)
class SubjectScoreAdmin(admin.ModelAdmin):
    list_display = ('user', 'subject', 'points', 'accuracy', 'updated_at')
    list_filter = ('subject', 'points')
    search_fields = ('user_profile__user__username', 'subject__name')
    
    def user(self, obj):
        return obj.user_profile.user.username
    user.short_description = 'Пользователь'
    
    def accuracy(self, obj):
        return f"{obj.get_accuracy_percentage()}%"
    accuracy.short_description = 'Точность'


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
