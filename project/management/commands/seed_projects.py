from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from pathlib import Path
import random

from project.models import (
    Project,
    ProjectLayer,
    ProjectStructure,
    LayerType,
    StructureType,
)
from experiment.models import PaymentCoefficient


PROJECT_TEMPLATES = [
    {
        "name": "پروژه آزادراه تهران-شمال",
        "masafat": Decimal("32.4"),
        "width": Decimal("30.0"),
        "contract_amount": Decimal("85000000000"),
        "start_km": Decimal("0.000"),
        "end_km": Decimal("32.400"),
    },
    {
        "name": "پروژه کمربندی جنوبی مشهد",
        "masafat": Decimal("24.8"),
        "width": Decimal("26.0"),
        "contract_amount": Decimal("62000000000"),
        "start_km": Decimal("0.000"),
        "end_km": Decimal("24.800"),
    },
    {
        "name": "پروژه توسعه محور اصفهان-یزد",
        "masafat": Decimal("41.5"),
        "width": Decimal("28.0"),
        "contract_amount": Decimal("92000000000"),
        "start_km": Decimal("5.000"),
        "end_km": Decimal("46.500"),
    },
    {
        "name": "پروژه راه دسترسی بندر چابهار",
        "masafat": Decimal("18.7"),
        "width": Decimal("24.0"),
        "contract_amount": Decimal("54000000000"),
        "start_km": Decimal("2.500"),
        "end_km": Decimal("21.200"),
    },
    {
        "name": "پروژه بهسازی محور تبریز-ارومیه",
        "masafat": Decimal("27.3"),
        "width": Decimal("27.0"),
        "contract_amount": Decimal("78000000000"),
        "start_km": Decimal("10.000"),
        "end_km": Decimal("37.300"),
    },
]


