from django.db import models
from django.contrib.auth.models import User
from schedule.models import Subject
from django.db.models.signals import post_save
from django.dispatch import receiver


class KnowledgeCard(models.Model):
    """Карточка знаний для объяснения тем"""
    title = models.CharField(max_length=200, verbose_name="Название темы")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, verbose_name="Предмет")
    difficulty_level = models.IntegerField(
        choices=[(1, 'Начальный'), (2, 'Средний'), (3, 'Продвинутый')],
        default=1,
        verbose_name="Уровень сложности"
    )
    
    # Основное содержание
    main_definition = models.TextField(verbose_name="Основное определение")
    simple_explanation = models.TextField(verbose_name="Простое объяснение")
    
    # Примеры и аналогии
    examples = models.TextField(blank=True, verbose_name="Примеры")
    analogies = models.TextField(blank=True, verbose_name="Аналогии")
    
    # Дополнительная информация
    key_concepts = models.TextField(blank=True, verbose_name="Ключевые концепции")
    common_mistakes = models.TextField(blank=True, verbose_name="Частые ошибки")
    
    # Метаданные
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.title} - {self.subject.name}"


class AIConversation(models.Model):
    """История диалогов с AI-ассистентом"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    student_question = models.TextField(verbose_name="Вопрос студента")
    ai_response = models.TextField(verbose_name="Ответ AI")
    related_cards = models.ManyToManyField(KnowledgeCard, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.student_question[:50]}..."


class StudyProgress(models.Model):
    """Прогресс изучения тем студентом"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    knowledge_card = models.ForeignKey(KnowledgeCard, on_delete=models.CASCADE)
    mastery_level = models.IntegerField(
        choices=[(1, 'Не изучено'), (2, 'В процессе'), (3, 'Изучено'), (4, 'Освоено')],
        default=1,
        verbose_name="Уровень освоения"
    )
    last_accessed = models.DateTimeField(auto_now=True)
    access_count = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ['user', 'knowledge_card']
    
    def __str__(self):
        return f"{self.user.username} - {self.knowledge_card.title}"


class QuestionCategory(models.Model):
    """Категории вопросов для AI-ассистента"""
    name = models.CharField(max_length=100, verbose_name="Название категории")
    description = models.TextField(blank=True, verbose_name="Описание")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, verbose_name="Предмет")
    
    def __str__(self):
        return f"{self.name} - {self.subject.name}"


