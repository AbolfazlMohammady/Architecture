from . import models
from django.views import generic
from django.contrib.auth.views import LoginView as Login
from django.contrib.auth.views import LogoutView as logout
from . import forms
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from project import models as project_models
from django.shortcuts import redirect
from django.contrib import messages
from django.utils.decorators import method_decorator
from .permissions import role_required
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
        
    
class ProfileView(LoginRequiredMixin, generic.UpdateView):
    template_name = "core/profile.html"
    model = models.User
    form_class = forms.UserProfileForm
    success_url = reverse_lazy("profile")
    
    def get_object(self, queryset=None):
        return self.request.user
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "اطلاعات پروفایل با موفقیت به‌روزرسانی شد.")
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        from project.models import Project
        # جمع‌آوری پروژه‌های مرتبط با کاربر
        projects = set()
        project_roles = {}
        # مدیر پروژه
        for p in user.managed_projects.all():
            projects.add(p)
            project_roles.setdefault(p.id, []).append('مدیر پروژه')
        # مدیر فنی
        for p in user.technical_projects.all():
            projects.add(p)
            project_roles.setdefault(p.id, []).append('مدیر فنی')
        # مدیر کنترل کیفیت
        for p in user.qc_projects.all():
            projects.add(p)
            project_roles.setdefault(p.id, []).append('مدیر کنترل کیفیت')
        # کارشناس پروژه
        for p in user.project_experts.all():
            projects.add(p)
            project_roles.setdefault(p.id, []).append('کارشناس پروژه')
        # پروژه‌های قابل دسترسی دستی
        for p in user.accessible_projects.all():
            projects.add(p)
            project_roles.setdefault(p.id, []).append('دسترسی دستی')
        # ساخت لیست پروژه‌ها با نقش‌ها
        all_user_projects = []
        for p in projects:
            all_user_projects.append({
                'project': p,
                'roles': project_roles.get(p.id, [])
            })
        context['all_user_projects'] = all_user_projects
        context['accessible_projects'] = user.accessible_projects.all()
        return context

@method_decorator(role_required(['ادمین']), name='dispatch')
class AdminUserListView(LoginRequiredMixin, UserPassesTestMixin, generic.ListView):
    model = models.User
    template_name = "core/admin/user_list.html"
    context_object_name = "users"
    
    def test_func(self):
        return self.request.user.is_staff
    
    def get_queryset(self):
        return super().get_queryset().select_related().prefetch_related('roles')

@method_decorator(role_required(['ادمین']), name='dispatch')
class AdminUserCreateView(LoginRequiredMixin, UserPassesTestMixin, generic.CreateView):
    model = models.User
    form_class = forms.AdminUserForm
    template_name = "core/admin/user_form.html"
    success_url = reverse_lazy("admin-user-list")
    
    def test_func(self):
        return self.request.user.is_staff
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "کاربر جدید با موفقیت ایجاد شد.")
        return response

@method_decorator(role_required(['ادمین']), name='dispatch')
class AdminUserUpdateView(LoginRequiredMixin, UserPassesTestMixin, generic.UpdateView):
    model = models.User
    form_class = forms.AdminUserForm
    template_name = "core/admin/user_form.html"
    success_url = reverse_lazy("admin-user-list")
    
    def test_func(self):
        return self.request.user.is_staff
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.pop('password1', None)
        kwargs.pop('password2', None)
        return kwargs
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "اطلاعات کاربر با موفقیت به‌روزرسانی شد.")
        return response

@method_decorator(role_required(['ادمین']), name='dispatch')
class AdminUserDeleteView(LoginRequiredMixin, UserPassesTestMixin, generic.DeleteView):
    model = models.User
    template_name = "core/admin/user_confirm_delete.html"
    success_url = reverse_lazy("admin-user-list")
    
    def test_func(self):
        return self.request.user.is_staff
    
    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(request, "کاربر با موفقیت حذف شد.")
        return response

