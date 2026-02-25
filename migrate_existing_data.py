"""
Миграция существующих данных для работы с группами
"""
import os
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'studysense.settings')
django.setup()

from django.db import connection
from schedule.models import Student, StudentGroup, ClassSchedule


def migrate_existing_data():
    """Миграция существующих данных"""
    
    print("🔄 Миграция существующих данных...")
    
    # 1. Создаем группы для существующих названий
    existing_groups = {}
    students = Student.objects.all()
    
    for student in students:
        group_name = student.group if student.group else "Не указана"
        
        if group_name not in existing_groups:
            # Создаем группу
            group, created = StudentGroup.objects.get_or_create(
                name=group_name,
                defaults={
                    'description': f'Группа {group_name}',
                    'faculty': 'Не указан',
                    'course': 1,
                    'is_active': True
                }
            )
            existing_groups[group_name] = group
            if created:
                print(f"✅ Создана группа: {group_name}")
        
        # Обновляем студента
        student.group = existing_groups[group_name]
        student.save()
        print(f"✅ Обновлен студент: {student.user.username} -> {group_name}")
    
    # 2. Обновляем расписание
    schedules = ClassSchedule.objects.all()
    for schedule in schedules:
        if schedule.group:
            # Ищем соответствующую группу
            try:
                group = StudentGroup.objects.get(name=schedule.group)
                schedule.group = group
                schedule.save()
                print(f"✅ Обновлено расписание: {schedule.subject.name} -> {group.name}")
            except StudentGroup.DoesNotExist:
                print(f"⚠️ Группа не найдена для расписания: {schedule.group}")
    
    print("\n🎉 Миграция завершена!")
    print("Теперь можно использовать систему групп в админ панели.")


if __name__ == '__main__':
    migrate_existing_data()
