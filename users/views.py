from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from .forms import (
    UserRegistrationForm, TeacherRegistrationForm,
    StudentRegistrationForm, ParentRegistrationForm, CustomLoginForm
)

from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from .forms import (
    UserRegistrationForm, TeacherRegistrationForm,
    StudentRegistrationForm, ParentRegistrationForm
)


def register(request):
    """Регистрация нового пользователя"""

    # 👇 ЭТО САМОЕ ВАЖНОЕ - для GET запроса передаем ВСЕ формы
    if request.method == 'GET':
        user_form = UserRegistrationForm()
        teacher_form = TeacherRegistrationForm()
        student_form = StudentRegistrationForm()
        parent_form = ParentRegistrationForm()

        return render(request, 'register.html', {
            'user_form': user_form,
            'teacher_form': teacher_form,
            'student_form': student_form,
            'parent_form': parent_form,
        })

    # 👇 ДЛЯ POST ЗАПРОСА
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)

        if user_form.is_valid():
            # Создаем пользователя
            user = user_form.save(commit=False)
            user.user_type = user_form.cleaned_data['user_type']
            user.save()

            user_type = user_form.cleaned_data['user_type']

            # Преподаватель
            if user_type == 'teacher':
                teacher_form = TeacherRegistrationForm(request.POST, request.FILES)
                if teacher_form.is_valid():
                    teacher_profile = teacher_form.save(commit=False)
                    teacher_profile.user = user
                    teacher_profile.status = 'pending'
                    teacher_profile.save()
                    messages.success(request,
                                     'Регистрация преподавателя завершена. Ожидайте подтверждения администратора.')
                    login(request, user)
                    return redirect('main:dashboard')
                else:
                    user.delete()
                    return render(request, 'register.html', {
                        'user_form': user_form,
                        'teacher_form': teacher_form,
                        'student_form': StudentRegistrationForm(),
                        'parent_form': ParentRegistrationForm(),
                        'user_type': user_type
                    })

            # Ученик
            elif user_type == 'student':
                student_form = StudentRegistrationForm(request.POST)
                if student_form.is_valid():
                    student_profile = student_form.save(commit=False)
                    student_profile.user = user
                    student_profile.save()
                    messages.success(request, 'Регистрация ученика успешно завершена!')
                    login(request, user)
                    return redirect('main:dashboard')
                else:
                    user.delete()
                    return render(request, 'register.html', {
                        'user_form': user_form,
                        'student_form': student_form,
                        'teacher_form': TeacherRegistrationForm(),
                        'parent_form': ParentRegistrationForm(),
                        'user_type': user_type
                    })

            # Родитель
            elif user_type == 'parent':
                parent_form = ParentRegistrationForm(request.POST)
                if parent_form.is_valid():
                    parent_profile = parent_form.save(commit=False)
                    parent_profile.user = user
                    parent_profile.save()
                    messages.success(request, 'Регистрация родителя успешно завершена!')
                    login(request, user)
                    return redirect('main:dashboard')
                else:
                    user.delete()
                    return render(request, 'register.html', {
                        'user_form': user_form,
                        'parent_form': parent_form,
                        'teacher_form': TeacherRegistrationForm(),
                        'student_form': StudentRegistrationForm(),
                        'user_type': user_type
                    })

        # Если user_form не валидна
        return render(request, 'register.html', {
            'user_form': user_form,
            'teacher_form': TeacherRegistrationForm(),
            'student_form': StudentRegistrationForm(),
            'parent_form': ParentRegistrationForm(),
        })
def user_login(request):
    """Авторизация пользователя"""
    if request.method == 'POST':
        form = CustomLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)

            if user is not None:
                login(request, user)
                messages.success(request, f'Добро пожаловать, {user.username}!')
                return redirect('main:dashboard')  # ← ВАЖНО: идем в main приложение
            else:
                messages.error(request, 'Неверное имя пользователя или пароль')
        else:
            messages.error(request, 'Ошибка в форме входа')
    else:
        form = CustomLoginForm()

    return render(request, 'login.html', {'form': form})


def user_logout(request):
    """Выход из системы"""
    logout(request)
    messages.success(request, 'Вы успешно вышли из системы')
    return redirect('users:login')  # ← ВАЖНО: идем обратно в users на логин