# Generated manually

from django.db import migrations, models


def populate_role_for_existing_approvals(apps, schema_editor):
    """برای تاییدیه‌های موجود، نقش را بر اساس approver پیدا می‌کند"""
    ExperimentApproval = apps.get_model('experiment', 'ExperimentApproval')
    ExperimentResponse = apps.get_model('experiment', 'ExperimentResponse')
    ExperimentRequest = apps.get_model('experiment', 'ExperimentRequest')
    Project = apps.get_model('project', 'Project')
    Role = apps.get_model('core', 'Role')
    UserProjectRole = apps.get_model('core', 'UserProjectRole')
    
    required_roles = [
        'نماینده پیمانکار',
        'نقشه بردار پیمانکار',
        'نقشه بردار نظارت',
        'نظارت پروژه',
        'مسئول آزمایشگاه',
        'مسئول HSSE پروژه',
    ]
    
    for approval in ExperimentApproval.objects.all():
        if approval.role:  # اگر قبلاً تنظیم شده باشد، رد می‌شود
            continue
        
        response = approval.experiment_response
        approver = approval.approver
        
        # پیدا کردن نقش approver
        for role_name in required_roles:
            # بررسی فیلدهای مستقیم پروژه
            project = response.experiment_request.project
            is_approver = False
            
            if role_name == 'نماینده پیمانکار' and project.project_manager_id == approver.id:
                is_approver = True
            elif role_name == 'نقشه بردار پیمانکار' and project.technical_manager_id == approver.id:
                is_approver = True
            elif role_name == 'نقشه بردار نظارت' and project.quality_control_manager_id == approver.id:
                is_approver = True
            elif role_name == 'نظارت پروژه' and project.quality_control_manager_id == approver.id:
                is_approver = True
            elif role_name == 'مسئول آزمایشگاه' and project.lab_manager_id == approver.id:
                is_approver = True
            elif role_name == 'مسئول HSSE پروژه' and project.hsse_manager_id == approver.id:
                is_approver = True
            
            # بررسی UserProjectRole
            if not is_approver:
                try:
                    role_obj = Role.objects.get(name=role_name)
                    upr = UserProjectRole.objects.filter(
                        user=approver,
                        role=role_obj
                    ).filter(
                        models.Q(projects=project) | models.Q(all_projects=True)
                    ).first()
                    if upr:
                        is_approver = True
                except:
                    pass
            
            if is_approver:
                approval.role = role_name
                approval.save(update_fields=['role'])
                break
        
        # اگر نقش پیدا نشد، از اولین نقش ممکن استفاده می‌کنیم
        if not approval.role:
            approval.role = required_roles[0]
            approval.save(update_fields=['role'])


def reverse_populate_role(apps, schema_editor):
    """برگشت تغییرات - نیازی نیست"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('experiment', '0013_sievesize'),
        ('core', '0009_alter_userprojectrole_all_projects_and_more'),
        ('project', '0013_alter_projectlayer_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='experimentapproval',
            name='role',
            field=models.CharField(default='', max_length=100, verbose_name='نقش تاییدکننده', help_text='نقش کاربر هنگام ثبت تاییدیه'),
            preserve_default=False,
        ),
        migrations.RunPython(populate_role_for_existing_approvals, reverse_populate_role),
        migrations.AlterUniqueTogether(
            name='experimentapproval',
            unique_together={('experiment_response', 'approver', 'role')},
        ),
    ]

