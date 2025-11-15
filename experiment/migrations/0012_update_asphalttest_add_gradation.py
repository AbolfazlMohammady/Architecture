# Generated manually

from django.db import migrations, models
import django.db.models.deletion
import django_jalali.db.models as jmodels


def migrate_asphalt_fields(apps, schema_editor):
    """تبدیل فیلدهای قدیمی AsphaltTest به فیلدهای جدید"""
    AsphaltTest = apps.get_model('experiment', 'AsphaltTest')
    
    # فیلدهای قدیمی: density, air_void, vma, vfa, stability, flow
    # فیلدهای جدید: bitumen_percentage, fracture_percentage, temperature, 
    #                air_void_percentage, vma_percentage, vfa_percentage, filler_to_bitumen_ratio
    
    # اگر داده‌ای وجود دارد، می‌توانیم آن را تبدیل کنیم
    # اما چون فیلدهای قدیمی و جدید متفاوت هستند، بهتر است داده‌های قدیمی را نگه داریم
    # یا اگر می‌خواهیم حذف کنیم، اینجا می‌توانیم انجام دهیم
    pass


def reverse_migrate_asphalt_fields(apps, schema_editor):
    """برگرداندن تغییرات"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('experiment', '0011_experimentapproval_approval_date'),
    ]

    operations = [
        # حذف فیلدهای قدیمی AsphaltTest
        migrations.RemoveField(
            model_name='asphalttest',
            name='density',
        ),
        migrations.RemoveField(
            model_name='asphalttest',
            name='air_void',
        ),
        migrations.RemoveField(
            model_name='asphalttest',
            name='vma',
        ),
        migrations.RemoveField(
            model_name='asphalttest',
            name='vfa',
        ),
        migrations.RemoveField(
            model_name='asphalttest',
            name='stability',
        ),
        migrations.RemoveField(
            model_name='asphalttest',
            name='flow',
        ),
        
        # اضافه کردن فیلدهای جدید AsphaltTest
        migrations.AddField(
            model_name='asphalttest',
            name='bitumen_percentage',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text='(طرح اختلاط) ۱۰٪+ >= X >= (طرح اختلاط) ۱۰٪-',
                max_digits=5,
                null=True,
                verbose_name='درصد قیر نسبت به مخلوط آسفالت'
            ),
        ),
        migrations.AddField(
            model_name='asphalttest',
            name='fracture_percentage',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text='باید >= 80 باشد',
                max_digits=5,
                null=True,
                verbose_name='درصد شکستگی'
            ),
        ),
        migrations.AddField(
            model_name='asphalttest',
            name='temperature',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text='163 >= X >= 136',
                max_digits=5,
                null=True,
                verbose_name='درجه حرارت آسفالت'
            ),
        ),
        migrations.AddField(
            model_name='asphalttest',
            name='air_void_percentage',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text='بیندر: 6 >= X >= 3, توپکا: 5 >= X >= 3',
                max_digits=5,
                null=True,
                verbose_name='درصد فضای خالی'
            ),
        ),
        migrations.AddField(
            model_name='asphalttest',
            name='vma_percentage',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text='15 >= X >= 13',
                max_digits=5,
                null=True,
                verbose_name='درصد حجمی فضای خالی (VMA)'
            ),
        ),
        migrations.AddField(
            model_name='asphalttest',
            name='vfa_percentage',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text='75 >= X >= 60',
                max_digits=5,
                null=True,
                verbose_name='درصد فضای خالی پرشده با قیر (VFA)'
            ),
        ),
        migrations.AddField(
            model_name='asphalttest',
            name='filler_to_bitumen_ratio',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text='1.2 >= X >= 0.6',
                max_digits=5,
                null=True,
                verbose_name='درصد فیلر به قیر'
            ),
        ),
        
        # اضافه کردن related_name به experiment_response
        migrations.AlterField(
            model_name='asphalttest',
            name='experiment_response',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='asphalt_tests',
                to='experiment.experimentresponse',
                verbose_name='پاسخ آزمایش'
            ),
        ),
        
        # ایجاد مدل AsphaltGradation
        migrations.CreateModel(
            name='AsphaltGradation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sieve_size', models.CharField(help_text='مثال: 3, 2.5, 2, 1.5, 1, 4/3, 2/1, ...', max_length=20, verbose_name='اندازه الک')),
                ('passing_percentage', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True, verbose_name='درصد عبوری')),
                ('created_at', jmodels.jDateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')),
                ('asphalt_test', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='gradations', to='experiment.asphalttest', verbose_name='آزمایش آسفالت')),
            ],
            options={
                'verbose_name': 'دانه\u200cبندی آسفالت',
                'verbose_name_plural': 'دانه\u200cبندی\u200cهای آسفالت',
                'ordering': ['asphalt_test', 'sieve_size'],
            },
        ),
    ]

