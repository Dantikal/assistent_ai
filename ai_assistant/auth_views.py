from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView as DjangoLoginView, LogoutView as DjangoLogoutView
from django.contrib import messages
from django import forms
from schedule.models import Student, StudentGroup


class CustomUserCreationForm(UserCreationForm):
    """Форма регистрации с выбором группы"""
    group = forms.ModelChoiceField(
        queryset=StudentGroup.objects.filter(is_active=True),
        empty_label="Выберите группу",
        required=True,
        label="Учебная группа"
    )


class CustomLogoutView(DjangoLogoutView):
    """Кастомный класс для выхода с перенаправлением"""
    next_page = 'login'
    
    def get(self, request, *args, **kwargs):
        """Разрешаем GET-запросы для выхода"""
        return self.post(request, *args, **kwargs)


def logout_view(request):
    """Простая функция для выхода (поддерживает GET)"""
    logout(request)
    return redirect('login')


def register(request):
    """Регистрация нового студента"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Создаем профиль студента с выбранной группой
            Student.objects.create(user=user, group=form.cleaned_data['group'])
            login(request, user)
            messages.success(request, 'Регистрация прошла успешно! Добро пожаловать в систему!')
            return redirect('dashboard')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'registration/register.html', {'form': form})
