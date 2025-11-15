from django.core.management.base import BaseCommand
from django.utils import timezone
import jdatetime
from project.models import Project, ProjectLayer
from experiment.models import (
    ExperimentRequest, ExperimentResponse, ExperimentApproval
)
from core.models import User
from decimal import Decimal
from django.core.files.base import ContentFile


class Command(BaseCommand):
    help = 'حذف آزمایشات قدیمی و ایجاد آزمایشات رد شده جدید در محدوده پروژه'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('شروع اصلاح آزمایشات رد شده...'))
        
        # دریافت پروژه با ID 1
        try:
            project = Project.objects.get(pk=1)
        except Project.DoesNotExist:
            self.stdout.write(self.style.ERROR('پروژه با ID 1 یافت نشد!'))
            return
        
        # حذف آزمایشات قدیمی که در کیلومتر 1114+ هستند
        old_experiments = ExperimentRequest.objects.filter(
            project=project,
            start_kilometer__gte=1000
        )
        count = old_experiments.count()
        if count > 0:
            self.stdout.write(self.style.WARNING(f'حذف {count} آزمایش قدیمی...'))
            for exp in old_experiments:
                exp.delete()
            self.stdout.write(self.style.SUCCESS(f'✓ {count} آزمایش قدیمی حذف شدند'))
        
        # دریافت کاربر
        user = User.objects.first()
        if not user:
            self.stdout.write(self.style.ERROR('هیچ کاربری یافت نشد!'))
            return
        
        # دریافت لایه‌های پروژه
        layers = ProjectLayer.objects.filter(project=project).order_by('order_from_top')
        if not layers.exists():
            self.stdout.write(self.style.ERROR('هیچ لایه‌ای برای این پروژه یافت نشد!'))
            return
        
        # دریافت انواع آزمایش
        from experiment.models import ExperimentType, ExperimentSubType
        experiment_type = ExperimentType.objects.first()
        experiment_subtype = ExperimentSubType.objects.first() if ExperimentSubType.objects.exists() else None
        
        if not experiment_type:
            self.stdout.write(self.style.ERROR('هیچ نوع آزمایشی یافت نشد!'))
            return
        
        # محاسبه محدوده کیلومتراژ پروژه
        project_start = float(project.start_kilometer) if project.start_kilometer else 0.0
        project_end = float(project.end_kilometer) if project.end_kilometer else project_start + 10.0
        project_range = project_end - project_start
        
        self.stdout.write(self.style.SUCCESS(f'محدوده پروژه: {project_start} تا {project_end}'))
        
        # ایجاد 3 آزمایش رد شده در محدوده پروژه
        for i, layer in enumerate(layers[:3], start=1):
            # محاسبه کیلومتراژ در محدوده پروژه
            # تقسیم محدوده به 4 قسمت و استفاده از 3 قسمت اول
            segment_size = project_range / 4
            km_start = project_start + (i - 1) * segment_size
            km_end = project_start + i * segment_size
            
            # ایجاد درخواست آزمایش
            dummy_file = ContentFile(b'')
            dummy_file.name = f'rejected_test_{project.id}_{i}.txt'
            
            exp_request = ExperimentRequest.objects.create(
                project=project,
                layer=layer,
                user=user,
                request_date=jdatetime.date.today(),
                start_kilometer=Decimal(str(km_start)),
                end_kilometer=Decimal(str(km_end)),
                description=f'آزمایش رد شده تست {i}',
                request_file=dummy_file,
                status=ExperimentRequest.IN_PROGRESS,
            )
            
            exp_request.experiment_type.add(experiment_type)
            if experiment_subtype:
                exp_request.experiment_subtype.add(experiment_subtype)
            
            # ایجاد پاسخ آزمایش
            response_file = ContentFile(b'')
            response_file.name = f'response_{exp_request.id}.txt'
            
            response = ExperimentResponse.objects.create(
                experiment_request=exp_request,
                response_date=jdatetime.date.today(),
                response_file=response_file,
                description=f'پاسخ آزمایش {i}',
            )
            
            # ایجاد تاییدیه رد شده
            ExperimentApproval.objects.create(
                experiment_response=response,
                approver=user,
                status=ExperimentApproval.REJECTED,
                approval_date=jdatetime.date.today(),
                penalty_percentage=Decimal('5.00'),
                description='آزمایش رد شده - تست رنگ',
            )
            
            self.stdout.write(self.style.SUCCESS(f'✓ آزمایش رد شده {i} ایجاد شد (کیلومتر {km_start:.3f} تا {km_end:.3f})'))
        
        self.stdout.write(self.style.SUCCESS('\n✓ تمام آزمایشات رد شده با موفقیت ایجاد شدند!'))


