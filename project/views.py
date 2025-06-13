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
        
        points = self.read_file(project.profile_file)
        
        layers = project_models.ProjectLayer.objects.filter(project=project)
        structures = project_models.ProjectStructure.objects.filter(project=project)
        # تبدیل شیء Project به دیکشنری ساده قابل JSON
        context['project_data'] = {
            'distance': project.distance,
            'width': project.width,
            'start_kilometer': project.start_kilometer,
            'end_kilometer': project.end_kilometer,
            "points":points,
            "layers": list(layers.values()),  # ✅ تبدیل به لیست دیکشنری
            "structures": list(structures.values()),  # 
            
        }
        return context

    def read_file(self,profile_file):
        context = {}
        if profile_file:
            try:
                df = pd.read_excel(profile_file, engine='openpyxl')
                
                # فرض بر این است که ۳ ستون اول فایل اکسل هستند: x، y، elevation (یا هر چیزی که هست)
                # می‌تونی نام ستون‌ها را به‌دلخواه تغییر بده
                data_points = df.iloc[:, :3].values.tolist()  # فقط ۳ ستون اول را بخوان
                land_points = []
                road_points = []
                for row in data_points:
                    land_points.append({"x":row[0],"y":row[1]})
                    road_points.append({"x":row[0],"y":row[2]})
                
                context['profile_points'] = {"landpoints":land_points,"roadpoints":road_points}
            except Exception as e:
                context['profile_points'] = []
                context['profile_error'] = str(e)
        else:
            context['profile_points'] = []
        
        return context
    
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
