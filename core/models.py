from django.db import models
from django.contrib.auth.models import AbstractUser
from .valirations import validate_national_code

# Create your models here.

class Role(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="نام نقش")
    description = models.TextField(blank=True, null=True, verbose_name="توضیحات")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاریخ به‌روزرسانی")

    class Meta:
        verbose_name = "نقش"
        verbose_name_plural = "نقش‌ها"
        ordering = ['name']

    def __str__(self):
        return self.name

class UserProjectRole(models.Model):
    """نقش کاربر در پروژه خاص یا همه پروژه‌ها"""
    user = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='project_roles',
        verbose_name="کاربر"
    )
    role = models.ForeignKey(
        'Role',
        on_delete=models.CASCADE,
        related_name='user_project_roles',
        verbose_name="نقش",
        help_text="نقش کاربر از لیست نقش‌های تعریف شده"
    )
    projects = models.ManyToManyField(
        'project.Project',
        related_name='user_roles',
        blank=True,
        verbose_name="پروژه‌ها",
        help_text="پروژه‌های مرتبط با این نقش"
    )
    all_projects = models.BooleanField(
        default=False,
        verbose_name="همه پروژه‌ها",
        help_text="اگر فعال باشد، این نقش برای همه پروژه‌ها اعمال می‌شود"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاریخ به‌روزرسانی")

    class Meta:
        verbose_name = "نقش کاربر در پروژه"
        verbose_name_plural = "نقش‌های کاربران در پروژه‌ها"
        ordering = ['user', 'role']
        unique_together = [['user', 'role']]

    def __str__(self):
        if self.all_projects:
            project_names = "همه پروژه‌ها"
        else:
            project_names = ", ".join([p.name for p in self.projects.all()[:3]])
            if self.projects.count() > 3:
                project_names += f" و {self.projects.count() - 3} پروژه دیگر"
        return f"{self.user.get_full_name()} - {self.role.name} - {project_names}"

class User(AbstractUser):
    REQUIRED_FIELDS = []
    national_id = models.CharField(max_length=10,
                                   unique=True,
                                   null=True,
                                   blank=True,
                                   verbose_name="کد ملی",
                                   validators=[validate_national_code]
                                   )
    roles = models.ManyToManyField(Role, blank=True,null=True ,related_name='users', verbose_name="نقش‌ها")
    # پروژه‌های قابل دسترسی برای هر کاربر
    accessible_projects = models.ManyToManyField(
        'project.Project',
        blank=True,
        related_name='users_with_access',
        verbose_name="پروژه‌های قابل دسترسی"
    )
    
    class Meta:
        verbose_name = "کاربر"
        verbose_name_plural = "کاربران"
        ordering = ['username']

    def __str__(self):
        return f"{self.get_full_name()} ({self.username})"
