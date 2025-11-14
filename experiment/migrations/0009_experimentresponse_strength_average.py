# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('experiment', '0008_experimentrequestkilometer_description'),
    ]

    operations = [
        migrations.AddField(
            model_name='experimentresponse',
            name='strength_average',
            field=models.DecimalField(blank=True, decimal_places=3, editable=False, max_digits=20, null=True, verbose_name='میانگین مقاومت'),
        ),
    ]

