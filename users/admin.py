from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *


class CustomUserAdmin(UserAdmin):
    """Кастомная админка для пользователей"""
    list_display = ('username', 'email', 'first_name', 'last_name', 'user_type', 'is_active')  # ← role -> user_type
    list_filter = ('user_type', 'is_active', 'is_staff')  # ← role -> user_type
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_registered',)

    fieldsets = UserAdmin.fieldsets + (
        ('Дополнительная информация', {
            'fields': ('user_type', 'phone', 'avatar')
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Дополнительная информация', {
            'fields': ('user_type', 'phone', 'avatar')
        }),
    )


admin.site.register(User, CustomUserAdmin)
admin.site.register(TeacherProfile)
admin.site.register(StudentProfile)
admin.site.register(ParentProfile)
admin.site.register(Application)
