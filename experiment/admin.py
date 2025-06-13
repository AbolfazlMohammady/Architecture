from django.contrib import admin
from .models import ExperimentType, ExperimentSubType, ConcretePlace, ExperimentRequest, ExperimentResponse, ExperimentApproval
from utils import baseAdminModel

class MyModelAdminMixin(admin.ModelAdmin, baseAdminModel.BtnDeleteSelected):
    pass

@admin.register(ExperimentType)
class ExperimentTypeAdmin(MyModelAdminMixin):
    list_display = ('name',)
    search_fields = ('name',)
    ordering = ('name',)

@admin.register(ExperimentSubType)
class ExperimentSubTypeAdmin(MyModelAdminMixin):
    list_display = ('name', 'experiment_type')
    list_filter = ('experiment_type',)
    search_fields = ('name', 'experiment_type__name')
    ordering = ('experiment_type', 'name')

@admin.register(ConcretePlace)
class ConcretePlaceAdmin(MyModelAdminMixin):
    list_display = ('name',)
    search_fields = ('name',)
    ordering = ('name',)

@admin.register(ExperimentRequest)
class ExperimentRequestAdmin(MyModelAdminMixin):
    list_display = ('project', 'layer', 'experiment_type', 'experiment_subtype', 'status', 'request_date', 'created_at')
    list_filter = ('status', 'experiment_type', 'project')
    search_fields = ('project__name', 'layer__layer_type__name', 'experiment_type__name', 'experiment_subtype__name')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'order')

@admin.register(ExperimentResponse)
class ExperimentResponseAdmin(MyModelAdminMixin):
    list_display = ('experiment_request', 'response_date', 'created_at')
    list_filter = ('response_date',)
    search_fields = ('experiment_request__project__name', 'description')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)

@admin.register(ExperimentApproval)
class ExperimentApprovalAdmin(MyModelAdminMixin):
    list_display = ('experiment_response', 'approver', 'status', 'created_at')
    list_filter = ('status', 'approver')
    search_fields = ('experiment_response__experiment_request__project__name', 'description')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)
