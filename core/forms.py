from django import forms
from django.contrib.auth.models import User, Group

class UserProfileForm(forms.ModelForm):
    # فیلد فقط‌خواندنی (مثلاً national_id)
    national_id = forms.CharField(min_length=10,max_length=10,disabled=True,label="کد ملی",required=False)  # فقط نمایشی

    class Meta:
        model = User
        fields = ["first_name", "last_name", "national_id", "groups"]

    def __init__(self, *args, **kwargs):
        user_instance = kwargs.get('instance')
        super().__init__(*args, **kwargs)
        self.fields['national_id'].widget.attrs["class"] = "form-control"
        self.fields['first_name'].widget.attrs["class"] = "form-control"
        self.fields['last_name'].widget.attrs["class"] = "form-control"
        self.fields['groups'].widget.attrs["class"] = "form-control"
        self.fields['groups'].label = "سمت ها"
        # فقط گروه‌هایی که کاربر عضو آن‌هاست را نمایش بده
        if user_instance:
            self.fields['groups'].queryset = user_instance.groups.all()

        self.fields['groups'].disabled = True
