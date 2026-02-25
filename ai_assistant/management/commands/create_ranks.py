from django.core.management.base import BaseCommand
from ai_assistant.models import Rank


class Command(BaseCommand):
    help = 'Создает начальные ранги для системы'

    def handle(self, *args, **options):
        # Удаляем старые ранги если есть
        Rank.objects.all().delete()

        # Создаем ранги
        ranks_data = [
            {
                'level': 1,
                'name': 'IRON (Железо)',
                'emoji': '🥉',
                'min_points': 0,
                'max_points': 500,
                'color': 'primary',
                'description': 'Начинающий студент. Первые шаги в обучении.'
            },
            {
                'level': 2,
                'name': 'BRONZE (Бронза)',
                'emoji': '🥈',
                'min_points': 500,
                'max_points': 2000,
                'color': 'warning',
                'description': 'Крепкий фундамент. Вы хорошо учитесь.'
            },
            {
                'level': 3,
                'name': 'SILVER (Серебро)',
                'emoji': '🥉',
                'min_points': 2000,
                'max_points': 5000,
                'color': 'info',
                'description': 'Серебряный студент. Хорошие результаты.'
            },
            {
                'level': 4,
                'name': 'GOLD (Золото)',
                'emoji': '🥈',
                'min_points': 5000,
                'max_points': 10000,
                'color': 'warning',
                'description': 'Золотой студент. Отличные знания!'
            },
            {
                'level': 5,
                'name': 'PLATINUM (Платина)',
                'emoji': '🥇',
                'min_points': 10000,
                'max_points': 25000,
                'color': 'danger',
                'description': 'Платиновый уровень. Вы эксперт!'
            },
            {
                'level': 6,
                'name': 'DIAMOND (Алмаз)',
                'emoji': '🥇',
                'min_points': 25000,
                'max_points': 50000,
                'color': 'info',
                'description': 'Бриллиантовый студент. Блестящие результаты!'
            },
            {
                'level': 7,
                'name': 'MASTER (Мастер)',
                'emoji': '👑',
                'min_points': 50000,
                'max_points': 100000,
                'color': 'dark',
                'description': 'Мастер своего дела. Завидная подготовка.'
            },
            {
                'level': 8,
                'name': 'GRANDMASTER',
                'emoji': '👑',
                'min_points': 100000,
                'max_points': None,
                'color': 'gold',
                'description': 'Гранд-мастер! Легендарный уровень достижения!'
            }
        ]

        for data in ranks_data:
            Rank.objects.create(**data)
            self.stdout.write(
                self.style.SUCCESS(f"✅ Создан ранг: {data['emoji']} {data['name']}")
            )

        self.stdout.write(self.style.SUCCESS("\n✨ Все ранги успешно созданы!"))