class Command(BaseCommand):
    help = "Seed sample projects with layers, structures, and payment coefficients"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing sample data before seeding new records",
        )

    def handle(self, *args, **options):
        User = get_user_model()

        if options["reset"]:
            self._reset_sample_data()

        # Ensure at least one user exists to assign as managers
        user = User.objects.order_by("id").first()
        if not user:
            user = User.objects.create_user(
                username="seed_user",
                password="seed_password",
                first_name="Seed",
                last_name="User",
                email="seed@example.com",
            )
            self.stdout.write(self.style.WARNING("Created fallback user 'seed_user'"))

        # Ensure layer types exist
        layer_types_data = {
            "EMBANKMENT": "خاکریزی",
            "SUBBASE": "زیر اساس",
            "BASE": "اساس",
            "ASPHALT": "آسفالت گرم",
            "LEAN_CONCRETE": "بتن مگر",
        }
        layer_type_objects = {}
        for code, name in layer_types_data.items():
            lt, _ = LayerType.objects.get_or_create(name=name)
            layer_type_objects[code] = lt

        # Ensure structure types exist
        structure_types_data = ["پل", "آبرو", "تونل", "دیوار حائل"]
        structure_type_objects = {}
        for name in structure_types_data:
            st, _ = StructureType.objects.get_or_create(name=name)
            structure_type_objects[name] = st

        base_profile_dir = Path("project_profiles")
        base_profile_dir.mkdir(parents=True, exist_ok=True)

        created_projects = []
        for template in PROJECT_TEMPLATES:
            project, was_created = Project.objects.update_or_create(
                name=template["name"],
                defaults={
                    "start_date": timezone.now().date(),
                    "end_date": timezone.now().date(),
                    "contract_amount": template["contract_amount"],
                    "masafat": template["masafat"],
                    "width": template["width"],
                    "start_kilometer": template["start_km"],
                    "end_kilometer": template["end_km"],
                    "project_manager": user,
                    "technical_manager": user,
                    "quality_control_manager": user,
                    "lab_manager": user,
                    "hsse_manager": user,
                },
            )

            created_projects.append(project)
            if was_created:
                self.stdout.write(
                    self.style.SUCCESS(f"Created project: {project.name}")
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f"Updated project: {project.name}")
                )

            self._seed_layers(project, layer_type_objects)
            self._seed_structures(project, structure_type_objects)
            self._seed_payment_coefficients(project)

        total_projects = Project.objects.count()
        total_coeffs = PaymentCoefficient.objects.count()
        self.stdout.write(
            self.style.SUCCESS(
                f"Seeding completed. Total projects: {total_projects}, Payment coefficients: {total_coeffs}"
            )
        )

    # ------------------------------------------------------------------ helpers
    def _reset_sample_data(self):
        sample_names = [tpl["name"] for tpl in PROJECT_TEMPLATES]
        Project.objects.filter(name__in=sample_names).delete()
        self.stdout.write(self.style.WARNING("Previous sample projects removed."))

    def _seed_layers(self, project, layer_types):
        base_layers = [
            ("EMBANKMENT", 45, ProjectLayer.VARIABLE, ProjectLayer.IN_PROGRESS),
            ("SUBBASE", 28, ProjectLayer.FIXED, ProjectLayer.NOT_STARTED),
            ("BASE", 22, ProjectLayer.FIXED, ProjectLayer.NOT_STARTED),
            ("ASPHALT", 12, ProjectLayer.VARIABLE, ProjectLayer.IN_PROGRESS),
        ]

        ProjectLayer.objects.filter(project=project).delete()
        for order, (code, thickness, state, status) in enumerate(base_layers, start=1):
            ProjectLayer.objects.create(
                project=project,
                layer_type=layer_types[code],
                thickness_cm=thickness,
                order_from_top=order,
                state=state,
                status=status,
            )

        # Duplicate asphalt layer to test numbering
        ProjectLayer.objects.create(
            project=project,
            layer_type=layer_types["ASPHALT"],
            thickness_cm=9,
            order_from_top=len(base_layers) + 1,
            state=ProjectLayer.VARIABLE,
            status=ProjectLayer.NOT_STARTED,
        )

    def _seed_structures(self, project, structure_types):
        structures_data = [
            ("پل", 3000, 2950, 3080, ProjectStructure.IN_PROGRESS),
            ("آبرو", 7500, 7460, 7540, ProjectStructure.NOT_STARTED),
            ("دیوار حائل", 12400, 12360, 12480, ProjectStructure.COMPLETED),
        ]

        ProjectStructure.objects.filter(project=project).delete()
        for struct_name, location, start, end, status in structures_data:
            ProjectStructure.objects.create(
                project=project,
                structure_type=structure_types[struct_name],
                kilometer_location=location,
                start_kilometer=start,
                end_kilometer=end,
                status=status,
            )

    def _seed_payment_coefficients(self, project):
        # Remove existing coefficients for this project to avoid inflation
        project.paymentcoefficient_set.all().delete()

        layer_codes = ["EMBANKMENT", "SUBBASE", "BASE", "ASPHALT"]
        date_base = timezone.now().date()

        for layer_code in layer_codes:
            # Generate 5-8 coefficients with slight variation
            count = random.randint(5, 8)
            for idx in range(count):
                base_value = {
                    "EMBANKMENT": 0.85,
                    "SUBBASE": 0.9,
                    "BASE": 0.95,
                    "ASPHALT": 0.92,
                }[layer_code]
                variance = random.uniform(-0.12, 0.08)
                value = max(0.55, min(1.15, base_value + variance))

                PaymentCoefficient.objects.create(
                    project=project,
                    layer=layer_code,
                    coefficient=Decimal(str(round(value, 3))),
                    start_kilometer=Decimal(str(project.start_kilometer + Decimal(idx))),
                    end_kilometer=Decimal(str(project.start_kilometer + Decimal(idx) + Decimal("0.5"))),
                    calculation_date=date_base,
                )

