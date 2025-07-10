from django import forms
from . import models as project_models
from django_select2.forms import Select2Widget,Select2MultipleWidget
from core import models as core_models
from jalali_date.fields import JalaliDateField
from jalali_date.widgets import AdminJalaliDateWidget


class ProjectForm(forms.ModelForm):
    start_date = JalaliDateField(
        widget=AdminJalaliDateWidget,
        label='تاریخ شروع',
        required=True
    )
    
    end_date = JalaliDateField(
        widget=AdminJalaliDateWidget,
        label='تاریخ پایان',
        required=False
    )
    
    def __init__(self, *args, **kwargs):
        super(ProjectForm, self).__init__(*args, **kwargs)
        
        self.fields['name'].widget.attrs["class"] = "form-control form-control-sm"
        
        self.fields["project_manager"].widget = Select2Widget()
        self.fields["project_manager"].queryset = core_models.User.objects.all()
        self.fields["project_manager"].widget.attrs["class"] = "form-select"
        
        self.fields["technical_manager"].widget = Select2Widget()
        self.fields["technical_manager"].queryset = core_models.User.objects.all()
        self.fields["technical_manager"].widget.attrs["class"] = "form-select"
        
        self.fields["quality_control_manager"].widget = Select2Widget()
        self.fields["quality_control_manager"].queryset = core_models.User.objects.all()
        self.fields["quality_control_manager"].widget.attrs["class"] = "form-select"
        
        
        # self.fields["start_date"].widget.attrs["class"] = "form-control"
        # self.fields["end_date"].widget.attrs["class"] = "form-control"
        
        self.fields["budget"].widget.attrs["class"] = "form-control form-control-sm"
        self.fields["masafat"].widget.attrs["class"] = "form-control form-control-sm"
        self.fields["width"].widget.attrs["class"] = "form-control form-control-sm"
        self.fields["start_kilometer"].widget.attrs["class"] = "form-control form-control-sm"
        self.fields["end_kilometer"].widget.attrs["class"] = "form-control form-control-sm"
        self.fields["profile_file"].widget.attrs["class"] = "form-control form-control-sm"
        self.fields["project_experts"].widget = Select2MultipleWidget()
        self.fields["project_experts"].queryset = core_models.User.objects.all()
        self.fields["project_experts"].widget.attrs["class"] = "form-select"
        
    
    
    class Meta:
        model = project_models.Project
        fields = ['name',
                  'project_manager',
                  'technical_manager',
                  'quality_control_manager',
                  "project_experts",
                  "budget",
                  "masafat",
                  "width", 
                  "start_kilometer",
                  "end_kilometer", 
                  "profile_file",
                  "start_date",
                  "end_date"
                  ]
        # , 'start_date' "budget",
        # widgets = {
        #     'start_date': forms.DateInput(attrs={'type': 'date'}),
        #     'end_date': forms.DateInput(attrs={'type': 'date'}),
        # }

class ProjectLayerForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ProjectLayerForm, self).__init__(*args, **kwargs)
        
        self.fields["thickness_cm"].widget.attrs["class"] = "form-control form-control-sm"
        self.fields["order_from_top"].widget.attrs["class"] = "form-control form-control-sm"
        
        self.fields["project"].widget = Select2Widget()
        self.fields["project"].queryset = project_models.Project.objects.all()
        self.fields["project"].widget.attrs["class"] = "form-select"
        self.fields["project"].disabled = True
        
        self.fields["status"].widget.attrs["class"] = "form-select"
        self.fields["state"].widget.attrs["class"] = "form-select"
        
        self.fields["layer_type"].widget.attrs["class"] = "form-select"
        
        # اگر لایه جدید است، شماره ترتیب را به صورت خودکار تنظیم کن
        if not self.instance.pk:
            project = self.initial.get('project')
            if project:
                last_order = project_models.ProjectLayer.objects.filter(project=project).order_by('-order_from_top').first()
                self.initial['order_from_top'] = (last_order.order_from_top + 1) if last_order else 1
    
    class Meta:
        model = project_models.ProjectLayer
        fields = ['project', 'layer_type', 'thickness_cm', 'order_from_top', 'state', 'status']
        widgets = {
            'state': forms.Select(choices=project_models.ProjectLayer.LAYER_STATE),
        }
    
class ProjectStructureForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ProjectStructureForm, self).__init__(*args, **kwargs)
        
        self.fields["project"].widget = Select2Widget()
        self.fields["project"].queryset = project_models.Project.objects.all()
        self.fields["project"].widget.attrs["class"] = "form-select"
        self.fields["project"].disabled = True
        
        self.fields["structure_type"].widget.attrs["class"] = "form-select"
        self.fields["kilometer_location"].widget.attrs["class"] = "form-control form-control-sm"
    
        self.fields["start_kilometer"].widget.attrs["class"] = "form-control form-control-sm"
        self.fields["end_kilometer"].widget.attrs["class"] = "form-control form-control-sm"
        
    class Meta:
        model = project_models.ProjectStructure
        fields = ['project', 'structure_type', 'kilometer_location',"start_kilometer","end_kilometer"]