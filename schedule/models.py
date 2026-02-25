from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class StudentGroup(models.Model):
    """Модель учебных групп"""
    name = models.CharField(max_length=50, unique=True, verbose_name="Название группы")
    description = models.TextField(blank=True, verbose_name="Описание")
    faculty = models.CharField(max_length=100, blank=True, verbose_name="Факультет")
    course = models.IntegerField(verbose_name="Курс")
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True, verbose_name="Активна")

    class Meta:
        ordering = ['name']
        verbose_name = "Учебная группа"
        verbose_name_plural = "Учебные группы"

    def __str__(self):
        return f"{self.name} ({self.course} курс)"


class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    telegram_chat_id = models.CharField(max_length=50, blank=True, null=True)
    group = models.ForeignKey(StudentGroup, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Группа")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.group:
            return f"{self.user.get_full_name()} - {self.group.name}"
        return f"{self.user.get_full_name()} - Группа не указана"


class Teacher(models.Model):
    first_name = models.CharField(max_length=50, verbose_name="Имя")
    last_name = models.CharField(max_length=50, verbose_name="Фамилия")
    patronymic = models.CharField(max_length=50, blank=True, verbose_name="Отчество")
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True, verbose_name="Телефон")

    def get_full_name(self):
        return f"{self.last_name} {self.first_name} {self.patronymic}".strip()

    def __str__(self):
        return self.get_full_name()


class Subject(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название предмета")
    description = models.TextField(blank=True, verbose_name="Описание")
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, verbose_name="Преподаватель")

    def __str__(self):
        return self.name


class ClassSchedule(models.Model):
    DAYS_OF_WEEK = [
        (1, 'Понедельник'),
        (2, 'Вторник'),
        (3, 'Среда'),
        (4, 'Четверг'),
        (5, 'Пятница'),
        (6, 'Суббота'),
        (7, 'Воскресенье'),
    ]

    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, verbose_name="Предмет")
    group = models.ForeignKey(StudentGroup, on_delete=models.CASCADE, verbose_name="Группа")
    day_of_week = models.IntegerField(choices=DAYS_OF_WEEK, verbose_name="День недели")
    start_time = models.TimeField(verbose_name="Время начала")
    end_time = models.TimeField(verbose_name="Время окончания")
    room = models.CharField(max_length=20, verbose_name="Аудитория")
    is_active = models.BooleanField(default=True, verbose_name="Активно")

    def __str__(self):
        return f"{self.subject.name} - {self.group.name} - {self.get_day_of_week_display()}"

    class Meta:
        ordering = ['day_of_week', 'start_time']


class PersonalScheduleItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='personal_schedule_items')
    title = models.CharField(max_length=150, verbose_name="Название")
    day_of_week = models.IntegerField(choices=ClassSchedule.DAYS_OF_WEEK, verbose_name="День недели")
    start_time = models.TimeField(verbose_name="Время начала")
    end_time = models.TimeField(verbose_name="Время окончания")
    room = models.CharField(max_length=50, blank=True, verbose_name="Аудитория/место")
    notes = models.TextField(blank=True, verbose_name="Заметки")
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True, verbose_name="Активно")

    def __str__(self):
        return f"{self.title} - {self.get_day_of_week_display()}"

    class Meta:
        ordering = ['day_of_week', 'start_time']


class ScheduleNote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='schedule_notes')
    class_schedule = models.ForeignKey(ClassSchedule, on_delete=models.CASCADE, null=True, blank=True, related_name='schedule_notes')
    personal_item = models.ForeignKey(PersonalScheduleItem, on_delete=models.CASCADE, null=True, blank=True, related_name='schedule_notes')
    title = models.CharField(max_length=150, verbose_name="Заголовок")
    description = models.TextField(blank=True, verbose_name="Описание")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']


class Attendance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    schedule = models.ForeignKey(ClassSchedule, on_delete=models.CASCADE)
    date = models.DateField()
    is_present = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['student', 'schedule', 'date']
