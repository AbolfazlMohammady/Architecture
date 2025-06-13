from django.contrib import admin
from .models import Project, ProjectEx, LayerType, ProjectLayer, StructureType, ProjectStructure
from utils import baseAdminModel

class MyModelAdminMixin(admin.ModelAdmin,baseAdminModel.BtnDeleteSelected):
    pass


# کلاس ادمین برای مدل Project
@admin.register(Project)
class ProjectAdmin(MyModelAdminMixin):
    list_display = ('name', 'start_date', 'end_date', 'budget', 'project_manager', 'technical_manager', 'quality_control_manager')
    search_fields = ('name', 'project_manager__username', 'technical_manager__username', 'quality_control_manager__username')
    list_filter = ('start_date', 'end_date', 'project_manager', 'technical_manager', 'quality_control_manager','project_experts')
    autocomplete_fields = ['project_experts']
    ordering = ('start_date',)

# کلاس ادمین برای مدل ProjectEx
@admin.register(ProjectEx)
class ProjectExAdmin(MyModelAdminMixin):
    list_display = ('user', 'project', 'date_joined', 'date_left')
    search_fields = ('user__username', 'project__name')
    list_filter = ('date_joined', 'date_left')
    ordering = ('date_joined',)

# کلاس ادمین برای مدل LayerType
@admin.register(LayerType)
class LayerTypeAdmin(MyModelAdminMixin):
    list_display = ('name',)
    search_fields = ('name',)

# کلاس ادمین برای مدل ProjectLayer
@admin.register(ProjectLayer)
class ProjectLayerAdmin(MyModelAdminMixin):
    list_display = ('project', 'layer_type', 'thickness_cm', 'order_from_top')
    search_fields = ('project__name', 'layer_type__name')
    list_filter = ('project', 'layer_type')
    ordering = ('order_from_top',)

# کلاس ادمین برای مدل StructureType
@admin.register(StructureType)
class StructureTypeAdmin(MyModelAdminMixin):
    list_display = ('name',)
    search_fields = ('name',)

# کلاس ادمین برای مدل ProjectStructure
@admin.register(ProjectStructure)
class ProjectStructureAdmin(MyModelAdminMixin):
    list_display = ('project', 'structure_type', 'kilometer_location')
    search_fields = ('project__name', 'structure_type__name')
    list_filter = ('project', 'structure_type')
    ordering = ('kilometer_location',)

