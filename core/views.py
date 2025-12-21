from . import models
from django.views import generic
from django.contrib.auth.views import LoginView as Login
from django.contrib.auth.views import LogoutView as logout
from . import forms
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from project import models as project_models
from django.shortcuts import redirect, render
from django.contrib import messages
from django.utils.decorators import method_decorator
from .permissions import role_required
from experiment.models import ExperimentRequest, ExperimentApproval
from project.models import ProjectLayer
from datetime import datetime, timedelta
from django.utils import timezone
from django.urls import reverse, NoReverseMatch
# Create your views here.

class LoginView(Login):
    redirect_authenticated_user = True
    template_name = "core/login.html"
    def get_success_url(self):
        return "/"

class LogoutView(logout):
    template_name = "core/logout.html"
    

class HomeView(LoginRequiredMixin,generic.ListView):
    template_name = "core/home.html"
    model = project_models.Project
    
    def get_queryset(self):
        return self.model.objects.all().order_by('-updated_at')[:5]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['latest_projects'] = self.get_queryset()
        
        # محاسبه وضعیت کلی پروژه‌ها
        total_projects = self.model.objects.count()
        active_projects = self.model.objects.filter(end_date__isnull=True).count()
        completed_projects = self.model.objects.filter(end_date__isnull=False).count()
        stopped_projects = total_projects - active_projects - completed_projects
        
        context['project_status'] = {
            'active': round((active_projects / total_projects) * 100) if total_projects > 0 else 0,
            'completed': round((completed_projects / total_projects) * 100) if total_projects > 0 else 0,
            'stopped': round((stopped_projects / total_projects) * 100) if total_projects > 0 else 0
        }
        
        # محاسبه پیشرفت پروژه‌ها
        projects = self.get_queryset()
        project_progress = []
        for project in projects:
            total_layers = project.projectlayer_set.count()
            completed_layers = project.projectlayer_set.filter(status=ProjectLayer.COMPLETED).count()
            progress = round((completed_layers / total_layers) * 100) if total_layers > 0 else 0
            project_progress.append({
                'name': project.name,
                'progress': progress
            })
        context['project_progress'] = project_progress
        
        # محاسبه کیفیت آزمایشات در 6 ماه اخیر
        six_months_ago = timezone.now() - timedelta(days=180)
        
        # محاسبه تعداد آزمایشات تایید شده برای هر ماه
        experiment_quality = []
        for i in range(6):
            month_start = timezone.now() - timedelta(days=30 * (i + 1))
            month_end = timezone.now() - timedelta(days=30 * i)
            
            # تعداد آزمایشات تایید شده در این ماه
            month_approved = ExperimentApproval.objects.filter(
                created_at__gte=month_start,
                created_at__lt=month_end,
                status=ExperimentApproval.APPROVED
            ).count()
            
            # تعداد کل آزمایشات در این ماه
            month_total = ExperimentRequest.objects.filter(
                created_at__gte=month_start,
                created_at__lt=month_end
            ).count()
            
            # محاسبه درصد قبولی
            approval_rate = round((month_approved / month_total) * 100) if month_total > 0 else 0
            
            # اضافه کردن اطلاعات به لیست
            experiment_quality.append({
                'month': month_start.strftime('%Y-%m'),
                'approved_count': month_approved,
                'total_count': month_total,
                'approval_rate': approval_rate
            })
        
        context['experiment_quality'] = experiment_quality
        
        # محاسبه وضعیت مالی (فعلاً تخمینی)
        total_budget = sum(project.contract_amount or 0 for project in self.model.objects.all())
        if total_budget > 0:
            context['financial_status'] = {
                'spent': 60,  # فعلاً تخمینی - 60% کل بودجه
                'remaining': 35,  # فعلاً تخمینی - 35% کل بودجه
                'unexpected': 5  # فعلاً تخمینی - 5% کل بودجه
            }
        else:
            context['financial_status'] = {
                'spent': 0,
                'remaining': 0,
                'unexpected': 0
            }
        
        # محاسبه میانگین وزنی ضرایب پرداخت برای هر لایه
        # فرمول: (مجموع (مبلغ قرارداد پروژه × ضریب پرداخت پروژه)) / مجموع مبلغ قراردادها
        from experiment.models import PaymentCoefficient
        from project.models import Project
        
        def get_user_accessible_projects(user):
            """دریافت لیست پروژه‌های قابل دسترسی کاربر"""
            if user.is_superuser:
                # برای superuser همه پروژه‌ها
                return Project.objects.all()
            else:
                # برای سایر کاربران، فقط پروژه‌های قابل دسترسی
                projects = set()
                projects.update(user.managed_projects.all())
                projects.update(user.technical_projects.all())
                projects.update(user.qc_projects.all())
                projects.update(user.project_experts.all())
                projects.update(user.accessible_projects.all())
                return list(projects)
        
        def calculate_weighted_average(layer_type):
            """
            محاسبه میانگین وزنی برای یک لایه
            فرمول: (مجموع (contract_amount × coefficient)) / مجموع contract_amount
            """
            # دریافت پروژه‌های قابل دسترسی کاربر
            user_projects = get_user_accessible_projects(self.request.user)
            
            # فقط پروژه‌های اصلی (بدون parent) با مبلغ قرارداد را در نظر می‌گیریم
            main_projects = [p for p in user_projects if p.parent_project is None and p.contract_amount is not None]
            
            total_weighted_sum = 0
            total_contract_amount = 0
            
            for project in main_projects:
                # دریافت آخرین ضریب پرداخت برای این پروژه و این لایه بر اساس تاریخ محاسبه
                latest_coefficient = PaymentCoefficient.objects.filter(
                    project=project,
                    layer=layer_type
                ).order_by('-calculation_date').first()
                
                if latest_coefficient and project.contract_amount:
                    contract_amount = float(project.contract_amount)
                    coefficient = float(latest_coefficient.coefficient)
                    
                    # اضافه کردن به مجموع وزنی
                    total_weighted_sum += contract_amount * coefficient
                    total_contract_amount += contract_amount
            
            # محاسبه میانگین وزنی
            if total_contract_amount > 0:
                weighted_avg = total_weighted_sum / total_contract_amount
                return round(weighted_avg, 2)
            return 0
        
        embankment_avg = calculate_weighted_average('EMBANKMENT')
        subbase_avg = calculate_weighted_average('SUBBASE')
        base_avg = calculate_weighted_average('BASE')
        asphalt_avg = calculate_weighted_average('ASPHALT')
        
        context['payment_coefficients'] = {
            'embankment': {
                'name': 'خاکریزی',
                'avg': embankment_avg,
                'remaining': round(1.2 - embankment_avg, 2) if embankment_avg > 0 else 1.2
            },
            'subbase': {
                'name': 'زیر اساس',
                'avg': subbase_avg,
                'remaining': round(1.2 - subbase_avg, 2) if subbase_avg > 0 else 1.2
            },
            'base': {
                'name': 'اساس',
                'avg': base_avg,
                'remaining': round(1.2 - base_avg, 2) if base_avg > 0 else 1.2
            },
            'asphalt': {
                'name': 'آسفالت گرم',
                'avg': asphalt_avg,
                'remaining': round(1.2 - asphalt_avg, 2) if asphalt_avg > 0 else 1.2
            }
        }

        return context

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
        context['user_info'] = {
            'full_name': user.get_full_name(),
            'first_name': user.first_name,
            'last_name': user.last_name,
            'username': user.username,
            'national_id': user.national_id,
        }
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

