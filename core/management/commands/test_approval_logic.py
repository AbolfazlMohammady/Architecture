from django.core.management.base import BaseCommand
from experiment.models import ExperimentResponse
from core.models import User


class Command(BaseCommand):
    help = 'تست منطق تایید برای یک کاربر خاص'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='نام کاربری برای تست')
        parser.add_argument('--response-id', type=int, help='ID پاسخ آزمایش')

    def handle(self, *args, **options):
        username = options.get('username')
        response_id = options.get('response_id')
        
        if not username or not response_id:
            self.stdout.write(self.style.ERROR('لطفاً username و response_id را وارد کنید'))
            self.stdout.write('مثال: python manage.py test_approval_logic --username r.bavafa --response-id 6')
            return
        
        try:
            user = User.objects.get(username=username)
            response = ExperimentResponse.objects.get(pk=response_id)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'کاربر {username} پیدا نشد'))
            return
        except ExperimentResponse.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'پاسخ آزمایش {response_id} پیدا نشد'))
            return
        
        self.stdout.write(f"\n=== تست منطق تایید ===\n")
        self.stdout.write(f"کاربر: {user.username} ({user.get_full_name()})\n")
        self.stdout.write(f"پاسخ آزمایش ID: {response_id}\n")
        self.stdout.write(f"پروژه: {response.experiment_request.project.name}\n\n")
        
        can_approve = False
        user_roles = []
        
        for role in response.get_required_approval_roles():
            approvers = response.get_approvers_for_role(role)
            self.stdout.write(f"نقش: {role}")
            self.stdout.write(f"  تاییدکنندگان: {[u.username for u in approvers]}")
            
            if user in approvers:
                can_approve = True
                user_roles.append(role)
                self.stdout.write(self.style.SUCCESS(f"  ✓ کاربر {user.username} می‌تواند برای این نقش تایید کند"))
            else:
                self.stdout.write(self.style.WARNING(f"  ✗ کاربر {user.username} نمی‌تواند برای این نقش تایید کند"))
            self.stdout.write("")
        
        if can_approve:
            self.stdout.write(self.style.SUCCESS(f"\n✓ کاربر {user.username} می‌تواند تایید کند برای نقش‌های: {user_roles}"))
        else:
            self.stdout.write(self.style.ERROR(f"\n✗ کاربر {user.username} نمی‌تواند تایید کند"))
        
        # بررسی تاییدیه‌های موجود
        self.stdout.write(f"\n=== تاییدیه‌های موجود ===\n")
        approvals = response.experimentapproval_set.all()
        if approvals.exists():
            for approval in approvals:
                self.stdout.write(f"تاییدکننده: {approval.approver.username}, وضعیت: {approval.get_status_display()}, تاریخ: {approval.approval_date}")
        else:
            self.stdout.write("هیچ تاییدیه‌ای ثبت نشده است")
        
        # بررسی وضعیت تایید بر اساس نقش
        self.stdout.write(f"\n=== وضعیت تایید بر اساس نقش ===\n")
        status_by_role = response.get_approval_status_by_role()
        for role, status in status_by_role.items():
            self.stdout.write(f"{role}: {status}")
