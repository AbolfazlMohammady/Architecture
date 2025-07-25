from django.db import models
from core.models import User
from project.models import Project, ProjectLayer
from django_jalali.db import models as jmodels

# Create your models here.

class ExperimentType(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="نام آزمایش")

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "نوع آزمایش"
        verbose_name_plural = "انواع آزمایشات"

class ExperimentSubType(models.Model):
    name = models.CharField(max_length=100, verbose_name="نام زیرنوع")
    experiment_type = models.ForeignKey(ExperimentType, on_delete=models.CASCADE, verbose_name="نوع آزمایش")
    
    def __str__(self):
        return f"{self.experiment_type.name} - {self.name}"
    
    class Meta:
        verbose_name = "زیرنوع آزمایش"
        verbose_name_plural = "زیرنوع‌های آزمایش"
    
class ConcretePlace(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="محل بتن‌ریزی")

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "محل بتن‌ریزی"
        verbose_name_plural = "محل‌های بتن‌ریزی"

class ExperimentRequest(models.Model):
    PENDING = 0
    IN_PROGRESS = 1
    COMPLETED = 2
    REJECTED = 3
    
    EXPERIMENT_STATUS = (
        (PENDING, 'در انتظار بررسی'),
        (IN_PROGRESS, 'در حال انجام'),
        (COMPLETED, 'تکمیل شده'),
        (REJECTED, 'رد شده'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="کاربر")
    project = models.ForeignKey(Project, on_delete=models.CASCADE, verbose_name="پروژه")
    layer = models.ForeignKey(ProjectLayer, on_delete=models.CASCADE, verbose_name="لایه")
    experiment_type = models.ManyToManyField(ExperimentType, verbose_name="نوع آزمایش")
    experiment_subtype = models.ManyToManyField(ExperimentSubType, verbose_name="زیرنوع آزمایش", blank=True)
    concrete_place = models.ForeignKey(ConcretePlace, on_delete=models.CASCADE, verbose_name="محل بتن‌ریزی", null=True, blank=True)
    status = models.PositiveSmallIntegerField(choices=EXPERIMENT_STATUS, default=PENDING, verbose_name="وضعیت")
    request_file = models.FileField(upload_to='experiment_requests/', verbose_name="فایل درخواست")
    created_at = jmodels.jDateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    request_date = jmodels.jDateField(verbose_name="تاریخ درخواست")
    start_kilometer = models.DecimalField(max_digits=20, decimal_places=3, verbose_name="کیلومتراژ شروع")
    end_kilometer = models.DecimalField(max_digits=20, decimal_places=3, verbose_name="کیلومتراژ پایان")
    description = models.TextField(verbose_name="توضیحات", null=True, blank=True)
    target_density = models.DecimalField(max_digits=20, decimal_places=3, verbose_name="حد تراکم", null=True, blank=True)
    target_strength = models.DecimalField(max_digits=20, decimal_places=3, verbose_name="حد مقاومت فشاری", null=True, blank=True)

    order = models.PositiveIntegerField(editable=False, verbose_name="شماره اردر")
    
    class Meta:
        verbose_name = "درخواست آزمایش"
        verbose_name_plural = "درخواست‌های آزمایش"
        unique_together = ('project', 'order')
        ordering = ['project', 'order']

    def save(self, *args, **kwargs):
        if not self.pk:
            last_order = ExperimentRequest.objects.filter(project=self.project).aggregate(models.Max('order'))['order__max']
            self.order = (last_order or 0) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.project.name} - {self.order}"

class ExperimentRequestApproval(models.Model):
    APPROVED = 1
    REJECTED = 2
    STATUS_CHOICES = (
        (APPROVED, 'تایید شده'),
        (REJECTED, 'رد شده'),
    )
    
    experiment_request = models.ForeignKey(ExperimentRequest, on_delete=models.CASCADE, verbose_name="درخواست آزمایش")
    approver = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="تایید کننده")
    status = models.PositiveSmallIntegerField(choices=STATUS_CHOICES, verbose_name="وضعیت")
    description = models.TextField(verbose_name="توضیحات", null=True, blank=True)
    created_at = jmodels.jDateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")

    def __str__(self):
        return f"تایید درخواست {self.experiment_request} توسط {self.approver}"
    
    class Meta:
        verbose_name = "تایید درخواست آزمایش"
        verbose_name_plural = "تاییدهای درخواست آزمایش"
        ordering = ['-created_at']