class DashboardView(LoginRequiredMixin, generic.TemplateView):
    template_name = "core/dashboard.html"

    # تعریف دسترسی‌ها بر اساس نقش و url nameهای درست (سراسری)
    ROLE_ACCESS = {
        'ادمین': [
            {'name': 'مدیریت کاربران', 'url_name': 'admin-user-list'},
            {'name': 'پروفایل', 'url_name': 'profile'},
            {'name': 'لیست پروژه‌ها', 'url_name': 'project-list'},
            {'name': 'ایجاد پروژه', 'url_name': 'create-project'},
            {'name': 'لیست آزمایشات', 'url_name': 'experiment:experiment_request_list'},
            {'name': 'ثبت درخواست آزمایش', 'url_name': 'experiment:experiment_request_create'},
            {'name': 'آزمایشات', 'url_name': 'experiment:experiment_type_list'},
            {'name': 'اعلان‌ها', 'url_name': 'experiment:notification_list'},
        ],
        'مدیر عامل موسسه': [
            {'name': 'پروفایل', 'url_name': 'profile'},
            {'name': 'لیست پروژه‌ها', 'url_name': 'project-list'},
            {'name': 'لیست آزمایشات', 'url_name': 'experiment:experiment_request_list'},
            {'name': 'اعلان‌ها', 'url_name': 'experiment:notification_list'},
        ],
        'مدیر فنی موسسه': [
            {'name': 'پروفایل', 'url_name': 'profile'},
            {'name': 'لیست پروژه‌ها', 'url_name': 'project-list'},
            {'name': 'لیست آزمایشات', 'url_name': 'experiment:experiment_request_list'},
        ],
        'مدیر کنترل کیفی موسسه': [
            {'name': 'پروفایل', 'url_name': 'profile'},
            {'name': 'لیست پروژه‌ها', 'url_name': 'project-list'},
            {'name': 'لیست آزمایشات', 'url_name': 'experiment:experiment_request_list'},
        ],
        'کارشناس موسسه': [
            {'name': 'پروفایل', 'url_name': 'profile'},
            {'name': 'لیست پروژه‌ها', 'url_name': 'project-list'},
        ],
        # سایر نقش‌ها را به همین صورت اضافه کن...
    }

    # دسترسی‌های هر نقش در هر پروژه (بر اساس داکیومنت)
    PROJECT_ROLE_ACCESS = {
        'مدیر پروژه': [
            {'name': 'داشبورد پروژه', 'url_name': 'dashboard'},
            {'name': 'ویرایش پروژه', 'url_name': 'project-update'},
            {'name': 'لایه‌های پروژه', 'url_name': 'project-layer-list'},
            {'name': 'ابنیه‌های پروژه', 'url_name': 'project-structure-list'},
            {'name': 'درخواست آزمایش', 'url_name': 'experiment:experiment_request_create'},
            {'name': 'لیست آزمایشات', 'url_name': 'experiment:experiment_request_list'},
        ],
        'مدیر فنی': [
            {'name': 'داشبورد پروژه', 'url_name': 'dashboard'},
            {'name': 'لایه‌های پروژه', 'url_name': 'project-layer-list'},
            {'name': 'ابنیه‌های پروژه', 'url_name': 'project-structure-list'},
            {'name': 'لیست آزمایشات', 'url_name': 'experiment:experiment_request_list'},
        ],
        'مدیر کنترل کیفیت': [
            {'name': 'داشبورد پروژه', 'url_name': 'dashboard'},
            {'name': 'لیست آزمایشات', 'url_name': 'experiment:experiment_request_list'},
        ],
        'کارشناس پروژه': [
            {'name': 'داشبورد پروژه', 'url_name': 'dashboard'},
            {'name': 'لیست آزمایشات', 'url_name': 'experiment:experiment_request_list'},
        ],
        'دسترسی دستی': [
            {'name': 'داشبورد پروژه', 'url_name': 'dashboard'},
        ],
    }

    def get_context_data(self, **kwargs):
        from project.models import Project, ProjectLayer
        from experiment.models import ExperimentRequest, Notification, ExperimentApproval
        from django.utils import timezone
        from datetime import timedelta
        context = super().get_context_data(**kwargs)
        user = self.request.user
        roles = user.roles.values_list('name', flat=True)
        context['roles'] = list(roles)
        # --- Global Access (by role) ---
        access_set = set()
        access_list = []
        from django.urls import reverse, NoReverseMatch
        for role in roles:
            for item in self.ROLE_ACCESS.get(role, []):
                key = (item['name'], item['url_name'])
                if key not in access_set:
                    try:
                        url = reverse(item['url_name'])
                    except NoReverseMatch:
                        url = "#"
                    access_list.append({'name': item['name'], 'url': url})
                    access_set.add(key)
        context['access'] = access_list
        context['user_info'] = {
            'full_name': user.get_full_name(),
            'first_name': user.first_name,
            'last_name': user.last_name,
            'username': user.username,
            'national_id': user.national_id,
        }
        # --- User Projects & Roles ---
        projects = set()
        project_roles = {}
        for p in user.managed_projects.all():
            projects.add(p)
            project_roles.setdefault(p.id, []).append('مدیر پروژه')
        for p in user.technical_projects.all():
            projects.add(p)
            project_roles.setdefault(p.id, []).append('مدیر فنی')
        for p in user.qc_projects.all():
            projects.add(p)
            project_roles.setdefault(p.id, []).append('مدیر کنترل کیفیت')
        for p in user.project_experts.all():
            projects.add(p)
            project_roles.setdefault(p.id, []).append('کارشناس پروژه')
        for p in user.accessible_projects.all():
            projects.add(p)
            project_roles.setdefault(p.id, []).append('دسترسی دستی')
        # جدا کردن پروژه‌های اصلی و زیرپروژه‌ها
        main_projects_list = []
        sub_projects_dict = {}
        
        for p in projects:
            roles_in_project = project_roles.get(p.id, [])
            accesses = []
            for role in roles_in_project:
                for item in self.PROJECT_ROLE_ACCESS.get(role, []):
                    try:
                        url = reverse(item['url_name'], kwargs={'pk': p.id})
                    except Exception:
                        try:
                            url = reverse(item['url_name'])
                        except Exception:
                            url = "#"
                    accesses.append({'name': item['name'], 'url': url})
            seen = set()
            unique_accesses = []
            for a in accesses:
                if a['name'] not in seen:
                    unique_accesses.append(a)
                    seen.add(a['name'])
            # --- Calculate project progress ---
            total_layers = ProjectLayer.objects.filter(project=p).count()
            completed_layers = ProjectLayer.objects.filter(project=p, status=ProjectLayer.COMPLETED).count()
            progress = round((completed_layers / total_layers) * 100) if total_layers > 0 else 0
            
            project_data = {
                'id': p.id,
                'name': p.name,
                'roles': roles_in_project,
                'accesses': unique_accesses,
                'status': 'active' if not p.end_date else 'completed',
                'progress': progress,
            }
            
            # اگر پروژه اصلی است
            if p.is_main_project():
                main_projects_list.append(project_data)
            else:
                # زیرپروژه است
                parent_id = p.parent_project.id
                if parent_id not in sub_projects_dict:
                    sub_projects_dict[parent_id] = []
                sub_projects_dict[parent_id].append(project_data)
        
        context['user_projects'] = main_projects_list
        context['sub_projects_dict'] = sub_projects_dict
        # --- KPI: Project Status ---
        all_projects = Project.objects.all()
        total_projects = all_projects.count()
        active_projects = all_projects.filter(end_date__isnull=True).count()
        completed_projects = all_projects.filter(end_date__isnull=False).count()
        stopped_projects = total_projects - active_projects - completed_projects
        context['project_status_kpi'] = {
            'active': round((active_projects / total_projects) * 100) if total_projects > 0 else 0,
            'completed': round((completed_projects / total_projects) * 100) if total_projects > 0 else 0,
            'stopped': round((stopped_projects / total_projects) * 100) if total_projects > 0 else 0
        }
        # --- KPI: Project Progress (average of all) ---
        all_progress = []
        for p in all_projects:
            total_layers = ProjectLayer.objects.filter(project=p).count()
            completed_layers = ProjectLayer.objects.filter(project=p, status=ProjectLayer.COMPLETED).count()
            progress = round((completed_layers / total_layers) * 100) if total_layers > 0 else 0
            all_progress.append(progress)
        context['project_progress_kpi'] = round(sum(all_progress) / len(all_progress)) if all_progress else 0
        # Add remaining for chart
        context['project_progress_kpi_remaining'] = 100 - context['project_progress_kpi']
        # --- KPI: Financial (dummy, can be replaced with real) ---
        total_budget = sum([p.contract_amount or 0 for p in all_projects])
        context['financial_kpi'] = {
            'spent': 60 if total_budget else 0,
            'remaining': 35 if total_budget else 0,
            'unexpected': 5 if total_budget else 0
        }
        # --- KPI: Experiment Quality (last 6 months) ---
        six_months_ago = timezone.now() - timedelta(days=180)
        experiment_quality = []
        for i in range(6):
            month_start = timezone.now() - timedelta(days=30 * (i + 1))
            month_end = timezone.now() - timedelta(days=30 * i)
            month_approved = ExperimentApproval.objects.filter(
                created_at__gte=month_start,
                created_at__lt=month_end,
                status=ExperimentApproval.APPROVED
            ).count()
            month_total = ExperimentRequest.objects.filter(
                created_at__gte=month_start,
                created_at__lt=month_end
            ).count()
            approval_rate = round((month_approved / month_total) * 100) if month_total > 0 else 0
            experiment_quality.append({
                'month': month_start.strftime('%Y-%m'),
                'approved_count': month_approved,
                'total_count': month_total,
                'approval_rate': approval_rate
            })
        context['experiment_quality_kpi'] = experiment_quality
        # Add last month approval rate and remaining for chart
        if experiment_quality:
            last = experiment_quality[-1]
            context['experiment_quality_last_approval_rate'] = last.get('approval_rate', 0)
            context['experiment_quality_last_remaining'] = 100 - last.get('approval_rate', 0)
        else:
            context['experiment_quality_last_approval_rate'] = 0
            context['experiment_quality_last_remaining'] = 100
        # --- User's Latest Projects (limit 5, with progress) ---
        latest_projects = sorted(main_projects_list, key=lambda x: x['progress'], reverse=True)[:5]
        context['latest_projects'] = latest_projects
        # --- User's Latest Experiment Requests (limit 5) ---
        user_experiment_requests = ExperimentRequest.objects.filter(user=user).order_by('-created_at')[:5]
        context['latest_experiments'] = [
            {
                'project': er.project.name,
                'order': er.order,
                'type': er.experiment_type.name,
                'status': er.get_status_display(),
                'created_at': er.created_at,
                'request_file': er.request_file.url if er.request_file else None
            }
            for er in user_experiment_requests
        ]
        # --- User's Unread Notifications (limit 5) ---
        user_notifications = Notification.objects.filter(user=user, is_read=False).order_by('-created_at')[:5]
        context['notifications'] = [
            {
                'message': n.message,
                'created_at': n.created_at,
                'experiment': n.experiment_request.project.name if n.experiment_request else None
            }
            for n in user_notifications
        ]
        
        # --- نمودارهای دایره‌ای برای داشبورد مدیریتی ---
        # دریافت فیلتر زمانی از GET
        days_filter = self.request.GET.get('days', None)
        date_from = self.request.GET.get('date_from', None)
        date_to = self.request.GET.get('date_to', None)
        
        # فیلتر بر اساس تاریخ آزمایش (request_date) نه تاریخ ثبت (created_at)
        all_experiments = ExperimentRequest.objects.all()
        
        # فیلتر بر اساس تاریخ آزمایش (request_date)
        # jDateField می‌تواند مستقیماً با date object مقایسه شود
        if date_from and date_to:
            # استفاده از فیلتر تقویمی
            try:
                import jdatetime
                from datetime import datetime as dt
                # تبدیل فرمت تاریخ
                date_from_clean = date_from.replace('/', '-')
                date_to_clean = date_to.replace('/', '-')
                date_from_parts = date_from_clean.split('-')
                date_to_parts = date_to_clean.split('-')
                if len(date_from_parts) == 3 and len(date_to_parts) == 3:
                    jy, jm, jd = int(date_from_parts[0]), int(date_from_parts[1]), int(date_from_parts[2])
                    # تبدیل شمسی به میلادی با jdatetime
                    jalali_date_from = jdatetime.date(jy, jm, jd)
                    date_from_obj = jalali_date_from.togregorian()
                    
                    jy, jm, jd = int(date_to_parts[0]), int(date_to_parts[1]), int(date_to_parts[2])
                    jalali_date_to = jdatetime.date(jy, jm, jd)
                    date_to_obj = jalali_date_to.togregorian() + timedelta(days=1)
                    
                    all_experiments = all_experiments.filter(
                        request_date__gte=date_from_obj,
                        request_date__lt=date_to_obj
                    )
                    context['date_from'] = date_from_clean.replace('-', '/')
                    context['date_to'] = date_to_clean.replace('-', '/')
                    context['filter_type'] = 'calendar'
                else:
                    raise ValueError("Invalid date format")
            except Exception as e:
                # در صورت خطا، بدون فیلتر
                context['filter_type'] = None
        elif days_filter:
            # استفاده از فیلتر روز
            days_filter = int(days_filter)
            # تبدیل تاریخ میلادی به شمسی برای فیلتر
            import jdatetime
            today = timezone.now().date()
            date_filter_start = today - timedelta(days=days_filter)
            # تبدیل به تاریخ شمسی
            jalali_date = jdatetime.date.fromgregorian(date=date_filter_start)
            # فیلتر بر اساس سال و ماه شمسی
            all_experiments = all_experiments.filter(request_date__year__gte=jalali_date.year)
            if jalali_date.year == jdatetime.date.today().year:
                all_experiments = all_experiments.filter(request_date__month__gte=jalali_date.month)
            context['days_filter'] = days_filter
            context['filter_type'] = 'days'
        else:
            # بدون فیلتر - نمایش همه
            context['days_filter'] = None
            context['filter_type'] = None
        
        # محاسبه وضعیت آزمایشات با فیلتر زمانی (استفاده از get_actual_status)
        # همچنین بررسی RECOMPACT برای نمایش جداگانه
        experiment_status_data = {
            'completed': 0,  # قابل قبول (شامل تایید شده و ری‌کامپکت)
            'rejected': 0,
            'in_progress': 0,
            'pending': 0,
            'recompact': 0,  # ری‌کامپکت (برای نمایش جداگانه با رنگ بنفش)
        }
        
        for exp in all_experiments:
            actual_status = exp.get_actual_status()
            # بررسی اینکه آیا ری‌کامپکت است یا نه
            is_recompact = False
            if actual_status == ExperimentRequest.COMPLETED:
                # بررسی تاییدیه‌ها برای تشخیص ری‌کامپکت
                responses = exp.experimentresponse_set.all()
                if responses.exists():
                    latest_response = responses.order_by('-created_at').first()
                    approvals = latest_response.experimentapproval_set.all()
                    if approvals.filter(status=ExperimentApproval.RECOMPACT).exists():
                        is_recompact = True
                        experiment_status_data['recompact'] += 1
                    else:
                        experiment_status_data['completed'] += 1
                else:
                    experiment_status_data['completed'] += 1
            elif actual_status == ExperimentRequest.REJECTED:
                experiment_status_data['rejected'] += 1
            elif actual_status == ExperimentRequest.IN_PROGRESS:
                experiment_status_data['in_progress'] += 1
            else:  # PENDING
                experiment_status_data['pending'] += 1
        
        # قابل قبول = تایید شده + ری‌کامپکت
        experiment_status_data['acceptable'] = experiment_status_data['completed'] + experiment_status_data['recompact']
        
        total_experiments = sum([
            experiment_status_data['completed'],
            experiment_status_data['rejected'],
            experiment_status_data['in_progress'],
            experiment_status_data['pending'],
            experiment_status_data['recompact']
        ])
        context['experiment_status_data'] = experiment_status_data
        context['total_experiments'] = total_experiments
        
        # محاسبه حجم کل بر اساس لایه‌ها (فقط آزمایشات قابل قبول)
        # حجم = طول (کیلومتر) × عرض (متر) × ضخامت (سانتی‌متر) → تبدیل به متر مکعب
        # حجم (متر مکعب) = طول (کیلومتر) × 1000 × عرض (متر) × ضخامت (سانتی‌متر) / 100
        # = طول × عرض × ضخامت × 10
        volume_data = {
            'embankment': 0,  # خاکریزی (متر مکعب)
            'concrete': 0,    # بتن ریزی (متر مکعب)
            'asphalt': 0,     # آسفالت (متر مکعب)
        }
        
        # استفاده از همان فیلتر برای حجم - فقط آزمایشات قابل قبول
        filtered_experiments = all_experiments
        
        for exp in filtered_experiments:
            # فقط آزمایشات قابل قبول را حساب می‌کنیم
            actual_status = exp.get_actual_status()
            if actual_status != ExperimentRequest.COMPLETED:
                continue
            
            # محاسبه طول (کیلومتر)
            length_km = float(exp.end_kilometer - exp.start_kilometer) if exp.end_kilometer and exp.start_kilometer else 0
            if length_km <= 0:
                continue
            
            # گرفتن عرض پروژه (متر)
            project_width = float(exp.project.width) if exp.project.width else 0
            if project_width <= 0:
                continue
            
            # گرفتن ضخامت لایه (سانتی‌متر)
            layer_thickness = float(exp.layer.thickness_cm) if exp.layer and exp.layer.thickness_cm else 0
            if layer_thickness <= 0:
                continue
            
            # محاسبه حجم به متر مکعب: طول (کیلومتر) × 1000 × عرض (متر) × ضخامت (سانتی‌متر) / 100
            volume_m3 = length_km * 1000 * project_width * (layer_thickness / 100)
            
            # تشخیص نوع لایه
            if exp.layer and exp.layer.layer_type:
                layer_name = exp.layer.layer_type.name.lower()
                if 'خاک' in layer_name or 'خاکریزی' in layer_name:
                    volume_data['embankment'] += volume_m3
                elif 'بتن' in layer_name or 'concrete' in layer_name:
                    volume_data['concrete'] += volume_m3
                elif 'آسفالت' in layer_name or 'asphalt' in layer_name:
                    volume_data['asphalt'] += volume_m3
        
        total_volume = sum(volume_data.values())
        context['volume_data'] = volume_data
        context['total_volume'] = total_volume
        
        # محاسبه آمار به ازای هر پروژه
        from project.models import Project
        projects_stats = []
        all_projects = Project.objects.all()
        
        for project in all_projects:
            project_experiments = all_experiments.filter(project=project)
            project_status_data = {
                'completed': 0,
                'rejected': 0,
                'in_progress': 0,
                'pending': 0,
                'recompact': 0,
            }
            
            for exp in project_experiments:
                actual_status = exp.get_actual_status()
                is_recompact = False
                if actual_status == ExperimentRequest.COMPLETED:
                    responses = exp.experimentresponse_set.all()
                    if responses.exists():
                        latest_response = responses.order_by('-created_at').first()
                        approvals = latest_response.experimentapproval_set.all()
                        if approvals.filter(status=ExperimentApproval.RECOMPACT).exists():
                            is_recompact = True
                            project_status_data['recompact'] += 1
                        else:
                            project_status_data['completed'] += 1
                    else:
                        project_status_data['completed'] += 1
                elif actual_status == ExperimentRequest.REJECTED:
                    project_status_data['rejected'] += 1
                elif actual_status == ExperimentRequest.IN_PROGRESS:
                    project_status_data['in_progress'] += 1
                else:
                    project_status_data['pending'] += 1
            
            project_status_data['acceptable'] = project_status_data['completed'] + project_status_data['recompact']
            project_total = sum([
                project_status_data['completed'],
                project_status_data['rejected'],
                project_status_data['in_progress'],
                project_status_data['pending'],
                project_status_data['recompact']
            ])
            
            # محاسبه حجم برای این پروژه (فقط آزمایشات قابل قبول)
            project_volume_data = {
                'embankment': 0,  # خاکریزی (متر مکعب)
                'concrete': 0,    # بتن ریزی (متر مکعب)
                'asphalt': 0,     # آسفالت (متر مکعب)
            }
            
            for exp in project_experiments:
                # فقط آزمایشات قابل قبول
                actual_status = exp.get_actual_status()
                if actual_status != ExperimentRequest.COMPLETED:
                    continue
                
                # محاسبه طول (کیلومتر)
                length_km = float(exp.end_kilometer - exp.start_kilometer) if exp.end_kilometer and exp.start_kilometer else 0
                if length_km <= 0:
                    continue
                
                # گرفتن عرض پروژه (متر)
                project_width = float(exp.project.width) if exp.project.width else 0
                if project_width <= 0:
                    continue
                
                # گرفتن ضخامت لایه (سانتی‌متر)
                layer_thickness = float(exp.layer.thickness_cm) if exp.layer and exp.layer.thickness_cm else 0
                if layer_thickness <= 0:
                    continue
                
                # محاسبه حجم به متر مکعب
                volume_m3 = length_km * 1000 * project_width * (layer_thickness / 100)
                
                # تشخیص نوع لایه
                if exp.layer and exp.layer.layer_type:
                    layer_name = exp.layer.layer_type.name.lower()
                    if 'خاک' in layer_name or 'خاکریزی' in layer_name:
                        project_volume_data['embankment'] += volume_m3
                    elif 'بتن' in layer_name or 'concrete' in layer_name:
                        project_volume_data['concrete'] += volume_m3
                    elif 'آسفالت' in layer_name or 'asphalt' in layer_name:
                        project_volume_data['asphalt'] += volume_m3
            
            project_volume_total = sum(project_volume_data.values())
            
            if project_total > 0 or project_volume_total > 0:
                projects_stats.append({
                    'project': project,
                    'stats': project_status_data,
                    'total': project_total,
                    'volume': project_volume_data,
                    'volume_total': project_volume_total,
                })
        
        context['projects_stats'] = projects_stats
        
        return context

