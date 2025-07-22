from django.contrib import admin
from .models import ExperimentType, ExperimentSubType, ConcretePlace, ExperimentRequest, ExperimentRequestApproval, ExperimentResponse, ExperimentApproval, PaymentCoefficient, ExperimentRequestKilometer, ExperimentRequestFile
from utils import baseAdminModel

class MyModelAdminMixin(admin.ModelAdmin, baseAdminModel.BtnDeleteSelected):
    pass

class ExperimentRequestKilometerInline(admin.TabularInline):
    model = ExperimentRequestKilometer
    extra = 1

class ExperimentRequestFileInline(admin.TabularInline):
    model = ExperimentRequestFile
    extra = 1

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
    inlines = [ExperimentRequestKilometerInline, ExperimentRequestFileInline]
    list_display = ('project', 'layer', 'get_experiment_types', 'get_experiment_subtypes', 'status', 'request_date', 'created_at')
    list_filter = ('status', 'experiment_type', 'project')
    search_fields = ('project__name', 'layer__layer_type__name', 'experiment_type__name', 'experiment_subtype__name')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'order')

    def get_experiment_types(self, obj):
        return ", ".join([et.name for et in obj.experiment_type.all()])
    get_experiment_types.short_description = 'انواع آزمایش'

    def get_experiment_subtypes(self, obj):
        return ", ".join([st.name for st in obj.experiment_subtype.all()])
    get_experiment_subtypes.short_description = 'زیرنوع‌های آزمایش'

@admin.register(ExperimentRequestApproval)
class ExperimentRequestApprovalAdmin(MyModelAdminMixin):
    list_display = ('experiment_request', 'approver', 'status', 'created_at')
    list_filter = ('status', 'approver')
    search_fields = ('experiment_request__project__name', 'description')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)

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

@admin.register(PaymentCoefficient)
class PaymentCoefficientAdmin(MyModelAdminMixin):
    list_display = ('project', 'layer', 'coefficient', 'start_kilometer', 'end_kilometer', 'calculation_date')
    list_filter = ('layer', 'project', 'calculation_date')
    search_fields = ('project__name',)
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('project')

admin.site.register(ExperimentRequestKilometer)
admin.site.register(ExperimentRequestFile)
