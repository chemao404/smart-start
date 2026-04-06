from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    USER_TYPES = (
        ('student', 'Ученик'),
        ('teacher', 'Преподаватель'),
        ('parent', 'Родитель'),
    )

    user_type = models.CharField(
        max_length=20,
        choices=USER_TYPES,
        verbose_name='Тип пользователя'
    )
    phone = models.CharField(
        max_length=15,
        blank=True,
        verbose_name='Телефон'
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        null=True,
        blank=True,
        verbose_name='Аватар'
    )
    date_registered = models.DateTimeField(
        default=timezone.now,
        verbose_name='Дата регистрации'
    )

    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='custom_user_set',
        related_query_name='user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='custom_user_set',
        related_query_name='user',
    )

    def __str__(self):
        return f"{self.username} - {self.get_user_type_display()}"

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


class TeacherProfile(models.Model):
    STATUS_CHOICES = (
        ('pending', 'На рассмотрении'),
        ('approved', 'Одобрен'),
        ('rejected', 'Отклонен'),
    )

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='teacher_profile',
        verbose_name='Пользователь'
    )

    specialization = models.CharField(
        max_length=200,
        verbose_name='Специализация',
        blank=True,  # можно оставить пустым в форме
        null=True,  # можно сохранить NULL в базе
        default=''  # значение по умолчанию
    )

    experience = models.TextField(
        verbose_name='Опыт работы',
        blank=True,
        null=True,
        default=''
    )

    education = models.TextField(
        verbose_name='Образование',
        blank=True,
        null=True,
        default=''
    )

    about = models.TextField(
        verbose_name='О себе',
        blank=True,
        null=True,
        default=''
    )

    documents = models.FileField(
        upload_to='teacher_docs/',
        null=True,
        blank=True,
        verbose_name='Документы'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Статус'
    )

    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_teachers',
        verbose_name='Проверил'
    )

    review_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Дата проверки'
    )

    review_comment = models.TextField(
        blank=True,
        verbose_name='Комментарий проверки',
        default=''
    )

    def __str__(self):
        return f"Профиль преподавателя: {self.user.get_full_name() or self.user.username}"

    class Meta:
        verbose_name = 'Профиль преподавателя'
        verbose_name_plural = 'Профили преподавателей'
class StudentProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='student_profile',
        verbose_name='Пользователь'
    )

    school = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name='Школа',
        default=''
    )

    grade = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Класс'
    )

    preferred_teachers = models.ManyToManyField(
        TeacherProfile,
        blank=True,
        related_name='preferred_students',
        verbose_name='Предпочитаемые преподаватели'
    )

    parent = models.ForeignKey(
        'ParentProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children',
        verbose_name='Родитель'
    )

    def __str__(self):
        return f"Профиль ученика: {self.user.get_full_name() or self.user.username}"

    class Meta:
        verbose_name = 'Профиль ученика'
        verbose_name_plural = 'Профили учеников'


class ParentProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='parent_profile',
        verbose_name='Пользователь'
    )

    contact_phone = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        verbose_name='Контактный телефон',
        default=''
    )

    alternative_email = models.EmailField(
        blank=True,
        null=True,
        verbose_name='Альтернативный email',
        default=''
    )

    def __str__(self):
        return f"Профиль родителя: {self.user.get_full_name() or self.user.username}"

    class Meta:
        verbose_name = 'Профиль родителя'
        verbose_name_plural = 'Профили родителей'
class Application(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Ожидает'),
        ('approved', 'Принята'),
        ('rejected', 'Отклонена'),
    )

    student = models.ForeignKey(
        'StudentProfile',
        on_delete=models.CASCADE,
        related_name='applications',
        verbose_name='Ученик'
    )
    teacher = models.ForeignKey(
        'TeacherProfile',
        on_delete=models.CASCADE,
        related_name='applications',
        verbose_name='Преподаватель'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Статус'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    message = models.TextField(
        blank=True,
        verbose_name='Сообщение ученика'
    )
    teacher_comment = models.TextField(
        blank=True,
        verbose_name='Комментарий преподавателя'
    )

    class Meta:
        verbose_name = 'Заявка'
        verbose_name_plural = 'Заявки'

    def __str__(self):
        return f"Заявка от {self.student.user.username} к {self.teacher.user.username}"