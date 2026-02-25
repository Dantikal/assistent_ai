"""
URL configuration for studysense project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import get_user_model
from ai_assistant import views as ai_views
from ai_assistant import auth_views as auth_views_module

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
    path('accounts/logout/', auth_views_module.CustomLogoutView.as_view(), name='logout'),
    path('register/', ai_views.register, name='register'),
    path('', include('ai_assistant.urls')),
    path('schedule/', include('schedule.urls')),
    path('notifications/', include('notifications.urls')),
]
