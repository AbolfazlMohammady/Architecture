# Generated manually to set parent_project=None for existing projects

from django.db import migrations


def set_parent_project_to_none(apps, schema_editor):
    """تنظیم parent_project=None برای همه پروژه‌های موجود"""
    Project = apps.get_model('project', 'Project')
    # همه پروژه‌هایی که parent_project ندارند را به None تنظیم می‌کنیم
    # این برای پروژه‌های موجود قبل از اضافه شدن فیلد parent_project است
    Project.objects.filter(parent_project__isnull=True).update(parent_project=None)


def reverse_set_parent_project_to_none(apps, schema_editor):
    """Reverse migration - هیچ کاری لازم نیست"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0015_rename_budget_to_contract_amount'),
    ]

    operations = [
        migrations.RunPython(set_parent_project_to_none, reverse_set_parent_project_to_none),
    ]






