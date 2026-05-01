from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseBadRequest
from django.utils import timezone
from datetime import datetime, time, timedelta

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


def _get_week_start_date():
    """
    Current week start (Monday), used for "present week" schedule.
    """
    today = timezone.localdate()
    return today - timedelta(days=today.weekday())


def _get_teacher_for_schedule(request):
    """
    Decide which teacher schedule to show on /schedule depending on role.
    """
    user = request.user

    if user.user_type == 'teacher':
        return user.teacher_profile

    if user.user_type == 'student':
        return user.student_profile.preferred_teachers.first()

    if user.user_type == 'parent':
        child = user.parent_profile.children.first()
        if not child:
            return None
        return child.preferred_teachers.first()

    if user.is_superuser:
        teacher_id = request.GET.get('teacher_id')
        if teacher_id:
            return get_object_or_404(TeacherProfile, id=teacher_id)
        return TeacherProfile.objects.filter(status='approved').first()

    return None


@login_required
def schedule(request):
    teacher = _get_teacher_for_schedule(request)
    if teacher is None:
        return render(request, 'schedule.html', {
            'teacher': None,
            'week_start_date': _get_week_start_date(),
            'can_edit': False,
            'is_active': False,
            'slots_by_key': {},
            'scheduled_slot_keys': [],
            'booked_surnames_by_slot_key': {},
            'student_surnames': [],
            'hours': list(range(9, 20)),
        })

    can_edit = request.user.user_type == 'teacher' and request.user.teacher_profile == teacher

    week_start_date = _get_week_start_date()
    schedule_week = TeacherSchedule.objects.filter(
        teacher=teacher,
        week_start_date=week_start_date,
    ).first()

    is_active = bool(schedule_week and schedule_week.is_active)

    slots_by_key = {}
    if schedule_week:
        for slot in schedule_week.slots.all():
            slots_by_key[f"{slot.day_of_week}-{slot.hour}"] = slot

    scheduled_slot_keys = list(slots_by_key.keys())

    booked_surnames_by_slot_key = {}
    if schedule_week:
        lessons = StudentLesson.objects.filter(
            schedule_slot__schedule=schedule_week
        ).select_related('student__user', 'schedule_slot')

        for lesson in lessons:
            slot = lesson.schedule_slot
            key = f"{slot.day_of_week}-{slot.hour}"
            booked_surnames_by_slot_key.setdefault(key, []).append(
                lesson.student.user.last_name or lesson.student.user.username
            )

    return render(request, 'schedule.html', {
        'teacher': teacher,
        'week_start_date': week_start_date,
        'can_edit': can_edit,
        'is_active': is_active,
        'slots_by_key': slots_by_key,
        'scheduled_slot_keys': scheduled_slot_keys,
        'booked_surnames_by_slot_key': booked_surnames_by_slot_key,
        'hours': list(range(9, 20)),
        'days': [
            (0, 'Пн'),
            (1, 'Вт'),
            (2, 'Ср'),
            (3, 'Чт'),
            (4, 'Пт'),
            (5, 'Сб'),
            (6, 'Вс'),
        ],
    })


@login_required
def schedule_manage(request):
    if request.method != 'POST':
        return redirect('main:schedule')

    if request.user.user_type != 'teacher':
        return redirect('main:schedule')

    action = request.POST.get('action')
    selected_slots_str = request.POST.get('selected_slots', '')
    selected_slot_keys = [s for s in selected_slots_str.split(',') if s]
    if not action or not selected_slot_keys:
        return redirect('main:schedule')

    week_start_date = _get_week_start_date()
    teacher = request.user.teacher_profile

    schedule_week, _ = TeacherSchedule.objects.get_or_create(
        teacher=teacher,
        week_start_date=week_start_date,
        defaults={'is_active': False},
    )

    # Parse/validate keys before using them.
    parsed_cells = []
    for key in selected_slot_keys:
        try:
            day_s, hour_s = key.split('-', 1)
            day = int(day_s)
            hour = int(hour_s)
        except ValueError:
            continue
        if day < 0 or day > 6:
            continue
        if hour < 9 or hour > 19:
            continue
        parsed_cells.append((day, hour))

    if action == 'create_slots':
        schedule_week.is_active = True
        schedule_week.save(update_fields=['is_active'])

        # Teacher re-records the week: replace existing slots.
        TeacherScheduleSlot.objects.filter(schedule=schedule_week).delete()

        for day, hour in parsed_cells:
            TeacherScheduleSlot.objects.create(
                schedule=schedule_week,
                day_of_week=day,
                hour=hour,
            )

    elif action == 'delete_bookings':
        # Teacher cancels student's reservations for selected cells.
        if not schedule_week.is_active:
            return redirect('main:schedule')

        for day, hour in parsed_cells:
            slots = TeacherScheduleSlot.objects.filter(
                schedule=schedule_week,
                day_of_week=day,
                hour=hour,
            )
            StudentLesson.objects.filter(schedule_slot__in=slots).delete()

    else:
        return HttpResponseBadRequest("Unknown action")

    return redirect('main:schedule')


