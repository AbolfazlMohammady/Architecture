# Generated manually

from django.db import migrations
import django_jalali.db.models as jmodels


class Migration(migrations.Migration):

    dependencies = [
        ('experiment', '0010_alter_experimentrequestfile_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='experimentapproval',
            name='approval_date',
            field=jmodels.jDateField(verbose_name='تاریخ تایید'),
        ),
    ]

