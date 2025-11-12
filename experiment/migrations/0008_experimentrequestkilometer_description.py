from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('experiment', '0007_experimentrequestfile_experimentrequestkilometer'),
    ]

    operations = [
        migrations.AddField(
            model_name='experimentrequestkilometer',
            name='description',
            field=models.TextField(blank=True, null=True, verbose_name='توضیحات بازه'),
        ),
    ]