@login_required
def dashboard_experiment_status_detail(request):
    """نمایش جزئیات وضعیت آزمایشات بر اساس فیلتر زمانی"""
    from django.utils import timezone
    from datetime import timedelta
    from experiment.models import ExperimentRequest
    
    days_filter = request.GET.get('days', None)
    date_from = request.GET.get('date_from', None)
    date_to = request.GET.get('date_to', None)
    status_type = request.GET.get('status', 'completed')  # completed, rejected, in_progress, pending, recompact
    
    all_experiments = ExperimentRequest.objects.all()
    
    # استفاده از همان منطق فیلتر داشبورد
    if date_from and date_to:
        try:
            import jdatetime
            date_from_parts = date_from.split('-')
            date_to_parts = date_to.split('-')
            if len(date_from_parts) == 3 and len(date_to_parts) == 3:
                jy, jm, jd = int(date_from_parts[0]), int(date_from_parts[1]), int(date_from_parts[2])
                jalali_date_from = jdatetime.date(jy, jm, jd)
                date_from_obj = jalali_date_from.togregorian()
                
                jy, jm, jd = int(date_to_parts[0]), int(date_to_parts[1]), int(date_to_parts[2])
                jalali_date_to = jdatetime.date(jy, jm, jd)
                date_to_obj = jalali_date_to.togregorian() + timedelta(days=1)
                
                all_experiments = all_experiments.filter(
                    request_date__gte=date_from_obj,
                    request_date__lt=date_to_obj
                )
        except:
            days_filter = 30
            today = timezone.now().date()
            date_filter_start = today - timedelta(days=days_filter)
            all_experiments = all_experiments.filter(request_date__gte=date_filter_start)
    elif days_filter:
        days_filter = int(days_filter)
        today = timezone.now().date()
        date_filter_start = today - timedelta(days=days_filter)
        all_experiments = all_experiments.filter(request_date__gte=date_filter_start)
    else:
        days_filter = 30
        today = timezone.now().date()
        date_filter_start = today - timedelta(days=days_filter)
        all_experiments = all_experiments.filter(request_date__gte=date_filter_start)
    
    # فیلتر بر اساس وضعیت
    from experiment.models import ExperimentApproval
    filtered_experiments = []
    
    for exp in all_experiments:
        actual_status = exp.get_actual_status()
        if status_type == 'completed' or status_type == 'acceptable':
            # قابل قبول = تایید شده (بدون ری‌کامپکت)
            if actual_status == ExperimentRequest.COMPLETED:
                responses = exp.experimentresponse_set.all()
                if responses.exists():
                    latest_response = responses.order_by('-created_at').first()
                    approvals = latest_response.experimentapproval_set.all()
                    if not approvals.filter(status=ExperimentApproval.RECOMPACT).exists():
                        filtered_experiments.append(exp)
                else:
                    filtered_experiments.append(exp)
        elif status_type == 'recompact':
            # ری‌کامپکت
            if actual_status == ExperimentRequest.COMPLETED:
                responses = exp.experimentresponse_set.all()
                if responses.exists():
                    latest_response = responses.order_by('-created_at').first()
                    approvals = latest_response.experimentapproval_set.all()
                    if approvals.filter(status=ExperimentApproval.RECOMPACT).exists():
                        filtered_experiments.append(exp)
        elif status_type == 'rejected':
            if actual_status == ExperimentRequest.REJECTED:
                filtered_experiments.append(exp)
        elif status_type == 'in_progress':
            if actual_status == ExperimentRequest.IN_PROGRESS:
                filtered_experiments.append(exp)
        elif status_type == 'pending':
            if actual_status == ExperimentRequest.PENDING:
                filtered_experiments.append(exp)
    
    status_names = {
        'completed': 'قابل قبول',
        'acceptable': 'قابل قبول',
        'recompact': 'ری‌کامپکت',
        'rejected': 'رد شده',
        'in_progress': 'در حال انجام',
        'pending': 'در انتظار بررسی',
    }
    
    return render(request, 'core/dashboard_experiment_status_detail.html', {
        'experiments': filtered_experiments,
        'status_type': status_type,
        'status_name': status_names.get(status_type, 'نامشخص'),
        'days_filter': days_filter if days_filter else None,
        'date_from': date_from if date_from else None,
        'date_to': date_to if date_to else None,
    })

