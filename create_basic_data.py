"""
Создание базовых данных для StudySense
"""
import os
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'studysense.settings')
django.setup()

from django.contrib.auth.models import User
from schedule.models import Teacher, Subject, ClassSchedule, Student


def create_basic_data():
    """Создание базовых данных для демонстрации"""
    
    print("🎓 Создание базовых данных для StudySense...")
    
    # Создание преподавателей
    teachers_data = [
        {
            'last_name': 'Иванов',
            'first_name': 'Иван',
            'patronymic': 'Петрович',
            'email': 'ivanov@example.com',
            'phone': '+7(999)123-45-67'
        },
        {
            'last_name': 'Петрова',
            'first_name': 'Мария',
            'patronymic': 'Сергеевна',
            'email': 'petrova@example.com',
            'phone': '+7(999)987-65-43'
        },
        {
            'last_name': 'Сидоров',
            'first_name': 'Алексей',
            'patronymic': 'Викторович',
            'email': 'sidorov@example.com',
            'phone': '+7(999)456-78-90'
        }
    ]
    
    teachers = []
    for teacher_data in teachers_data:
        teacher, created = Teacher.objects.get_or_create(
            last_name=teacher_data['last_name'],
            first_name=teacher_data['first_name'],
            patronymic=teacher_data['patronymic'],
            defaults={
                'email': teacher_data['email'],
                'phone': teacher_data['phone']
            }
        )
        teachers.append(teacher)
        if created:
            print(f"✅ Создан преподаватель: {teacher.get_full_name()}")
        else:
            print(f"ℹ️ Преподаватель уже существует: {teacher.get_full_name()}")
    
    # Создание предметов
    subjects_data = [
        {
            'name': 'Математический анализ',
            'description': 'Изучение функций, пределов, производных, интегралов',
            'teacher': teachers[0]  # Иванов И.П.
        },
        {
            'name': 'Линейная алгебра',
            'description': 'Векторы, матрицы, системы линейных уравнений',
            'teacher': teachers[0]  # Иванов И.П.
        },
        {
            'name': 'Программирование',
            'description': 'Основы алгоритмизации и языки программирования',
            'teacher': teachers[1]  # Петрова М.С.
        },
        {
            'name': 'Базы данных',
            'description': 'Проектирование и использование баз данных',
            'teacher': teachers[1]  # Петрова М.С.
        },
        {
            'name': 'Физика',
            'description': 'Механика, термодинамика, электромагнетизм',
            'teacher': teachers[2]  # Сидоров А.В.
        },
        {
            'name': 'Химия',
            'description': 'Органическая и неорганическая химия',
            'teacher': teachers[2]  # Сидоров А.В.
        }
    ]
    
    subjects = []
    for subject_data in subjects_data:
        subject, created = Subject.objects.get_or_create(
            name=subject_data['name'],
            defaults={
                'description': subject_data['description'],
                'teacher': subject_data['teacher']
            }
        )
        subjects.append(subject)
        if created:
            print(f"✅ Создан предмет: {subject.name}")
        else:
            print(f"ℹ️ Предмет уже существует: {subject.name}")
    
    # Создание тестового студента
    try:
        # Проверяем, есть ли пользователь admin
        admin_user = User.objects.get(username='admin')
        
        # Создаем или получаем студента
        student, created = Student.objects.get_or_create(
            user=admin_user,
            defaults={
                'group': 'ИТ-301',
                'telegram_chat_id': '123456789'
            }
        )
        
        if created:
            print(f"✅ Создан студент: {student}")
        else:
            print(f"ℹ️ Студент уже существует: {student}")
            
        # Создаем тестовое расписание для группы ИТ-301
        create_sample_schedule(student, subjects)
        
    except User.DoesNotExist:
        print("❌ Пользователь 'admin' не найден!")
    
    print("\n🎉 Базовые данные созданы!")
    print("Теперь студенты могут составлять расписание через интерфейс.")


def create_sample_schedule(student, subjects):
    """Создание примера расписания"""
    
    schedule_data = [
        # Понедельник
        {'day': 1, 'subject': subjects[0], 'start': '09:00', 'end': '10:30', 'room': '101'},  # Матанализ
        {'day': 1, 'subject': subjects[2], 'start': '10:45', 'end': '12:15', 'room': '205'},  # Программирование
        {'day': 1, 'subject': subjects[4], 'start': '13:15', 'end': '14:45', 'room': '301'},  # Физика
        
        # Вторник
        {'day': 2, 'subject': subjects[1], 'start': '09:00', 'end': '10:30', 'room': '102'},  # Лин. алгебра
        {'day': 2, 'subject': subjects[3], 'start': '10:45', 'end': '12:15', 'room': '206'},  # Базы данных
        
        # Среда
        {'day': 3, 'subject': subjects[0], 'start': '09:00', 'end': '10:30', 'room': '103'},  # Матанализ
        {'day': 3, 'subject': subjects[5], 'start': '13:15', 'end': '14:45', 'room': '302'},  # Химия
        
        # Четверг
        {'day': 4, 'subject': subjects[2], 'start': '09:00', 'end': '10:30', 'room': '207'},  # Программирование
        {'day': 4, 'subject': subjects[1], 'start': '10:45', 'end': '12:15', 'room': '104'},  # Лин. алгебра
        
        # Пятница
        {'day': 5, 'subject': subjects[4], 'start': '09:00', 'end': '10:30', 'room': '303'},  # Физика
        {'day': 5, 'subject': subjects[3], 'start': '10:45', 'end': '12:15', 'room': '208'},  # Базы данных
    ]
    
    for item in schedule_data:
        schedule, created = ClassSchedule.objects.get_or_create(
            group=student.group,
            day_of_week=item['day'],
            subject=item['subject'],
            start_time=item['start'],
            end_time=item['end'],
            defaults={
                'room': item['room'],
                'is_active': True
            }
        )
        
        if created:
            print(f"✅ Добавлена пара: {item['subject'].name} ({item['day']} день)")
        else:
            print(f"ℹ️ Пара уже существует: {item['subject'].name} ({item['day']} день)")


if __name__ == '__main__':
    create_basic_data()
