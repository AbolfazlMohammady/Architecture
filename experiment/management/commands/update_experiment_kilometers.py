from django.core.management.base import BaseCommand
from project.models import Project
from experiment.models import ExperimentRequest
from decimal import Decimal


class Command(BaseCommand):
    help = 'به‌روزرسانی کیلومتراژ آزمایشات به محدوده پروژه'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('شروع به‌روزرسانی کیلومتراژ آزمایشات...'))
        
        # دریافت پروژه با ID 1
        try:
            project = Project.objects.get(pk=1)
        except Project.DoesNotExist:
            self.stdout.write(self.style.ERROR('پروژه با ID 1 یافت نشد!'))
            return
        
        # محاسبه محدوده کیلومتراژ پروژه
        project_start = float(project.start_kilometer) if project.start_kilometer else 0.0
        project_end = float(project.end_kilometer) if project.end_kilometer else project_start + 10.0
        project_range = project_end - project_start
        
        self.stdout.write(self.style.SUCCESS(f'محدوده پروژه: {project_start} تا {project_end}'))
        
        # پیدا کردن آزمایشات با کیلومتراژ بالا
        old_experiments = ExperimentRequest.objects.filter(
            project=project,
            start_kilometer__gte=1000
        ).order_by('id')
        
        count = old_experiments.count()
        if count == 0:
            self.stdout.write(self.style.WARNING('هیچ آزمایشی با کیلومتراژ بالا یافت نشد!'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'یافت شد: {count} آزمایش'))
        
        # تقسیم محدوده پروژه به بخش‌های مساوی
        segment_size = project_range / (count + 1) if count > 0 else project_range
        
        # به‌روزرسانی هر آزمایش
        for i, exp in enumerate(old_experiments, start=1):
            old_start = float(exp.start_kilometer)
            old_end = float(exp.end_kilometer)
            old_range = old_end - old_start
            
            # محاسبه کیلومتراژ جدید
            new_start = project_start + (i * segment_size)
            new_end = new_start + old_range  # حفظ طول بازه
            
            # اطمینان از اینکه در محدوده پروژه است
            if new_end > project_end:
                new_end = project_end
                new_start = new_end - old_range
                if new_start < project_start:
                    new_start = project_start
                    new_end = project_start + old_range
            
            # به‌روزرسانی
            exp.start_kilometer = Decimal(str(new_start))
            exp.end_kilometer = Decimal(str(new_end))
            exp.save()
            
            self.stdout.write(self.style.SUCCESS(
                f'✓ آزمایش {exp.id}: {old_start} تا {old_end} -> {new_start:.3f} تا {new_end:.3f}'
            ))
        
        self.stdout.write(self.style.SUCCESS(f'\n✓ {count} آزمایش با موفقیت به‌روزرسانی شدند!'))


