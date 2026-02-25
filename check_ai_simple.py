"""
Простая проверка AI без Django
"""
import os

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'studysense.settings')

import django
django.setup()

from ai_assistant.ai_service import ai_assistant

def check_ai_status():
    """Проверка статуса AI-ассистента"""
    status = ai_assistant.get_status()
    
    print("🤖 Статус AI-ассистента:")
    print(f"   Включен: {'✅ Да' if status['enabled'] else '❌ Нет'}")
    print(f"   Режим: {status['mode'].upper()}")
    
    if status['mode'] == 'ollama':
        print(f"   Модель: {status['model']}")
        print(f"   Хост: {status['host']}")
        print("\n📝 Для запуска Ollama:")
        print("   1. Скачайте с https://ollama.com/download")
        print("   2. Запустите: ollama serve")
        print(f"   3. Скачайте модель: ollama pull {status['model']}")
        
    elif status['mode'] == 'openai':
        print(f"   Модель: {status['model']}")
        print("\n📝 Для настройки OpenAI:")
        print("   1. Получите API ключ на https://platform.openai.com/")
        print("   2. Добавьте ключ в settings.py: OPENAI_API_KEY")
        
    else:
        print("\n📝 Для включения AI:")
        print("   1. Настройте Ollama (бесплатно)")
        print("   2. Или настройте OpenAI API (платно)")

if __name__ == "__main__":
    check_ai_status()
