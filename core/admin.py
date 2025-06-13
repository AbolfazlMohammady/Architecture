from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from utils import baseAdminModel
from . import models
# Register your models here.


class MyModelAdminMixin(BaseUserAdmin,baseAdminModel.BtnDeleteSelected):
    pass



@admin.register(models.User)
class UserAdmin(MyModelAdminMixin):
    list_display = ("username", "first_name", "last_name", "national_id", "is_staff")
    list_filter = ("is_staff", "is_active","national_id")
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("اطلاعات شخصی", {"fields": ("first_name", "last_name", "national_id")}),
        ("دسترسی ها", {"fields": ("is_active", "is_staff",
                                    "is_superuser", "groups")})
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide"),
            "fields": ("username", "first_name", "last_name", "national_id", "password1", "password2")
        }),
    )
    search_fields = ("username", "national_id", "first_name", "last_name")
    ordering = ("username",)
    
    
    

