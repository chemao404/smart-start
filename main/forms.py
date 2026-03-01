from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User

from django import forms
from .models import NewsModel


class NewsForm(forms.ModelForm):
    class Meta:
        model = NewsModel
        fields = ['title', 'text', 'image', 'pub_date']
        widgets = {
            'pub_date': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control',
            }, format='%Y-%m-%dT%H:%M'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Форматируем начальное значение для datetime-local
        if self.instance and self.instance.pub_date:
            self.initial['pub_date'] = self.instance.pub_date.strftime('%Y-%m-%dT%H:%M')
class UserRegistrationForm(UserCreationForm):
    """Базовая форма регистрации"""
    USER_TYPES = (
        ('student', 'Ученик'),
        ('teacher', 'Преподаватель'),
        ('parent', 'Родитель'),
    )

    user_type = forms.ChoiceField(choices=USER_TYPES, widget=forms.RadioSelect,
                                  label='Кто вы?')
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=15, required=False, label='Телефон')

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'user_type',
                  'phone', 'password1', 'password2')



class CustomLoginForm(AuthenticationForm):
    """Кастомная форма входа"""
    username = forms.CharField(label='Имя пользователя или Email',
                               widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label='Пароль',
                               widget=forms.PasswordInput(attrs={'class': 'form-control'}))