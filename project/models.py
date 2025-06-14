from django.db import models
from core import models as core_models
from django_jalali.db import models as jmodels
from .validators import validate_excel_file
# Create your models here.
class Project(models.Model):
    name = models.CharField(max_length=100, unique=True,verbose_name="نام پروژه")
    start_date = jmodels.jDateField(verbose_name="تاریخ شروع",null=True,blank=True)
    end_date = jmodels.jDateField(verbose_name="تاریخ پایان",null=True,blank=True)
    budget = models.DecimalField(max_digits=50, decimal_places=0, blank=True, null=True, verbose_name="بودجه")
    created_at = jmodels.jDateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    updated_at = jmodels.jDateTimeField(auto_now=True, verbose_name="تاریخ به‌روزرسانی")
    
    # اضافه کردن related_name برای جلوگیری از تداخل
    project_manager = models.ForeignKey(
        core_models.User, 
        on_delete=models.PROTECT, 
        null=True, 
        blank=True,
        related_name='managed_projects',
        verbose_name="مدیر پروژه",
        help_text="مدیر پروژه را انتخاب کنید"
    )
    
    technical_manager = models.ForeignKey(
        core_models.User, 
        on_delete=models.PROTECT, 
        null=True, 
        blank=True,
        related_name='technical_projects',
        verbose_name="مدیر فنی",
        help_text="مدیر فنی را انتخاب کنید"
    )
    
    quality_control_manager = models.ForeignKey(
        core_models.User, 
        on_delete=models.PROTECT, 
        null=True, 
        blank=True,
        related_name='qc_projects',
        verbose_name="مدیر کنترل کیفیت",
        help_text="مدیر کنترل کیفیت را انتخاب کنید"
    )
    
    project_experts = models.ManyToManyField(
        core_models.User,
        blank=True,
        through='ProjectEx',  # اتصال از طریق مدل ProjectEx
        through_fields=('project', 'user'),
        related_name='project_experts',
        verbose_name="کارشناسان پروژه",
        help_text="کارشناسان پروژه را انتخاب کنید"
    )
    
    distance = models.DecimalField(verbose_name="فاصله (کیلومتر)", help_text="فاصله پروژه به کیلومتر",max_digits=20,decimal_places=3)
    width = models.DecimalField(verbose_name="عرض (متر)", help_text="عرض پروژه به متر",max_digits=20,decimal_places=3)
    start_kilometer = models.DecimalField(verbose_name="کیلومتر شروع", help_text="کیلومتر شروع پروژه",max_digits=20,decimal_places=3)
    end_kilometer = models.DecimalField(verbose_name="کیلومتر پایان", help_text="کیلومتر پایان پروژه",max_digits=20,decimal_places=3)
    profile_file = models.FileField(verbose_name="پروفیل",
                                    upload_to='project_profiles/',
                                    null=True, blank=True,
                                    validators=[validate_excel_file]
                                    )

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "پروژه"
        verbose_name_plural = "پروژه‌ها"
        

class ProjectEx(models.Model):
    user = models.ForeignKey(core_models.User, on_delete=models.CASCADE,verbose_name="کارشناس") 
    project = models.ForeignKey(Project, on_delete=models.CASCADE, verbose_name="پروژه")
    date_joined = jmodels.jDateField(verbose_name="تاریخ ورود",auto_now_add=True)
    date_left = jmodels.jDateField(null=True, blank=True, verbose_name="تاریخ خروج")

    def __str__(self):
        return f"{self.user.username} - {self.project.name}"
    
    class Meta:
        verbose_name = "کارشناس پروژه"
        verbose_name_plural = "کارشناسان پروژه"
        unique_together = ('user', 'project')
        ordering = ['-date_joined']

class LayerType(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="نوع لایه")

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "نوع لایه"
        verbose_name_plural = "انواع لایه‌ها"

class ProjectLayer(models.Model):
    
    NOT_STARTED = 0
    IN_PROGRESS = 1
    COMPLETED = 2
    STOPPED = 3
    CANCELED = 4
    
    PROJECT_LAYER_STATUS = [
        (NOT_STARTED, 'شروع نشده'),
        (IN_PROGRESS, 'در حال انجام'),
        (COMPLETED, 'تکمیل شده'),
        (STOPPED, 'متوقف شده'),
        (CANCELED, 'لغو شده'),
    ]

    VARIABLE = 0
    FIXED = 1
    
    LAYER_STATE = [
        (VARIABLE, 'متغیر'),
        (FIXED, 'ثابت'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, verbose_name="پروژه")
    layer_type = models.ForeignKey(LayerType, on_delete=models.PROTECT, verbose_name="نوع لایه")
    thickness_cm = models.PositiveSmallIntegerField(verbose_name="ضخامت (سانتی‌متر)")
    order_from_top = models.PositiveSmallIntegerField(verbose_name="ترتیب از بالا")
    state = models.PositiveSmallIntegerField(
        choices=LAYER_STATE,
        default=FIXED,
        verbose_name="حالت",
        help_text="حالت لایه را انتخاب کنید"
    )

    status = models.PositiveSmallIntegerField(
        choices=PROJECT_LAYER_STATUS,
        default=NOT_STARTED,
        verbose_name="وضعیت",
        help_text="وضعیت لایه را انتخاب کنید"
    )
    
    def __str__(self):
        return f"{self.layer_type.name} - {self.project.name}"
    
    class Meta:
        verbose_name = "لایه پروژه"
        verbose_name_plural = "لایه‌های پروژه"
        unique_together = ('project', 'layer_type')
        ordering = ['order_from_top']

class StructureType(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="نوع اَبنیه")

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "نوع اَبنیه"
        verbose_name_plural = "انواع اَبنیه ها"
    
    
class ProjectStructure(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, verbose_name="پروژه")
    structure_type = models.ForeignKey(StructureType, on_delete=models.PROTECT, verbose_name="نوع اَبنیه")
    kilometer_location = models.PositiveBigIntegerField(verbose_name="موقعیت کیلومتری")
    start_kilometer = models.PositiveBigIntegerField(verbose_name="کیلومتر شروع", help_text="کیلومتر شروع اَبنیه")
    end_kilometer = models.PositiveBigIntegerField(verbose_name="کیلومتر پایان", help_text="کیلومتر پایان اَبنیه")
    
    NOT_STARTED = 0
    IN_PROGRESS = 1
    COMPLETED = 2
    STOPPED = 3
    CANCELED = 4
    # اضافه کردن وضعیت پروژه به صورت انتخابی
    
    PROJECT_STRUCTURE_STATUS = [
        (NOT_STARTED, 'شروع نشده'),
        (IN_PROGRESS, 'در حال انجام'),
        (COMPLETED, 'تکمیل شده'),
        (STOPPED, 'متوقف شده'),
        (CANCELED, 'لغو شده'),
    ]
    
    status = models.PositiveSmallIntegerField(
        choices=PROJECT_STRUCTURE_STATUS,
        default=NOT_STARTED,
        verbose_name="وضعیت",
        help_text="وضعیت ابینه را انتخاب کنید"
    )
    
    def __str__(self):
        return f"{self.structure_type.name}"
    
    class Meta:
        verbose_name = "اَبنیه پروژه"
        verbose_name_plural = "اَبنیه های پروژه"
        unique_together = ('project', 'structure_type')
        ordering = ['kilometer_location']


