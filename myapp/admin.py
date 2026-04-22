from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Student, Department, Intervention


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'name', 'user_type', 'department', 'is_active')
    list_filter = ('user_type', 'is_active', 'department')
    search_fields = ('email', 'name')
    ordering = ('email',)

    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Personal Info', {'fields': ('name', 'phone')}),
        ('Role & Department', {'fields': ('user_type', 'department')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'user_type', 'name', 'department'),
        }),
    )


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('name', 'student_id', 'department', 'risk_level', 'overall_score')
    list_filter = ('risk_level', 'department')
    search_fields = ('name', 'student_id')


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)


@admin.register(Intervention)
class InterventionAdmin(admin.ModelAdmin):
    list_display = ('student', 'manager', 'intervention_type', 'status', 'created_at')
    list_filter = ('status', 'intervention_type')
    search_fields = ('student__name',)