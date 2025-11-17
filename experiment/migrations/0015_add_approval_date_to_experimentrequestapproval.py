# Generated manually

import django_jalali.db.models
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('experiment', '0014_add_role_to_experimentapproval'),
    ]

    operations = [
        migrations.AddField(
            model_name='experimentrequestapproval',
            name='approval_date',
            field=django_jalali.db.models.jDateField(blank=True, null=True, verbose_name='تاریخ تایید'),
        ),
    ]

