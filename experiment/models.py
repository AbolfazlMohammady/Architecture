from django.db import models
from core.models import User
from project.models import Project, ProjectLayer
from django_jalali.db import models as jmodels

# Create your models here.

class ExperimentType(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="نام نوع آزمایش")

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "آزمایش"
        verbose_name_plural = "آزمایشات"

class ExperimentSubType(models.Model):
    name = models.CharField(max_length=100, verbose_name="نام زیرنوع")
    experiment_type = models.ForeignKey(ExperimentType, on_delete=models.CASCADE, verbose_name="آزمایش")
    
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
    experiment_type = models.ManyToManyField(ExperimentType, verbose_name="آزمایش")
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
    
    def get_actual_status(self):
        """محاسبه وضعیت واقعی بر اساس پاسخ‌ها و تاییدیه‌ها"""
        # اگر پاسخ وجود دارد
        responses = self.experimentresponse_set.all()
        if responses.exists():
            # آخرین پاسخ را بررسی می‌کنیم
            latest_response = responses.order_by('-created_at').first()
            
            # بررسی تاییدیه‌های آخرین پاسخ
            approvals = latest_response.experimentapproval_set.all()
            if approvals.exists():
                # اگر هر کدام از تاییدیه‌ها رد شده باشد
                if approvals.filter(status=ExperimentApproval.REJECTED).exists():
                    return self.REJECTED
                # اگر همه تایید شده باشند
                approval_status = latest_response.get_approval_status_by_role()
                if all(v == 'تایید شده' for v in approval_status.values() if v != 'تعریف نشده'):
                    return self.COMPLETED
                # در غیر این صورت در حال بررسی است
                return self.IN_PROGRESS
            # اگر پاسخ وجود دارد اما تاییدیه ندارد
            return self.IN_PROGRESS
        
        # اگر پاسخ وجود ندارد، وضعیت درخواست را برمی‌گردانیم
        return self.status
    
    def get_status_display_color(self):
        """رنگ badge بر اساس وضعیت واقعی"""
        actual_status = self.get_actual_status()
        if actual_status == self.PENDING:
            return 'bg-warning'
        elif actual_status == self.IN_PROGRESS:
            return 'bg-info'
        elif actual_status == self.COMPLETED:
            return 'bg-success'
        elif actual_status == self.REJECTED:
            return 'bg-danger'
        return 'bg-secondary'

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
    approval_date = jmodels.jDateField(verbose_name="تاریخ تایید", null=True, blank=True)
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
    strength_average = models.DecimalField(max_digits=20, decimal_places=3, verbose_name="میانگین مقاومت", null=True, blank=True, editable=False)
    
    def calculate_strength_average(self):
        """محاسبه میانگین مقاومت از 3 فیلد مقاومت"""
        results = []
        if self.strength_result1 is not None:
            results.append(float(self.strength_result1))
        if self.strength_result2 is not None:
            results.append(float(self.strength_result2))
        if self.strength_result3 is not None:
            results.append(float(self.strength_result3))
        if results:
            from decimal import Decimal
            return Decimal(str(sum(results) / len(results)))
        return None
    
    def save(self, *args, **kwargs):
        """محاسبه و ذخیره میانگین مقاومت قبل از ذخیره"""
        if self.strength_result1 is not None or self.strength_result2 is not None or self.strength_result3 is not None:
            self.strength_average = self.calculate_strength_average()
        else:
            self.strength_average = None
        super().save(*args, **kwargs)
    
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
        approvers = []
        
        # ابتدا از UserProjectRole استفاده می‌کنیم (اولویت با نقش‌های تعریف شده در ادمین)
        from core.models import UserProjectRole, Role
        try:
            # پیدا کردن Role با نام داده شده
            role_obj = Role.objects.get(name=role_name)
            
            # ابتدا نقش‌های مربوط به این پروژه خاص را پیدا می‌کنیم
            project_roles = UserProjectRole.objects.filter(
                role=role_obj,
                projects=project
            ).select_related('user')
            approvers.extend([role.user for role in project_roles if role.user not in approvers])
            
            # سپس نقش‌هایی که برای همه پروژه‌ها تعریف شده‌اند (all_projects=True)
            global_roles = UserProjectRole.objects.filter(
                role=role_obj,
                all_projects=True
            ).select_related('user')
            approvers.extend([role.user for role in global_roles if role.user not in approvers])
        except Role.DoesNotExist:
            # اگر نقش در Role model تعریف نشده باشد، از فیلدهای مستقیم پروژه استفاده می‌کنیم
            pass
        
        # اگر از UserProjectRole کسی پیدا نشد، از فیلدهای تعریف شده در مدل Project استفاده می‌کنیم (برای سازگاری با کد قدیمی)
        if not approvers:
            if role_name == 'نماینده پیمانکار':
                if project.project_manager:
                    approvers.append(project.project_manager)
            elif role_name == 'نقشه بردار پیمانکار':
                if project.technical_manager:
                    approvers.append(project.technical_manager)
            elif role_name == 'نقشه بردار نظارت':
                if project.quality_control_manager:
                    approvers.append(project.quality_control_manager)
            elif role_name == 'نظارت پروژه':
                if project.quality_control_manager:
                    approvers.append(project.quality_control_manager)
            elif role_name == 'مسئول آزمایشگاه':
                if project.lab_manager:
                    approvers.append(project.lab_manager)
            elif role_name == 'مسئول HSSE پروژه':
                if project.hsse_manager:
                    approvers.append(project.hsse_manager)
        
        return approvers

    def get_approval_status_by_role(self):
        """وضعیت تایید هر نقش را به صورت دیکشنری برمی‌گرداند"""
        status = {}
        for role in self.get_required_approval_roles():
            approvers = self.get_approvers_for_role(role)
            if not approvers:
                status[role] = 'تعریف نشده'
                continue
            # فیلتر کردن تاییدیه‌ها بر اساس نقش
            approvals = self.experimentapproval_set.filter(
                approver__in=approvers,
                role=role
            )
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
    role = models.CharField(max_length=100, verbose_name="نقش تاییدکننده", help_text="نقش کاربر هنگام ثبت تاییدیه")
    status = models.PositiveSmallIntegerField(choices=STATUS_CHOICES, verbose_name="وضعیت")
    approval_date = jmodels.jDateField(verbose_name="تاریخ تایید")
    penalty_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="درصد جریمه")
    description = models.TextField(verbose_name="توضیحات", null=True, blank=True)
    created_at = jmodels.jDateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")

    def __str__(self):
        return f"تایید {self.experiment_response} توسط {self.approver} ({self.role})"
    
    class Meta:
        verbose_name = "تایید آزمایش"
        verbose_name_plural = "تاییدهای آزمایش"
        ordering = ['-created_at']
        unique_together = [('experiment_response', 'approver', 'role')]

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
    """آزمایش آسفالت با 8 فیلد طبق داکیومنت"""
    experiment_response = models.ForeignKey(ExperimentResponse, on_delete=models.CASCADE, verbose_name="پاسخ آزمایش", related_name='asphalt_tests')
    layer_type = models.CharField(max_length=50, choices=[
        ('BINDER', 'بیندر'),
        ('TOPAK', 'توپکا'),
    ], verbose_name="نوع لایه")
    
    # 1. دانه‌بندی در مدل جداگانه AsphaltGradation مدیریت می‌شود
    
    # 2. درصد قیر نسبت به مخلوط آسفالت
    bitumen_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        verbose_name="درصد قیر نسبت به مخلوط آسفالت", 
        null=True, 
        blank=True,
        help_text="(طرح اختلاط) ۱۰٪+ >= X >= (طرح اختلاط) ۱۰٪-"
    )
    
    # 3. درصد شکستگی
    fracture_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        verbose_name="درصد شکستگی", 
        null=True, 
        blank=True,
        help_text="باید >= 80 باشد"
    )
    
    # 4. درجه حرارت آسفالت
    temperature = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        verbose_name="درجه حرارت آسفالت", 
        null=True, 
        blank=True,
        help_text="163 >= X >= 136"
    )
    
    # 5. درصد فضای خالی
    air_void_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        verbose_name="درصد فضای خالی", 
        null=True, 
        blank=True,
        help_text="بیندر: 6 >= X >= 3, توپکا: 5 >= X >= 3"
    )
    
    # 6. درصد حجمی فضای خالی
    vma_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        verbose_name="درصد حجمی فضای خالی (VMA)", 
        null=True, 
        blank=True,
        help_text="15 >= X >= 13"
    )
    
    # 7. درصد فضای خالی پرشده با قیر
    vfa_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        verbose_name="درصد فضای خالی پرشده با قیر (VFA)", 
        null=True, 
        blank=True,
        help_text="75 >= X >= 60"
    )
    
    # 8. درصد فیلر به قیر
    filler_to_bitumen_ratio = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        verbose_name="درصد فیلر به قیر", 
        null=True, 
        blank=True,
        help_text="1.2 >= X >= 0.6"
    )
    
    created_at = jmodels.jDateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")

    def __str__(self):
        return f"آزمایش آسفالت {self.get_layer_type_display()} - {self.experiment_response}"

    class Meta:
        verbose_name = "آزمایش آسفالت"
        verbose_name_plural = "آزمایشات آسفالت"
        ordering = ['-created_at']


