from django.core.management.base import BaseCommand
from experiment.models import ExperimentType, ExperimentSubType, ConcretePlace


class Command(BaseCommand):
    help = 'ایجاد تمام انواع آزمایش، زیرنوع‌ها و محل‌های بتن‌ریزی طبق داکیومنت'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('شروع ایجاد داده‌های آزمایش...'))
        
        # 1. ایجاد محل‌های بتن‌ریزی
        self.stdout.write(self.style.SUCCESS('\n=== ایجاد محل‌های بتن‌ریزی ==='))
        concrete_places = [
            'فونداسیون',
            'کوله',
            'دستک',
            'ستون',
            'شناژ',
            'دال',
            'تیر پیش‌ساخته',
            'بتن ماهیچه (پشت‌بند جدول)',
            'باکس پیش‌ساخته',
        ]
        
        for place_name in concrete_places:
            place, created = ConcretePlace.objects.get_or_create(name=place_name)
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ ایجاد شد: {place_name}'))
            else:
                self.stdout.write(self.style.WARNING(f'  موجود بود: {place_name}'))
        
        # 2. ایجاد انواع آزمایش و زیرنوع‌های آن‌ها
        self.stdout.write(self.style.SUCCESS('\n=== ایجاد انواع آزمایش و زیرنوع‌ها ==='))
        
        experiment_types_data = [
            {
                'name': 'ترانشه برداری مسیر',
                'subtypes': [
                    'وزن مخصوص',
                    'دانه بندی',
                    'گچی و نمکی',
                    'دامنه خمیری',
                    'مواد آلی',
                ]
            },
            {
                'name': 'تراکم نسبی',
                'subtypes': [
                    'بستر',
                    'راکفیل',
                    'خاکریزی',
                    'سابگرید',
                    'زیراساس',
                    'اساس',
                    'VSS',
                ]
            },
            {
                'name': 'مصالح سنگی',
                'subtypes': [
                    'دانه بندی',
                    'S.E',
                    'گام خمیری',
                    'حد روانی',
                    'درصد شکستگی',
                ]
            },
            {
                'name': 'مقاومت فشاری بتن و ملات',
                'subtypes': [
                    'B_100',
                    'B_200',
                    'B_250',
                    'B_300',
                    'B_350',
                    'B_400',
                    'C_8',
                    'C_16',
                    'C_20',
                    'C_24',
                    'C_28',
                    'C_32',
                    'ملات بنایی',
                ]
            },
            {
                'name': 'قیرپاشی',
                'subtypes': [
                    'پریمکت',
                    'تک کت',
                ]
            },
            {
                'name': 'آسفالت',
                'subtypes': [
                    'بیندر',
                    'توپکا',
                ]
            },
        ]
        
        for exp_type_data in experiment_types_data:
            # ایجاد یا دریافت نوع آزمایش
            exp_type, created = ExperimentType.objects.get_or_create(
                name=exp_type_data['name']
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'\n✓ ایجاد شد: {exp_type.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'\n  موجود بود: {exp_type.name}'))
            
            # ایجاد زیرنوع‌ها
            for subtype_name in exp_type_data['subtypes']:
                subtype, created = ExperimentSubType.objects.get_or_create(
                    name=subtype_name,
                    experiment_type=exp_type
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'  ✓ زیرنوع ایجاد شد: {subtype_name}'))
                else:
                    self.stdout.write(self.style.WARNING(f'    موجود بود: {subtype_name}'))
        
        self.stdout.write(self.style.SUCCESS('\n✓ تمام داده‌ها با موفقیت ایجاد شدند!'))
        self.stdout.write(self.style.SUCCESS(f'  - تعداد انواع آزمایش: {ExperimentType.objects.count()}'))
        self.stdout.write(self.style.SUCCESS(f'  - تعداد زیرنوع‌ها: {ExperimentSubType.objects.count()}'))
        self.stdout.write(self.style.SUCCESS(f'  - تعداد محل‌های بتن‌ریزی: {ConcretePlace.objects.count()}'))

