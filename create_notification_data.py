"""
Создание начальных данных для тестирования уведомлений
"""
import os
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'studysense.settings')
django.setup()

from schedule.models import StudentGroup, Subject, Teacher, ClassSchedule
from notifications.models import NotificationSettings
from django.contrib.auth.models import User


def create_notification_data():
    """Создание данных для тестирования уведомлений"""
    
    print("🔄 Создание данных для тестирования уведомлений...")
    
    # 1. Создаем настройки уведомлений
    settings, created = NotificationSettings.objects.get_or_create(
        id=1,  # Только одна запись
        defaults={
            'enable_notifications': True,
            'notification_before_minutes': 10,
            'late_threshold_minutes': 5,
        }
    )
    if created:
        print("✅ Настройки уведомлений созданы")
    else:
        print("✅ Настройки уведомлений уже существуют")
    
    # 2. Создаем тестовые группы
    groups = []
    group_names = ['ИТ-301', 'ИТ-302', 'ИТ-303']
    
    for group_name in group_names:
        group, created = StudentGroup.objects.get_or_create(
            name=group_name,
            defaults={
                'description': f'Группа {group_name}',
                'faculty': 'Факультет информационных технологий',
                'course': 3,
                'is_active': True
            }
        )
        groups.append(group)
        if created:
            print(f"✅ Группа {group_name} создана")
    
    # 3. Создаем преподавателей
    teachers = []
    teacher_data = [
        {'first_name': 'Иван', 'last_name': 'Петров', 'patronymic': 'Сергеевич'},
        {'first_name': 'Мария', 'last_name': 'Иванова', 'patronymic': 'Алексеевна'},
        {'first_name': 'Алексей', 'last_name': 'Сидоров', 'patronymic': 'Викторович'},
    ]
    
    for data in teacher_data:
        teacher, created = Teacher.objects.get_or_create(
            first_name=data['first_name'],
            last_name=data['last_name'],
            patronymic=data['patronymic'],
            defaults={
                'email': f"{data['first_name'].lower()}.{data['last_name'].lower()}@university.ru",
                'phone': f"+7(900)123-45-6{len(teachers)}"
            }
        )
        teachers.append(teacher)
        if created:
            print(f"✅ Преподаватель {teacher.get_full_name()} создан")
    
    # 4. Создаем предметы
    subjects = []
    subject_data = [
        {'name': 'Программирование', 'teacher': teachers[0]},
        {'name': 'Базы данных', 'teacher': teachers[1]},
        {'name': 'Алгоритмы', 'teacher': teachers[2]},
    ]
    
    for data in subject_data:
        subject, created = Subject.objects.get_or_create(
            name=data['name'],
            defaults={
                'teacher': data['teacher'],
                'description': f'Курс по изучению {data["name"].lower()}'
            }
        )
        subjects.append(subject)
        if created:
            print(f"✅ Предмет {subject.name} создан")
    
    # 5. Создаем расписание на сегодня
    from datetime import date, time
    today = date.today()
    day_of_week = today.weekday() + 1  # Конвертация в формат модели (1-7)
    
    schedule_data = [
        {
            'subject': subjects[0],
            'group': groups[0],
            'day_of_week': day_of_week,
            'start_time': time(9, 0),
            'end_time': time(10, 30),
            'room': '301'
        },
        {
            'subject': subjects[1],
            'group': groups[0],
            'day_of_week': day_of_week,
            'start_time': time(10, 45),
            'end_time': time(12, 15),
            'room': '302'
        },
        {
            'subject': subjects[2],
            'group': groups[1],
            'day_of_week': day_of_week,
            'start_time': time(9, 0),
            'end_time': time(10, 30),
            'room': '303'
        },
    ]
    
    for data in schedule_data:
        schedule, created = ClassSchedule.objects.get_or_create(
            subject=data['subject'],
            group=data['group'],
            day_of_week=data['day_of_week'],
            start_time=data['start_time'],
            end_time=data['end_time'],
            room=data['room'],
            defaults={'is_active': True}
        )
        if created:
            print(f"✅ Расписание {schedule.subject.name} для {schedule.group.name} создано")
    
    print("\n🎉 Данные для тестирования уведомлений созданы!")
    print("\n📋 Что теперь нужно сделать:")
    print("1. Запустите Redis: redis-server")
    print("2. Запустите Celery worker: celery -A studysense worker -l info")
    print("3. Запустите Celery beat: celery -A studysense beat -l info")
    print("4. Запустите Django сервер: python manage.py runserver")
    print("5. Зарегистрируйте студентов и добавьте их chat_id в профиле")
    print("\n🔔 Уведомления будут отправляться автоматически!")


if __name__ == '__main__':
    create_notification_data()
