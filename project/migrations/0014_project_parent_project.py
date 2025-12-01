# Generated manually for sub-projects feature

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0013_alter_projectlayer_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='name',
            field=models.CharField(max_length=100, verbose_name='نام پروژه'),
        ),
        migrations.AddField(
            model_name='project',
            name='parent_project',
            field=models.ForeignKey(
                blank=True,
                help_text='اگر این پروژه زیرپروژه است، پروژه اصلی را انتخاب کنید',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='sub_projects',
                to='project.project',
                verbose_name='پروژه اصلی'
            ),
        ),
        migrations.AlterUniqueTogether(
            name='project',
            unique_together={('name', 'parent_project')},
        ),
    ]