@login_required
def dashboard_volume_detail(request):
    """نمایش جزئیات حجم کار بر اساس نوع لایه"""
    from django.utils import timezone
    from datetime import timedelta
    from experiment.models import ExperimentRequest
    
    days_filter = request.GET.get('days', None)
    date_from = request.GET.get('date_from', None)
    date_to = request.GET.get('date_to', None)
    volume_type = request.GET.get('type', 'embankment')  # embankment, concrete, asphalt
    
    filtered_experiments = ExperimentRequest.objects.all()
    
    # استفاده از همان منطق فیلتر داشبورد
    if date_from and date_to:
        try:
            import jdatetime
            date_from_parts = date_from.split('-')
            date_to_parts = date_to.split('-')
            if len(date_from_parts) == 3 and len(date_to_parts) == 3:
                jy, jm, jd = int(date_from_parts[0]), int(date_from_parts[1]), int(date_from_parts[2])
                jalali_date_from = jdatetime.date(jy, jm, jd)
                date_from_obj = jalali_date_from.togregorian()
                
                jy, jm, jd = int(date_to_parts[0]), int(date_to_parts[1]), int(date_to_parts[2])
                jalali_date_to = jdatetime.date(jy, jm, jd)
                date_to_obj = jalali_date_to.togregorian() + timedelta(days=1)
                
                filtered_experiments = filtered_experiments.filter(
                    request_date__gte=date_from_obj,
                    request_date__lt=date_to_obj
                )
        except:
            days_filter = 30
            today = timezone.now().date()
            date_filter_start = today - timedelta(days=days_filter)
            filtered_experiments = filtered_experiments.filter(request_date__gte=date_filter_start)
    elif days_filter:
        days_filter = int(days_filter)
        today = timezone.now().date()
        date_filter_start = today - timedelta(days=days_filter)
        filtered_experiments = filtered_experiments.filter(request_date__gte=date_filter_start)
    else:
        days_filter = 30
        today = timezone.now().date()
        date_filter_start = today - timedelta(days=days_filter)
        filtered_experiments = filtered_experiments.filter(request_date__gte=date_filter_start)
    
    # فیلتر بر اساس نوع لایه
    volume_experiments = []
    for exp in filtered_experiments:
        if exp.layer and exp.layer.layer_type:
            layer_name = exp.layer.layer_type.name.lower()
            if volume_type == 'embankment' and ('خاک' in layer_name or 'خاکریزی' in layer_name):
                volume_experiments.append(exp)
            elif volume_type == 'concrete' and ('بتن' in layer_name or 'concrete' in layer_name):
                volume_experiments.append(exp)
            elif volume_type == 'asphalt' and ('آسفالت' in layer_name or 'asphalt' in layer_name):
                volume_experiments.append(exp)
    
    volume_names = {
        'embankment': 'خاکریزی',
        'concrete': 'بتن ریزی',
        'asphalt': 'آسفالت',
    }
    
    # محاسبه حجم کل و حجم هر آزمایش (متر مکعب)
    # فقط آزمایشات قابل قبول
    total_volume = 0
    experiments_with_volume = []
    for exp in volume_experiments:
        actual_status = exp.get_actual_status()
        if actual_status != ExperimentRequest.COMPLETED:
            continue
            
        volume_m3 = 0
        if exp.end_kilometer and exp.start_kilometer and exp.project.width and exp.layer and exp.layer.thickness_cm:
            # محاسبه طول (کیلومتر)
            length_km = float(exp.end_kilometer - exp.start_kilometer)
            if length_km > 0:
                # گرفتن عرض پروژه (متر)
                project_width = float(exp.project.width)
                # گرفتن ضخامت لایه (سانتی‌متر)
                layer_thickness = float(exp.layer.thickness_cm)
                # محاسبه حجم به متر مکعب
                volume_m3 = length_km * 1000 * project_width * (layer_thickness / 100)
                total_volume += volume_m3
        
        experiments_with_volume.append({
            'experiment': exp,
            'volume': volume_m3
        })
    
    return render(request, 'core/dashboard_volume_detail.html', {
        'experiments': experiments_with_volume,
        'volume_type': volume_type,
        'volume_name': volume_names.get(volume_type, 'نامشخص'),
        'days_filter': days_filter if days_filter else None,
        'date_from': date_from if date_from else None,
        'date_to': date_to if date_to else None,
        'total_volume': total_volume,
    })

