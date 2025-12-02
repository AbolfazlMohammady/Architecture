# Generated manually for renaming budget to contract_amount

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0014_project_parent_project'),
    ]

    operations = [
        migrations.RenameField(
            model_name='project',
            old_name='budget',
            new_name='contract_amount',
        ),
        migrations.AlterField(
            model_name='project',
            name='contract_amount',
            field=models.DecimalField(blank=True, decimal_places=0, max_digits=50, null=True, verbose_name='رقم قرارداد'),
        ),
    ]

