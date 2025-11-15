from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from utils import baseAdminModel
from . import models
# Register your models here.


class MyModelAdminMixin(BaseUserAdmin,baseAdminModel.BtnDeleteSelected):
    pass


class UserProjectRoleInline(admin.StackedInline):
    """Inline برای مدیریت نقش‌های کاربر در پروژه‌ها"""
    model = models.UserProjectRole
    extra = 1
    fields = ('role', 'all_projects', 'projects')
    verbose_name = "نقش در پروژه"
    verbose_name_plural = "نقش‌های کاربر در پروژه‌ها"
    filter_horizontal = ('projects',)  # برای انتخاب چندتایی پروژه‌ها


@admin.register(models.User)
class UserAdmin(MyModelAdminMixin):
    list_display = ("username", "first_name", "last_name", "national_id", "is_staff")
    list_filter = ("is_staff", "is_active","national_id")
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("اطلاعات شخصی", {"fields": ("first_name", "last_name", "national_id")}),
        ("دسترسی ها", {"fields": ("is_active", "is_staff",
                                    "is_superuser", "groups")})
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide"),
            "fields": ("username", "first_name", "last_name", "national_id", "password1", "password2")
        }),
    )
    search_fields = ("username", "national_id", "first_name", "last_name")
    ordering = ("username",)
    inlines = [UserProjectRoleInline]


@admin.register(models.UserProjectRole)
class UserProjectRoleAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'all_projects', 'get_projects', 'created_at')
    list_filter = ('role', 'all_projects', 'created_at')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'role__name', 'projects__name')
    ordering = ('user', 'role')
    filter_horizontal = ('projects',)  # برای انتخاب چندتایی پروژه‌ها
    fields = ('user', 'role', 'all_projects', 'projects')
    
    def get_projects(self, obj):
        """نمایش پروژه‌ها در لیست"""
        if obj.all_projects:
            return "همه پروژه‌ها"
        projects = obj.projects.all()
        if not projects.exists():
            return "هیچ پروژه‌ای انتخاب نشده"
        names = ", ".join([p.name for p in projects[:3]])
        if projects.count() > 3:
            names += f" و {projects.count() - 3} پروژه دیگر"
        return names
    get_projects.short_description = "پروژه‌ها"
    

