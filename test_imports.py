"""
Простой тест для проверки импортов
"""
import os
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'studysense.settings')
django.setup()

try:
    from ai_assistant.auth_views import CustomLogoutView
    print("✅ CustomLogoutView импортируется успешно")
except ImportError as e:
    print(f"❌ Ошибка импорта CustomLogoutView: {e}")

try:
    from ai_assistant import auth_views as auth_views_module
    print("✅ auth_views module импортируется успешно")
except ImportError as e:
    print(f"❌ Ошибка импорта auth_views module: {e}")

try:
    from ai_assistant import views as ai_views
    print("✅ ai_views импортируется успешно")
except ImportError as e:
    print(f"❌ Ошибка импорта ai_views: {e}")

print("\n🎯 Проверка завершена!")
