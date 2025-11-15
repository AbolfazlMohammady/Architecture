# Generated manually

from django.db import migrations, models
import django.db.models.deletion


def migrate_role_name_to_role(apps, schema_editor):
    """تبدیل role_name به role"""
    UserProjectRole = apps.get_model('core', 'UserProjectRole')
    Role = apps.get_model('core', 'Role')
    
    for upr in UserProjectRole.objects.all():
        # پیدا کردن یا ایجاد Role با نام role_name
        role, created = Role.objects.get_or_create(name=upr.role_name)
        upr.role_id = role.id
        upr.save()


def migrate_project_to_projects(apps, schema_editor):
    """تبدیل project به projects"""
    UserProjectRole = apps.get_model('core', 'UserProjectRole')
    
    for upr in UserProjectRole.objects.all():
        if upr.project_id:
            # اگر project وجود دارد، آن را به projects اضافه می‌کنیم
            upr.projects.add(upr.project_id)
        else:
            # اگر project خالی است، all_projects را True می‌کنیم
            upr.all_projects = True
            upr.save()


def reverse_migrate_role_to_role_name(apps, schema_editor):
    """برگرداندن role به role_name"""
    UserProjectRole = apps.get_model('core', 'UserProjectRole')
    
    for upr in UserProjectRole.objects.all():
        if upr.role_id:
            role = apps.get_model('core', 'Role').objects.get(id=upr.role_id)
            upr.role_name = role.name
            upr.save()


def reverse_migrate_projects_to_project(apps, schema_editor):
    """برگرداندن projects به project"""
    UserProjectRole = apps.get_model('core', 'UserProjectRole')
    
    for upr in UserProjectRole.objects.all():
        projects = upr.projects.all()
        if projects.exists():
            # اولین پروژه را به project اختصاص می‌دهیم
            upr.project_id = projects.first().id
            upr.save()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_userprojectrole'),
        ('project', '0013_alter_projectlayer_status'),
    ]

    operations = [
        # حذف unique_together قدیمی (قبل از تغییر فیلدها)
        migrations.AlterUniqueTogether(
            name='userprojectrole',
            unique_together=set(),
        ),
        # اضافه کردن فیلد role (ForeignKey) - موقتاً nullable
        migrations.AddField(
            model_name='userprojectrole',
            name='role',
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='user_project_roles',
                to='core.role',
                verbose_name='نقش'
            ),
        ),
        # اضافه کردن فیلد all_projects
        migrations.AddField(
            model_name='userprojectrole',
            name='all_projects',
            field=models.BooleanField(default=False, verbose_name='همه پروژه\u200cها'),
        ),
        # اضافه کردن ManyToManyField برای projects (قبل از تبدیل داده‌ها)
        migrations.AddField(
            model_name='userprojectrole',
            name='projects',
            field=models.ManyToManyField(
                blank=True,
                related_name='user_roles',
                to='project.project',
                verbose_name='پروژه\u200cها'
            ),
        ),
        # تبدیل role_name به role
        migrations.RunPython(migrate_role_name_to_role, reverse_migrate_role_to_role_name),
        # تبدیل project به projects
        migrations.RunPython(migrate_project_to_projects, reverse_migrate_projects_to_project),
        # حذف فیلد project
        migrations.RemoveField(
            model_name='userprojectrole',
            name='project',
        ),
        # حذف فیلد role_name
        migrations.RemoveField(
            model_name='userprojectrole',
            name='role_name',
        ),
        # تنظیم role به required (بعد از تبدیل داده‌ها)
        migrations.AlterField(
            model_name='userprojectrole',
            name='role',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='user_project_roles',
                to='core.role',
                verbose_name='نقش'
            ),
        ),
        # اضافه کردن unique_together جدید
        migrations.AlterUniqueTogether(
            name='userprojectrole',
            unique_together={('user', 'role')},
        ),
        # تغییر ordering
        migrations.AlterModelOptions(
            name='userprojectrole',
            options={
                'verbose_name': 'نقش کاربر در پروژه',
                'verbose_name_plural': 'نقش\u200cهای کاربران در پروژه\u200cها',
                'ordering': ['user', 'role'],
            },
        ),
    ]

