from django.db import models

from users.models import TeacherProfile, StudentProfile
class NewsModel(models.Model):
    title = models.CharField(max_length=100)
    text = models.TextField()
    image = models.ImageField(upload_to='images/')
    pub_date = models.DateTimeField('date published')
    def __str__(self):
        return self.title
    class Meta:
        verbose_name = 'news'
        verbose_name_plural = 'news'


class TeacherSchedule(models.Model):
    """
    Teacher's schedule for a given week (week_start_date is Monday).
    """

    teacher = models.ForeignKey(
        TeacherProfile,
        on_delete=models.CASCADE,
        related_name="schedules",
    )
    week_start_date = models.DateField()
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("teacher", "week_start_date")
        verbose_name = "Teacher schedule"
        verbose_name_plural = "Teacher schedules"

    def __str__(self):
        return f"Schedule of {self.teacher.user.username} ({self.week_start_date})"


class TeacherScheduleSlot(models.Model):
    """
    One slot corresponds to a specific day-of-week + hour.
    day_of_week: 0=Mon ... 6=Sun
    hour: 9..19 (we'll show as start time HH:00)
    """

    schedule = models.ForeignKey(
        TeacherSchedule,
        on_delete=models.CASCADE,
        related_name="slots",
    )
    day_of_week = models.PositiveSmallIntegerField()
    hour = models.PositiveSmallIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("schedule", "day_of_week", "hour")
        verbose_name = "Teacher schedule slot"
        verbose_name_plural = "Teacher schedule slots"

    def __str__(self):
        return f"Slot: {self.day_of_week} @ {self.hour}:00"


class StudentLesson(models.Model):
    """
    A student's reservation for a specific teacher schedule slot.
    """

    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name="lessons",
        verbose_name="Ученик",
    )
    schedule_slot = models.ForeignKey(
        TeacherScheduleSlot,
        on_delete=models.CASCADE,
        related_name="lessons",
        verbose_name="Слот расписания преподавателя",
    )
    lesson_title = models.CharField(
        max_length=200,
        default="Занятие",
        verbose_name="Предмет/занятие",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("student", "schedule_slot")
        verbose_name = "Запись ученика на занятие"
        verbose_name_plural = "Записи учеников на занятия"

    def __str__(self):
        return f"{self.student.user.username} -> {self.schedule_slot}"