def _get_student_for_schedule(request):
    user = request.user
    if user.user_type == 'student':
        return user.student_profile
    if user.user_type == 'parent':
        # For now use the first child.
        child = user.parent_profile.children.first()
        return child
    return None


@login_required
def student_schedule(request):
    student = _get_student_for_schedule(request)
    if student is None:
        return redirect('main:dashboard')

    teacher_id = request.GET.get('teacher_id')
    teacher = None
    if teacher_id:
        candidate = get_object_or_404(TeacherProfile, id=teacher_id)
        if candidate.status == 'approved' and student.preferred_teachers.filter(id=candidate.id).exists():
            teacher = candidate
    if teacher is None:
        teacher = student.preferred_teachers.filter(status='approved').first()

    week_start_date = _get_week_start_date()

    day_param = request.GET.get('day', '0')
    try:
        selected_day_idx = int(day_param)
    except ValueError:
        selected_day_idx = 0
    selected_day_idx = max(0, min(6, selected_day_idx))

    schedule_week = None
    is_active = False
    available_hours_for_day = []
    available_slot_keys = set()

    if teacher is not None:
        schedule_week = TeacherSchedule.objects.filter(
            teacher=teacher,
            week_start_date=week_start_date,
        ).first()

        is_active = bool(schedule_week and schedule_week.is_active)
        if is_active:
            slots = schedule_week.slots.all()
            available_slot_keys = {f"{s.day_of_week}-{s.hour}" for s in slots}
            available_hours_for_day = sorted(
                slots.filter(day_of_week=selected_day_idx).values_list('hour', flat=True)
            )

    # Booked lessons table (for this week + chosen teacher)
    my_lessons = []
    if teacher is not None:
        lessons = StudentLesson.objects.filter(
            student=student,
            schedule_slot__schedule=schedule_week,
        ).select_related(
            'schedule_slot',
            'schedule_slot__schedule__teacher__user',
        )
        for lesson in lessons:
            slot = lesson.schedule_slot
            start_dt = datetime.combine(
                week_start_date + timedelta(days=slot.day_of_week),
                time(hour=slot.hour),
            )
            start_dt = timezone.make_aware(start_dt, timezone.get_current_timezone())
            teacher_user = slot.schedule.teacher.user
            teacher_name = teacher_user.get_full_name() or teacher_user.username
            my_lessons.append({
                'lesson_title': lesson.lesson_title,
                'teacher_name': teacher_name,
                'start_datetime': start_dt,
            })
    # Sort in python to keep template simple.
    my_lessons.sort(key=lambda x: x['start_datetime'])

    day_tabs = []
    for idx, label in [(0, 'Пн'), (1, 'Вт'), (2, 'Ср'), (3, 'Чт'), (4, 'Пт'), (5, 'Сб'), (6, 'Вс')]:
        day_tabs.append({
            'day_idx': idx,
            'label': label,
            'date_obj': week_start_date + timedelta(days=idx),
        })

    return render(request, 'student_schedule.html', {
        'student': student,
        'teacher': teacher,
        'is_active': is_active,
        'week_start_date': week_start_date,
        'selected_day_idx': selected_day_idx,
        'day_tabs': day_tabs,
        'available_hours_for_day': available_hours_for_day,
        'my_lessons': my_lessons,
        'hours': list(range(9, 20)),
    })


