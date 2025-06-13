from django import forms
from . import models as project_models
from django_select2.forms import Select2Widget,Select2MultipleWidget
from core import models as core_models


class ProjectForm(forms.ModelForm):
    
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
        
        # self.fields["budget"].widget.attrs["class"] = "form-control"
        self.fields["distance"].widget.attrs["class"] = "form-control form-control-sm"
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
                  'technical_manager','quality_control_manager',
                  "project_experts","distance",
                  "width", "start_kilometer",
                  "end_kilometer", "profile_file",
                
                  
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
        
        self.fields["status"].widget.attrs["class"] = "form-select "
        
        self.fields["layer_type"].widget.attrs["class"] = "form-select"
        print("current status value:", self.instance.status)

    
    class Meta:
        model = project_models.ProjectLayer
        fields = ['project', 'layer_type', 'thickness_cm', 'order_from_top', 'status']
    
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