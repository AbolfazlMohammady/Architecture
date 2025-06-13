from django.core.management.base import BaseCommand
from experiment.models import ExperimentType, ExperimentSubType

class Command(BaseCommand):
    help = 'Adds more experiment types and subtypes'

    def handle(self, *args, **kwargs):
        # Add more experiment types
        experiment_types = [
            {
                'name': 'آزمایش بتن',
                'subtypes': [
                    'مقاومت فشاری',
                    'مقاومت کششی',
                    'مقاومت خمشی',
                    'مقاومت کششی غیرمستقیم',
                    'مقاومت برشی',
                    'مقاومت پیچشی',
                    'مقاومت کششی مستقیم',
                    'مقاومت کششی غیرمستقیم',
                    'مقاومت خمشی خالص',
                    'مقاومت خمشی مرکب'
                ]
            },
            {
                'name': 'آزمایش آسفالت',
                'subtypes': [
                    'مقاومت فشاری',
                    'مقاومت کششی',
                    'مقاومت خمشی',
                    'مقاومت کششی غیرمستقیم',
                    'مقاومت برشی',
                    'مقاومت پیچشی',
                    'مقاومت کششی مستقیم',
                    'مقاومت کششی غیرمستقیم',
                    'مقاومت خمشی خالص',
                    'مقاومت خمشی مرکب'
                ]
            },
            {
                'name': 'آزمایش خاک',
                'subtypes': [
                    'مقاومت فشاری',
                    'مقاومت کششی',
                    'مقاومت خمشی',
                    'مقاومت برشی',
                    'مقاومت پیچشی',
                    'مقاومت کششی مستقیم',
                    'مقاومت کششی غیرمستقیم',
                    'مقاومت خمشی خالص',
                    'مقاومت خمشی مرکب'
                ]
            },
            {
                'name': 'آزمایش سنگ',
                'subtypes': [
                    'مقاومت فشاری',
                    'مقاومت کششی',
                    'مقاومت خمشی',
                    'مقاومت برشی',
                    'مقاومت پیچشی',
                    'مقاومت کششی مستقیم',
                    'مقاومت کششی غیرمستقیم',
                    'مقاومت خمشی خالص',
                    'مقاومت خمشی مرکب'
                ]
            }
        ]

        for exp_type_data in experiment_types:
            # Create or get experiment type
            exp_type, created = ExperimentType.objects.get_or_create(
                name=exp_type_data['name']
            )
            self.stdout.write(
                self.style.SUCCESS(f'{"Created" if created else "Found"} experiment type: {exp_type.name}')
            )

            # Create subtypes
            for subtype_name in exp_type_data['subtypes']:
                subtype, created = ExperimentSubType.objects.get_or_create(
                    name=subtype_name,
                    experiment_type=exp_type
                )
                self.stdout.write(
                    self.style.SUCCESS(f'{"Created" if created else "Found"} subtype: {subtype.name} for {exp_type.name}')
                ) 