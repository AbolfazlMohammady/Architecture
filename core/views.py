from . import models
from django.views import generic
from django.contrib.auth.views import LoginView as Login
from django.contrib.auth.views import LogoutView as logout
from . import forms
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from project import models as project_models
# Create your views here.

class LoginView(Login):
    redirect_authenticated_user = True
    template_name = "core/login.html"

class LogoutView(logout):
    template_name = "core/logout.html"
    

class HomeView(LoginRequiredMixin,generic.ListView):
    template_name = "core/home.html"
    model = project_models.Project
    
    
    
    def get_queryset(self):
        return super().get_queryset().order_by("-updated_at")[:5]
        
    
class ProfileView(LoginRequiredMixin,generic.UpdateView):
    http_method_names = ["get"]
    template_name = "core/profile.html"
    model = models.User
    form_class = forms.UserProfileForm
    success_url = reverse_lazy("profile")
    # fields = ["first_name", "last_name", "national_id", "groups"]
    
    def get_object(self, queryset = None):
        return self.request.user
    
    def form_valid(self, form):
        # داده‌های جدید را ذخیره می‌کنیم
        response = super().form_valid(form)
        
        return response