class Rank(models.Model):
    """Система рангов для студентов"""
    RANK_COLORS = [
        ('primary', 'Синий (IRON)'),
        ('success', 'Зеленый (BRONZE)'),
        ('info', 'Голубой (SILVER)'),
        ('warning', 'Оранжевый (GOLD)'),
        ('danger', 'Красный (PLATINUM)'),
        ('purple', 'Фиолетовый (DIAMOND)'),
        ('dark', 'Темный (MASTER)'),
        ('gold', 'Золотой (GRANDMASTER)'),
    ]
    
    level = models.IntegerField(unique=True, verbose_name="Уровень ранга")
    name = models.CharField(max_length=50, verbose_name="Название ранга")
    emoji = models.CharField(max_length=10, verbose_name="Эмодзи ранга")
    min_points = models.IntegerField(verbose_name="Минимум очков")
    max_points = models.IntegerField(null=True, blank=True, verbose_name="Максимум очков")
    color = models.CharField(
        max_length=20, 
        choices=RANK_COLORS,
        default='primary',
        verbose_name="Цвет рамки"
    )
    description = models.TextField(blank=True, verbose_name="Описание ранга")
    
    class Meta:
        ordering = ['level']
        verbose_name = "Ранг"
        verbose_name_plural = "Ранги"
    
    def __str__(self):
        return f"{self.emoji} {self.name} ({self.min_points}-{self.max_points or '∞'})"
    
    @staticmethod
    def get_rank_by_points(points):
        """Получить ранг по количеству очков"""
        try:
            return Rank.objects.filter(
                min_points__lte=points
            ).exclude(
                max_points__isnull=False,
                max_points__lt=points
            ).order_by('-min_points').first()
        except:
            return Rank.objects.filter(level=1).first()


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    points = models.IntegerField(default=0, verbose_name="Очки")
    correct_answers = models.IntegerField(default=0, verbose_name="Правильные ответы")
    wrong_answers = models.IntegerField(default=0, verbose_name="Неправильные ответы")

    class Meta:
        verbose_name = "Профиль пользователя"
        verbose_name_plural = "Профили пользователей"

    def __str__(self):
        return self.user.username
    
    def get_rank(self):
        """Получить текущий ранг студента"""
        return Rank.get_rank_by_points(self.points)
    
    def get_rank_name(self):
        """Получить название ранга с эмодзи"""
        rank = self.get_rank()
        if rank:
            return f"{rank.emoji} {rank.name}"
        return "Без ранга"
    
    def get_rank_color(self):
        """Получить цвет ранга"""
        rank = self.get_rank()
        if rank:
            return rank.color
        return "secondary"
    
    def get_rank_level(self):
        """Получить уровень ранга"""
        rank = self.get_rank()
        if rank:
            return rank.level
        return 0
    
    def get_points_to_next_rank(self):
        """Получить количество очков до следующего ранга"""
        current_rank = self.get_rank()
        if not current_rank:
            return 0
        
        next_rank = Rank.objects.filter(level__gt=current_rank.level).order_by('level').first()
        if next_rank:
            return max(0, next_rank.min_points - self.points)
        return 0
    
    def get_next_rank(self):
        """Получить информацию о следующем ранге"""
        current_rank = self.get_rank()
        if not current_rank:
            return None
        
        next_rank = Rank.objects.filter(level__gt=current_rank.level).order_by('level').first()
        return next_rank
    
    def get_rank_class(self):
        """Получить CSS класс для рамки аватара"""
        rank = self.get_rank()
        if not rank:
            return "rank-iron"
        
        rank_map = {
            1: 'iron',
            2: 'bronze', 
            3: 'silver',
            4: 'gold',
            5: 'platinum',
            6: 'diamond',
            7: 'master',
            8: 'grandmaster'
        }
        return f"rank-{rank_map.get(rank.level, 'iron')}"
    
    def get_progress_percentage(self):
        """Получить процент прогресса до следующего ранга"""
        current_rank = self.get_rank()
        if not current_rank:
            if self.points < 500:
                return int((self.points / 500) * 100)
            return 0
        
        next_rank = self.get_next_rank()
        if not next_rank:
            return 100  # Максимальный ранг
        
        points_in_current = self.points - current_rank.min_points
        points_needed = next_rank.min_points - current_rank.min_points
        
        if points_needed <= 0:
            return 100
        
        percentage = int((points_in_current / points_needed) * 100)
        return min(100, max(0, percentage))
    
    def get_accuracy_percentage(self):
        """Получить процент точности ответов"""
        total = self.correct_answers + self.wrong_answers
        if total == 0:
            return 0
        return int((self.correct_answers / total) * 100)


class SubjectScore(models.Model):
    """Очки студента по каждому предмету"""
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='subject_scores')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    points = models.IntegerField(default=0, verbose_name="Очки по предмету")
    correct_answers = models.IntegerField(default=0, verbose_name="Правильные ответы")
    wrong_answers = models.IntegerField(default=0, verbose_name="Неправильные ответы")
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user_profile', 'subject']
        verbose_name = "Рейтинг по предмету"
        verbose_name_plural = "Рейтинги по предметам"
        ordering = ['-points']
    
    def __str__(self):
        return f"{self.user_profile.user.username} - {self.subject.name} ({self.points} очков)"
    
    def get_accuracy_percentage(self):
        """Получить процент точности по предмету"""
        total = self.correct_answers + self.wrong_answers
        if total == 0:
            return 0
        return int((self.correct_answers / total) * 100)


@receiver(post_save, sender=User)
def _create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
