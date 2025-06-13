# A:\Develop\project\Online_monitoring_of_quality_control\experiment\urls.py

from django.urls import path
from . import views

app_name = 'experiment'

urlpatterns = [
    # List view (already correct from previous fix)
    path('requests/', views.experiment_request_list, name='experiment_request_list'),
    
    # CREATE view: Changed name to use underscores for consistency
    path('requests/create/', views.experiment_request_create, name='experiment_request_create'), 
    
    # DETAIL view: Changed name to use underscores for consistency
    path('requests/<int:pk>/', views.experiment_request_detail, name='experiment_request_detail'),
    
    # RESPONSE CREATE view: Changed name to use underscores for consistency
    path('responses/create/<int:pk>/', views.experiment_response_create, name='experiment_response_create'),
    
    # APPROVAL CREATE view: Changed name to use underscores for consistency
    path('approvals/create/<int:pk>/', views.experiment_approval_create, name='experiment_approval_create'),
    
    # API endpoints often use underscores, which is fine if you're consistent internally for APIs.
    # Leaving these as underscores for now, assuming they are internal API names.
    path('api/layers/', views.get_layers, name='get_layers'),
    path('api/subtypes/', views.get_subtypes, name='get_subtypes'),
]