@login_required
def student_schedule_book(request):
    if request.method != 'POST':
        return redirect('main:student_schedule')

    student = _get_student_for_schedule(request)
    if student is None:
        return redirect('main:dashboard')

    teacher_id = request.POST.get('teacher_id')
    if not teacher_id:
        return redirect('main:student_schedule')

    teacher = get_object_or_404(TeacherProfile, id=teacher_id)
    if teacher.status != 'approved' or not student.preferred_teachers.filter(id=teacher.id).exists():
        return redirect('main:student_schedule')

    week_start_date = _get_week_start_date()
    schedule_week = TeacherSchedule.objects.filter(
        teacher=teacher,
        week_start_date=week_start_date,
    ).first()

    if not schedule_week or not schedule_week.is_active:
        return redirect('main:student_schedule')

    slot_key = request.POST.get('slot_key', '')
    try:
        day_s, hour_s = slot_key.split('-', 1)
        day = int(day_s)
        hour = int(hour_s)
    except ValueError:
        return redirect('main:student_schedule')

    if day < 0 or day > 6 or hour < 9 or hour > 19:
        return redirect('main:student_schedule')

    schedule_slot = get_object_or_404(
        TeacherScheduleSlot,
        schedule=schedule_week,
        day_of_week=day,
        hour=hour,
    )

    StudentLesson.objects.get_or_create(
        student=student,
        schedule_slot=schedule_slot,
        defaults={'lesson_title': 'Занятие'},
    )

    return redirect(f"{reverse('main:student_schedule')}?teacher_id={teacher.id}&day={day}")


@login_required
def dashboard(request):
    user = request.user
    context = {
        'user': user,
    }

    if user.user_type == 'teacher':
        context['profile'] = user.teacher_profile
    elif user.user_type == 'student':
        context['profile'] = user.student_profile
        week_start_date = _get_week_start_date()
        lessons = StudentLesson.objects.filter(
            student=user.student_profile,
            schedule_slot__schedule__week_start_date=week_start_date,
        ).select_related(
            'schedule_slot',
            'schedule_slot__schedule__teacher__user',
        )
        my_lessons = []
        for lesson in lessons:
            slot = lesson.schedule_slot
            start_dt = datetime.combine(
                week_start_date + timedelta(days=slot.day_of_week),
                time(hour=slot.hour),
            )
            start_dt = timezone.make_aware(start_dt, timezone.get_current_timezone())
            teacher_user = slot.schedule.teacher.user
            teacher_name = teacher_user.get_full_name() or teacher_user.username
            my_lessons.append({
                'lesson_title': lesson.lesson_title,
                'teacher_name': teacher_name,
                'start_datetime': start_dt,
            })
        my_lessons.sort(key=lambda x: x['start_datetime'])
        context['my_lessons'] = my_lessons
    elif user.user_type == 'parent':
        context['profile'] = user.parent_profile

    return render(request, 'dashboard.html', context)


@login_required
def approve_teacher(request, teacher_id):
    if not request.user.is_superuser:
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
        return redirect('main:teacher_list')

    teacher = get_object_or_404(TeacherProfile, id=teacher_id, status='approved')
    student = request.user.student_profile

    existing = Application.objects.filter(
        student=student,
        teacher=teacher,
        status__in=['pending', 'approved']
    ).exists()

    if existing:
        return redirect('main:teacher_list')

    if request.method == 'POST':
        message = request.POST.get('message', '')
        Application.objects.create(
            student=student,
            teacher=teacher,
            message=message
        )
        return redirect('main:student_applications')

    return render(request, 'create_application.html', {
        'teacher': teacher
    })


@login_required
def student_applications(request):
    if request.user.user_type != 'student':
        return redirect('main:dashboard')

    student = request.user.student_profile
    applications = student.applications.select_related('teacher__user').all()

    return render(request, 'student_applications.html', {
        'applications': applications
    })


@login_required
def teacher_applications(request):
    if request.user.user_type != 'teacher':
        return redirect('main:dashboard')
    teacher = request.user.teacher_profile
    if teacher.status != 'approved':
        return redirect('main:dashboard')
    applications = teacher.applications.select_related('student__user').all()
    return render(request, 'teacher_applications.html', {
        'applications': applications
    })


@login_required
def handle_application(request, application_id):
    if request.user.user_type != 'teacher':
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
            # Connect student <-> teacher for schedule access.
            application.student.preferred_teachers.add(application.teacher)
        elif action == 'reject':
            application.status = 'rejected'
            application.teacher_comment = comment
            # Ensure student is not linked to this teacher.
            if application.student.preferred_teachers.filter(id=application.teacher.id).exists():
                application.student.preferred_teachers.remove(application.teacher)
        application.save()
        return redirect('main:teacher_applications')
    return render(request, 'handle_application.html', {
        'application': application
    })