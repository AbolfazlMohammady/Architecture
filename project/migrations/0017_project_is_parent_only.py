# Generated manually for adding is_parent_only field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0016_set_existing_projects_parent_to_none'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='is_parent_only',
            field=models.BooleanField(default=False, help_text='اگر این پروژه فقط یک پروژه اصلی است (بدون اطلاعات فنی)، این گزینه را فعال کنید', verbose_name='پروژه اصلی'),
        ),
    ]

