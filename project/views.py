from . import models as project_models
# from experiment import models as experiment_models
from django.views import generic
from django.db.models import Q
from django.urls import reverse_lazy,reverse
from . import forms as project_forms
from django.forms.models import model_to_dict
import pandas as pd
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
        
        # فیلتر پروژه‌ها بر اساس حضور کاربر در سمت‌های مختلف
        return super().get_queryset().filter(
            Q(project_manager=user) | 
            Q(technical_manager=user) | 
            Q(quality_control_manager=user) | 
            Q(project_experts=user)
        ).distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        projects = context['projects']

        project_progress_dict = {}

        for project in projects:
            project_layers = project_models.ProjectLayer.objects.filter(project=project)
            completed_layers = project_layers.filter(status=project_models.ProjectLayer.COMPLETED)
            if project_layers.exists():
                progress = (completed_layers.count() / project_layers.count()) * 100
            else:
                progress = 0
            project_progress_dict[project.id] = progress

        context['project_progress'] = project_progress_dict
        return context

class CreateProjectView(generic.CreateView):
    model = project_models.Project
    form_class = project_forms.ProjectForm
    template_name = 'project/create-project.html'
    # success_url = reverse_lazy("create-project-layer", kwargs={'pk': object.pk})
    
    def get_success_url(self):
        return reverse("create-project-layer", kwargs={'pk': self.object.pk})

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
        context['layers'] = project.projectlayer_set.all()  # یا: ProjectLayer.objects.filter(project=project)
        context['project'] = project
        return context

    
    def get_initial(self):
        context = super().get_initial()
        context['project'] = project_models.Project.objects.get(pk=self.kwargs['pk'])
        return context
    
    def form_valid(self, form):
        # Ensure it's saved even if the field is disabled in the form
        form.instance.project = project_models.Project.objects.get(pk=self.kwargs['pk'])
        return super().form_valid(form)

class ProjectLayerDetailView(generic.DetailView):
    model = project_models.ProjectLayer
    template_name = 'project/project-layer-detail.html'
    context_object_name = 'project_layer'
    
class ProjectLayerListView(generic.ListView):
    model = project_models.ProjectLayer
    template_name = 'project/project-layer-list.html'
    context_object_name = 'project_layers'
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
        profile_data = self.read_file(project.profile_file)
        
        # دریافت لایه‌ها و مرتب‌سازی بر اساس ترتیب از بالا
        layers = project_models.ProjectLayer.objects.filter(project=project).order_by('order_from_top')
        
        # دریافت ابنیه‌ها
        structures = project_models.ProjectStructure.objects.filter(project=project).order_by('kilometer_location')
        
        # دریافت درخواست‌های آزمایش
        from experiment.models import ExperimentRequest, ExperimentResponse, ExperimentApproval
        experiment_requests = ExperimentRequest.objects.filter(project=project).select_related(
            'layer', 'experiment_type', 'experiment_subtype'
        ).prefetch_related('experimentresponse_set__experimentapproval_set')
        
        # گروه‌بندی درخواست‌ها بر اساس لایه و کیلومتراژ
        experiment_data = {}
        for request in experiment_requests:
            layer_id = request.layer.id
            if layer_id not in experiment_data:
                experiment_data[layer_id] = []
            
            # بررسی وضعیت تایید
            approval_status = None
            if hasattr(request, 'experimentresponse_set') and request.experimentresponse_set.exists():
                response = request.experimentresponse_set.first()
                if hasattr(response, 'experimentapproval_set') and response.experimentapproval_set.exists():
                    approval = response.experimentapproval_set.first()
                    approval_status = approval.status
            
            experiment_data[layer_id].append({
                'id': request.id,
                'kilometer_start': float(request.start_kilometer),
                'kilometer_end': float(request.end_kilometer),
                'experiment_type': request.experiment_type.name,
                'experiment_subtype': request.experiment_subtype.name if request.experiment_subtype else None,
                'status': request.status,
                'approval_status': approval_status,
                'request_date': request.request_date.strftime('%Y/%m/%d') if request.request_date else None,
                'description': request.description,
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
                    'thickness_cm': layer.thickness_cm,
                    'order_from_top': layer.order_from_top,
                    'state': layer.state,  # 0: متغیر, 1: ثابت
                    'status': layer.status,  # 0: شروع نشده, 1: در حال انجام, 2: تکمیل شده
                    'experiments': experiment_data.get(layer.id, [])
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
        return context

    def read_file(self, profile_file):
        if not profile_file:
            return {'land_points': [], 'road_points': [], 'error': 'فایل پروفیل موجود نیست'}
        try:
            df = pd.read_excel(profile_file, engine='openpyxl')
            # تشخیص نام ستون‌ها
            columns = [col.lower() for col in df.columns]
            # حالت ۱: فایل با ستون‌های استاندارد (station, cutFill, graph)
            if 'station' in columns and 'cutfill' in columns:
                x = df[df.columns[columns.index('station')]].astype(float) / 1000  # تبدیل به کیلومتر
                y1 = df[df.columns[columns.index('cutfill')]].astype(float)
                land_points = [{"x": float(xv), "y": float(yv)} for xv, yv in zip(x, y1)]
                # اگر ستون ارتفاع دوم (مثلاً graph) وجود داشت و غیر صفر بود
                if 'graph' in columns and df[df.columns[columns.index('graph')]].abs().sum() > 0:
                    y2 = df[df.columns[columns.index('graph')]].astype(float)
                    road_points = [{"x": float(xv), "y": float(yv)} for xv, yv in zip(x, y2)]
                else:
                    road_points = []
            # حالت ۲: فایل با سه ستون عددی (بدون نام خاص)
            elif len(df.columns) >= 2:
                x = df.iloc[:, 0].astype(float) / 1000
                y1 = df.iloc[:, 1].astype(float)
                land_points = [{"x": float(xv), "y": float(yv)} for xv, yv in zip(x, y1)]
                if len(df.columns) >= 3 and df.iloc[:, 2].abs().sum() > 0:
                    y2 = df.iloc[:, 2].astype(float)
                    road_points = [{"x": float(xv), "y": float(yv)} for xv, yv in zip(x, y2)]
                else:
                    road_points = []
            else:
                return {'land_points': [], 'road_points': [], 'error': 'ساختار فایل اکسل نامعتبر است'}
            return {
                'land_points': land_points,
                'road_points': road_points,
                'total_points': len(land_points)
            }
        except Exception as e:
            return {'land_points': [], 'road_points': [], 'error': str(e)}
    
class ProjectUpdateView(generic.UpdateView):
    model = project_models.Project
    # fields = ['name', 'budget', 'start_date', 'end_date', 'project_manager']  # به‌دلخواه
    # fields = "__all__"
    form_class = project_forms.ProjectForm
    template_name = 'project/project-update.html'
    context_object_name = 'project'

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
