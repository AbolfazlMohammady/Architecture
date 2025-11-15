# Generated manually

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_alter_user_roles'),
        ('project', '0013_alter_projectlayer_status'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserProjectRole',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role_name', models.CharField(help_text='مثال: نظارت پیمانکار، نظارت کارفرما، نماینده پیمانکار و...', max_length=100, verbose_name='نام نقش')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='تاریخ به\u200cروزرسانی')),
                ('project', models.ForeignKey(blank=True, help_text='اگر خالی باشد، این نقش برای همه پروژه\u200cها اعمال می\u200cشود', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='user_roles', to='project.project', verbose_name='پروژه')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='project_roles', to='core.user', verbose_name='کاربر')),
            ],
            options={
                'verbose_name': 'نقش کاربر در پروژه',
                'verbose_name_plural': 'نقش\u200cهای کاربران در پروژه\u200cها',
                'ordering': ['user', 'project', 'role_name'],
                'unique_together': {('user', 'project', 'role_name')},
            },
        ),
    ]

