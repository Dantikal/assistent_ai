from django.db import models
from django.contrib.auth.models import User
from schedule.models import Subject, PersonalScheduleItem
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone


class TaskCompletion(models.Model):
    """Отслеживание выполнения задач в расписании"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    schedule_item = models.ForeignKey(PersonalScheduleItem, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Персональная задача")
    class_schedule = models.ForeignKey('schedule.ClassSchedule', on_delete=models.CASCADE, null=True, blank=True, verbose_name="Занятие из расписания")
    is_completed = models.BooleanField(default=False, verbose_name="Выполнено")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Время выполнения")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Выполнение задачи"
        verbose_name_plural = "Выполнения задач"
        constraints = [
            models.UniqueConstraint(fields=['user', 'schedule_item'], name='unique_user_schedule_item'),
            models.UniqueConstraint(fields=['user', 'class_schedule'], name='unique_user_class_schedule'),
        ]
    
    def __str__(self):
        if self.schedule_item:
            return f"{self.user.username} - {self.schedule_item.title}: {'✓' if self.is_completed else '○'}"
        elif self.class_schedule:
            return f"{self.user.username} - {self.class_schedule.subject.name}: {'✓' if self.is_completed else '○'}"
        return f"{self.user.username} - Неизвестная задача: {'✓' if self.is_completed else '○'}"
    
    def save(self, *args, **kwargs):
        if self.is_completed and not self.completed_at:
            self.completed_at = timezone.now()
        elif not self.is_completed:
            self.completed_at = None
        super().save(*args, **kwargs)


class NoteCompletion(models.Model):
    """Отслеживание выполнения заметок в расписании"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    schedule_note = models.ForeignKey('schedule.ScheduleNote', on_delete=models.CASCADE, verbose_name="Заметка")
    is_completed = models.BooleanField(default=False, verbose_name="Выполнено")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Время выполнения")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Выполнение заметки"
        verbose_name_plural = "Выполнения заметок"
        unique_together = ['user', 'schedule_note']
    
    def __str__(self):
        return f"{self.user.username} - {self.schedule_note.title}: {'✓' if self.is_completed else '○'}"
    
    def save(self, *args, **kwargs):
        if self.is_completed and not self.completed_at:
            self.completed_at = timezone.now()
        elif not self.is_completed:
            self.completed_at = None
        super().save(*args, **kwargs)


