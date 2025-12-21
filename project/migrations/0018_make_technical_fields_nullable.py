# Generated manually for making technical fields nullable

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0017_project_is_parent_only'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='width',
            field=models.DecimalField(decimal_places=3, help_text='عرض پروژه به متر', max_digits=20, null=True, blank=True, verbose_name='عرض (متر)'),
        ),
        migrations.AlterField(
            model_name='project',
            name='start_kilometer',
            field=models.DecimalField(decimal_places=3, help_text='کیلومتر شروع پروژه', max_digits=20, null=True, blank=True, verbose_name='کیلومتر شروع'),
        ),
        migrations.AlterField(
            model_name='project',
            name='end_kilometer',
            field=models.DecimalField(decimal_places=3, help_text='کیلومتر پایان پروژه', max_digits=20, null=True, blank=True, verbose_name='کیلومتر پایان'),
        ),
        migrations.AlterField(
            model_name='project',
            name='masafat',
            field=models.DecimalField(decimal_places=3, help_text='مسافت پروژه به کیلومتر', max_digits=20, null=True, blank=True, verbose_name='مسافت (کیلومتر)'),
        ),
    ]

