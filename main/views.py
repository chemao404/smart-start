from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from main.forms import NewsForm
from users.models import *
from main.models import *


class NewsListView(ListView):
    model = NewsModel
    context_object_name = 'news'
    template_name = 'news_list.html'


class NewsDetailView(DetailView):
    model = NewsModel
    context_object_name = 'new'
    template_name = 'news_detail.html'


class NewsCreateView(SuccessMessageMixin, CreateView):
    model = NewsModel
    form_class = NewsForm
    template_name = 'news_form.html'
    success_url = reverse_lazy('main:news_list')


class NewsUpdateView(SuccessMessageMixin, UpdateView):
    model = NewsModel
    form_class = NewsForm
    template_name = 'news_form.html'
    success_url = reverse_lazy('main:news_list')



class NewsDeleteView(DeleteView):
    model = NewsModel
    context_object_name = 'new'
    template_name = 'news_confirm_delete.html'
    success_url = reverse_lazy('main:news_list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        return super().delete(request, *args, **kwargs)


def index(request):
    teachers = TeacherProfile.objects.filter(status='approved')[:3]
    context = {
        'teachers': teachers
    }
    return render(request, 'index.html', context)



def contact(request):
    return render(request, 'contact.html')


@login_required
def dashboard(request):
    user = request.user

    if user.user_type == 'teacher':
        teacher_profile = user.teacher_profile
        if teacher_profile.status == 'pending':
            messages.info(request, '⚠️ Ваш профиль находится на проверке у администратора')
        elif teacher_profile.status == 'rejected':
            messages.warning(
                request,
                f'❌ Ваш профиль отклонен. Причина: {teacher_profile.review_comment}'
            )
        elif teacher_profile.status == 'approved':
            messages.success(request, '✅ Ваш профиль одобрен! Вам доступны все функции.')

    context = {
        'user': user,
    }

    if user.user_type == 'teacher':
        context['profile'] = user.teacher_profile
    elif user.user_type == 'student':
        context['profile'] = user.student_profile
    elif user.user_type == 'parent':
        context['profile'] = user.parent_profile

    return render(request, 'dashboard.html', context)


@login_required
def approve_teacher(request, teacher_id):
    if not request.user.is_superuser:
        messages.error(request, 'У вас нет прав для этого действия!')
        return redirect('main:dashboard')
    teacher = get_object_or_404(TeacherProfile, id=teacher_id)

    if request.method == 'POST':
        status = request.POST.get('status')
        comment = request.POST.get('comment', '')

        teacher.status = status
        teacher.reviewed_by = request.user
        teacher.review_date = timezone.now()
        teacher.review_comment = comment
        teacher.save()

        if status == 'approved':
            messages.success(
                request,
                f'✅ Преподаватель {teacher.user.get_full_name()} одобрен!'
            )
        else:
            messages.success(
                request,
                f'❌ Преподаватель {teacher.user.get_full_name()} отклонен!'
            )

        return redirect('main:teacher_list')

    return render(request, 'approve_teacher.html', {
        'teacher': teacher
    })


@login_required
def teacher_list(request):
    teachers = TeacherProfile.objects.all().select_related('user')
    if request.user.user_type in ['student', 'parent']:
        teachers = teachers.filter(status='approved')
    search = request.GET.get('search', '')
    if search:
        teachers = teachers.filter(
            models.Q(specialization__icontains=search) |
            models.Q(user__first_name__icontains=search) |
            models.Q(user__last_name__icontains=search)
        )

    return render(request, 'teacher_list.html', {
        'teachers': teachers,
        'search': search,
        'user_type': request.user.user_type
    })


@login_required
def create_application(request, teacher_id):
    if request.user.user_type != 'student':
        messages.error(request, 'Только ученики могут создавать заявки')
        return redirect('main:teacher_list')

    teacher = get_object_or_404(TeacherProfile, id=teacher_id, status='approved')
    student = request.user.student_profile

    existing = Application.objects.filter(
        student=student,
        teacher=teacher,
        status__in=['pending', 'approved']
    ).exists()

    if existing:
        messages.warning(request, 'У вас уже есть активная заявка к этому преподавателю')
        return redirect('main:teacher_list')

    if request.method == 'POST':
        message = request.POST.get('message', '')
        Application.objects.create(
            student=student,
            teacher=teacher,
            message=message
        )
        messages.success(request, '✅ Заявка отправлена! Ожидайте ответа преподавателя.')
        return redirect('main:student_applications')

    return render(request, 'create_application.html', {
        'teacher': teacher
    })


@login_required
def student_applications(request):
    if request.user.user_type != 'student':
        messages.error(request, 'Это страница для учеников')
        return redirect('main:dashboard')

    student = request.user.student_profile
    applications = student.applications.select_related('teacher__user').all()

    return render(request, 'student_applications.html', {
        'applications': applications
    })


@login_required
def teacher_applications(request):
    if request.user.user_type != 'teacher':
        messages.error(request, 'Это страница для преподавателей')
        return redirect('main:dashboard')
    teacher = request.user.teacher_profile
    if teacher.status != 'approved':
        messages.warning(request, 'Ваш профиль еще не одобрен администратором')
        return redirect('main:dashboard')
    applications = teacher.applications.select_related('student__user').all()
    return render(request, 'teacher_applications.html', {
        'applications': applications
    })


@login_required
def handle_application(request, application_id):
    if request.user.user_type != 'teacher':
        messages.error(request, 'Только преподаватели могут обрабатывать заявки')
        return redirect('main:dashboard')
    application = get_object_or_404(
        Application,
        id=application_id,
        teacher=request.user.teacher_profile
    )
    if request.method == 'POST':
        action = request.POST.get('action')
        comment = request.POST.get('comment', '')
        if action == 'approve':
            application.status = 'approved'
            application.teacher_comment = comment
            messages.success(request, f'✅ Заявка от {application.student.user.username} принята')
        elif action == 'reject':
            application.status = 'rejected'
            application.teacher_comment = comment
            messages.success(request, f'❌ Заявка от {application.student.user.username} отклонена')
        application.save()
        return redirect('main:teacher_applications')
    return render(request, 'handle_application.html', {
        'application': application
    })