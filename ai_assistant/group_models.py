from django.db import models
from django.contrib.auth.models import User


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


class GroupSchedule(models.Model):
    """Шаблоны расписаний для групп"""
    group = models.ForeignKey(StudentGroup, on_delete=models.CASCADE, verbose_name="Группа")
    name = models.CharField(max_length=100, verbose_name="Название шаблона")
    description = models.TextField(blank=True, verbose_name="Описание")
    is_default = models.BooleanField(default=False, verbose_name="Шаблон по умолчанию")
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Создал")

    class Meta:
        ordering = ['name']
        verbose_name = "Шаблон расписания"
        verbose_name_plural = "Шаблоны расписаний"

    def __str__(self):
        return f"{self.name} - {self.group.name}"


class GroupScheduleItem(models.Model):
    """Элементы шаблона расписания"""
    template = models.ForeignKey(GroupSchedule, on_delete=models.CASCADE, verbose_name="Шаблон")
    subject = models.ForeignKey('schedule.Subject', on_delete=models.CASCADE, verbose_name="Предмет")
    day_of_week = models.IntegerField(verbose_name="День недели")
    start_time = models.TimeField(verbose_name="Время начала")
    end_time = models.TimeField(verbose_name="Время окончания")
    room = models.CharField(max_length=20, verbose_name="Аудитория")
    break_time = models.TimeField(null=True, blank=True, verbose_name="Время перерыва")

    class Meta:
        ordering = ['day_of_week', 'start_time']
        verbose_name = "Элемент шаблона"
        verbose_name_plural = "Элементы шаблона"

    def __str__(self):
        return f"{self.subject.name} - {self.template.group.name}"
