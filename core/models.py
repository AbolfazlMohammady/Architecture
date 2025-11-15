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
    project = models.ForeignKey(
        'project.Project',
        on_delete=models.CASCADE,
        related_name='user_roles',
        null=True,
        blank=True,
        verbose_name="پروژه",
        help_text="اگر خالی باشد، این نقش برای همه پروژه‌ها اعمال می‌شود"
    )
    role_name = models.CharField(
        max_length=100,
        verbose_name="نام نقش",
        help_text="مثال: نظارت پیمانکار، نظارت کارفرما، نماینده پیمانکار و..."
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاریخ به‌روزرسانی")

    class Meta:
        verbose_name = "نقش کاربر در پروژه"
        verbose_name_plural = "نقش‌های کاربران در پروژه‌ها"
        ordering = ['user', 'project', 'role_name']
        unique_together = [['user', 'project', 'role_name']]

    def __str__(self):
        project_name = self.project.name if self.project else "همه پروژه‌ها"
        return f"{self.user.get_full_name()} - {self.role_name} - {project_name}"

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
