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
    mix_design = forms.CharField(
        label='طرح اختلاط',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
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
        self.fields['project'].queryset = Project.objects.all()
        
        self.fields['layer'].widget = Select2Widget()
        if self.instance.pk and self.instance.project:
            self.fields['layer'].queryset = self.instance.project.projectlayer_set.all()
        else:
            self.fields['layer'].queryset = ProjectLayer.objects.none()
        
        self.fields['experiment_type'].widget = Select2MultipleWidget()
        self.fields['experiment_type'].queryset = models.ExperimentType.objects.all()
        self.fields['experiment_subtype'].widget = Select2MultipleWidget()
        self.fields['experiment_subtype'].queryset = models.ExperimentSubType.objects.all()
        
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
    
    def clean(self):
        cleaned_data = super().clean()
        experiment_types = cleaned_data.get('experiment_type')
        # اگر هیچ نوع آزمایشی انتخاب نشده باشد، اعتبارسنجی انجام نمی‌شود
        if not experiment_types:
            return cleaned_data
        # نام انواع آزمایش انتخاب شده را به صورت لیست رشته بگیر
        type_names = [et.name for et in experiment_types]
        # اگر مقاومت فشاری بتن و ملات انتخاب شده باشد، محل بتن‌ریزی اجباری شود
        if any('مقاومت فشاری بتن' in name for name in type_names):
            if not cleaned_data.get('concrete_place'):
                self.add_error('concrete_place', 'انتخاب محل بتن‌ریزی الزامی است.')
        # اگر آسفالت انتخاب شده باشد، طرح اختلاط اجباری شود
        if any('آسفالت' in name for name in type_names):
            if not cleaned_data.get('mix_design'):
                self.add_error('mix_design', 'وارد کردن طرح اختلاط الزامی است.')
        # اگر خاکریزی انتخاب شده باشد، حد تراکم اجباری شود
        if any('خاکریزی' in name for name in type_names):
            if not cleaned_data.get('target_density'):
                self.add_error('target_density', 'وارد کردن حد تراکم الزامی است.')
        # اگر ملات بنایی انتخاب شده باشد، حد مقاومت فشاری اجباری شود
        if any('ملات بنایی' in name for name in type_names):
            if not cleaned_data.get('target_strength'):
                self.add_error('target_strength', 'وارد کردن حد مقاومت فشاری الزامی است.')
        return cleaned_data
    
    class Meta:
        model = models.ExperimentRequest
        fields = [
            'project', 'layer', 'experiment_type', 'experiment_subtype',
            'concrete_place', 'request_date', 'start_kilometer', 'end_kilometer',
            'description', 'target_density', 'target_strength', 'request_file',
            'mix_design',
        ]
        widgets = {
            'request_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
            'experiment_type': Select2MultipleWidget(),
            'experiment_subtype': Select2MultipleWidget(),
            'mix_design': forms.TextInput(attrs={'class': 'form-control'}),
        }

class ExperimentRequestApprovalForm(forms.ModelForm):
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
        self.fields['experiment_request'].widget = forms.HiddenInput()
        self.fields['status'].widget.attrs.update({'class': 'form-select'})
        self.fields['description'].widget.attrs.update({'class': 'form-control', 'rows': 3})
    
    class Meta:
        model = models.ExperimentRequestApproval
        fields = ['experiment_request', 'status', 'approval_date', 'description']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
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

class PaymentCoefficientForm(forms.ModelForm):
    calculation_date = JalaliDateField(
        widget=AdminJalaliDateWidget,
        label='تاریخ محاسبه',
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
        
        # تنظیم محدودیت ضریب پرداخت
        self.fields['coefficient'].widget.attrs.update({
            'min': '0',
            'max': '1.2',
            'step': '0.01'
        })
    
    class Meta:
        model = models.PaymentCoefficient
        fields = ['project', 'layer', 'coefficient', 'start_kilometer', 'end_kilometer', 'calculation_date']
        widgets = {
            'project': Select2Widget(attrs={'class': 'form-select'}),
            'layer': forms.Select(attrs={'class': 'form-select'}),
            'coefficient': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'start_kilometer': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'end_kilometer': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
        }
    
    def clean_coefficient(self):
        coefficient = self.cleaned_data.get('coefficient')
        if coefficient is not None:
            if coefficient < 0 or coefficient > 1.2:
                raise forms.ValidationError('ضریب پرداخت باید بین 0 تا 1.2 باشد.')
        return coefficient

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