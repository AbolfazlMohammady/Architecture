from django.core.management.base import BaseCommand
from experiment.models import ExperimentResponse, ExperimentApproval
from core.models import User


class Command(BaseCommand):
    help = 'تست کردن که آیا تاییدیه‌ها برای نقش‌های UserProjectRole درست کار می‌کنند'

    def add_arguments(self, parser):
        parser.add_argument('--response-id', type=int, help='ID پاسخ آزمایش برای تست')

    def handle(self, *args, **options):
        response_id = options.get('response_id')
        
        if not response_id:
            # پیدا کردن اولین پاسخ آزمایش که تاییدیه دارد
            response = ExperimentResponse.objects.filter(experimentapproval__isnull=False).first()
            if not response:
                self.stdout.write(self.style.ERROR('هیچ پاسخ آزمایشی با تاییدیه پیدا نشد'))
                return
            response_id = response.id
        
        try:
            response = ExperimentResponse.objects.get(pk=response_id)
        except ExperimentResponse.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'پاسخ آزمایش {response_id} پیدا نشد'))
            return
        
        self.stdout.write(f"\n=== تست تاییدیه‌ها برای پاسخ آزمایش ID: {response_id} ===\n")
        self.stdout.write(f"پروژه: {response.experiment_request.project.name}\n\n")
        
        # بررسی وضعیت تایید بر اساس نقش
        status_by_role = response.get_approval_status_by_role()
        
        self.stdout.write("وضعیت تایید بر اساس نقش:\n")
        for role, status in status_by_role.items():
            approvers = response.get_approvers_for_role(role)
            approver_names = [u.username for u in approvers]
            
            # بررسی تاییدیه‌های موجود برای این نقش
            approvals = ExperimentApproval.objects.filter(
                experiment_response=response,
                role=role
            )
            
            self.stdout.write(f"\nنقش: {role}")
            self.stdout.write(f"  تاییدکنندگان: {approver_names}")
            self.stdout.write(f"  وضعیت: {status}")
            
            if approvals.exists():
                self.stdout.write(f"  تاییدیه‌های ثبت شده:")
                for approval in approvals:
                    self.stdout.write(f"    - {approval.approver.username}: {approval.get_status_display()} (نقش: {approval.role})")
            else:
                self.stdout.write(f"  ⚠ هیچ تاییدیه‌ای برای این نقش ثبت نشده است")
        
        # بررسی اینکه آیا فیلد role در تاییدیه‌ها وجود دارد
        self.stdout.write(f"\n\n=== بررسی فیلد role در تاییدیه‌ها ===\n")
        all_approvals = ExperimentApproval.objects.filter(experiment_response=response)
        if all_approvals.exists():
            for approval in all_approvals:
                if hasattr(approval, 'role') and approval.role:
                    self.stdout.write(self.style.SUCCESS(f"✓ تاییدیه ID {approval.id}: نقش = '{approval.role}'"))
                else:
                    self.stdout.write(self.style.ERROR(f"✗ تاییدیه ID {approval.id}: نقش تنظیم نشده است!"))
        else:
            self.stdout.write("هیچ تاییدیه‌ای ثبت نشده است")
        
        # تست: بررسی اینکه آیا کاربر با UserProjectRole می‌تواند تایید کند
        self.stdout.write(f"\n\n=== تست کاربران با UserProjectRole ===\n")
        from core.models import UserProjectRole, Role
        
        for role_name in response.get_required_approval_roles():
            try:
                role_obj = Role.objects.get(name=role_name)
                upr_list = UserProjectRole.objects.filter(role=role_obj)
                
                if upr_list.exists():
                    self.stdout.write(f"\nنقش '{role_name}':")
                    for upr in upr_list:
                        approvers = response.get_approvers_for_role(role_name)
                        if upr.user in approvers:
                            self.stdout.write(self.style.SUCCESS(f"  ✓ {upr.user.username} در لیست approvers است"))
                        else:
                            self.stdout.write(self.style.WARNING(f"  ⚠ {upr.user.username} در لیست approvers نیست"))
            except Role.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"  ⚠ نقش '{role_name}' در Role model تعریف نشده است"))

