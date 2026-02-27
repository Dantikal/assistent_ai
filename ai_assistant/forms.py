from django import forms
from django.utils import timezone
from django.contrib.auth.models import User
from .models import UserProfile, StudentNote, PointsAdjustment, Post
from schedule.models import Subject


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['avatar']


class StudentNoteForm(forms.ModelForm):
    """Форма для создания и редактирования заметок студента"""
    
    class Meta:
        model = StudentNote
        fields = ['title', 'content', 'category', 'priority', 'subject', 'deadline', 'tags']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите заголовок заметки...',
                'rows': 1
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Введите содержание заметки...',
                'rows': 4
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'priority': forms.Select(attrs={
                'class': 'form-select'
            }),
            'subject': forms.Select(attrs={
                'class': 'form-select',
                'empty_label': 'Выберите предмет (необязательно)'
            }),
            'deadline': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'tags': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Теги через запятую (например: математика, экзамен, важно)'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Устанавливаем минимальную дату для дедлайна - текущее время
        self.fields['deadline'].widget.attrs['min'] = timezone.now().strftime('%Y-%m-%dT%H:%M')


class QuickNoteForm(forms.ModelForm):
    """Быстрая форма для создания заметок"""
    
    class Meta:
        model = StudentNote
        fields = ['title', 'content', 'priority']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Быстрая заметка...',
                'rows': 1
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Текст заметки...',
                'rows': 3
            }),
            'priority': forms.Select(attrs={
                'class': 'form-select'
            })
        }


class PointsAdjustmentForm(forms.ModelForm):
    """Форма для изменения очков пользователя"""
    
    class Meta:
        model = PointsAdjustment
        fields = ['user', 'points_change', 'reason']
        widgets = {
            'user': forms.Select(attrs={
                'class': 'form-select',
                'placeholder': 'Выберите пользователя'
            }),
            'points_change': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите количество очков (может быть отрицательным)',
                'min': -10000,
                'max': 10000,
                'step': 1
            }),
            'reason': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Причина изменения очков',
                'maxlength': 200
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Фильтруем пользователей только с профилями
        self.fields['user'].queryset = User.objects.all().select_related('userprofile')
        
        # Добавляем текущее количество очков в help_text
        if 'user' in self.data:
            try:
                user_id = int(self.data.get('user'))
                user_profile = UserProfile.objects.get(user_id=user_id)
                self.fields['points_change'].help_text = f'Текущие очки: {user_profile.points}'
            except (ValueError, UserProfile.DoesNotExist):
                pass
        elif self.instance.pk:
            user_profile = self.instance.user.userprofile
            self.fields['points_change'].help_text = f'Текущие очки: {user_profile.points}'
    
    def clean_points_change(self):
        """Валидация изменения очков"""
        points_change = self.cleaned_data['points_change']
        if points_change == 0:
            raise forms.ValidationError('Изменение очков не может быть равно нулю')
        
        # Проверяем, чтобы у пользователя не стало отрицательных очков
        user = self.cleaned_data.get('user')
        if user:
            try:
                user_profile = user.userprofile
                if user_profile.points + points_change < 0:
                    raise forms.ValidationError(
                        f'У пользователя не может быть отрицательное количество очков. '
                        f'Текущие: {user_profile.points}, попытка изменить на: {points_change}'
                    )
            except UserProfile.DoesNotExist:
                # Если профиля нет, создаем его
                UserProfile.objects.create(user=user, points=0)
        
        return points_change


class PostForm(forms.ModelForm):
    """Форма для создания поста"""
    
    poll_options = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'Каждый вариант с новой строки',
            'class': 'form-control'
        }),
        required=False,
        help_text='Для опросов: каждый вариант ответа с новой строки'
    )
    
    class Meta:
        model = Post
        fields = ['content', 'image', 'post_type']
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Что у вас нового?',
                'class': 'form-control'
            }),
            'post_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            })
        }