class PointsAdjustment(models.Model):
    """История изменений очков пользователя"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    points_change = models.IntegerField(verbose_name="Изменение очков")
    reason = models.CharField(max_length=200, verbose_name="Причина изменения")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата изменения")
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name="points_adjustments_made",
        verbose_name="Кто изменил"
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Изменение очков"
        verbose_name_plural = "Изменения очков"
    
    def __str__(self):
        return f"{self.user.username}: {self.points_change:+d} - {self.reason}"


class StudentNote(models.Model):
    """Заметки студента"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    title = models.CharField(max_length=200, verbose_name="Заголовок")
    content = models.TextField(verbose_name="Содержание заметки")
    
    # Категории и приоритеты
    PRIORITY_CHOICES = [
        ('low', 'Низкий'),
        ('medium', 'Средний'), 
        ('high', 'Высокий'),
        ('urgent', 'Срочный'),
    ]
    
    CATEGORY_CHOICES = [
        ('general', 'Общее'),
        ('homework', 'Домашнее задание'),
        ('exam', 'Экзамен'),
        ('project', 'Проект'),
        ('idea', 'Идея'),
        ('reminder', 'Напоминание'),
    ]
    
    priority = models.CharField(
        max_length=10, 
        choices=PRIORITY_CHOICES, 
        default='medium',
        verbose_name="Приоритет"
    )
    
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='general',
        verbose_name="Категория"
    )
    
    # Даты
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")
    
    # Статус выполнения
    is_completed = models.BooleanField(default=False, verbose_name="Выполнено")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Время выполнения")
    deadline = models.DateTimeField(null=True, blank=True, verbose_name="Срок выполнения")
    
    # Дополнительные статусы
    is_pinned = models.BooleanField(default=False, verbose_name="Закреплено")
    
    # Связь с предметом (опционально)
    subject = models.ForeignKey(
        Subject, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name="Предмет"
    )
    
    # Теги для удобного поиска
    tags = models.CharField(
        max_length=500, 
        blank=True, 
        help_text="Введите теги через запятую",
        verbose_name="Теги"
    )
    
    class Meta:
        ordering = ['-is_pinned', '-created_at']
        verbose_name = "Заметка студента"
        verbose_name_plural = "Заметки студентов"
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"
    
    def save(self, *args, **kwargs):
        if self.is_completed and not self.completed_at:
            self.completed_at = timezone.now()
        elif not self.is_completed:
            self.completed_at = None
        super().save(*args, **kwargs)
    
    def get_tags_list(self):
        """Возвращает список тегов"""
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
    
    def is_overdue(self):
        """Проверяет, просрочена ли заметка"""
        if self.deadline and not self.is_completed:
            return timezone.now() > self.deadline
        return False


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
    
    def get_leaderboard_position(self):
        """Получить позицию в таблице лидеров"""
        try:
            from django.db.models import Count
            # Считаем позицию пользователя по очкам
            higher_scores = UserProfile.objects.filter(points__gt=self.points).count()
            return higher_scores + 1
        except:
            return None
    
    @property
    def is_top_player(self):
        """Проверить является ли пользователь топ-игроком (топ-10)"""
        try:
            position = self.get_leaderboard_position()
            return position and position <= 10
        except:
            return False
    
    @property
    def leaderboard_position(self):
        """Получить позицию в рейтинге для шаблона"""
        return self.get_leaderboard_position()


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


