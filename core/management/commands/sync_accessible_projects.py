from django.core.management.base import BaseCommand
from core.models import User, UserProjectRole
from project.models import Project


class Command(BaseCommand):
    help = "Syncs user.accessible_projects from Project role fields, Project experts, and UserProjectRole assignments."

    def handle(self, *args, **options):
        total_links = 0
        for user in User.objects.all().prefetch_related('accessible_projects', 'project_roles__projects'):
            # جمع‌آوری پروژه‌های مرتبط از فیلدهای پروژه
            projects = set()
            # از طریق فیلدهای مستقیم پروژه
            project_qs = Project.objects.filter(project_manager=user) | \
                         Project.objects.filter(technical_manager=user) | \
                         Project.objects.filter(quality_control_manager=user) | \
                         Project.objects.filter(lab_manager=user) | \
                         Project.objects.filter(hsse_manager=user) | \
                         Project.objects.filter(project_experts=user)
            for p in project_qs.distinct():
                projects.add(p)
            # از طریق UserProjectRole
            for upr in user.project_roles.all():
                if upr.all_projects:
                    for p in Project.objects.all():
                        projects.add(p)
                else:
                    for p in upr.projects.all():
                        projects.add(p)
            # به accessible_projects اضافه کن
            before = set(user.accessible_projects.all())
            to_add = [p for p in projects if p not in before]
            if to_add:
                user.accessible_projects.add(*to_add)
                total_links += len(to_add)
                self.stdout.write(f"Updated {user.username}: +{len(to_add)} projects")
        self.stdout.write(self.style.SUCCESS(f"Sync completed. Added {total_links} accessible project links.")) 



