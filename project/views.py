from . import models as project_models
# from experiment import models as experiment_models
from django.views import generic
from django.db.models import Q
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from . import forms as project_forms
from django.forms.models import model_to_dict
import pandas as pd
import re
import math
from experiment.views import get_layer_display_name


def assign_layer_display_names(layers):
    """
    Attach display_name attribute to each layer with numbering for duplicate layer types.
    Uses Persian numbers and converts "خاکریزی" to "خاک ریز".
    """
    layers = list(layers)
    name_counts = {}
    for layer in layers:
        # تبدیل "خاکریزی" به "خاک ریز"
        layer_name = layer.layer_type.name.replace('خاکریزی', 'خاک ریز')
        name_counts[layer_name] = name_counts.get(layer_name, 0) + 1

    indices = {name: 0 for name in name_counts}
    persian_numbers = ['', 'یک', 'دو', 'سه', 'چهار', 'پنج', 'شش', 'هفت', 'هشت', 'نه', 'ده']
    for layer in layers:
        # تبدیل "خاکریزی" به "خاک ریز"
        layer_name = layer.layer_type.name.replace('خاکریزی', 'خاک ریز')
        if name_counts[layer_name] > 1:
            indices[layer_name] += 1
            index = indices[layer_name]
            # تبدیل عدد به فارسی
            if index <= 10:
                persian_index = persian_numbers[index]
            else:
                persian_index = str(index)
            layer.display_name = f"{layer_name} {persian_index}"
        else:
            layer.display_name = layer_name
    return layers
# Create your views here.

class ProjectDetailView(generic.DetailView):
    model = project_models.Project
    template_name = 'project/project-detail.html'
    context_object_name = 'project'

class ProjectListView(generic.ListView):
    model = project_models.Project
    template_name = 'project/project-list.html'
    context_object_name = 'projects'
    paginate_by = 30
    
    def get_queryset(self):
        user = self.request.user
        
        # بررسی اینکه آیا کاربر لاگین شده است
        if not user.is_authenticated:
            return project_models.Project.objects.none()
        
        # بررسی اینکه آیا کاربر نقش دارد
        try:
            user_roles = set(user.roles.values_list('name', flat=True))
        except AttributeError:
            # اگر کاربر نقش نداشته باشد
            user_roles = set()
        
        global_roles = set(['ادمین', 'مدیر عامل موسسه', 'مدیر فنی موسسه', 'مدیر کنترل کیفی موسسه', 'کارشناس موسسه'])
        if user_roles & global_roles:
            return super().get_queryset()
        # فقط پروژه‌های مرتبط با کاربر
        return super().get_queryset().filter(
            Q(project_manager=user) | 
            Q(technical_manager=user) | 
            Q(quality_control_manager=user) | 
            Q(project_experts=user)
        ).distinct()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # بررسی اینکه آیا کاربر لاگین شده است
        if not user.is_authenticated:
            context['error_message'] = 'برای مشاهده لیست پروژه‌ها، لطفاً ابتدا وارد حساب کاربری خود شوید.'
            context['projects'] = []
            context['project_progress'] = {}
            context['main_projects'] = []
            context['sub_projects_dict'] = {}
            return context
        
        projects = context['projects']
        
        # جدا کردن پروژه‌های اصلی و زیرپروژه‌ها
        main_projects = []
        sub_projects_dict = {}  # {parent_id: [sub_projects]}
        main_project_ids = set()  # برای ردیابی پروژه‌های اصلی که باید نمایش داده شوند
        main_projects_dict = {}  # {project_id: project} برای جلوگیری از تکرار
        
        for project in projects:
            if project.is_main_project():
                # اگر قبلاً اضافه نشده باشد
                if project.id not in main_project_ids:
                    main_projects.append(project)
                    main_project_ids.add(project.id)
                    main_projects_dict[project.id] = project
            else:
                parent_id = project.parent_project.id
                if parent_id not in sub_projects_dict:
                    sub_projects_dict[parent_id] = []
                sub_projects_dict[parent_id].append(project)
                # اگر کاربر به زیرپروژه دسترسی دارد اما به پروژه اصلی دسترسی ندارد،
                # پروژه اصلی را هم به لیست اضافه کن (فقط برای نمایش)
                if parent_id not in main_project_ids:
                    parent_project = project.parent_project
                    main_projects.append(parent_project)
                    main_project_ids.add(parent_id)
                    main_projects_dict[parent_id] = parent_project

        project_progress_dict = {}

        # محاسبه پیشرفت برای همه پروژه‌ها (اصلی و زیرپروژه‌ها)
        all_projects = list(projects)
        for project in all_projects:
            project_layers = project_models.ProjectLayer.objects.filter(project=project)
            completed_layers = project_layers.filter(status=project_models.ProjectLayer.COMPLETED)
            if project_layers.exists():
                progress = round((completed_layers.count() / project_layers.count()) * 100)
            else:
                progress = 0
            project_progress_dict[project.id] = progress

        context['project_progress'] = project_progress_dict
        context['main_projects'] = main_projects
        context['sub_projects_dict'] = sub_projects_dict
        return context