class ExperimentResponse(models.Model):
    experiment_request = models.ForeignKey(ExperimentRequest, on_delete=models.CASCADE, verbose_name="درخواست آزمایش")
    response_file = models.FileField(upload_to='experiment_responses/', verbose_name="فایل پاسخ")
    created_at = jmodels.jDateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    response_date = jmodels.jDateField(verbose_name="تاریخ پاسخ")
    description = models.TextField(verbose_name="توضیحات", null=True, blank=True)
    
    # نتایج آزمایشات
    density_result = models.DecimalField(max_digits=20, decimal_places=3, verbose_name="نتیجه تراکم", null=True, blank=True)
    thickness_result = models.DecimalField(max_digits=20, decimal_places=3, verbose_name="نتیجه ضخامت", null=True, blank=True)
    strength_result1 = models.DecimalField(max_digits=20, decimal_places=3, verbose_name="نتیجه مقاومت 1", null=True, blank=True)
    strength_result2 = models.DecimalField(max_digits=20, decimal_places=3, verbose_name="نتیجه مقاومت 2", null=True, blank=True)
    strength_result3 = models.DecimalField(max_digits=20, decimal_places=3, verbose_name="نتیجه مقاومت 3", null=True, blank=True)
    
    class Meta:
        verbose_name = "پاسخ آزمایش"
        verbose_name_plural = "پاسخ‌های آزمایش"

    def __str__(self):
        return f"{self.experiment_request.project.name} - {self.experiment_request.order}"

    def get_required_approval_roles(self):
        """لیست نقش‌های کلیدی که باید تاییدیه بدهند (مطابق داکیومنت)"""
        return [
            'نماینده پیمانکار',
            'نقشه بردار پیمانکار',
            'نقشه بردار نظارت',
            'نظارت پروژه',
            'مسئول آزمایشگاه',
            'مسئول HSSE پروژه',
        ]

    def get_approvers_for_role(self, role_name):
        """بر اساس نقش، کاربر(ان) مرتبط با پروژه را برگردان"""
        project = self.experiment_request.project
        # اینجا باید بر اساس ساختار پروژه و نقش‌ها، کاربر را پیدا کنیم
        # نمونه: اگر نقش 'مسئول آزمایشگاه' باشد، از پروژه یا نقش‌های کاربر پیدا کن
        # اینجا فقط نمونه ساده (نیاز به تکمیل بر اساس مدل پروژه واقعی)
        if role_name == 'نماینده پیمانکار':
            return [project.project_manager] if project.project_manager else []
        if role_name == 'نقشه بردار پیمانکار':
            return [project.technical_manager] if project.technical_manager else []
        if role_name == 'نقشه بردار نظارت':
            return [project.quality_control_manager] if project.quality_control_manager else []
        if role_name == 'نظارت پروژه':
            return [project.quality_control_manager] if project.quality_control_manager else []
        if role_name == 'مسئول آزمایشگاه':
            # فرض: اولین کاربر با نقش مسئول آزمایشگاه در پروژه
            return [u for u in project.project_experts.all() if u.roles.filter(name='مسئول آزمایشگاه').exists()]
        if role_name == 'مسئول HSSE پروژه':
            return [u for u in project.project_experts.all() if u.roles.filter(name='مسئول HSSE پروژه').exists()]
        return []

    def get_approval_status_by_role(self):
        """وضعیت تایید هر نقش را به صورت دیکشنری برمی‌گرداند"""
        status = {}
        for role in self.get_required_approval_roles():
            approvers = self.get_approvers_for_role(role)
            if not approvers:
                status[role] = 'تعریف نشده'
                continue
            approvals = self.experimentapproval_set.filter(approver__in=approvers)
            if not approvals.exists():
                status[role] = 'در انتظار'
            elif approvals.filter(status=ExperimentApproval.REJECTED).exists():
                status[role] = 'رد شده'
            elif approvals.filter(status=ExperimentApproval.APPROVED).count() == len(approvers):
                status[role] = 'تایید شده'
            else:
                status[role] = 'در انتظار'
        return status

    def is_fully_approved(self):
        """آیا همه نقش‌های کلیدی تایید کرده‌اند؟"""
        status = self.get_approval_status_by_role()
        return all(v == 'تایید شده' for v in status.values() if v != 'تعریف نشده')

class ExperimentApproval(models.Model):
    APPROVED = 1
    REJECTED = 2
    STATUS_CHOICES = (
        (APPROVED, 'تایید شده'),
        (REJECTED, 'رد شده'),
    )
    
    experiment_response = models.ForeignKey(ExperimentResponse, on_delete=models.CASCADE, verbose_name="پاسخ آزمایش")
    approver = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="تایید کننده")
    status = models.PositiveSmallIntegerField(choices=STATUS_CHOICES, verbose_name="وضعیت")
    penalty_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="درصد جریمه")
    description = models.TextField(verbose_name="توضیحات", null=True, blank=True)
    created_at = jmodels.jDateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")

    def __str__(self):
        return f"تایید {self.experiment_response} توسط {self.approver}"
    
    class Meta:
        verbose_name = "تایید آزمایش"
        verbose_name_plural = "تاییدهای آزمایش"
        ordering = ['-created_at']

