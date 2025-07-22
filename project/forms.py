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
    lab_manager = forms.ModelChoiceField(
        queryset=core_models.User.objects.all(),
        label='مسئول آزمایشگاه',
        required=False,
        widget=Select2Widget(attrs={'class': 'form-select'})
    )
    hsse_manager = forms.ModelChoiceField(
        queryset=core_models.User.objects.all(),
        label='مسئول HSSE پروژه',
        required=False,
        widget=Select2Widget(attrs={'class': 'form-select'})
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
        
        self.fields["lab_manager"].widget = Select2Widget()
        self.fields["lab_manager"].queryset = core_models.User.objects.all()
        self.fields["lab_manager"].widget.attrs["class"] = "form-select"
        self.fields["hsse_manager"].widget = Select2Widget()
        self.fields["hsse_manager"].queryset = core_models.User.objects.all()
        self.fields["hsse_manager"].widget.attrs["class"] = "form-select"
        
        
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
        
    
    
    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        project_manager = cleaned_data.get('project_manager')
        technical_manager = cleaned_data.get('technical_manager')
        quality_control_manager = cleaned_data.get('quality_control_manager')
        budget = cleaned_data.get('budget')
        masafat = cleaned_data.get('masafat')
        width = cleaned_data.get('width')
        start_kilometer = cleaned_data.get('start_kilometer')
        end_kilometer = cleaned_data.get('end_kilometer')
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if name and project_manager and technical_manager and quality_control_manager and budget and masafat and width and start_kilometer and end_kilometer and start_date:
            # بررسی وجود پروژه مشابه با همان مشخصات
            existing_project = project_models.Project.objects.filter(
                name=name,
                project_manager=project_manager,
                technical_manager=technical_manager,
                quality_control_manager=quality_control_manager,
                budget=budget,
                masafat=masafat,
                width=width,
                start_kilometer=start_kilometer,
                end_kilometer=end_kilometer,
                start_date=start_date
            ).exclude(pk=self.instance.pk if self.instance.pk else None)
            
            if existing_project.exists():
                raise forms.ValidationError(
                    "پروژه‌ای با این مشخصات قبلاً وجود دارد. لطفاً مشخصات را تغییر دهید."
                )
        
        return cleaned_data
    
    class Meta:
        model = project_models.Project
        fields = ['name',
                  'project_manager',
                  'technical_manager',
                  'quality_control_manager',
                  "lab_manager",
                  "hsse_manager",
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

    def clean(self):
        cleaned_data = super().clean()
        project = cleaned_data.get('project')
        order_from_top = cleaned_data.get('order_from_top')
        if project and order_from_top is not None:
            # فقط ترتیب باید یکتا باشد
            existing_layer = project_models.ProjectLayer.objects.filter(
                project=project,
                order_from_top=order_from_top
            ).exclude(pk=self.instance.pk if self.instance.pk else None)
            if existing_layer.exists():
                raise forms.ValidationError(
                    "در هر پروژه، ترتیب لایه‌ها نباید تکراری باشد. لطفاً ترتیب دیگری انتخاب کنید."
                )
        return cleaned_data

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
    
    def clean(self):
        cleaned_data = super().clean()
        project = cleaned_data.get('project')
        structure_type = cleaned_data.get('structure_type')
        start_kilometer = cleaned_data.get('start_kilometer')
        end_kilometer = cleaned_data.get('end_kilometer')
        status = cleaned_data.get('status')
        
        if project and structure_type and start_kilometer is not None and end_kilometer is not None and status is not None:
            # بررسی وجود ابنیه مشابه با همان مشخصات (به جز موقعیت کیلومتری)
            existing_structure = project_models.ProjectStructure.objects.filter(
                project=project,
                structure_type=structure_type,
                start_kilometer=start_kilometer,
                end_kilometer=end_kilometer,
                status=status
            ).exclude(pk=self.instance.pk if self.instance.pk else None)
            
            if existing_structure.exists():
                raise forms.ValidationError(
                    "ابنیه‌ای با این مشخصات قبلاً وجود دارد. لطفاً مشخصات را تغییر دهید یا موقعیت کیلومتری را تغییر دهید."
                )
        
        return cleaned_data
        
    class Meta:
        model = project_models.ProjectStructure
        fields = ['project', 'structure_type', 'kilometer_location',"start_kilometer","end_kilometer"]