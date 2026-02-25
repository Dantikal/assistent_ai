"""
URL configuration for studysense project.
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import get_user_model
from django.contrib.auth import views as auth_views  # ДОБАВЬТЕ ЭТУ СТРОКУ
from ai_assistant import views as ai_views
from ai_assistant.auth_views import CustomLogoutView, logout_view
from django.conf import settings
from django.conf.urls.static import static

User = get_user_model()

def create_admin_user():
    """Создание суперпользователя если он не существует"""
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
        print("Суперпользователь 'admin' создан с паролем 'admin123'")
    else:
        print("Суперпользователь 'admin' уже существует")

# Создаем админа при запуске
create_admin_user()

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('accounts/logout/', CustomLogoutView.as_view(), name='logout'),
    path('logout/', logout_view, name='logout_simple'),  # Используем простую функцию
    path('register/', ai_views.register, name='register'),
    path('', include('ai_assistant.urls')),
    path('schedule/', include('schedule.urls')),
    path('notifications/', include('notifications.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)