class PaymentCoefficient(models.Model):
    LAYER_CHOICES = [
        ('ASPHALT', 'آسفالت گرم'),
        ('BASE', 'اساس'),
        ('SUBBASE', 'زیراساس'),
        ('EMBANKMENT', 'خاکریزی'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, verbose_name="پروژه")
    layer = models.CharField(max_length=20, choices=LAYER_CHOICES, verbose_name="لایه")
    coefficient = models.DecimalField(max_digits=4, decimal_places=2, verbose_name="ضریب پرداخت")
    start_kilometer = models.DecimalField(max_digits=20, decimal_places=3, verbose_name="کیلومتراژ شروع")
    end_kilometer = models.DecimalField(max_digits=20, decimal_places=3, verbose_name="کیلومتراژ پایان")
    calculation_date = jmodels.jDateField(verbose_name="تاریخ محاسبه")
    created_at = jmodels.jDateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    
    class Meta:
        verbose_name = "ضریب پرداخت"
        verbose_name_plural = "ضرایب پرداخت"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.project.name} - {self.get_layer_display()} - {self.coefficient}"

class Message(models.Model):
    RESPONSE_MESSAGE = 0
    REQUEST_MESSAGE = 1
    
    MESSAGE_TYPE = [
        
        (RESPONSE_MESSAGE, 'پاسخ'),
        (REQUEST_MESSAGE, 'درخواست'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    experiment_request = models.ForeignKey(ExperimentRequest, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    message_type = models.PositiveSmallIntegerField(choices=MESSAGE_TYPE)

    def __str__(self):
        return f"{self.user.username} - {self.experiment_request.project.name}"

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="کاربر")
    experiment_request = models.ForeignKey(ExperimentRequest, on_delete=models.CASCADE, verbose_name="درخواست آزمایش")
    message = models.TextField(verbose_name="پیام")
    is_read = models.BooleanField(default=False, verbose_name="خوانده شده")
    created_at = jmodels.jDateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")

    def __str__(self):
        return f"اعلان برای {self.user} - {self.experiment_request}"

    class Meta:
        verbose_name = "اعلان"
        verbose_name_plural = "اعلان‌ها"
        ordering = ['-created_at']

class AsphaltTest(models.Model):
    experiment_response = models.ForeignKey(ExperimentResponse, on_delete=models.CASCADE, verbose_name="پاسخ آزمایش")
    layer_type = models.CharField(max_length=50, choices=[
        ('BINDER', 'بیندر'),
        ('TOPAK', 'توپکا'),
    ], verbose_name="نوع لایه")
    density = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="چگالی")
    air_void = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="درصد هوای مخلوط")
    vma = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="VMA")
    vfa = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="VFA")
    stability = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="پایداری")
    flow = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="روانی")
    created_at = jmodels.jDateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")

    def __str__(self):
        return f"آزمایش آسفالت {self.layer_type} - {self.experiment_response}"

    class Meta:
        verbose_name = "آزمایش آسفالت"
        verbose_name_plural = "آزمایشات آسفالت"
        ordering = ['-created_at']

class ExperimentResponseKilometer(models.Model):
    experiment_response = models.ForeignKey('ExperimentResponse', on_delete=models.CASCADE, related_name='kilometer_ranges')
    start_kilometer = models.DecimalField(max_digits=20, decimal_places=3, verbose_name="کیلومتراژ شروع")
    end_kilometer = models.DecimalField(max_digits=20, decimal_places=3, verbose_name="کیلومتراژ پایان")

    def __str__(self):
        return f"{self.start_kilometer} تا {self.end_kilometer}"

class ExperimentResponseFile(models.Model):
    experiment_response = models.ForeignKey('ExperimentResponse', on_delete=models.CASCADE, related_name='files')
    file = models.FileField(upload_to='experiment_responses/', verbose_name="فایل پاسخ")

    def __str__(self):
        return f"فایل {self.file.name}"

class ExperimentRequestKilometer(models.Model):
    experiment_request = models.ForeignKey('ExperimentRequest', on_delete=models.CASCADE, related_name='kilometer_ranges')
    start_kilometer = models.DecimalField(max_digits=20, decimal_places=3, verbose_name="کیلومتراژ شروع")
    end_kilometer = models.DecimalField(max_digits=20, decimal_places=3, verbose_name="کیلومتراژ پایان")

    def __str__(self):
        return f"{self.start_kilometer} تا {self.end_kilometer}"

    class Meta:
        verbose_name = "بازه کیلومتراژ درخواست"
        verbose_name_plural = "بازه‌های کیلومتراژ درخواست"

class ExperimentRequestFile(models.Model):
    experiment_request = models.ForeignKey('ExperimentRequest', on_delete=models.CASCADE, related_name='files')
    file = models.FileField(upload_to='experiment_requests/', verbose_name="فایل درخواست")

    def __str__(self):
        return f"فایل {self.file.name}"

    class Meta:
        verbose_name = "فایل درخواست آزمایش"
        verbose_name_plural = "فایل‌های درخواست آزمایش"