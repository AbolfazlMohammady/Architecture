from django.core.management.base import BaseCommand
from django.forms.models import model_to_dict
from core.models import User, UserProjectRole, Role
from project.models import Project
import json


class Command(BaseCommand):
    help = "Prints users, their accessible projects, global roles, and project-role bindings for auditing visibility/inbox access."

    def handle(self, *args, **options):
        role_by_id = {r.id: r.name for r in Role.objects.all()}
        proj_by_id = {p.id: p.name for p in Project.objects.all()}

        report = []
        for u in User.objects.all().prefetch_related('accessible_projects', 'roles', 'project_roles__projects', 'project_roles__role'):
            accessible_projects = [
                {"id": p.id, "name": p.name} for p in u.accessible_projects.all()
            ]
            global_roles = [r.name for r in u.roles.all()]
            project_roles = []
            for upr in u.project_roles.all():
                project_roles.append({
                    "role": upr.role.name if upr.role else None,
                    "all_projects": bool(upr.all_projects),
                    "projects": [{"id": p.id, "name": p.name} for p in upr.projects.all()]
                })
            report.append({
                "user": u.username,
                "full_name": u.get_full_name(),
                "is_superuser": bool(u.is_superuser),
                "accessible_projects": accessible_projects,
                "global_roles": global_roles,
                "project_roles": project_roles,
            })
        self.stdout.write(json.dumps(report, ensure_ascii=False, indent=2)) 



