from django import forms

from .models import PersonalScheduleItem, ScheduleNote


class PersonalScheduleItemForm(forms.ModelForm):
    class Meta:
        model = PersonalScheduleItem
        fields = ['title', 'day_of_week', 'start_time', 'end_time', 'room', 'notes']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Напр. Английский'}),
            'day_of_week': forms.Select(attrs={'class': 'form-select'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'room': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Кабинет'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Напр. домашка, ссылка на материал'}),
        }


class ScheduleNoteForm(forms.ModelForm):
    class Meta:
        model = ScheduleNote
        fields = ['title', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Напр. Домашняя работа'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Опиши что нужно сделать'}),
        }