class AsphaltGradation(models.Model):
    """دانه‌بندی آسفالت (الک‌ها)"""
    asphalt_test = models.ForeignKey(AsphaltTest, on_delete=models.CASCADE, verbose_name="آزمایش آسفالت", related_name='gradations')
    sieve_size = models.CharField(max_length=20, verbose_name="اندازه الک", help_text="مثال: 3, 2.5, 2, 1.5, 1, 4/3, 2/1, ...")
    passing_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        verbose_name="درصد عبوری", 
        null=True, 
        blank=True
    )
    created_at = jmodels.jDateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")

    def __str__(self):
        return f"الک {self.sieve_size} - {self.passing_percentage}%"

    class Meta:
        verbose_name = "دانه‌بندی آسفالت"
        verbose_name_plural = "دانه‌بندی‌های آسفالت"
        ordering = ['asphalt_test', 'sieve_size']


class SieveSize(models.Model):
    """لیست اندازه‌های الک قابل انتخاب در ادمین"""
    name = models.CharField(max_length=50, unique=True, verbose_name="اندازه الک")
    order = models.PositiveIntegerField(default=0, verbose_name="ترتیب نمایش")
    created_at = jmodels.jDateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")

    class Meta:
        verbose_name = "اندازه الک"
        verbose_name_plural = "اندازه‌های الک"
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

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
    description = models.TextField(null=True, blank=True, verbose_name="توضیحات بازه")

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