class TaskCategory(models.Model):
    """Категории задач для трекера"""
    name = models.CharField(max_length=100, verbose_name="Название категории")
    color = models.CharField(max_length=7, default="#667eea", verbose_name="Цвет категории (hex)")
    icon = models.CharField(max_length=50, default="fas fa-tasks", verbose_name="Иконка (Font Awesome)")
    description = models.TextField(blank=True, verbose_name="Описание")
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Категория задач"
        verbose_name_plural = "Категории задач"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class TaskTracker(models.Model):
    """Трекер задач студента"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(TaskCategory, on_delete=models.CASCADE, verbose_name="Категория")
    title = models.CharField(max_length=200, verbose_name="Заголовок задачи")
    description = models.TextField(blank=True, verbose_name="Описание задачи")
    deadline = models.DateTimeField(null=True, blank=True, verbose_name="Дедлайн")
    is_completed = models.BooleanField(default=False, verbose_name="Выполнено")
    points = models.IntegerField(default=1, verbose_name="Баллы за выполнение")
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата выполнения")
    
    class Meta:
        verbose_name = "Задача"
        verbose_name_plural = "Задачи"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"
    
    def save(self, *args, **kwargs):
        # Если задача выполнена и не была выполнена ранее
        if self.is_completed and not self.completed_at:
            self.completed_at = timezone.now()
            # Начисляем баллы пользователю
            profile, _ = UserProfile.objects.get_or_create(user=self.user)
            profile.points += self.points
            profile.save(update_fields=['points'])
            
            # Обновляем статистику по общему рейтингу
            from .views import update_subject_score
            update_subject_score(profile, 'Общий рейтинг', self.points, 1, 0)
        elif not self.is_completed and self.completed_at:
            # Если статус выполнения снят
            self.completed_at = None
            # Убираем баллы
            profile, _ = UserProfile.objects.get_or_create(user=self.user)
            profile.points = max(0, profile.points - self.points)
            profile.save(update_fields=['points'])
            
            # Обновляем статистику по общему рейтингу
            from .views import update_subject_score
            update_subject_score(profile, 'Общий рейтинг', -self.points, 0, 1)
        
        super().save(*args, **kwargs)


@receiver(post_save, sender=User)
def _create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


class ChessGame(models.Model):
    """Шахматная партия"""
    RESULT_CHOICES = [
        ('white_win', 'Победа белых'),
        ('black_win', 'Победа черных'),
        ('draw', 'Ничья'),
        ('playing', 'Игра идет'),
        ('abandoned', 'Брошена'),
    ]
    
    DIFFICULTY_CHOICES = [
        ('easy', 'Легкий'),
        ('medium', 'Нормальный'),
        ('hard', 'Сложный'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    bot_difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, verbose_name="Сложность бота")
    result = models.CharField(max_length=20, choices=RESULT_CHOICES, default='playing', verbose_name="Результат")
    user_color = models.CharField(max_length=5, choices=[('white', 'Белые'), ('black', 'Черные')], default='white', verbose_name="Цвет пользователя")
    
    # Позиция в формате FEN
    fen_position = models.TextField(default='rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1', verbose_name="Позиция FEN")
    
    # История ходов в формате PGN
    moves_history = models.TextField(blank=True, verbose_name="История ходов")
    
    # Время партии
    started_at = models.DateTimeField(auto_now_add=True, verbose_name="Начало партии")
    ended_at = models.DateTimeField(null=True, blank=True, verbose_name="Конец партии")
    
    # Очки за партию
    points_earned = models.IntegerField(default=0, verbose_name="Заработанные очки")
    
    class Meta:
        verbose_name = "Шахматная партия"
        verbose_name_plural = "Шахматные партии"
        ordering = ['-started_at']
    
    def __str__(self):
        return f"Шахматы: {self.user.username} vs {self.get_bot_difficulty_display()} ({self.get_result_display()})"
    
    def calculate_points(self):
        """Рассчитывает очки за партию"""
        if self.result == 'playing':
            return 0
        
        # Базовые очки в зависимости от сложности
        base_points = {
            'easy': 10,
            'medium': 25,
            'hard': 50,
        }
        
        # Множитель в зависимости от результата
        result_multiplier = {
            'white_win': 1.0 if self.user_color == 'white' else 0.0,
            'black_win': 1.0 if self.user_color == 'black' else 0.0,
            'draw': 0.5,
            'abandoned': 0.0,
        }
        
        points = int(base_points[self.bot_difficulty] * result_multiplier.get(self.result, 0))
        
        # Бонус за быструю победу
        if self.result in ['white_win', 'black_win'] and self.ended_at:
            duration = (self.ended_at - self.started_at).total_seconds()
            if duration < 60:  # Меньше минуты
                points = int(points * 1.5)
            elif duration < 300:  # Меньше 5 минут
                points = int(points * 1.2)
        
        return points
    
    def save(self, *args, **kwargs):
        # Рассчитываем очки при сохранении результата
        if self.result != 'playing' and not self.points_earned:
            self.points_earned = self.calculate_points()
            # Добавляем очки пользователю
            if self.points_earned > 0:
                profile, _ = UserProfile.objects.get_or_create(user=self.user)
                profile.points += self.points_earned
                profile.save()
        
        # Устанавливаем время окончания
        if self.result != 'playing' and not self.ended_at:
            from django.utils import timezone
            self.ended_at = timezone.now()
        
        super().save(*args, **kwargs)


class ChessStats(models.Model):
    """Статистика шахмат пользователя"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    
    # Общая статистика
    games_played = models.IntegerField(default=0, verbose_name="Сыграно партий")
    games_won = models.IntegerField(default=0, verbose_name="Побед")
    games_drawn = models.IntegerField(default=0, verbose_name="Ничьих")
    games_lost = models.IntegerField(default=0, verbose_name="Поражений")
    
    # Статистика по сложностям
    easy_wins = models.IntegerField(default=0, verbose_name="Побед над легкими")
    medium_wins = models.IntegerField(default=0, verbose_name="Побед над нормальными")
    hard_wins = models.IntegerField(default=0, verbose_name="Побед над сложными")
    
    # Очки в шахматах
    chess_points = models.IntegerField(default=0, verbose_name="Очков в шахматах")
    
    # Лучшие достижения
    fastest_win = models.DurationField(null=True, blank=True, verbose_name="Самая быстрая победа")
    current_streak = models.IntegerField(default=0, verbose_name="Текущая серия побед")
    best_streak = models.IntegerField(default=0, verbose_name="Лучшая серия побед")
    
    class Meta:
        verbose_name = "Шахматная статистика"
        verbose_name_plural = "Шахматная статистика"
    
    def __str__(self):
        return f"Статистика шахмат {self.user.username}"
    
    @property
    def win_rate(self):
        """Процент побед"""
        if self.games_played == 0:
            return 0
        return round((self.games_won / self.games_played) * 100, 1)
    
    def update_stats(self, game):
        """Обновляет статистику после партии"""
        self.games_played += 1
        
        if game.result == 'draw':
            self.games_drawn += 1
            self.current_streak = 0
        elif (game.result == 'white_win' and game.user_color == 'white') or \
             (game.result == 'black_win' and game.user_color == 'black'):
            self.games_won += 1
            self.current_streak += 1
            self.best_streak = max(self.best_streak, self.current_streak)
            
            # Обновляем победы по сложностям
            if game.bot_difficulty == 'easy':
                self.easy_wins += 1
            elif game.bot_difficulty == 'medium':
                self.medium_wins += 1
            elif game.bot_difficulty == 'hard':
                self.hard_wins += 1
            
            # Обновляем самую быструю победу
            if game.ended_at:
                duration = game.ended_at - game.started_at
                if self.fastest_win is None or duration < self.fastest_win:
                    self.fastest_win = duration
        else:
            self.games_lost += 1
            self.current_streak = 0
        
        self.chess_points += game.points_earned
        self.save()
        
        # Обновляем очки по предмету "Шахматы" в общей системе
        try:
            from .views import update_subject_score
            profile = UserProfile.objects.get(user=self.user)
            update_subject_score(profile, 'Шахматы', game.points_earned, 1 if game.result != 'draw' else 0, 0)
        except:
            pass


