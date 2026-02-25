"""
Тест URL patterns
"""
import os
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'studysense.settings')
django.setup()

from django.urls import get_resolver

try:
    resolver = get_resolver()
    patterns = resolver.url_patterns
    
    print("🔍 URL Patterns:")
    for pattern in patterns:
        print(f"  - {pattern.pattern}")
    
    print(f"\n✅ Всего URL patterns: {len(patterns)}")
    
    # Проверяем конкретные URL
    logout_url = None
    login_url = None
    
    for pattern in patterns:
        if pattern.name == 'logout':
            logout_url = pattern.pattern
        elif pattern.name == 'login':
            login_url = pattern.pattern
    
    print(f"\n🔍 Login URL: {login_url}")
    print(f"🔍 Logout URL: {logout_url}")
    
    if logout_url and login_url:
        print("✅ URL для входа/выхода настроены правильно")
    else:
        print("❌ Проблема с URL для входа/выхода")

except Exception as e:
    print(f"❌ Ошибка: {e}")
