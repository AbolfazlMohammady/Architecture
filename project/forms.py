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
    
    is_parent_only = forms.BooleanField(
        required=False,
        label='پروژه اصلی',
        help_text='اگر این پروژه فقط یک پروژه اصلی است (بدون اطلاعات فنی)، این گزینه را فعال کنید',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    def __init__(self, *args, **kwargs):
        super(ProjectForm, self).__init__(*args, **kwargs)
        
        self.fields['name'].widget.attrs["class"] = "form-control form-control-sm"
        
        # تنظیم مقدار اولیه برای is_parent_only
        if self.instance and self.instance.pk:
            self.fields['is_parent_only'].initial = self.instance.is_parent_only
        
        # اگر is_parent_only فعال است، فیلدهای فنی را اختیاری می‌کنیم
        # بررسی می‌کنیم که آیا در داده‌های POST یا initial، is_parent_only فعال است
        is_parent_only = False
        if self.data and 'is_parent_only' in self.data:
            # بررسی checkbox - اگر 'on' باشد یعنی فعال است
            checkbox_value = self.data.get('is_parent_only')
            is_parent_only = checkbox_value == 'on' or checkbox_value == 'True' or checkbox_value == 'true'
            print(f"[FORM DEBUG] is_parent_only from POST: {checkbox_value} -> {is_parent_only}")
        elif self.instance and self.instance.pk:
            is_parent_only = getattr(self.instance, 'is_parent_only', False)
            print(f"[FORM DEBUG] is_parent_only from instance: {is_parent_only}")
        
        if is_parent_only:
            print(f"[FORM DEBUG] Setting technical fields as optional")
            # فیلدهای فنی را اختیاری می‌کنیم
            if 'start_date' in self.fields:
                self.fields['start_date'].required = False
            if 'masafat' in self.fields:
                self.fields['masafat'].required = False
            if 'width' in self.fields:
                self.fields['width'].required = False
            if 'start_kilometer' in self.fields:
                self.fields['start_kilometer'].required = False
            if 'end_kilometer' in self.fields:
                self.fields['end_kilometer'].required = False
            if 'profile_file' in self.fields:
                self.fields['profile_file'].required = False
        
        # فیلد پروژه اصلی - فقط پروژه‌های اصلی (بدون parent) را نشان می‌دهد
        # تنظیم queryset برای parent_project
        
        # ابتدا همه پروژه‌ها را بگیریم
        parent_queryset = project_models.Project.objects.all()
        print(f"[PARENT_PROJECT DEBUG] Total projects: {parent_queryset.count()}")
        print(f"[PARENT_PROJECT DEBUG] Project names: {list(parent_queryset.values_list('name', flat=True))}")
        
        # اگر در حال ویرایش هستیم، نباید خود پروژه را در لیست parent_project نشان دهیم
        if self.instance and self.instance.pk:
            parent_queryset = parent_queryset.exclude(pk=self.instance.pk)
            print(f"[PARENT_PROJECT DEBUG] After excluding self (pk={self.instance.pk}): {parent_queryset.count()}")
        
        # فیلتر کردن فقط پروژه‌های اصلی (پروژه‌هایی که parent_project ندارند یا None است)
        # ابتدا بررسی می‌کنیم که آیا فیلد parent_project وجود دارد
        try:
            # تلاش برای فیلتر کردن پروژه‌های اصلی
            main_projects = parent_queryset.filter(parent_project__isnull=True)
            print(f"[PARENT_PROJECT DEBUG] Main projects (parent_project__isnull=True): {main_projects.count()}")
            print(f"[PARENT_PROJECT DEBUG] Main project names: {list(main_projects.values_list('name', flat=True))}")
            # استفاده از main_projects - اگر همه پروژه‌ها parent_project=None داشته باشند، همه نمایش داده می‌شوند
            parent_queryset = main_projects
        except Exception as e:
            # اگر خطا داد (مثلاً فیلد وجود ندارد)، همه پروژه‌ها را نشان می‌دهیم
            print(f"[PARENT_PROJECT DEBUG] Error filtering: {str(e)}")
            print(f"[PARENT_PROJECT DEBUG] Using all projects due to error")
        
        # مرتب‌سازی بر اساس نام و force evaluate کردن queryset
        parent_queryset = parent_queryset.order_by('name')
        
        # Force evaluate کردن queryset با تبدیل به لیست (برای اطمینان از اینکه queryset evaluate شده است)
        # اما این کار را نمی‌کنیم چون باعث می‌شود queryset دیگر lazy نباشد
        # در عوض، فقط queryset را تنظیم می‌کنیم
        
        print(f"[PARENT_PROJECT DEBUG] Final queryset count: {parent_queryset.count()}")
        print(f"[PARENT_PROJECT DEBUG] Final project names: {list(parent_queryset.values_list('name', flat=True))}")
        
        # بررسی widget
        if 'parent_project' in self.fields:
            print(f"[PARENT_PROJECT DEBUG] Widget type before: {type(self.fields['parent_project'].widget)}")
        
        # تنظیم queryset برای parent_project
        self.fields["parent_project"].queryset = parent_queryset
        self.fields["parent_project"].label = "پروژه اصلی"
        self.fields["parent_project"].help_text = "اگر این پروژه زیرپروژه است، پروژه اصلی را انتخاب کنید"
        self.fields["parent_project"].required = False
        # اضافه کردن یک option خالی برای placeholder
        self.fields["parent_project"].empty_label = "انتخاب کنید..."
        
        # ایجاد widget جدید با choices از queryset
        # استفاده از forms.Select برای نمایش static queryset
        widget = forms.Select(attrs={"class": "form-select select2"})
        
        # تنظیم choices از queryset به صورت دستی
        # ابتدا empty_label را اضافه می‌کنیم
        choices = [('', 'انتخاب کنید...')]
        # سپس تمام پروژه‌ها را اضافه می‌کنیم
        for project in parent_queryset:
            choices.append((project.id, str(project)))
        
        widget.choices = choices
        self.fields["parent_project"].widget = widget
        
        print(f"[PARENT_PROJECT DEBUG] Widget type after: {type(self.fields['parent_project'].widget)}")
        print(f"[PARENT_PROJECT DEBUG] Widget attrs: {self.fields['parent_project'].widget.attrs}")
        print(f"[PARENT_PROJECT DEBUG] Field queryset count: {self.fields['parent_project'].queryset.count()}")
        print(f"[PARENT_PROJECT DEBUG] Field queryset: {list(self.fields['parent_project'].queryset.values_list('id', 'name'))}")
        
        # بررسی اینکه آیا widget options را دارد یا نه
        try:
            widget_options = list(self.fields["parent_project"].widget.choices)
            print(f"[PARENT_PROJECT DEBUG] Widget choices count: {len(widget_options)}")
            print(f"[PARENT_PROJECT DEBUG] Widget choices: {widget_options[:5]}")  # نمایش 5 مورد اول
        except Exception as e:
            print(f"[PARENT_PROJECT DEBUG] Error getting widget choices: {str(e)}")
        
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
        
        self.fields["contract_amount"].widget.attrs["class"] = "form-control form-control-sm"
        self.fields["is_parent_only"].widget.attrs["class"] = "form-check-input"
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
        parent_project = cleaned_data.get('parent_project')
        project_manager = cleaned_data.get('project_manager')
        technical_manager = cleaned_data.get('technical_manager')
        quality_control_manager = cleaned_data.get('quality_control_manager')
        contract_amount = cleaned_data.get('contract_amount')
        is_parent_only = cleaned_data.get('is_parent_only', False)
        masafat = cleaned_data.get('masafat')
        width = cleaned_data.get('width')
        start_kilometer = cleaned_data.get('start_kilometer')
        end_kilometer = cleaned_data.get('end_kilometer')
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        # اگر پروژه اصلی است (is_parent_only=True)، فیلدهای فنی اختیاری هستند
        if is_parent_only:
            # اگر پروژه اصلی است، نباید parent_project داشته باشد
            if parent_project:
                raise forms.ValidationError(
                    "پروژه اصلی نمی‌تواند زیرپروژه باشد. لطفاً فیلد 'پروژه اصلی' را غیرفعال کنید یا پروژه اصلی را حذف کنید."
                )
            # فیلدهای فنی را اختیاری می‌کنیم (نیازی به validation ندارند)
            # اگر start_date خالی است، آن را None می‌کنیم تا validation خطا ندهد
            # همچنین باید required را False کنیم
            if 'start_date' in self.fields:
                self.fields['start_date'].required = False
            if not start_date:
                cleaned_data['start_date'] = None
        else:
            # اگر پروژه اصلی نیست، فیلدهای فنی باید پر شوند (مگر اینکه زیرپروژه باشد)
            if not parent_project:
                # پروژه اصلی باید اطلاعات فنی داشته باشد
                if not masafat or not width or not start_kilometer or not end_kilometer or not start_date:
                    raise forms.ValidationError(
                        "برای پروژه‌های اصلی (غیر از پروژه‌های فقط اصلی)، اطلاعات فنی (مسافت، عرض، کیلومتر شروع و پایان، تاریخ شروع) الزامی است."
                    )
        
        # بررسی اینکه parent_project باید یک پروژه اصلی باشد (نه زیرپروژه)
        if parent_project:
            if parent_project.parent_project is not None:
                raise forms.ValidationError(
                    f"پروژه '{parent_project.name}' خود یک زیرپروژه است. فقط می‌توانید پروژه‌های اصلی را به عنوان پروژه اصلی انتخاب کنید."
                )
            # بررسی اینکه پروژه نمی‌تواند والد خودش باشد
            if self.instance.pk and parent_project.pk == self.instance.pk:
                raise forms.ValidationError(
                    "یک پروژه نمی‌تواند پروژه اصلی خودش باشد."
                )
        
        # بررسی یکتایی نام در پروژه اصلی (یا پروژه‌های اصلی)
        if name:
            existing_project = project_models.Project.objects.filter(
                name=name,
                parent_project=parent_project
            ).exclude(pk=self.instance.pk if self.instance.pk else None)
            
            if existing_project.exists():
                if parent_project:
                    raise forms.ValidationError(
                        f"زیرپروژه‌ای با نام '{name}' در پروژه اصلی '{parent_project.name}' قبلاً وجود دارد."
                    )
                else:
                    raise forms.ValidationError(
                        f"پروژه اصلی‌ای با نام '{name}' قبلاً وجود دارد."
                    )
        
        # بررسی وجود پروژه مشابه فقط برای پروژه‌هایی که اطلاعات فنی دارند
        if not is_parent_only and name and project_manager and technical_manager and quality_control_manager and contract_amount and masafat and width and start_kilometer and end_kilometer and start_date:
            # بررسی وجود پروژه مشابه با همان مشخصات (اختیاری - برای جلوگیری از تکرار کامل)
            existing_project = project_models.Project.objects.filter(
                name=name,
                parent_project=parent_project,
                project_manager=project_manager,
                technical_manager=technical_manager,
                quality_control_manager=quality_control_manager,
                contract_amount=contract_amount,
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
                  'parent_project',
                  'project_manager',
                  'technical_manager',
                  'quality_control_manager',
                  "lab_manager",
                  "hsse_manager",
                  "project_experts",
                  "contract_amount",
                  "is_parent_only",
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
        self.order_auto_assigned = False
        self.order_original_value = None
        
        self.fields["thickness_cm"].widget.attrs["class"] = "form-control form-control-sm"
        self.fields["order_from_top"].widget.attrs["class"] = "form-control form-control-sm"
        
        self.fields["project"].widget = Select2Widget()
        self.fields["project"].queryset = project_models.Project.objects.all()
        self.fields["project"].widget.attrs["class"] = "form-select"
        self.fields["project"].disabled = True
        
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
            existing_orders = set(
                project_models.ProjectLayer.objects.filter(
                    project=project
                ).exclude(pk=self.instance.pk if self.instance.pk else None)
                 .values_list('order_from_top', flat=True)
            )
            if order_from_top in existing_orders:
                next_order = 1
                while next_order in existing_orders:
                    next_order += 1
                cleaned_data['order_from_top'] = next_order
                self.order_auto_assigned = True
                self.order_original_value = order_from_top
        return cleaned_data

    class Meta:
        model = project_models.ProjectLayer
        fields = ['project', 'layer_type', 'thickness_cm', 'order_from_top', 'state']
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