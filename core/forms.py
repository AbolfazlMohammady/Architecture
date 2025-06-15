from django import forms
from django.contrib.auth.models import User, Group
from .models import User as CustomUser, Role

class UserProfileForm(forms.ModelForm):
    # فیلد فقط‌خواندنی (مثلاً national_id)
    national_id = forms.CharField(min_length=10, max_length=10, disabled=True, label="کد ملی", required=False)
    roles = forms.ModelMultipleChoiceField(
        queryset=Role.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        label="نقش‌ها",
        required=False
    )

    class Meta:
        model = CustomUser
        fields = ["first_name", "last_name", "national_id", "roles"]

    def __init__(self, *args, **kwargs):
        user_instance = kwargs.get('instance')
        super().__init__(*args, **kwargs)
        self.fields['national_id'].widget.attrs["class"] = "form-control"
        self.fields['first_name'].widget.attrs["class"] = "form-control"
        self.fields['last_name'].widget.attrs["class"] = "form-control"
        
        # اگر کاربر ادمین نیست، فقط نقش‌های خودش را می‌بیند
        if user_instance and not user_instance.is_staff:
            self.fields['roles'].queryset = user_instance.roles.all()
            self.fields['roles'].disabled = True

class AdminUserForm(forms.ModelForm):
    password1 = forms.CharField(label="رمز عبور", widget=forms.PasswordInput)
    password2 = forms.CharField(label="تکرار رمز عبور", widget=forms.PasswordInput)
    roles = forms.ModelMultipleChoiceField(
        queryset=Role.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        label="نقش‌ها",
        required=False
    )
    accessible_projects = forms.ModelMultipleChoiceField(
        queryset=None,
        widget=forms.CheckboxSelectMultiple,
        label="پروژه‌های قابل دسترسی",
        required=False
    )

    class Meta:
        model = CustomUser
        fields = ["username", "first_name", "last_name", "national_id", "is_active", "is_staff", "roles", "accessible_projects"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs["class"] = "form-control"
        # مقداردهی queryset پروژه‌ها
        from project.models import Project
        self.fields['accessible_projects'].queryset = Project.objects.all()

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("رمزهای عبور مطابقت ندارند")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
            self.save_m2m()
            # ذخیره پروژه‌های قابل دسترسی
            if 'accessible_projects' in self.cleaned_data:
                user.accessible_projects.set(self.cleaned_data['accessible_projects'])
        return user
