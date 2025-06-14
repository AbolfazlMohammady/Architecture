from django import forms
from . import models
from django_select2.forms import Select2Widget, Select2MultipleWidget
from django_jalali.forms import jDateField
from project.models import Project, ProjectLayer
from jalali_date.fields import JalaliDateField
from jalali_date.widgets import AdminJalaliDateWidget

class ExperimentRequestForm(forms.ModelForm):
    request_date = JalaliDateField(
        widget=AdminJalaliDateWidget,
        label='تاریخ درخواست',
        required=True
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # تنظیم کلاس‌های فرم
        for field in self.fields:
            if isinstance(self.fields[field].widget, (forms.TextInput, forms.NumberInput, forms.Textarea)):
                self.fields[field].widget.attrs['class'] = 'form-control form-control-sm'
            elif isinstance(self.fields[field].widget, forms.Select):
                self.fields[field].widget.attrs['class'] = 'form-select'
        
        # تنظیم ویجت‌های Select2 و queryset‌ها
        self.fields['project'].widget = Select2Widget()
        self.fields['project'].queryset = Project.objects.all()
        
        self.fields['layer'].widget = Select2Widget()
        if self.instance.pk and self.instance.project:
            self.fields['layer'].queryset = self.instance.project.projectlayer_set.all()
        else:
            self.fields['layer'].queryset = ProjectLayer.objects.none()
        
        self.fields['experiment_type'].widget = Select2Widget()
        self.fields['experiment_type'].queryset = models.ExperimentType.objects.all()
        
        self.fields['experiment_subtype'].widget = Select2Widget()
        if self.instance.pk and self.instance.experiment_type:
            self.fields['experiment_subtype'].queryset = self.instance.experiment_type.experimentsubtype_set.all()
        else:
            self.fields['experiment_subtype'].queryset = models.ExperimentSubType.objects.none()
        
        self.fields['concrete_place'].widget = Select2Widget()
        self.fields['concrete_place'].queryset = models.ConcretePlace.objects.all()
        
        # فیلتر کردن لایه‌ها بر اساس پروژه انتخاب شده
        if 'project' in self.data:
            try:
                project_id = int(self.data.get('project'))
                self.fields['layer'].queryset = ProjectLayer.objects.filter(project_id=project_id)
            except (ValueError, TypeError):
                pass
        
        # فیلتر کردن زیرنوع‌ها بر اساس نوع آزمایش انتخاب شده
        if 'experiment_type' in self.data:
            try:
                experiment_type_id = int(self.data.get('experiment_type'))
                self.fields['experiment_subtype'].queryset = models.ExperimentSubType.objects.filter(experiment_type_id=experiment_type_id)
            except (ValueError, TypeError):
                pass
    
    class Meta:
        model = models.ExperimentRequest
        fields = [
            'project', 'layer', 'experiment_type', 'experiment_subtype',
            'concrete_place', 'request_date', 'start_kilometer', 'end_kilometer',
            'description', 'target_density', 'target_strength', 'request_file'
        ]
        widgets = {
            'request_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class ExperimentResponseForm(forms.ModelForm):
    response_date = JalaliDateField(
        widget=AdminJalaliDateWidget,
        label='تاریخ پاسخ',
        required=True
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # تنظیم کلاس‌های فرم
        for field in self.fields:
            if isinstance(self.fields[field].widget, (forms.TextInput, forms.NumberInput, forms.Textarea)):
                self.fields[field].widget.attrs['class'] = 'form-control form-control-sm'
            elif isinstance(self.fields[field].widget, forms.Select):
                self.fields[field].widget.attrs['class'] = 'form-select'
        
        # تنظیم ویجت Select2 برای درخواست آزمایش
        self.fields['experiment_request'].widget = Select2Widget()
    
    class Meta:
        model = models.ExperimentResponse
        fields = [
            'experiment_request', 'response_date', 'description',
            'density_result', 'thickness_result',
            'strength_result1', 'strength_result2', 'strength_result3',
            'response_file'
        ]
        widgets = {
            'response_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class ExperimentApprovalForm(forms.ModelForm):
    approval_date = JalaliDateField(
        widget=AdminJalaliDateWidget,
        label='تاریخ تایید',
        required=True
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # تنظیم کلاس‌های فرم
        for field in self.fields:
            if isinstance(self.fields[field].widget, (forms.TextInput, forms.NumberInput, forms.Textarea)):
                self.fields[field].widget.attrs['class'] = 'form-control form-control-sm'
            elif isinstance(self.fields[field].widget, forms.Select):
                self.fields[field].widget.attrs['class'] = 'form-select'
    
    class Meta:
        model = models.ExperimentApproval
        fields = ['experiment_response', 'status', 'approval_date', 'description']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['experiment_response'].widget = forms.HiddenInput()
        self.fields['status'].widget.attrs.update({'class': 'form-select'})
        self.fields['description'].widget.attrs.update({'class': 'form-control'})

class ExperimentTypeForm(forms.ModelForm):
    class Meta:
        model = models.ExperimentType
        fields = ['name']

class ExperimentSubTypeForm(forms.ModelForm):
    class Meta:
        model = models.ExperimentSubType
        fields = ['name', 'experiment_type']

class ConcretePlaceForm(forms.ModelForm):
    class Meta:
        model = models.ConcretePlace
        fields = ['name'] 