class Post(models.Model):
    """Посты пользователей"""
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    content = models.TextField(verbose_name="Текст поста")
    image = models.ImageField(upload_to='posts/', blank=True, null=True, verbose_name="Изображение")
    post_type = models.CharField(
        max_length=20,
        choices=[
            ('text', 'Текст'),
            ('image', 'Изображение'),
            ('poll', 'Опрос'),
        ],
        default='text',
        verbose_name="Тип поста"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    
    class Meta:
        verbose_name = "Пост"
        verbose_name_plural = "Посты"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Пост от {self.author.username} ({self.created_at.strftime('%d.%m.%Y %H:%M')})"
    
    def get_likes_count(self):
        return self.likes.count()
    
    def get_comments_count(self):
        return self.comments.count()
    
    def is_liked_by(self, user):
        if not user.is_authenticated:
            return False
        return self.likes.filter(user=user).exists()


class PollOption(models.Model):
    """Варианты ответа для опросов"""
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='poll_options')
    text = models.CharField(max_length=200, verbose_name="Текст варианта")
    votes_count = models.IntegerField(default=0, verbose_name="Количество голосов")
    
    class Meta:
        verbose_name = "Вариант опроса"
        verbose_name_plural = "Варианты опроса"
    
    def __str__(self):
        return f"{self.text} ({self.votes_count} голосов)"


class PollVote(models.Model):
    """Голоса в опросах"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    option = models.ForeignKey(PollOption, on_delete=models.CASCADE)
    voted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'option']
        verbose_name = "Голос в опросе"
        verbose_name_plural = "Голоса в опросах"


class PostLike(models.Model):
    """Лайки постов"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'post']
        verbose_name = "Лайк поста"
        verbose_name_plural = "Лайки постов"


class Comment(models.Model):
    """Комментарии к постам"""
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(verbose_name="Текст комментария")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    
    class Meta:
        verbose_name = "Комментарий"
        verbose_name_plural = "Комментарии"
        ordering = ['created_at']
    
    def __str__(self):
        return f"Комментарий от {self.author.username} к посту {self.post.id}"