class CreateProjectView(generic.CreateView):
    model = project_models.Project
    form_class = project_forms.ProjectForm
    template_name = 'project/create-project.html'
    # success_url = reverse_lazy("create-project-layer", kwargs={'pk': object.pk})
    
    def get_success_url(self):
        # اگر پروژه اصلی است (is_parent_only=True)، به صفحه جزئیات پروژه هدایت می‌شود
        # در غیر این صورت به صفحه ایجاد لایه هدایت می‌شود
        if self.object.is_parent_only:
            return reverse("project-detail", kwargs={'pk': self.object.pk})
        return reverse("create-project-layer", kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        response = super().form_valid(form)
        project = self.object
        user = self.request.user
        
        # تنظیم is_parent_only
        is_parent_only = form.cleaned_data.get('is_parent_only', False)
        try:
            project.is_parent_only = is_parent_only
            project.save(update_fields=['is_parent_only'])
        except Exception as e:
            # اگر فیلد is_parent_only وجود ندارد، migration اجرا نشده است
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error saving is_parent_only: {e}")
            messages.error(self.request, "خطا در ذخیره اطلاعات. لطفاً migration را اجرا کنید: python manage.py migrate project")
        
        # اگر project_manager تنظیم نشده باشد، کاربر فعلی را به عنوان project_manager تنظیم کن
        if not project.project_manager:
            project.project_manager = user
            project.save(update_fields=['project_manager'])
        
        # اگر technical_manager تنظیم نشده باشد، کاربر فعلی را به عنوان technical_manager تنظیم کن
        if not project.technical_manager:
            project.technical_manager = user
            project.save(update_fields=['technical_manager'])
        
        # اگر quality_control_manager تنظیم نشده باشد، کاربر فعلی را به عنوان quality_control_manager تنظیم کن
        if not project.quality_control_manager:
            project.quality_control_manager = user
            project.save(update_fields=['quality_control_manager'])
        
        # اضافه کردن کاربر به کارشناسان پروژه اگر نیست
        if user not in project.project_experts.all():
            project.project_experts.add(user)
        
        lab_manager = form.cleaned_data.get('lab_manager')
        hsse_manager = form.cleaned_data.get('hsse_manager')
        # اگر مسئول آزمایشگاه انتخاب شده و جزو کارشناسان پروژه نیست اضافه کن
        if lab_manager and lab_manager not in project.project_experts.all():
            project.project_experts.add(lab_manager)
        # اگر مسئول HSSE انتخاب شده و جزو کارشناسان پروژه نیست اضافه کن
        if hsse_manager and hsse_manager not in project.project_experts.all():
            project.project_experts.add(hsse_manager)
        return response

# class ExperimentRequestListView(generic.ListView):
#     model = experiment_models.ExperimentRequest
#     template_name = 'project/experiment-request-list.html'
#     context_object_name = 'experiment_requests'
#     paginate_by = 30

#     def get_queryset(self):
#         return super().get_queryset().filter(user=self.request.user).order_by('-created_at')


class CreateProjectLayerView(generic.CreateView):
    model = project_models.ProjectLayer
    form_class = project_forms.ProjectLayerForm
    template_name = 'project/create-project-layer.html'
    # success_url = reverse_lazy("create-project-structure")

    # def form_valid(self, form):
    #     form.instance.project = project_models.Project.objects.get(pk=self.kwargs['pk'])
    #     return super().form_valid(form)
    def get_success_url(self):
        return reverse("create-project-layer", kwargs={'pk': self.object.project.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = project_models.Project.objects.get(pk=self.kwargs['pk'])
        layers_qs = project.projectlayer_set.all().order_by('order_from_top')
        context['layers'] = assign_layer_display_names(layers_qs)  # یا: ProjectLayer.objects.filter(project=project)
        context['project'] = project
        # لایه‌های قبلی برای استفاده مجدد
        previous_layers = project.projectlayer_set.all().order_by('order_from_top')
        context['previous_layers'] = assign_layer_display_names(previous_layers)
        return context

    
    def get_initial(self):
        context = super().get_initial()
        context['project'] = project_models.Project.objects.get(pk=self.kwargs['pk'])
        return context
    
    def form_valid(self, form):
        # Ensure it's saved even if the field is disabled in the form
        form.instance.project = project_models.Project.objects.get(pk=self.kwargs['pk'])

        if getattr(form, 'order_auto_assigned', False):
            messages.warning(
                self.request,
                f"ترتیب انتخاب شده ({form.order_original_value}) قبلاً استفاده شده بود. ترتیب جدید {form.cleaned_data.get('order_from_top')} به‌صورت خودکار تنظیم شد."
            )
        # Additional validation to ensure no duplicates
        existing_layer = project_models.ProjectLayer.objects.filter(
            project=form.instance.project,
            layer_type=form.instance.layer_type,
            thickness_cm=form.instance.thickness_cm,
            state=form.instance.state,
            status=form.instance.status,
            order_from_top=form.cleaned_data.get('order_from_top'),
        ).exclude(pk=form.instance.pk if form.instance.pk else None)
        if existing_layer.exists():
            form.add_error(None, "لایه‌ای با این مشخصات و ترتیب قبلاً وجود دارد. لطفاً ترتیب را تغییر دهید یا مشخصات متفاوتی وارد کنید.")
            return self.form_invalid(form)
        return super().form_valid(form)

class ProjectLayerDetailView(generic.DetailView):
    model = project_models.ProjectLayer
    template_name = 'project/project-layer-detail.html'
    context_object_name = 'project_layer'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        assign_layer_display_names([context['project_layer']])
        return context
    
class ProjectLayerListView(generic.ListView):
    model = project_models.ProjectLayer
    template_name = 'project/project-layer-list.html'
    context_object_name = 'project_layers'
    paginate_by = 30
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project_id = self.kwargs['pk']
        context["project"] = project_models.Project.objects.get(id=project_id)
        # ساخت جدول خلاصه: چند بار هر نوع لایه استفاده شده و ترتیب‌ها
        layers = self.get_queryset()
        summary = {}
        for layer in layers:
            lt = layer.layer_type.name
            if lt not in summary:
                summary[lt] = {"count": 0, "orders": []}
            summary[lt]["count"] += 1
            summary[lt]["orders"].append(layer.order_from_top)
        # مرتب‌سازی ترتیب‌ها
        for lt in summary:
            summary[lt]["orders"].sort()
        context["layer_type_summary"] = summary

        page_obj = context.get('page_obj')
        if page_obj is not None:
            annotated_layers = assign_layer_display_names(page_obj.object_list)
            page_obj.object_list = annotated_layers
            context['project_layers'] = page_obj
        else:
            layers = assign_layer_display_names(context.get('project_layers', layers))
            context['project_layers'] = layers
        return context
    
    def get_queryset(self):
        # Get the project ID from the URL
        project_id = self.kwargs['pk']
        
        # Filter the ProjectLayer objects based on the project ID
        return super().get_queryset().filter(project__id=project_id).order_by('order_from_top')
    
class CreateProjectStructureView(generic.CreateView):
    model = project_models.ProjectStructure
    form_class = project_forms.ProjectStructureForm
    template_name = 'project/create-project-structure.html'
    # success_url = reverse_lazy("create-project-structure")
    context_object_name = 'project_structure'
    
    def get_success_url(self):
        return reverse_lazy("create-project-structure", kwargs={"pk": self.kwargs["pk"]})

    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = project_models.Project.objects.get(pk=self.kwargs['pk'])
        context["structure"] = project_models.ProjectStructure.objects.filter(project=context['project'])
        return context

    
    def get_initial(self):
        context = super().get_initial()
        context['project'] = project_models.Project.objects.get(pk=self.kwargs['pk'])
        return context
    
    def form_valid(self, form):
        # Ensure it's saved even if the field is disabled in the form
        form.instance.project = project_models.Project.objects.get(pk=self.kwargs['pk'])
        return super().form_valid(form)


class ProjectDashboardView(generic.DetailView):
    model = project_models.Project
    template_name = 'project/dashboard.html'
    context_object_name = 'project'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project:project_models.Project = self.get_object()
        
        # خواندن فایل پروفیل
        profile_data = self.read_file(project.profile_file, project)
        
        # دریافت لایه‌ها و مرتب‌سازی بر اساس ترتیب از بالا
        layers = project_models.ProjectLayer.objects.filter(project=project).order_by('order_from_top')
        
        # دریافت ابنیه‌ها
        structures = project_models.ProjectStructure.objects.filter(project=project).order_by('kilometer_location')
        
        # دریافت درخواست‌های آزمایش
        from experiment.models import ExperimentRequest, ExperimentResponse, ExperimentApproval
        experiment_requests = ExperimentRequest.objects.filter(project=project).select_related(
            'layer'
        ).prefetch_related(
            'experiment_type', 'experiment_subtype',
            'experimentresponse_set__experimentapproval_set'
        )
        
        # گروه‌بندی درخواست‌ها بر اساس لایه و کیلومتراژ
        experiment_data = {}
        for request in experiment_requests:
            layer_id = request.layer.id
            if layer_id not in experiment_data:
                experiment_data[layer_id] = []
            
            # محاسبه وضعیت واقعی بر اساس پاسخ‌ها و تاییدیه‌ها
            actual_status = request.get_actual_status()
            
            # بررسی وضعیت تایید برای نمایش در داشبورد
            approval_status = None
            has_rejected = False
            latest_response = None
            latest_response_date = None
            response_status = None  # 'approved' | 'rejected' | None
            is_recompact = False
            if hasattr(request, 'experimentresponse_set') and request.experimentresponse_set.exists():
                latest_response = request.experimentresponse_set.order_by('-created_at').first()
                latest_response_date = latest_response.response_date.strftime('%Y/%m/%d') if latest_response and latest_response.response_date else None
                if hasattr(latest_response, 'experimentapproval_set') and latest_response.experimentapproval_set.exists():
                    # بررسی اینکه آیا هر کدام رد شده است
                    has_rejected = latest_response.experimentapproval_set.filter(status=ExperimentApproval.REJECTED).exists()
                    # بررسی وضعیت کامل تایید
                    approval_status_by_role = latest_response.get_approval_status_by_role()
                    if all(v == 'تایید شده' for v in approval_status_by_role.values() if v != 'تعریف نشده'):
                        approval_status = ExperimentApproval.APPROVED
                        response_status = 'approved'
                    elif has_rejected:
                        approval_status = ExperimentApproval.REJECTED
                        response_status = 'rejected'
                    else:
                        approval_status = None  # در حال بررسی
                # تشخیص ریکامپکت از توضیحات پاسخ
                if latest_response and latest_response.description and 'ریکامپکت' in latest_response.description:
                    is_recompact = True
            
            # دریافت نام نمایشی لایه
            layer_display_name = get_layer_display_name(request.layer) if request.layer else None
            
            experiment_data[layer_id].append({
                'id': request.id,
                'order': request.order,
                'kilometer_start': float(request.start_kilometer),
                'kilometer_end': float(request.end_kilometer),
                'experiment_type': ', '.join([et.name for et in request.experiment_type.all()]),
                'experiment_subtype': ', '.join([est.name for est in request.experiment_subtype.all()]) if request.experiment_subtype.exists() else None,
                'status': actual_status,  # استفاده از وضعیت واقعی
                'approval_status': approval_status,
                'has_rejected': has_rejected,
                'request_date': request.request_date.strftime('%Y/%m/%d') if request.request_date else None,
                'latest_response_date': latest_response_date,
                'response_status': response_status,
                'is_recompact': is_recompact,
                'description': request.description,
                'layer_display_name': layer_display_name,
            })
        
        # ساخت executed_ranges برای هر لایه بر اساس آزمایش‌های همان لایه
        layer_executed_ranges = {}
        for layer in layers:
            layer_executed_ranges[layer.id] = []
        for request in experiment_requests:
            if request.status in [1, 2]:  # فقط آزمایش‌های در حال انجام یا تکمیل شده
                layer_id = request.layer.id
                layer_executed_ranges[layer_id].append({
                    'start': float(request.start_kilometer),
                    'end': float(request.end_kilometer)
                })
        # تبدیل شیء Project به دیکشنری ساده قابل JSON
        context['project_data'] = {
            'id': project.id,
            'name': project.name,
            'masafat': float(project.masafat),
            'width': float(project.width),
            'start_kilometer': float(project.start_kilometer),
            'end_kilometer': float(project.end_kilometer),
            "profile_data": profile_data,
            "layers": [
                {
                    'id': layer.id,
                    'name': layer.layer_type.name,
                    'display_name': get_layer_display_name(layer),
                    'thickness_cm': layer.thickness_cm,
                    'order_from_top': layer.order_from_top,
                    'state': layer.state,  # 0: متغیر, 1: ثابت
                    'status': layer.status,  # 0: در انتظار آزمایش, 1: در حال انجام, 2: تکمیل شده
                    'experiments': experiment_data.get(layer.id, []),
                    'executed_ranges': layer_executed_ranges.get(layer.id, [])
                } for layer in layers
            ],
            "structures": [
                {
                    'id': structure.id,
                    'name': structure.structure_type.name,
                    'kilometer_location': structure.kilometer_location,
                    'start_kilometer': structure.start_kilometer,
                    'end_kilometer': structure.end_kilometer,
                    'status': structure.status
                } for structure in structures
            ],
        }
        # چاپ executed_ranges هر لایه برای بررسی
        for layer in context['project_data']['layers']:
            print(f"LAYER: {layer['name']} executed_ranges: {layer.get('executed_ranges')}")
        print('TEST')
        return context

    def read_file(self, profile_file, project=None):
        import re
        import pandas as pd
        import math
        if not profile_file:
            return {'land_points': [], 'road_points': [], 'error': 'فایل پروفیل موجود نیست'}
        try:
            df = pd.read_excel(profile_file, engine='openpyxl')
            columns = [col.lower().strip() for col in df.columns]

            def parse_station(val):
                if pd.isna(val):
                    return None
                val = str(val).replace(',', '').strip()
                # پشتیبانی از فرمت 6+300.00
                match = re.match(r"(\d+)\+(\d+\.?\d*)", val)
                if match:
                    return float(match.group(1)) * 1000 + float(match.group(2))
                try:
                    return float(val)
                except Exception:
                    return None

            def parse_value(val):
                if pd.isna(val) or val == '':
                    return None
                val = str(val).replace('m', '').replace('M', '').strip()
                try:
                    return float(val)
                except Exception:
                    return None

            land_points = []
            road_points = []
            # حالت ویژه: فقط اختلاف ارتفاع داریم و ستون Elevation Design بی‌معنی است
            if ('station' in columns and 'elevation difference' in columns):
                station_col = [c for c in df.columns if c.lower().strip() in ['station', 'ایستگاه']][0]
                diff_col = [c for c in df.columns if c.lower().strip() in ['elevation difference', 'اختلاف ارتفاع']][0]
                x = df[station_col].apply(parse_station)
                y = df[diff_col].apply(parse_value)
                # استفاده از مقادیر واقعی Elevation Difference (بدون نرمال‌سازی)
                # این باعث می‌شود محور Y از minimum Elevation Difference شروع شود
                land_points = [
                    {"x": float(xv) / 1000, "y": float(yv)}
                    for xv, yv in zip(x, y) if xv is not None and yv is not None
                ]
                # road_points روی Y=0 هستند (Elevation Design = 0)
                road_points = [
                    {"x": float(xv) / 1000, "y": 0.0}
                    for xv in x if xv is not None
                ]
                # محاسبه start_kilometer و end_kilometer از داده‌های فایل
                valid_x = [xv for xv in x if xv is not None]
                if valid_x and project:
                    min_station = min(valid_x) / 1000  # تبدیل به کیلومتر
                    max_station = max(valid_x) / 1000  # تبدیل به کیلومتر
                    # به‌روزرسانی start_kilometer و end_kilometer در پروژه
                    project.start_kilometer = min_station
                    project.end_kilometer = max_station
                    project.save(update_fields=['start_kilometer', 'end_kilometer'])
            # حالت‌های دیگر (قبلی)
            elif ('station' in columns and 'cutfill' in columns):
                station_col = [c for c in df.columns if c.lower().strip() in ['station', 'ایستگاه']][0]
                y1_col = [c for c in df.columns if c.lower().strip() in ['cutfill', 'اختلاف ارتفاع']][0]
                x = df[station_col].apply(parse_station)
                y1 = df[y1_col].apply(parse_value)
                land_points = [
                    {"x": float(xv) / 1000, "y": float(yv)}
                    for xv, yv in zip(x, y1) if xv is not None and yv is not None
                ]
                road_points = [
                    {"x": float(xv) / 1000, "y": 0.0}
                    for xv in x if xv is not None
                ]
            elif len(df.columns) >= 2:
                x = df.iloc[:, 0].apply(parse_station)
                y1 = df.iloc[:, 1].apply(parse_value)
                land_points = [
                    {"x": float(xv) / 1000, "y": float(yv)}
                    for xv, yv in zip(x, y1) if xv is not None and yv is not None
                ]
                if len(df.columns) >= 3:
                    y2 = df.iloc[:, 2].apply(parse_value)
                    road_points = [
                        {"x": float(xv) / 1000, "y": float(yv)}
                        for xv, yv in zip(x, y2) if xv is not None and yv is not None
                    ]
                else:
                    road_points = [
                        {"x": float(xv) / 1000, "y": 0.0}
                        for xv in x if xv is not None
                    ]
            else:
                return {'land_points': [], 'road_points': [], 'error': 'ساختار فایل اکسل نامعتبر است'}

            # حذف نقاط نامعتبر (NaN)
            def is_valid_point(p):
                return (
                    p is not None and
                    'x' in p and 'y' in p and
                    p['x'] is not None and p['y'] is not None and
                    not (isinstance(p['x'], float) and math.isnan(p['x'])) and
                    not (isinstance(p['y'], float) and math.isnan(p['y']))
                )
            land_points = [p for p in land_points if is_valid_point(p)]
            road_points = [p for p in road_points if is_valid_point(p)]

            # مرتب‌سازی بر اساس x برای جلوگیری از نویز و ناهماهنگی
            land_points = sorted(land_points, key=lambda p: p['x'])
            road_points = sorted(road_points, key=lambda p: p['x'])

            # --- حذف نرمال‌سازی خودکار ---
            # استفاده از مقادیر واقعی داده‌ها (بدون نرمال‌سازی)
            # این باعث می‌شود محور Y از minimum Elevation Difference شروع شود
            warning = None

            result = {
                'land_points': land_points,
                'road_points': road_points,
                'total_points': len(land_points)
            }
            if warning:
                result['warning'] = warning
            return result
        except Exception as e:
            return {'land_points': [], 'road_points': [], 'error': str(e)}
    
class ProjectUpdateView(generic.UpdateView):
    model = project_models.Project
    # fields = ['name', 'contract_amount', 'start_date', 'end_date', 'project_manager']  # به‌دلخواه
    # fields = "__all__"
    form_class = project_forms.ProjectForm
    template_name = 'project/project-update.html'
    context_object_name = 'project'

    def form_valid(self, form):
        response = super().form_valid(form)
        project = self.object
        
        # تنظیم is_parent_only
        is_parent_only = form.cleaned_data.get('is_parent_only', False)
        project.is_parent_only = is_parent_only
        project.save(update_fields=['is_parent_only'])
        
        return response

    def get_success_url(self):
        return reverse('project-detail', kwargs={'pk': self.object.pk})

class ProjectLayerUpdateView(generic.UpdateView):
    model = project_models.ProjectLayer
    form_class = project_forms.ProjectLayerForm
    template_name = "project/project-layer-update.html"
    
    def get_success_url(self):
        return reverse('project-layer-detail',kwargs={"pk":self.object.pk})

class projectLayerDeleteView(generic.DeleteView):
    model = project_models.ProjectLayer
    template_name = 'project/project-layer-confirm-delete.html'  # قالب تأیید حذف
    success_url = reverse_lazy('project-list')  # مسیر برگشت بعد از حذف
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class ProjectStructureListView(generic.ListView):
    model = project_models.ProjectStructure
    template_name = 'project/project-structure-list.html'
    context_object_name = 'project_structure'
    paginate_by = 30
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project_id = self.kwargs['pk']
        context["project"] = project_models.Project.objects.get(id=project_id)
        return context
    
    def get_queryset(self):
        # Get the project ID from the URL
        project_id = self.kwargs['pk']
        
        # Filter the ProjectLayer objects based on the project ID
        return super().get_queryset().filter(project__id=project_id)
    
class ProjectStructureDetailView(generic.DetailView):
    model = project_models.ProjectStructure
    template_name = 'project/project-structure-detail.html'
    context_object_name = 'project_structure'

class ProjectStructureDeleteView(generic.DeleteView):
    model = project_models.ProjectStructure
    template_name = 'project/project-structure-confirm-delete.html'  # قالب تأیید حذف
    # success_url = reverse_lazy('project-structure-list')  # مسیر برگشت بعد از حذف
    
    
    def get_success_url(self):
        return reverse('project-structure-list',kwargs={"pk":self.object.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    
class ProjectStructureUpdateView(generic.UpdateView):
    model = project_models.ProjectStructure
    form_class = project_forms.ProjectStructureForm
    template_name = "project/project-structure-update.html"
    
    def get_success_url(self):
        return reverse('project-structure-detail',kwargs={"pk":self.object.pk})


class ExperimentGridDashboardView(generic.DetailView):
    """داشبورد شطرنجی برای نمایش درخواست‌های آزمایش"""
    model = project_models.Project
    template_name = 'project/experiment_grid_dashboard.html'
    context_object_name = 'project'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.get_object()
        
        # دریافت لایه‌ها و مرتب‌سازی
        layers = project_models.ProjectLayer.objects.filter(project=project).order_by('order_from_top')
        
        # دریافت درخواست‌های آزمایش
        from experiment.models import ExperimentRequest, ExperimentResponse, ExperimentApproval
        from experiment.views import get_layer_display_name
        
        experiment_requests = ExperimentRequest.objects.filter(project=project).select_related(
            'layer'
        ).prefetch_related(
            'experiment_type', 'experiment_subtype',
            'experimentresponse_set__experimentapproval_set'
        )
        
        # محاسبه بازه کیلومتراژ (ستون‌ها)
        # تقسیم پروژه به بازه‌های 0.1 کیلومتری
        start_km = float(project.start_kilometer)
        end_km = float(project.end_kilometer)
        km_range = end_km - start_km
        
        # ایجاد بازه‌های کیلومتراژ (هر 0.1 کیلومتر)
        cell_size = 0.1  # اندازه هر سلول به کیلومتر
        columns = []
        current_km = start_km
        while current_km < end_km:
            columns.append({
                'start': round(current_km, 1),
                'end': round(min(current_km + cell_size, end_km), 1),
                'label': f"{round(current_km, 1)}-{round(min(current_km + cell_size, end_km), 1)}"
            })
            current_km += cell_size
        
        # ساخت داده‌های grid
        grid_data = []
        for layer in layers:
            layer_display_name = get_layer_display_name(layer)
            row_data = {
                'layer_id': layer.id,
                'layer_name': layer_display_name,
                'cells': []
            }
            
            # برای هر ستون (بازه کیلومتراژ)
            for col in columns:
                # پیدا کردن درخواست‌های آزمایش که با این بازه همپوشانی دارند
                overlapping_requests = experiment_requests.filter(
                    layer=layer,
                    start_kilometer__lt=col['end'],
                    end_kilometer__gt=col['start']
                )
                
                cell_info = None
                if overlapping_requests.exists():
                    # استفاده از اولین درخواست (اگر چندتایی باشد)
                    request = overlapping_requests.first()
                    
                    # محاسبه وضعیت
                    actual_status = request.get_actual_status()
                    
                    # بررسی پاسخ و تاییدیه
                    response_status = None
                    is_recompact = False
                    latest_response = None
                    
                    if request.experimentresponse_set.exists():
                        latest_response = request.experimentresponse_set.order_by('-created_at').first()
                        approvals = latest_response.experimentapproval_set.all()
                        
                        if approvals.exists():
                            if approvals.filter(status=ExperimentApproval.REJECTED).exists():
                                response_status = 'rejected'
                            elif latest_response.is_fully_approved():
                                response_status = 'approved'
                            
                            # بررسی ریکامپکت (اگر در توضیحات یا description باشد)
                            if latest_response.description and 'ریکامپکت' in latest_response.description:
                                is_recompact = True
                    
                    # تعیین رنگ بر اساس وضعیت
                    color = None
                    if is_recompact:
                        color = 'purple'  # بنفش برای ریکامپکت
                    elif response_status == 'approved':
                        color = 'green'  # سبز برای قابل قبول
                    elif response_status == 'rejected':
                        color = 'red'  # قرمز برای غیر قابل قبول
                    elif actual_status == ExperimentRequest.IN_PROGRESS:
                        color = 'orange'  # نارنجی برای تایید شده (رفته برای آزمایش)
                    elif actual_status == ExperimentRequest.PENDING:
                        color = 'lightgray'  # طوسی روشن برای درخواست ثبت شده
                    else:
                        color = 'lightgray'
                    
                    cell_info = {
                        'request_id': request.id,
                        'color': color,
                        'status': actual_status,
                        'request_date': request.request_date.strftime('%Y/%m/%d') if request.request_date else None,
                        'response_date': latest_response.response_date.strftime('%Y/%m/%d') if latest_response and latest_response.response_date else None,
                        'experiment_type': ', '.join([et.name for et in request.experiment_type.all()]),
                        'description': request.description,
                        'response_description': latest_response.description if latest_response else None,
                        'is_recompact': is_recompact,
                    }
                
                row_data['cells'].append(cell_info)
            
            grid_data.append(row_data)
        
        context['grid_data'] = grid_data
        context['columns'] = columns
        context['project'] = project
        context['start_km'] = start_km
        context['end_km'] = end_km
        
        return context
