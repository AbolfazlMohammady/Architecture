# A:\Develop\project\Online_monitoring_of_quality_control\experiment\urls.py

from django.urls import path
from . import views

app_name = 'experiment'

urlpatterns = [
    # درخواست‌های آزمایش
    path('requests/', views.experiment_request_list, name='experiment_request_list'),
    path('requests/create/', views.experiment_request_create, name='experiment_request_create'),
    path('requests/<int:pk>/edit/', views.experiment_request_edit, name='experiment_request_edit'),
    path('requests/<int:pk>/', views.experiment_request_detail, name='experiment_request_detail'),
    path('requests/<int:pk>/update/', views.experiment_request_update, name='experiment_request_update'),
    path('requests/<int:pk>/delete/', views.experiment_request_delete, name='experiment_request_delete'),
    
    # پاسخ‌های آزمایش
    path('responses/', views.experiment_response_list, name='experiment_response_list'),
    path('responses/create/<int:pk>/', views.experiment_response_create, name='experiment_response_create'),
    path('responses/<int:pk>/', views.experiment_response_detail, name='experiment_response_detail'),
    path('responses/<int:pk>/update/', views.experiment_response_update, name='experiment_response_update'),
    path('responses/<int:pk>/delete/', views.experiment_response_delete, name='experiment_response_delete'),
    
    # انواع آزمایش
    path('types/', views.experiment_type_list, name='experiment_type_list'),
    path('types/create/', views.experiment_type_create, name='experiment_type_create'),
    path('types/<int:pk>/update/', views.experiment_type_update, name='experiment_type_update'),
    path('types/<int:pk>/delete/', views.experiment_type_delete, name='experiment_type_delete'),
    
    # زیرگروه‌های آزمایش
    path('subtypes/', views.experiment_subtype_list, name='experiment_subtype_list'),
    path('subtypes/create/', views.experiment_subtype_create, name='experiment_subtype_create'),
    path('subtypes/<int:pk>/update/', views.experiment_subtype_update, name='experiment_subtype_update'),
    path('subtypes/<int:pk>/delete/', views.experiment_subtype_delete, name='experiment_subtype_delete'),
    
    # محل‌های بتن‌ریزی
    path('places/', views.concrete_place_list, name='concrete_place_list'),
    path('places/create/', views.concrete_place_create, name='concrete_place_create'),
    path('places/<int:pk>/update/', views.concrete_place_update, name='concrete_place_update'),
    path('places/<int:pk>/delete/', views.concrete_place_delete, name='concrete_place_delete'),
    
    # API endpoints for dynamic loading
    path('ajax/get-layers/', views.get_layers, name='get_layers'),
    path('ajax/get-subtypes/', views.get_subtypes, name='get_subtypes'),
    path('ajax/get-types/', views.get_experiment_types, name='get_types'),
    path('ajax/get-places/', views.get_concrete_places, name='get_places'),
    path('asphalt-test/create/<int:response_id>/', views.asphalt_test_create, name='asphalt_test_create'),
    path('experiment-approval/create/<int:response_id>/', views.experiment_approval_create, name='experiment_approval_create'),
    path('notifications/', views.notification_list, name='notification_list'),
    path('notifications/<int:notification_id>/mark-read/', views.notification_mark_read, name='notification_mark_read'),
]