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
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # تنظیم کلاس‌های فرم
        for field in self.fields:
            if isinstance(self.fields[field].widget, (forms.TextInput, forms.NumberInput, forms.Textarea)):
                self.fields[field].widget.attrs['class'] = 'form-control form-control-sm'
            elif isinstance(self.fields[field].widget, forms.Select):
                self.fields[field].widget.attrs['class'] = 'form-select'
        
        # تنظیم ویجت‌های Select2 و queryset‌ها
        self.fields['project'].widget = Select2Widget()
        if user is not None:
            self.fields['project'].queryset = Project.objects.filter(users_with_access=user)
        else:
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
    
    class Meta:
        model = models.ExperimentResponse
        fields = ['response_date', 'response_file', 'density_result', 'thickness_result', 
                 'strength_result1', 'strength_result2', 'strength_result3', 'description']
        widgets = {
            'response_file': forms.FileInput(attrs={'class': 'form-control'}),
            'density_result': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'thickness_result': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'strength_result1': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'strength_result2': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'strength_result3': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
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
        
        # تنظیم فیلدهای خاص
        self.fields['experiment_response'].widget = forms.HiddenInput()
        self.fields['status'].widget.attrs.update({'class': 'form-select'})
        self.fields['description'].widget.attrs.update({'class': 'form-control', 'rows': 3})
        self.fields['penalty_percentage'].widget.attrs.update({'class': 'form-control'})
    
    class Meta:
        model = models.ExperimentApproval
        fields = ['experiment_response', 'status', 'approval_date', 'penalty_percentage', 'description']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'penalty_percentage': forms.NumberInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

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

class AsphaltTestForm(forms.ModelForm):
    class Meta:
        model = models.AsphaltTest
        fields = [
            'layer_type', 'density', 'air_void', 'vma', 'vfa',
            'stability', 'flow'
        ]
        widgets = {
            'layer_type': forms.Select(attrs={'class': 'form-select'}),
            'density': forms.NumberInput(attrs={'class': 'form-control'}),
            'air_void': forms.NumberInput(attrs={'class': 'form-control'}),
            'vma': forms.NumberInput(attrs={'class': 'form-control'}),
            'vfa': forms.NumberInput(attrs={'class': 'form-control'}),
            'stability': forms.NumberInput(attrs={'class': 'form-control'}),
            'flow': forms.NumberInput(attrs={'class': 'form-control'}),
        } 