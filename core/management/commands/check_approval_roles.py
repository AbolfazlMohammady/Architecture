from django.core.management.base import BaseCommand
from core.models import Role
from experiment.models import ExperimentResponse


class Command(BaseCommand):
    help = 'بررسی تطابق نام نقش‌های مورد نیاز با نقش‌های تعریف شده در Role model'

    def handle(self, *args, **options):
        # نقش‌های مورد نیاز از get_required_approval_roles
        # استفاده از یک نمونه ExperimentResponse برای دریافت لیست نقش‌ها
        if ExperimentResponse.objects.exists():
            sample = ExperimentResponse.objects.first()
            required_roles = sample.get_required_approval_roles()
        else:
            # در صورت عدم وجود نمونه، از لیست پیش‌فرض استفاده می‌کنیم
            required_roles = [
                'نظارت پروژه',
                'مسئول آزمایشگاه',
            ]
        
        # نقش‌های تعریف شده در Role model
        defined_roles = Role.objects.all().values_list('name', flat=True)
        
        self.stdout.write("\n=== بررسی تطابق نقش‌ها ===\n")
        self.stdout.write(f"نقش‌های مورد نیاز: {required_roles}\n")
        self.stdout.write(f"نقش‌های تعریف شده در Role model: {list(defined_roles)}\n\n")
        
        missing_roles = []
        for role_name in required_roles:
            if role_name not in defined_roles:
                missing_roles.append(role_name)
                self.stdout.write(self.style.WARNING(f"⚠ نقش '{role_name}' در Role model تعریف نشده است!"))
            else:
                self.stdout.write(self.style.SUCCESS(f"✓ نقش '{role_name}' در Role model تعریف شده است"))
        
        if missing_roles:
            self.stdout.write(self.style.ERROR(f"\n❌ {len(missing_roles)} نقش در Role model تعریف نشده است!"))
            self.stdout.write("لطفاً این نقش‌ها را در ادمین پنل اضافه کنید:\n")
            for role in missing_roles:
                self.stdout.write(f"  - {role}")
        else:
            self.stdout.write(self.style.SUCCESS("\n✓ همه نقش‌ها در Role model تعریف شده‌اند"))
        
        # بررسی یک نمونه ExperimentResponse
        if ExperimentResponse.objects.exists():
            sample_response = ExperimentResponse.objects.first()
            self.stdout.write(f"\n\n=== بررسی نمونه پاسخ آزمایش (ID: {sample_response.id}) ===\n")
            project = sample_response.experiment_request.project
            self.stdout.write(f"پروژه: {project.name}\n")
            
            for role_name in required_roles:
                approvers = sample_response.get_approvers_for_role(role_name)
                self.stdout.write(f"\nنقش: {role_name}")
                if approvers:
                    self.stdout.write(f"  ✓ {len(approvers)} تاییدکننده پیدا شد:")
                    for approver in approvers:
                        self.stdout.write(f"    - {approver.username} ({approver.get_full_name()})")
                else:
                    self.stdout.write(self.style.WARNING(f"  ⚠ هیچ تاییدکننده‌ای پیدا نشد"))
