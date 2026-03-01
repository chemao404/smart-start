from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, TeacherProfile, StudentProfile, ParentProfile


class UserRegistrationForm(UserCreationForm):
    """Главная форма регистрации (выбор роли)"""
    USER_TYPES = (
        ('student', 'Ученик'),
        ('teacher', 'Преподаватель'),
        ('parent', 'Родитель'),
    )

    user_type = forms.ChoiceField(
        choices=USER_TYPES,
        widget=forms.RadioSelect,
        label='Кто вы?'
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Введите email'})
    )
    phone = forms.CharField(
        max_length=15,
        required=False,
        label='Телефон',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите телефон'})
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name',
                  'user_type', 'phone', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Добавляем классы для всех полей
        for field_name in ['username', 'first_name', 'last_name', 'password1', 'password2']:
            self.fields[field_name].widget.attrs.update({
                'class': 'form-control',
                'placeholder': f'Введите {self.fields[field_name].label}'
            })


class TeacherRegistrationForm(forms.ModelForm):
    """Форма для преподавателя"""
    specialization = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Например: Математика, Физика, Английский язык'
        })
    )
    education = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Укажите ваше образование (ВУЗ, факультет, год окончания)'
        })
    )
    experience = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Расскажите о вашем опыте работы'
        })
    )
    about = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Напишите немного о себе, своих методах преподавания'
        })
    )
    documents = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control'
        })
    )

    class Meta:
        model = TeacherProfile
        fields = ['specialization', 'education', 'experience', 'about', 'documents']

class StudentRegistrationForm(forms.ModelForm):
    """Форма для ученика"""

    class Meta:
        model = StudentProfile
        fields = ('school', 'grade')
        widgets = {
            'school': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Название школы'
            }),
            'grade': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Класс'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['school'].required = False
        self.fields['grade'].required = False


class ParentRegistrationForm(forms.ModelForm):
    """Форма для родителя"""

    class Meta:
        model = ParentProfile
        fields = ('contact_phone', 'alternative_email')
        widgets = {
            'contact_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Контактный телефон'
            }),
            'alternative_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Альтернативный email'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['contact_phone'].required = False
        self.fields['alternative_email'].required = False


class CustomLoginForm(AuthenticationForm):
    """Форма входа"""
    username = forms.CharField(
        label='Имя пользователя или Email',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Имя пользователя или Email'})
    )
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Пароль'})
    )