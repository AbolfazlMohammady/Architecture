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
