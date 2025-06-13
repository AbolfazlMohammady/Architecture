from django.urls import path
from . import views

urlpatterns = [
    path('<int:pk>/', views.ProjectDetailView.as_view(),name="project-detail"),
    path('projects/', views.ProjectListView.as_view(), name="project-list"),
    path('create-project/', views.CreateProjectView.as_view(), name="create-project"),
    path("create-project-layer/<int:pk>/", views.CreateProjectLayerView.as_view(), name="create-project-layer"),
    path("project-layer/<int:pk>/", views.ProjectLayerDetailView.as_view(), name="project-layer-detail"),
    path("project-layer-list/<int:pk>/", views.ProjectLayerListView.as_view(), name="project-layer-list"),
    path("create-project-structure/<int:pk>/", views.CreateProjectStructureView.as_view(), name="create-project-structure"),
    path("project-update/<int:pk>/", views.ProjectUpdateView.as_view(), name="project-update"),
    path("dashboard/<int:pk>/",views.ProjectDashboardView.as_view(),name="dashboard"),
    path("project-layer-update/<int:pk>/",views.ProjectLayerUpdateView.as_view(),name="project-layer-update"),
    path("project-layer-delete/<int:pk>/",views.projectLayerDeleteView.as_view(),name="project-layer-delete"),
    
    path("project-structure-update/<int:pk>/",views.ProjectStructureUpdateView.as_view(),name="project-structure-update"),
    path("project-structure-delete/<int:pk>/",views.ProjectStructureDeleteView.as_view(),name="project-structure-delete"),
    path("project-structure-list/<int:pk>/", views.ProjectStructureListView.as_view(), name="project-structure-list"),
    path("project-structure/<int:pk>/", views.ProjectStructureDetailView.as_view(), name="project-structure-detail"),
    
    
]