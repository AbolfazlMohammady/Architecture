from django.core.management.base import BaseCommand
from django.utils import timezone
import jdatetime
from project.models import Project, ProjectLayer, LayerType
from experiment.models import (
    ExperimentType, ExperimentSubType, ConcretePlace,
    ExperimentRequest, PaymentCoefficient
)
from core.models import User
from decimal import Decimal
import random


class Command(BaseCommand):
    help = 'ایجاد داده‌های نمونه: 2 پروژه، آزمایشات و ضرایب پرداخت'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('شروع ایجاد داده‌های نمونه...'))
        
        # دریافت یا ایجاد کاربر
        user, _ = User.objects.get_or_create(
            username='admin',
            defaults={
                'first_name': 'مدیر',
                'last_name': 'سیستم',
                'email': 'admin@example.com',
            }
        )
        
        # دریافت یا ایجاد انواع آزمایش (باید ابتدا setup_experiment_data اجرا شود)
        experiment_type_concrete, _ = ExperimentType.objects.get_or_create(
            name='مقاومت فشاری بتن و ملات'
        )
        experiment_type_asphalt, _ = ExperimentType.objects.get_or_create(
            name='آسفالت'
        )
        experiment_type_compaction, _ = ExperimentType.objects.get_or_create(
            name='تراکم نسبی'
        )
        
        # دریافت یا ایجاد محل بتن‌ریزی
        concrete_place, _ = ConcretePlace.objects.get_or_create(
            name='فونداسیون'
        )
        
        # دریافت زیرنوع‌ها (باید ابتدا setup_experiment_data اجرا شود)
        subtype_embankment, _ = ExperimentSubType.objects.get_or_create(
            name='خاکریزی',
            experiment_type=experiment_type_compaction
        )
        subtype_concrete, _ = ExperimentSubType.objects.get_or_create(
            name='C_28',
            experiment_type=experiment_type_concrete
        )
        subtype_asphalt_binder, _ = ExperimentSubType.objects.get_or_create(
            name='بیندر',
            experiment_type=experiment_type_asphalt
        )
        
        # دریافت یا ایجاد انواع لایه
        layer_type_asphalt, _ = LayerType.objects.get_or_create(
            name='آسفالت گرم'
        )
        layer_type_base, _ = LayerType.objects.get_or_create(
            name='اساس'
        )
        layer_type_subbase, _ = LayerType.objects.get_or_create(
            name='زیر اساس'
        )
        layer_type_embankment, _ = LayerType.objects.get_or_create(
            name='خاکریزی'
        )
        
        # ایجاد پروژه 1
        project1, created1 = Project.objects.get_or_create(
            name='پروژه آزادراه تهران-شمال',
            defaults={
                'masafat': Decimal('120.500'),
                'width': Decimal('12.5'),
                'start_kilometer': Decimal('0.000'),
                'end_kilometer': Decimal('120.500'),
                'contract_amount': Decimal('500000000000'),
                'project_manager': user,
                'technical_manager': user,
                'quality_control_manager': user,
            }
        )
        if created1:
            self.stdout.write(self.style.SUCCESS(f'✓ پروژه 1 ایجاد شد: {project1.name}'))
        
        # ایجاد لایه‌های پروژه 1
        layers1 = []
        for i, (layer_type, thickness) in enumerate([
            (layer_type_embankment, 50),
            (layer_type_subbase, 30),
            (layer_type_base, 20),
            (layer_type_asphalt, 10),
        ], start=1):
            layer, _ = ProjectLayer.objects.get_or_create(
                project=project1,
                layer_type=layer_type,
                thickness_cm=thickness,
                defaults={
                    'order_from_top': i,
                    'state': ProjectLayer.VARIABLE,
                    'status': ProjectLayer.IN_PROGRESS,
                }
            )
            layers1.append(layer)
        
        # ایجاد پروژه 2
        project2, created2 = Project.objects.get_or_create(
            name='پروژه جاده مرند-جلفا',
            defaults={
                'masafat': Decimal('85.300'),
                'width': Decimal('10.0'),
                'start_kilometer': Decimal('0.000'),
                'end_kilometer': Decimal('85.300'),
                'contract_amount': Decimal('350000000000'),
                'project_manager': user,
                'technical_manager': user,
                'quality_control_manager': user,
            }
        )
        if created2:
            self.stdout.write(self.style.SUCCESS(f'✓ پروژه 2 ایجاد شد: {project2.name}'))
        
        # ایجاد لایه‌های پروژه 2
        layers2 = []
        for i, (layer_type, thickness) in enumerate([
            (layer_type_embankment, 45),
            (layer_type_subbase, 25),
            (layer_type_base, 18),
            (layer_type_asphalt, 8),
        ], start=1):
            layer, _ = ProjectLayer.objects.get_or_create(
                project=project2,
                layer_type=layer_type,
                thickness_cm=thickness,
                defaults={
                    'order_from_top': i,
                    'state': ProjectLayer.VARIABLE,
                    'status': ProjectLayer.IN_PROGRESS,
                }
            )
            layers2.append(layer)
        
        # ایجاد آزمایشات برای پروژه 1
        self.stdout.write(self.style.SUCCESS('ایجاد آزمایشات برای پروژه 1...'))
        for i, layer in enumerate(layers1):
            if layer.layer_type == layer_type_embankment:
                exp_type = experiment_type_compaction
                exp_subtype = subtype_embankment
                target_density = Decimal('95.5')
                target_strength = None
                concrete_place_obj = None
                mix_design = None
            elif layer.layer_type == layer_type_asphalt:
                exp_type = experiment_type_asphalt
                exp_subtype = subtype_asphalt_binder
                target_density = None
                target_strength = None
                concrete_place_obj = None
                mix_design = 'طرح اختلاط آسفالت گرم'
            else:
                exp_type = experiment_type_concrete
                exp_subtype = subtype_concrete
                target_density = None
                target_strength = Decimal('25.0')
                concrete_place_obj = concrete_place
                mix_design = None
            
            request_date = jdatetime.date.today()
            
            # ایجاد فایل خالی برای request_file (اجباری است)
            from django.core.files.base import ContentFile
            dummy_file = ContentFile(b'')
            dummy_file.name = f'dummy_{project1.id}_{i+1}.txt'
            
            exp_request, _ = ExperimentRequest.objects.get_or_create(
                project=project1,
                layer=layer,
                order=i+1,
                defaults={
                    'user': user,
                    'request_date': request_date,
                    'start_kilometer': Decimal(f'{i*30}.000'),
                    'end_kilometer': Decimal(f'{(i+1)*30}.000'),
                    'target_density': target_density,
                    'target_strength': target_strength,
                    'description': f'آزمایش برای لایه {layer.layer_type.name}',
                    'request_file': dummy_file,
                }
            )
            exp_request.experiment_type.add(exp_type)
            exp_request.experiment_subtype.add(exp_subtype)
            if concrete_place_obj:
                exp_request.concrete_place = concrete_place_obj
                exp_request.save()
        
        # ایجاد آزمایشات برای پروژه 2
        self.stdout.write(self.style.SUCCESS('ایجاد آزمایشات برای پروژه 2...'))
        for i, layer in enumerate(layers2):
            if layer.layer_type == layer_type_embankment:
                exp_type = experiment_type_compaction
                exp_subtype = subtype_embankment
                target_density = Decimal('96.0')
                target_strength = None
                concrete_place_obj = None
                mix_design = None
            elif layer.layer_type == layer_type_asphalt:
                exp_type = experiment_type_asphalt
                exp_subtype = subtype_asphalt_binder
                target_density = None
                target_strength = None
                concrete_place_obj = None
                mix_design = 'طرح اختلاط آسفالت گرم'
            else:
                exp_type = experiment_type_concrete
                exp_subtype = subtype_concrete
                target_density = None
                target_strength = Decimal('28.0')
                concrete_place_obj = concrete_place
                mix_design = None
            
            request_date = jdatetime.date.today()
            
            # ایجاد فایل خالی برای request_file (اجباری است)
            from django.core.files.base import ContentFile
            dummy_file = ContentFile(b'')
            dummy_file.name = f'dummy_{project2.id}_{i+1}.txt'
            
            exp_request, _ = ExperimentRequest.objects.get_or_create(
                project=project2,
                layer=layer,
                order=i+1,
                defaults={
                    'user': user,
                    'request_date': request_date,
                    'start_kilometer': Decimal(f'{i*20}.000'),
                    'end_kilometer': Decimal(f'{(i+1)*20}.000'),
                    'target_density': target_density,
                    'target_strength': target_strength,
                    'description': f'آزمایش برای لایه {layer.layer_type.name}',
                    'request_file': dummy_file,
                }
            )
            exp_request.experiment_type.add(exp_type)
            exp_request.experiment_subtype.add(exp_subtype)
            if concrete_place_obj:
                exp_request.concrete_place = concrete_place_obj
                exp_request.save()
        
        # ایجاد ضرایب پرداخت برای پروژه 1
        self.stdout.write(self.style.SUCCESS('ایجاد ضرایب پرداخت برای پروژه 1...'))
        # ایجاد ضرایب با الگوهای کاملاً متفاوت برای هر لایه
        layer_coefficients_project1 = {
            'EMBANKMENT': [0.88, 0.90, 0.92, 0.94, 0.96, 0.98, 1.00, 0.99, 0.97, 0.95],  # روند صعودی-نزولی، میانگین: ~0.95
            'SUBBASE': [0.85, 0.87, 0.89, 0.91, 0.93, 0.95, 0.97, 0.96, 0.94, 0.92],  # روند صعودی-نزولی، میانگین: ~0.92
            'BASE': [0.92, 0.94, 0.96, 0.98, 1.00, 1.02, 1.04, 1.03, 1.01, 0.99],  # روند صعودی-نزولی، میانگین: ~0.99
            'ASPHALT': [0.95, 0.97, 0.99, 1.01, 1.03, 1.05, 1.07, 1.06, 1.04, 1.02],  # روند صعودی-نزولی، میانگین: ~1.02
        }
        
        for layer_code, coefficients in layer_coefficients_project1.items():
            for i, coeff in enumerate(coefficients):
                calculation_date = jdatetime.date.today()
                PaymentCoefficient.objects.get_or_create(
                    project=project1,
                    layer=layer_code,
                    start_kilometer=Decimal(f'{i*12}.000'),
                    end_kilometer=Decimal(f'{(i+1)*12}.000'),
                    defaults={
                        'coefficient': Decimal(str(coeff)),
                        'calculation_date': calculation_date,
                    }
                )
        
        # ایجاد ضرایب پرداخت برای پروژه 2
        self.stdout.write(self.style.SUCCESS('ایجاد ضرایب پرداخت برای پروژه 2...'))
        # ایجاد ضرایب با الگوهای کاملاً متفاوت برای هر لایه (روند نزولی-صعودی)
        layer_coefficients_project2 = {
            'EMBANKMENT': [0.94, 0.92, 0.90, 0.88, 0.86, 0.88, 0.90, 0.92, 0.94, 0.96],  # روند نزولی-صعودی، میانگین: ~0.91
            'SUBBASE': [0.91, 0.89, 0.87, 0.85, 0.83, 0.85, 0.87, 0.89, 0.91, 0.93],  # روند نزولی-صعودی، میانگین: ~0.88
            'BASE': [0.97, 0.95, 0.93, 0.91, 0.89, 0.91, 0.93, 0.95, 0.97, 0.99],  # روند نزولی-صعودی، میانگین: ~0.94
            'ASPHALT': [1.00, 0.98, 0.96, 0.94, 0.92, 0.94, 0.96, 0.98, 1.00, 1.02],  # روند نزولی-صعودی، میانگین: ~0.97
        }
        
        for layer_code, coefficients in layer_coefficients_project2.items():
            for i, coeff in enumerate(coefficients):
                calculation_date = jdatetime.date.today()
                PaymentCoefficient.objects.get_or_create(
                    project=project2,
                    layer=layer_code,
                    start_kilometer=Decimal(f'{i*8}.000'),
                    end_kilometer=Decimal(f'{(i+1)*8}.000'),
                    defaults={
                        'coefficient': Decimal(str(coeff)),
                        'calculation_date': calculation_date,
                    }
                )
        
        self.stdout.write(self.style.SUCCESS('\n✓ تمام داده‌های نمونه با موفقیت ایجاد شدند!'))
        self.stdout.write(self.style.SUCCESS(f'  - پروژه 1: {project1.name}'))
        self.stdout.write(self.style.SUCCESS(f'  - پروژه 2: {project2.name}'))
        self.stdout.write(self.style.SUCCESS(f'  - تعداد آزمایشات: {ExperimentRequest.objects.count()}'))
        self.stdout.write(self.style.SUCCESS(f'  - تعداد ضرایب پرداخت: {PaymentCoefficient.objects.count()}'))

