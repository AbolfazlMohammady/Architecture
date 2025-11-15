import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.views import generic
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from . import models, forms
from project.models import ProjectLayer
from django.contrib import messages
from django.db.models import Q, Avg, Max, Min
from decimal import Decimal
# Helpers
def get_layer_display_name(layer):
    """نمایش نام لایه با شماره فارسی برای لایه‌های تکراری"""
    # تبدیل "خاکریزی" به "خاک ریز"
    layer_name = layer.layer_type.name.replace('خاکریزی', 'خاک ریز')
    
    siblings = layer.project.projectlayer_set.filter(
        layer_type=layer.layer_type
    ).order_by('order_from_top')
    if siblings.count() > 1:
        sibling_list = list(siblings)
        try:
            index = sibling_list.index(layer) + 1
            # تبدیل عدد به فارسی
            persian_numbers = ['', 'یک', 'دو', 'سه', 'چهار', 'پنج', 'شش', 'هفت', 'هشت', 'نه', 'ده']
            if index <= 10:
                persian_index = persian_numbers[index]
            else:
                persian_index = str(index)
            return f"{layer_name} {persian_index}"
        except ValueError:
            pass
    return layer_name


def find_blocking_lower_layers(project, target_layer, ranges):
    """
    ranges: list of (Decimal start, Decimal end)
    Returns list of lower layers (لایه‌های زیرین) که تایید نشده‌اند برای بازه‌های همپوشان.
    
    لایه‌های زیرین = لایه‌هایی که order_from_top بیشتر دارند (پایین‌تر هستند)
    
    فقط قسمت‌هایی که همپوشانی کیلومتراژ دارند بررسی می‌شوند، نه کل لایه.
    """
    if not ranges:
        return []
    
    # لایه‌های زیرین: order_from_top بیشتر = پایین‌تر
    lower_layers = ProjectLayer.objects.filter(
        project=project,
        order_from_top__gt=target_layer.order_from_top  # تغییر از __lt به __gt
    )
    
    blocking = []
    for lower in lower_layers:
        # بررسی برای هر بازه کیلومتراژ که آیا این لایه زیرین blocking است
        layer_blocked = False
        
        for start, end in ranges:
            # پیدا کردن درخواست‌های آزمایش این لایه که با این بازه همپوشانی دارند
            overlap_requests = models.ExperimentRequest.objects.filter(
                project=project,
                layer=lower,
                start_kilometer__lt=end,
                end_kilometer__gt=start,
            )
            
            # اگر هیچ درخواست آزمایشی برای این بازه همپوشان وجود نداشت، blocking نیست
            if not overlap_requests.exists():
                continue  # این بازه blocking نیست، به بازه بعدی برو
            
            # بررسی اینکه آیا برای این بازه همپوشان، حداقل یک آزمایش تایید شده وجود دارد
            approved_for_this_range = False
            
            for req in overlap_requests:
                # بررسی همپوشانی دقیق
                req_start = float(req.start_kilometer)
                req_end = float(req.end_kilometer)
                
                # محاسبه بازه همپوشانی واقعی
                overlap_start = max(float(start), req_start)
                overlap_end = min(float(end), req_end)
                
                # اگر همپوشانی واقعی وجود دارد
                if overlap_start < overlap_end:
                    # بررسی اینکه آیا این درخواست تایید شده است
                    for resp in req.experimentresponse_set.all():
                        if resp.is_fully_approved():
                            approved_for_this_range = True
                            break
                    if approved_for_this_range:
                        break
            
            # اگر برای این بازه همپوشان تایید نشده، لایه blocking است
            if not approved_for_this_range:
                layer_blocked = True
                break  # نیازی به بررسی بقیه بازه‌ها نیست
        
        # اگر لایه برای حداقل یک بازه blocking بود، به لیست اضافه می‌شود
        if layer_blocked:
            blocking.append(lower)
    
    return blocking
from .forms import (
    ExperimentResponseKilometerFormSet, 
    ExperimentResponseFileFormSet,
    ExperimentRequestKilometerFormSet,
    ExperimentRequestFileFormSet,
    AsphaltTestFormSet
)

# تنظیم لاگر
logger = logging.getLogger(__name__)

# Create your views here.

class ExperimentRequestListView(LoginRequiredMixin, generic.ListView):
    model = models.ExperimentRequest
    template_name = 'experiment/experiment-request-list.html'
    context_object_name = 'experiment_requests'
    paginate_by = 30

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # فیلتر کردن بر اساس دسترسی کاربر به پروژه‌ها
        if not user.is_superuser:
            # فقط درخواست‌های پروژه‌هایی که کاربر به آن‌ها دسترسی دارد
            queryset = queryset.filter(project__in=user.accessible_projects.all())
        
        project_id = self.request.GET.get('project')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # فقط پروژه‌های قابل دسترسی کاربر
        if user.is_superuser:
            context['projects'] = models.Project.objects.all()
        else:
            context['projects'] = user.accessible_projects.all()
        return context

class ExperimentRequestCreateView(LoginRequiredMixin, generic.CreateView):
    model = models.ExperimentRequest
    form_class = forms.ExperimentRequestForm
    template_name = 'experiment/experiment-request-form.html'
    success_url = reverse_lazy('experiment:experiment-request-list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

class ExperimentRequestDetailView(LoginRequiredMixin, generic.DetailView):
    model = models.ExperimentRequest
    template_name = 'experiment/experiment-request-detail.html'
    context_object_name = 'experiment_request'
    
    def dispatch(self, request, *args, **kwargs):
        # چک کردن دسترسی کاربر به پروژه
        obj = self.get_object()
        if not request.user.is_superuser:
            if obj.project not in request.user.accessible_projects.all():
                messages.error(request, 'شما به این پروژه دسترسی ندارید.')
                return redirect('experiment:experiment_request_list')
        return super().dispatch(request, *args, **kwargs)

class ExperimentResponseCreateView(LoginRequiredMixin, generic.CreateView):
    model = models.ExperimentResponse
    form_class = forms.ExperimentResponseForm
    template_name = 'experiment/experiment_response_form.html'
    success_url = reverse_lazy('experiment:experiment_request_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        experiment_request_id = self.kwargs.get('experiment_request_id')
        if experiment_request_id:
            experiment_request = get_object_or_404(models.ExperimentRequest, id=experiment_request_id)
            kwargs['experiment_request'] = experiment_request
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        experiment_request_id = self.kwargs.get('experiment_request_id')
        experiment_request = get_object_or_404(models.ExperimentRequest, id=experiment_request_id)
        context['experiment_request'] = experiment_request
        return context

    def form_valid(self, form):
        experiment_request_id = self.kwargs.get('experiment_request_id')
        experiment_request = get_object_or_404(models.ExperimentRequest, id=experiment_request_id)
        form.instance.experiment_request = experiment_request
        form.instance.user = self.request.user
        response = super().form_valid(form)
        
        # Update experiment request status
        experiment_request.status = 'completed'
        experiment_request.save()
        
        return response

class ExperimentApprovalCreateView(LoginRequiredMixin, generic.CreateView):
    model = models.ExperimentApproval
    form_class = forms.ExperimentApprovalForm
    template_name = 'experiment/experiment-approval-form.html'
    success_url = reverse_lazy('experiment:experiment-request-list')

    def get_initial(self):
        initial = super().get_initial()
        experiment_response_id = self.kwargs.get('pk')
        if experiment_response_id:
            initial['experiment_response'] = get_object_or_404(models.ExperimentResponse, pk=experiment_response_id)
            initial['approver'] = self.request.user
        return initial

    def form_valid(self, form):
        form.instance.approver = self.request.user
        return super().form_valid(form)

@login_required
def experiment_request_list(request):
    user = request.user
    
    # فیلتر کردن بر اساس دسترسی کاربر به پروژه‌ها
    if user.is_superuser:
        experiment_requests = models.ExperimentRequest.objects.all()
        projects = models.Project.objects.all()
    else:
        experiment_requests = models.ExperimentRequest.objects.filter(project__in=user.accessible_projects.all())
        projects = user.accessible_projects.all()
    
    # دریافت پارامترهای GET
    project_id = request.GET.get('project', '').strip()
    status = request.GET.get('status', '').strip()
    search = request.GET.get('search', '').strip()
    
    # دیباگ - چاپ مقادیر دریافتی
    print(f"DEBUG: GET params - project_id: '{project_id}', status: '{status}', search: '{search}'")
    print(f"DEBUG: All GET params: {dict(request.GET)}")
    
    # فیلتر بر اساس پروژه
    if project_id:
        try:
            project_id_int = int(project_id)
            # چک کردن دسترسی کاربر به پروژه
            if not user.is_superuser:
                if not user.accessible_projects.filter(id=project_id_int).exists():
                    messages.error(request, 'شما به این پروژه دسترسی ندارید.')
                    project_id_int = None
            if project_id_int:
                experiment_requests = experiment_requests.filter(project_id=project_id_int)
                print(f"DEBUG: Filtered by project_id: {project_id_int}, count: {experiment_requests.count()}")
        except (ValueError, TypeError) as e:
            print(f"DEBUG: Invalid project_id: {project_id}, error: {e}")
    
    # فیلتر بر اساس وضعیت
    if status:
        try:
            status_int = int(status)
            experiment_requests = experiment_requests.filter(status=status_int)
            print(f"DEBUG: Filtered by status: {status_int}, count: {experiment_requests.count()}")
        except (ValueError, TypeError) as e:
            print(f"DEBUG: Invalid status: {status}, error: {e}")
    
    # فیلتر بر اساس جستجو
    if search and search != 'None':
        experiment_requests = experiment_requests.filter(
            Q(description__icontains=search) | Q(project__name__icontains=search)
        )
        print(f"DEBUG: Filtered by search: {search}, count: {experiment_requests.count()}")
    
    # مرتب‌سازی بر اساس تاریخ ایجاد (جدیدترین اول)
    experiment_requests = experiment_requests.order_by('-created_at')
    
    # اضافه کردن نام نمایشی لایه به هر درخواست
    for exp_request in experiment_requests:
        exp_request.layer_display_name = get_layer_display_name(exp_request.layer) if exp_request.layer else '-'
    
    print(f"DEBUG: Final count: {experiment_requests.count()}")
    
    return render(request, 'experiment/experiment_request_list.html', {
        'experiment_requests': experiment_requests,
        'projects': projects,
        'selected_project': project_id,
        'selected_status': status,
        'search_query': search
    })

@login_required
def experiment_request_create(request):
    if request.method == 'POST':
        form = forms.ExperimentRequestForm(request.POST, request.FILES, user=request.user)
        kilometer_formset = ExperimentRequestKilometerFormSet(request.POST, prefix='kilometer')
        file_formset = ExperimentRequestFileFormSet(request.POST, request.FILES, prefix='file')
        if form.is_valid() and kilometer_formset.is_valid() and file_formset.is_valid():
            valid_ranges = []
            for km_form in kilometer_formset:
                if km_form.cleaned_data and not km_form.cleaned_data.get('DELETE', False):
                    start = km_form.cleaned_data.get('start_kilometer')
                    end = km_form.cleaned_data.get('end_kilometer')
                    if start is not None and end is not None:
                        valid_ranges.append((start, end))
            if not valid_ranges:
                kilometer_formset._non_form_errors = kilometer_formset.error_class(
                    ['حداقل یک بازه کیلومتراژ باید ثبت شود.']
                )
            else:
                decimal_ranges = [
                    (Decimal(str(rng[0])), Decimal(str(rng[1])))
                    for rng in valid_ranges
                ]
                project = form.cleaned_data.get('project')
                layer = form.cleaned_data.get('layer')
                blocking_layers = []
                if project and layer:
                    blocking_layers = find_blocking_lower_layers(project, layer, decimal_ranges)
                if blocking_layers:
                    names = [get_layer_display_name(blk) for blk in blocking_layers]
                    form.add_error(
                        None,
                        f'برای ثبت درخواست لایه انتخاب‌شده، ابتدا نتایج لایه‌های زیرین تایید شود: {"، ".join(names)}'
                    )
                else:
                    # چک کردن دسترسی کاربر به پروژه
                    project = form.cleaned_data.get('project')
                    if not request.user.is_superuser:
                        if project not in request.user.accessible_projects.all():
                            messages.error(request, 'شما به این پروژه دسترسی ندارید.')
                            return render(request, 'experiment/experiment_request_form.html', {
                                'form': form,
                                'kilometer_formset': kilometer_formset,
                                'file_formset': file_formset,
                                'user': request.user,
                            })
                    
                    experiment_request = form.save(commit=False)
                    experiment_request.user = request.user
                    start_values = [rng[0] for rng in decimal_ranges]
                    end_values = [rng[1] for rng in decimal_ranges]
                    experiment_request.start_kilometer = min(start_values)
                    experiment_request.end_kilometer = max(end_values)
                    experiment_request.save()
                    form.save_m2m()
                    kilometer_formset.instance = experiment_request
                    kilometer_formset.save()
                    file_formset.instance = experiment_request
                    file_formset.save()
                    # ارسال نوتیفیکیشن به همه نقش‌های کلیدی پروژه
                    from experiment.models import ExperimentResponse
                    temp_response = ExperimentResponse(experiment_request=experiment_request)  # فقط برای دسترسی به متد
                    notified_users = set()
                    for role in temp_response.get_required_approval_roles():
                        for user in temp_response.get_approvers_for_role(role):
                            if user and user.id not in notified_users:
                                models.Notification.objects.create(
                                    user=user,
                                    experiment_request=experiment_request,
                                    message=f'یک درخواست آزمایش جدید از {request.user.get_full_name()} برای پروژه {experiment_request.project.name} ثبت شد.'
                                )
                                notified_users.add(user.id)
                    messages.success(request, 'درخواست آزمایش با موفقیت ثبت شد.')
                    return redirect('experiment:experiment_request_list')
        else:
            print('Form errors:', form.errors)
            print('Kilometer formset errors:', kilometer_formset.errors)
            print('File formset errors:', file_formset.errors)
    else:
        form = forms.ExperimentRequestForm(user=request.user)
        kilometer_formset = ExperimentRequestKilometerFormSet(prefix='kilometer')
        file_formset = ExperimentRequestFileFormSet(prefix='file')
    return render(request, 'experiment/experiment_request_form.html', {
        'form': form,
        'kilometer_formset': kilometer_formset,
        'file_formset': file_formset,
        'user': request.user,
    })

@login_required
def experiment_request_edit(request, pk):
    experiment_request = get_object_or_404(models.ExperimentRequest, pk=pk)
    
    # چک کردن دسترسی کاربر به پروژه
    if not request.user.is_superuser:
        if experiment_request.project not in request.user.accessible_projects.all():
            messages.error(request, 'شما به این پروژه دسترسی ندارید.')
            return redirect('experiment:experiment_request_list')
    
    if request.method == 'POST':
        form = forms.ExperimentRequestForm(request.POST, request.FILES, instance=experiment_request, user=request.user)
        kilometer_formset = ExperimentRequestKilometerFormSet(
            request.POST,
            prefix='kilometer',
            instance=experiment_request
        )
        file_formset = ExperimentRequestFileFormSet(
            request.POST,
            request.FILES,
            prefix='file',
            instance=experiment_request
        )
        if form.is_valid() and kilometer_formset.is_valid() and file_formset.is_valid():
            valid_ranges = []
            for km_form in kilometer_formset:
                if km_form.cleaned_data and not km_form.cleaned_data.get('DELETE', False):
                    start = km_form.cleaned_data.get('start_kilometer')
                    end = km_form.cleaned_data.get('end_kilometer')
                    if start is not None and end is not None:
                        valid_ranges.append((start, end))
            if not valid_ranges:
                kilometer_formset._non_form_errors = kilometer_formset.error_class(
                    ['حداقل یک بازه کیلومتراژ باید ثبت شود.']
                )
            else:
                decimal_ranges = [
                    (Decimal(str(rng[0])), Decimal(str(rng[1])))
                    for rng in valid_ranges
                ]
                project = form.cleaned_data.get('project')
                layer = form.cleaned_data.get('layer')
                blocking_layers = []
                if project and layer:
                    blocking_layers = find_blocking_lower_layers(project, layer, decimal_ranges)
                if blocking_layers:
                    names = [get_layer_display_name(blk) for blk in blocking_layers]
                    form.add_error(
                        None,
                        f'برای ثبت درخواست لایه انتخاب‌شده، ابتدا نتایج لایه‌های زیرین تایید شود: {"، ".join(names)}'
                    )
                else:
                    # چک کردن دسترسی کاربر به پروژه جدید (اگر تغییر کرده باشد)
                    project = form.cleaned_data.get('project')
                    if not request.user.is_superuser:
                        if project not in request.user.accessible_projects.all():
                            messages.error(request, 'شما به این پروژه دسترسی ندارید.')
                            return render(request, 'experiment/experiment_request_form.html', {
                                'form': form,
                                'kilometer_formset': kilometer_formset,
                                'file_formset': file_formset,
                                'user': request.user,
                            })
                    
                    experiment_request_instance = form.save(commit=False)
                    start_values = [rng[0] for rng in decimal_ranges]
                    end_values = [rng[1] for rng in decimal_ranges]
                    experiment_request_instance.start_kilometer = min(start_values)
                    experiment_request_instance.end_kilometer = max(end_values)
                    experiment_request_instance.save()
                    form.save_m2m()
                    kilometer_formset.save()
                    file_formset.save()
                    messages.success(request, 'درخواست آزمایش با موفقیت بروزرسانی شد.')
                    return redirect('experiment:experiment_request_detail', pk=experiment_request.pk)
        else:
            print('Form errors:', form.errors)
            print('Kilometer formset errors:', kilometer_formset.errors)
            print('File formset errors:', file_formset.errors)
    else:
        form = forms.ExperimentRequestForm(instance=experiment_request, user=request.user)
        kilometer_formset = ExperimentRequestKilometerFormSet(prefix='kilometer', instance=experiment_request)
        file_formset = ExperimentRequestFileFormSet(prefix='file', instance=experiment_request)
    
    return render(request, 'experiment/experiment_request_form.html', {
        'form': form,
        'kilometer_formset': kilometer_formset,
        'file_formset': file_formset,
        'user': request.user,
    })

@login_required
def experiment_request_detail(request, pk):
    logger = logging.getLogger(__name__)
    experiment_request = get_object_or_404(models.ExperimentRequest, pk=pk)
    
    # چک کردن دسترسی کاربر به پروژه
    if not request.user.is_superuser:
        if experiment_request.project not in request.user.accessible_projects.all():
            messages.error(request, 'شما به این پروژه دسترسی ندارید.')
            return redirect('experiment:experiment_request_list')
    
    experiment_responses = models.ExperimentResponse.objects.filter(experiment_request=experiment_request)
    kilometer_ranges = experiment_request.kilometer_ranges.all()
    request_files = experiment_request.files.all()
    kilometer_ranges_list = list(kilometer_ranges.values('start_kilometer', 'end_kilometer', 'description'))
    request_files_list = list(request_files.values('file'))
    logger.info(f"[experiment_request_detail] pk={pk}, kilometer_ranges={kilometer_ranges.count()}, request_files={request_files.count()}")
    return render(request, 'experiment/experiment_request_detail.html', {
        'experiment_request': experiment_request,
        'experiment_responses': experiment_responses,
        'kilometer_ranges': kilometer_ranges,
        'request_files': request_files,
        'kilometer_ranges_list': kilometer_ranges_list,
        'request_files_list': request_files_list,
    })

@login_required
def experiment_response_create(request, pk):
    experiment_request = get_object_or_404(models.ExperimentRequest, pk=pk)
    # بررسی وجود پاسخ قبلی و تاییدیه کامل آن
    last_response = experiment_request.experimentresponse_set.order_by('-created_at').first()
    if last_response and not last_response.is_fully_approved():
        messages.error(request, 'تا زمانی که همه نقش‌های کلیدی پروژه پاسخ قبلی را تایید نکرده‌اند، امکان ثبت پاسخ جدید وجود ندارد.')
        return redirect('experiment:experiment_request_detail', pk=experiment_request.pk)
    # بررسی اینکه آیا آزمایش آسفالت است
    experiment_types = experiment_request.experiment_type.all()
    is_asphalt = any('آسفالت' in et.name for et in experiment_types)
    
    if request.method == 'POST':
        form = forms.ExperimentResponseForm(request.POST, request.FILES, experiment_request=experiment_request)
        kilometer_formset = ExperimentResponseKilometerFormSet(request.POST, prefix='kilometer')
        file_formset = ExperimentResponseFileFormSet(request.POST, request.FILES, prefix='file')
        asphalt_formset = None
        
        if is_asphalt:
            asphalt_formset = AsphaltTestFormSet(request.POST, prefix='asphalt')
        
        is_valid = form.is_valid() and kilometer_formset.is_valid() and file_formset.is_valid()
        if is_asphalt and asphalt_formset:
            is_valid = is_valid and asphalt_formset.is_valid()
        
        if is_valid:
            experiment_response = form.save(commit=False)
            experiment_response.experiment_request = experiment_request
            experiment_response.user = request.user
            experiment_response.save()
            kilometer_formset.instance = experiment_response
            kilometer_formset.save()
            file_formset.instance = experiment_response
            file_formset.save()
            
            # ذخیره فرم آسفالت
            if is_asphalt and asphalt_formset:
                asphalt_formset.instance = experiment_response
                asphalt_formset.save()
            
            # ارسال نوتیفیکیشن به همه نقش‌های کلیدی پروژه
            notified_users = set()
            for role in experiment_response.get_required_approval_roles():
                for user in experiment_response.get_approvers_for_role(role):
                    if user and user.id not in notified_users:
                        models.Notification.objects.create(
                            user=user,
                            experiment_request=experiment_response.experiment_request,
                            message=f'یک تاییدیه جدید برای پاسخ آزمایش پروژه {experiment_response.experiment_request.project.name} ثبت شد.'
                        )
                        notified_users.add(user.id)
            messages.success(request, 'پاسخ آزمایش با موفقیت ثبت شد.')
            return redirect('experiment:experiment_response_detail', pk=experiment_response.pk)
        else:
            print('Form errors:', form.errors)
            print('Form non_field_errors:', form.non_field_errors())
            print('Kilometer formset errors:', kilometer_formset.errors)
            print('Kilometer formset non_form_errors:', kilometer_formset.non_form_errors())
            print('File formset errors:', file_formset.errors)
            print('File formset non_form_errors:', file_formset.non_form_errors())
            if is_asphalt and asphalt_formset:
                print('Asphalt formset errors:', asphalt_formset.errors)
                print('Asphalt formset non_form_errors:', asphalt_formset.non_form_errors())
    else:
        form = forms.ExperimentResponseForm(experiment_request=experiment_request)
        kilometer_formset = ExperimentResponseKilometerFormSet(prefix='kilometer')
        file_formset = ExperimentResponseFileFormSet(prefix='file')
        asphalt_formset = None
        if is_asphalt:
            asphalt_formset = AsphaltTestFormSet(prefix='asphalt')

    layer_display_name = experiment_request.layer.layer_type.name
    siblings = experiment_request.project.projectlayer_set.filter(
        layer_type=experiment_request.layer.layer_type
    ).order_by('order_from_top')
    if siblings.count() > 1:
        layer_list = list(siblings)
        try:
            index = layer_list.index(experiment_request.layer) + 1
            layer_display_name = f"{layer_display_name} {index}"
        except ValueError:
            pass

    context = {
        'form': form,
        'kilometer_formset': kilometer_formset,
        'file_formset': file_formset,
        'experiment_request': experiment_request,
        'project': experiment_request.project,
        'layer': experiment_request.layer,
        'layer_display_name': layer_display_name,
        'experiment_types': experiment_request.experiment_type.all(),
        'experiment_subtypes': experiment_request.experiment_subtype.all(),
        'request_files': experiment_request.files.all(),
        'kilometer_ranges': experiment_request.kilometer_ranges.all(),
        'request_user': experiment_request.user,  # کاربری که درخواست داده
        'response_user': request.user,  # کاربری که پاسخ می‌دهد
    }
    return render(request, 'experiment/experiment_response_form.html', context)

@login_required
def experiment_approval_create(request, response_id):
    experiment_response = get_object_or_404(models.ExperimentResponse, pk=response_id)
    
    # بررسی اینکه آیا کاربر مجاز به تایید است
    can_approve = False
    user_roles = []
    for role in experiment_response.get_required_approval_roles():
        approvers = experiment_response.get_approvers_for_role(role)
        if request.user in approvers:
            can_approve = True
            user_roles.append(role)
    
    if not can_approve:
        messages.error(request, 'شما مجاز به ثبت تاییدیه برای این پاسخ آزمایش نیستید.')
        return redirect('experiment:experiment_response_detail', pk=response_id)
    
    if request.method == 'POST':
        post_data = request.POST.copy()
        if not post_data.get('experiment_response'):
            post_data['experiment_response'] = experiment_response.pk
        form = forms.ExperimentApprovalForm(post_data)
        if form.is_valid():
            approval = form.save(commit=False)
            approval.experiment_response = experiment_response
            approval.approver = request.user
            approval.save()
            # ارسال نوتیفیکیشن به همه نقش‌های کلیدی پروژه
            notified_users = set()
            for role in experiment_response.get_required_approval_roles():
                for user in experiment_response.get_approvers_for_role(role):
                    if user and user.id not in notified_users:
                        models.Notification.objects.create(
                            user=user,
                            experiment_request=experiment_response.experiment_request,
                            message=f'یک تاییدیه جدید برای پاسخ آزمایش پروژه {experiment_response.experiment_request.project.name} ثبت شد.'
                        )
                        notified_users.add(user.id)
            messages.success(request, 'تایید آزمایش با موفقیت ثبت شد.')
            return redirect('experiment:experiment_response_detail', pk=response_id)
    else:
        form = forms.ExperimentApprovalForm(initial={'experiment_response': experiment_response.pk})
    return render(request, 'experiment/experiment_approval_form.html', {
        'form': form,
        'experiment_response': experiment_response,
        'user_roles': user_roles
    })

@login_required
def experiment_request_approval_create(request, request_id):
    experiment_request = get_object_or_404(models.ExperimentRequest, pk=request_id)
    if request.method == 'POST':
        form = forms.ExperimentRequestApprovalForm(request.POST)
        if form.is_valid():
            approval = form.save(commit=False)
            approval.experiment_request = experiment_request
            approval.approver = request.user
            approval.save()
            
            # ایجاد اعلان برای درخواست کننده
            status_text = "تایید شد" if approval.status == models.ExperimentRequestApproval.APPROVED else "رد شد"
            models.Notification.objects.create(
                user=experiment_request.user,
                experiment_request=experiment_request,
                message=f'درخواست آزمایش شما توسط {request.user.get_full_name()} {status_text}.'
            )
            
            messages.success(request, 'تایید درخواست آزمایش با موفقیت ثبت شد.')
            return redirect('experiment:experiment_request_detail', pk=request_id)
    else:
        form = forms.ExperimentRequestApprovalForm()
    return render(request, 'experiment/experiment_request_approval_form.html', {
        'form': form,
        'experiment_request': experiment_request
    })

def payment_coefficient_create(request):
    logger.info(f"Accessing payment_coefficient_create view by user: {request.user}")
    try:
        if request.method == 'POST':
            logger.info("Processing POST request for payment coefficient creation")
            form = forms.PaymentCoefficientForm(request.POST)
            if form.is_valid():
                logger.info("Form is valid, saving payment coefficient")
                form.save()
                messages.success(request, 'ضریب پرداخت با موفقیت ثبت شد.')
                return redirect('experiment:payment_coefficient_list')
            else:
                logger.error(f"Form validation failed: {form.errors}")
        else:
            logger.info("Rendering payment coefficient form")
            form = forms.PaymentCoefficientForm()
        
        logger.info("Rendering payment_coefficient_form.html template")
        return render(request, 'experiment/payment_coefficient_form.html', {'form': form})
    except Exception as e:
        logger.error(f"Error in payment_coefficient_create: {str(e)}")
        messages.error(request, 'خطا در ایجاد ضریب پرداخت')
        return render(request, 'experiment/payment_coefficient_form.html', {'form': form})

def payment_coefficient_list(request):
    logger.info(f"Accessing payment_coefficient_list view by user: {request.user}")
    try:
        logger.info("Starting to fetch data from database...")
        
        # تست database connection
        try:
            coefficients = models.PaymentCoefficient.objects.all()
            logger.info(f"Successfully fetched {coefficients.count()} coefficients")
        except Exception as db_error:
            logger.error(f"Database error: {str(db_error)}")
            coefficients = []
        
        try:
            projects = models.Project.objects.all()
            logger.info(f"Successfully fetched {projects.count()} projects")
        except Exception as db_error:
            logger.error(f"Projects database error: {str(db_error)}")
            projects = []
        
        try:
            layers = models.PaymentCoefficient.LAYER_CHOICES
            logger.info(f"Successfully got layer choices: {layers}")
        except Exception as layer_error:
            logger.error(f"Layer choices error: {str(layer_error)}")
            layers = []
        
        project_id = request.GET.get('project')
        layer = request.GET.get('layer')
        
        logger.info(f"Filtering coefficients - project_id: {project_id}, layer: {layer}")
        
        if project_id and coefficients:
            coefficients = coefficients.filter(project_id=project_id)
        if layer and coefficients:
            coefficients = coefficients.filter(layer=layer)
        
        # محاسبه آمار ضرایب
        total_coefficients = coefficients.count()
        excellent_coefficients = coefficients.filter(coefficient__gte=1.0).count()
        weak_coefficients = coefficients.filter(coefficient__lt=0.6).count()
        needs_review_coefficients = coefficients.filter(coefficient__gte=0.6, coefficient__lt=1.0).count()
        
        logger.info(f"Calculated statistics - Total: {total_coefficients}, Excellent: {excellent_coefficients}, Weak: {weak_coefficients}, Needs Review: {needs_review_coefficients}")
        
        context = {
            'coefficients': coefficients,
            'projects': projects,
            'layers': layers,
            'selected_project': project_id,
            'selected_layer': layer,
            'total_coefficients': total_coefficients,
            'excellent_coefficients': excellent_coefficients,
            'weak_coefficients': weak_coefficients,
            'needs_review_coefficients': needs_review_coefficients,
        }
        
        logger.info("Rendering payment_coefficient_list.html template with data")
        return render(request, 'experiment/payment_coefficient_list.html', context)
    except Exception as e:
        logger.error(f"Error in payment_coefficient_list: {str(e)}")
        return render(request, 'experiment/simple_test.html', {
            'message': f'Error: {str(e)}'
        })

@login_required
def payment_coefficient_update(request, pk):
    coefficient = get_object_or_404(models.PaymentCoefficient, pk=pk)
    if request.method == 'POST':
        form = forms.PaymentCoefficientForm(request.POST, instance=coefficient)
        if form.is_valid():
            form.save()
            messages.success(request, 'ضریب پرداخت با موفقیت بروزرسانی شد.')
            return redirect('experiment:payment_coefficient_list')
    else:
        form = forms.PaymentCoefficientForm(instance=coefficient)
    
    return render(request, 'experiment/payment_coefficient_form.html', {'form': form})

@login_required
def payment_coefficient_delete(request, pk):
    coefficient = get_object_or_404(models.PaymentCoefficient, pk=pk)
    if request.method == 'POST':
        coefficient.delete()
        messages.success(request, 'ضریب پرداخت با موفقیت حذف شد.')
        return redirect('experiment:payment_coefficient_list')
    
    return render(request, 'experiment/payment_coefficient_confirm_delete.html', {
        'coefficient': coefficient
    })

@login_required
def update_experiment_kilometers(request):
    """به‌روزرسانی کیلومتراژ آزمایشات به محدوده پروژه"""
    if not request.user.is_superuser:
        messages.error(request, 'شما دسترسی به این صفحه را ندارید.')
        return redirect('experiment:experiment_request_list')
    
    from project.models import Project
    from decimal import Decimal
    
    project_id = request.GET.get('project_id', 1)
    try:
        project = Project.objects.get(pk=project_id)
    except Project.DoesNotExist:
        messages.error(request, f'پروژه با ID {project_id} یافت نشد!')
        return redirect('experiment:experiment_request_list')
    
    # محاسبه محدوده کیلومتراژ پروژه
    project_start = float(project.start_kilometer) if project.start_kilometer else 0.0
    project_end = float(project.end_kilometer) if project.end_kilometer else project_start + 10.0
    project_range = project_end - project_start
    
    # پیدا کردن آزمایشات با کیلومتراژ خارج از محدوده
    old_experiments = models.ExperimentRequest.objects.filter(
        project=project
    ).filter(
        models.Q(start_kilometer__gte=1000) | 
        models.Q(start_kilometer__lt=project_start) | 
        models.Q(start_kilometer__gt=project_end)
    ).order_by('id')
    
    count = old_experiments.count()
    if count == 0:
        messages.info(request, 'هیچ آزمایشی با کیلومتراژ خارج از محدوده یافت نشد!')
        return redirect('experiment:experiment_request_list')
    
    # تقسیم محدوده پروژه به بخش‌های مساوی
    segment_size = project_range / (count + 1) if count > 0 else project_range
    
    updated_count = 0
    # به‌روزرسانی هر آزمایش
    for i, exp in enumerate(old_experiments, start=1):
        old_start = float(exp.start_kilometer)
        old_end = float(exp.end_kilometer)
        old_range = old_end - old_start if old_end > old_start else 1.0  # حداقل 1 کیلومتر
        
        # محاسبه کیلومتراژ جدید
        new_start = project_start + (i * segment_size)
        new_end = new_start + old_range  # حفظ طول بازه
        
        # اطمینان از اینکه در محدوده پروژه است
        if new_end > project_end:
            new_end = project_end
            new_start = max(project_start, new_end - old_range)
        
        # به‌روزرسانی در model اصلی
        exp.start_kilometer = Decimal(str(new_start))
        exp.end_kilometer = Decimal(str(new_end))
        exp.save()
        
        # به‌روزرسانی در formset (اگر وجود داشته باشد)
        from experiment.models import ExperimentRequestKilometer
        km_ranges = ExperimentRequestKilometer.objects.filter(experiment_request=exp)
        if km_ranges.exists():
            # حذف بازه‌های قدیمی
            km_ranges.delete()
            # ایجاد بازه جدید
            ExperimentRequestKilometer.objects.create(
                experiment_request=exp,
                start_kilometer=Decimal(str(new_start)),
                end_kilometer=Decimal(str(new_end))
            )
        
        updated_count += 1
    
    messages.success(request, f'{updated_count} آزمایش با موفقیت به‌روزرسانی شدند! (محدوده: {project_start:.3f} تا {project_end:.3f})')
    return redirect('experiment:experiment_request_list')

def dashboard_charts(request):
    """نمایش نمودارهای ضریب پرداخت با میانگین ضرایب پرداخت"""
    logger.info(f"Accessing dashboard_charts view by user: {request.user}")
    try:
        # محاسبه میانگین ضرایب پرداخت برای هر لایه
        asphalt_avg = models.PaymentCoefficient.objects.filter(layer='ASPHALT').aggregate(Avg('coefficient'))['coefficient__avg'] or 0
        base_avg = models.PaymentCoefficient.objects.filter(layer='BASE').aggregate(Avg('coefficient'))['coefficient__avg'] or 0
        subbase_avg = models.PaymentCoefficient.objects.filter(layer='SUBBASE').aggregate(Avg('coefficient'))['coefficient__avg'] or 0
        embankment_avg = models.PaymentCoefficient.objects.filter(layer='EMBANKMENT').aggregate(Avg('coefficient'))['coefficient__avg'] or 0
        
        # داده‌های نمودار توزیع
        coefficients = models.PaymentCoefficient.objects.all()
        distribution_labels = ['0.0-0.2', '0.2-0.4', '0.4-0.6', '0.6-0.8', '0.8-1.0', '1.0-1.2']
        distribution_data = []
        for i in range(6):
            start = i * 0.2
            end = (i + 1) * 0.2
            count = coefficients.filter(coefficient__gte=start, coefficient__lt=end).count()
            distribution_data.append(count)
        
        # داده‌های نمودار پروژه‌ها برای هر لایه
        projects = models.Project.objects.all()
        project_labels = [project.name for project in projects]
        
        # محاسبه میانگین ضرایب برای هر پروژه و هر لایه
        project_data_by_layer = {
            'ASPHALT': [],
            'BASE': [],
            'SUBBASE': [],
            'EMBANKMENT': []
        }
        
        for project in projects:
            # آسفالت گرم
            asphalt_coeff = project.paymentcoefficient_set.filter(layer='ASPHALT').aggregate(Avg('coefficient'))['coefficient__avg'] or 0
            project_data_by_layer['ASPHALT'].append(float(round(asphalt_coeff, 2)))
            
            # اساس
            base_coeff = project.paymentcoefficient_set.filter(layer='BASE').aggregate(Avg('coefficient'))['coefficient__avg'] or 0
            project_data_by_layer['BASE'].append(float(round(base_coeff, 2)))
            
            # زیراساس
            subbase_coeff = project.paymentcoefficient_set.filter(layer='SUBBASE').aggregate(Avg('coefficient'))['coefficient__avg'] or 0
            project_data_by_layer['SUBBASE'].append(float(round(subbase_coeff, 2)))
            
            # خاکریزی
            embankment_coeff = project.paymentcoefficient_set.filter(layer='EMBANKMENT').aggregate(Avg('coefficient'))['coefficient__avg'] or 0
            project_data_by_layer['EMBANKMENT'].append(float(round(embankment_coeff, 2)))
        
        logger.info(f"Calculated payment coefficients by layer and project")
        
        context = {
            'asphalt_avg': round(asphalt_avg, 2),
            'base_avg': round(base_avg, 2),
            'subbase_avg': round(subbase_avg, 2),
            'embankment_avg': round(embankment_avg, 2),
            'distribution_labels': distribution_labels,
            'distribution_data': distribution_data,
            'project_labels': project_labels,
            'project_data_by_layer': project_data_by_layer,
        }
        
        logger.info("Rendering dashboard_charts.html template")
        return render(request, 'experiment/dashboard_charts.html', context)
    except Exception as e:
        logger.error(f"Error in dashboard_charts: {str(e)}")
        messages.error(request, 'خطا در بارگذاری نمودارهای ضریب پرداخت')
        return render(request, 'experiment/dashboard_charts.html', {
            'asphalt_avg': 0,
            'base_avg': 0,
            'subbase_avg': 0,
            'embankment_avg': 0,
            'distribution_labels': [],
            'distribution_data': [],
            'project_labels': [],
            'project_data_by_layer': {
                'ASPHALT': [],
                'BASE': [],
                'SUBBASE': [],
                'EMBANKMENT': []
            },
        })

@login_required
def layer_coefficient_detail(request, layer):
    """نمایش جزئیات ضریب پرداخت برای یک لایه خاص"""
    logger.info(f"Accessing layer_coefficient_detail view for layer: {layer} by user: {request.user}")
    try:
        coefficients = models.PaymentCoefficient.objects.filter(layer=layer)
        layer_name = dict(models.PaymentCoefficient.LAYER_CHOICES).get(layer, layer)
        
        logger.info(f"Found {coefficients.count()} coefficients for layer {layer}")
        
        return render(request, 'experiment/layer_coefficient_detail.html', {
            'coefficients': coefficients,
            'layer_name': layer_name,
            'layer_code': layer
        })
    except Exception as e:
        logger.error(f"Error in layer_coefficient_detail: {str(e)}")
        messages.error(request, 'خطا در بارگذاری جزئیات لایه')
        return render(request, 'experiment/layer_coefficient_detail.html', {
            'coefficients': [],
            'layer_name': layer,
            'layer_code': layer
        })

def test_view(request):
    """ویو تست برای بررسی عملکرد"""
    from datetime import datetime
    logger.info(f"Test view accessed by user: {request.user}")
    return render(request, 'experiment/test_view.html', {
        'message': 'Test view is working!',
        'user': request.user,
        'now': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

def simple_test(request):
    """ویو تست ساده بدون لاگین"""
    return render(request, 'experiment/simple_test.html', {
        'message': 'Simple test is working!'
    })

@login_required
def experiment_type_list(request):
    """نمایش لیست انواع آزمایشات"""
    experiment_types = models.ExperimentType.objects.all()
    return render(request, 'experiment/experiment_type_list.html', {'experiment_types': experiment_types})

@login_required
def experiment_type_create(request):
    """ایجاد نوع آزمایش جدید"""
    if request.method == 'POST':
        form = forms.ExperimentTypeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'نوع آزمایش با موفقیت ایجاد شد.')
            return redirect('experiment:experiment_type_list')
    else:
        form = forms.ExperimentTypeForm()
    return render(request, 'experiment/experiment_type_form.html', {'form': form})

@login_required
def experiment_type_update(request, pk):
    """بروزرسانی نوع آزمایش"""
    experiment_type = get_object_or_404(models.ExperimentType, pk=pk)
    if request.method == 'POST':
        form = forms.ExperimentTypeForm(request.POST, instance=experiment_type)
        if form.is_valid():
            form.save()
            messages.success(request, 'نوع آزمایش با موفقیت بروزرسانی شد.')
            return redirect('experiment:experiment_type_list')
    else:
        form = forms.ExperimentTypeForm(instance=experiment_type)
    return render(request, 'experiment/experiment_type_form.html', {'form': form})

@login_required
def experiment_type_delete(request, pk):
    """حذف نوع آزمایش"""
    experiment_type = get_object_or_404(models.ExperimentType, pk=pk)
    if request.method == 'POST':
        experiment_type.delete()
        messages.success(request, 'نوع آزمایش با موفقیت حذف شد.')
        return redirect('experiment:experiment_type_list')
    return render(request, 'experiment/experiment_type_confirm_delete.html', {'experiment_type': experiment_type})

@login_required
def experiment_subtype_list(request):
    """نمایش لیست زیرگروه‌های آزمایش"""
    experiment_subtypes = models.ExperimentSubType.objects.all()
    return render(request, 'experiment/experiment_subtype_list.html', {'experiment_subtypes': experiment_subtypes})

@login_required
def experiment_subtype_create(request):
    """ایجاد زیرگروه آزمایش جدید"""
    if request.method == 'POST':
        form = forms.ExperimentSubTypeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'زیرگروه آزمایش با موفقیت ایجاد شد.')
            return redirect('experiment:experiment_subtype_list')
    else:
        form = forms.ExperimentSubTypeForm()
    return render(request, 'experiment/experiment_subtype_form.html', {'form': form})

@login_required
def experiment_subtype_update(request, pk):
    """بروزرسانی زیرگروه آزمایش"""
    experiment_subtype = get_object_or_404(models.ExperimentSubType, pk=pk)
    if request.method == 'POST':
        form = forms.ExperimentSubTypeForm(request.POST, instance=experiment_subtype)
        if form.is_valid():
            form.save()
            messages.success(request, 'زیرگروه آزمایش با موفقیت بروزرسانی شد.')
            return redirect('experiment:experiment_subtype_list')
    else:
        form = forms.ExperimentSubTypeForm(instance=experiment_subtype)
    return render(request, 'experiment/experiment_subtype_form.html', {'form': form})

@login_required
def experiment_subtype_delete(request, pk):
    """حذف زیرگروه آزمایش"""
    experiment_subtype = get_object_or_404(models.ExperimentSubType, pk=pk)
    if request.method == 'POST':
        experiment_subtype.delete()
        messages.success(request, 'زیرگروه آزمایش با موفقیت حذف شد.')
        return redirect('experiment:experiment_subtype_list')
    return render(request, 'experiment/experiment_subtype_confirm_delete.html', {'experiment_subtype': experiment_subtype})

@login_required
def concrete_place_list(request):
    """نمایش لیست محل‌های بتن‌ریزی"""
    concrete_places = models.ConcretePlace.objects.all()
    return render(request, 'experiment/concrete_place_list.html', {'concrete_places': concrete_places})

@login_required
def concrete_place_create(request):
    """ایجاد محل بتن‌ریزی جدید"""
    if request.method == 'POST':
        form = forms.ConcretePlaceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'محل بتن‌ریزی با موفقیت ایجاد شد.')
            return redirect('experiment:concrete_place_list')
    else:
        form = forms.ConcretePlaceForm()
    return render(request, 'experiment/concrete_place_form.html', {'form': form})

@login_required
def concrete_place_update(request, pk):
    """بروزرسانی محل بتن‌ریزی"""
    concrete_place = get_object_or_404(models.ConcretePlace, pk=pk)
    if request.method == 'POST':
        form = forms.ConcretePlaceForm(request.POST, instance=concrete_place)
        if form.is_valid():
            form.save()
            messages.success(request, 'محل بتن‌ریزی با موفقیت بروزرسانی شد.')
            return redirect('experiment:concrete_place_list')
    else:
        form = forms.ConcretePlaceForm(instance=concrete_place)
    return render(request, 'experiment/concrete_place_form.html', {'form': form})

@login_required
def concrete_place_delete(request, pk):
    """حذف محل بتن‌ریزی"""
    concrete_place = get_object_or_404(models.ConcretePlace, pk=pk)
    if request.method == 'POST':
        concrete_place.delete()
        messages.success(request, 'محل بتن‌ریزی با موفقیت حذف شد.')
        return redirect('experiment:concrete_place_list')
    return render(request, 'experiment/concrete_place_confirm_delete.html', {'concrete_place': concrete_place})

@login_required
def experiment_request_update(request, pk):
    """بروزرسانی درخواست آزمایش"""
    experiment_request = get_object_or_404(models.ExperimentRequest, pk=pk)
    if request.method == 'POST':
        form = forms.ExperimentRequestForm(request.POST, request.FILES, instance=experiment_request, user=request.user)
        kilometer_formset = ExperimentRequestKilometerFormSet(
            request.POST,
            prefix='kilometer',
            instance=experiment_request
        )
        file_formset = ExperimentRequestFileFormSet(
            request.POST,
            request.FILES,
            prefix='file',
            instance=experiment_request
        )
        if form.is_valid() and kilometer_formset.is_valid() and file_formset.is_valid():
            valid_ranges = []
            for km_form in kilometer_formset:
                if km_form.cleaned_data and not km_form.cleaned_data.get('DELETE', False):
                    start = km_form.cleaned_data.get('start_kilometer')
                    end = km_form.cleaned_data.get('end_kilometer')
                    if start is not None and end is not None:
                        valid_ranges.append((start, end))
            
            if not valid_ranges:
                kilometer_formset._non_form_errors = kilometer_formset.error_class(
                    ['حداقل یک بازه کیلومتراژ باید ثبت شود.']
                )
            else:
                decimal_ranges = [
                    (Decimal(str(rng[0])), Decimal(str(rng[1])))
                    for rng in valid_ranges
                ]
                project = form.cleaned_data.get('project')
                layer = form.cleaned_data.get('layer')
                
                # بررسی محدوده کیلومتراژ پروژه
                out_of_range = False
                if project:
                    project_start = float(project.start_kilometer) if project.start_kilometer else 0.0
                    project_end = float(project.end_kilometer) if project.end_kilometer else project_start + 10.0
                    
                    # بررسی اینکه آیا کیلومتراژها در محدوده پروژه هستند
                    for rng in decimal_ranges:
                        if rng[0] < project_start or rng[1] > project_end:
                            out_of_range = True
                            break
                    
                    if out_of_range:
                        kilometer_formset._non_form_errors = kilometer_formset.error_class(
                            [f'کیلومتراژ باید در محدوده پروژه باشد ({project_start:.3f} تا {project_end:.3f})']
                        )
                
                blocking_layers = []
                if project and layer and not out_of_range:
                    blocking_layers = find_blocking_lower_layers(project, layer, decimal_ranges)
                if blocking_layers:
                    names = [get_layer_display_name(blk) for blk in blocking_layers]
                    form.add_error(
                        None,
                        f'برای ثبت درخواست لایه انتخاب‌شده، ابتدا نتایج لایه‌های زیرین تایید شود: {"، ".join(names)}'
                    )
                elif not out_of_range:
                    experiment_request = form.save(commit=False)
                    start_values = [rng[0] for rng in decimal_ranges]
                    end_values = [rng[1] for rng in decimal_ranges]
                    experiment_request.start_kilometer = min(start_values)
                    experiment_request.end_kilometer = max(end_values)
                    experiment_request.save()
                    form.save_m2m()
                    kilometer_formset.instance = experiment_request
                    kilometer_formset.save()
                    file_formset.instance = experiment_request
                    file_formset.save()
                    messages.success(request, 'درخواست آزمایش با موفقیت بروزرسانی شد.')
                    return redirect('experiment:experiment_request_list')
    else:
        form = forms.ExperimentRequestForm(instance=experiment_request, user=request.user)
        kilometer_formset = ExperimentRequestKilometerFormSet(
            prefix='kilometer',
            instance=experiment_request
        )
        # اگر formset خالی است اما کیلومتراژ در model اصلی وجود دارد، آن را اضافه می‌کنیم
        if not kilometer_formset.forms and experiment_request.start_kilometer and experiment_request.end_kilometer:
            from experiment.models import ExperimentRequestKilometer
            # بررسی اینکه آیا قبلاً ExperimentRequestKilometer وجود دارد یا نه
            if not ExperimentRequestKilometer.objects.filter(experiment_request=experiment_request).exists():
                # ایجاد یک formset با یک فرم که از model اصلی پر شده
                ExperimentRequestKilometer.objects.create(
                    experiment_request=experiment_request,
                    start_kilometer=experiment_request.start_kilometer,
                    end_kilometer=experiment_request.end_kilometer
                )
                # دوباره formset را ایجاد می‌کنیم
                kilometer_formset = ExperimentRequestKilometerFormSet(
                    prefix='kilometer',
                    instance=experiment_request
                )
        file_formset = ExperimentRequestFileFormSet(
            prefix='file',
            instance=experiment_request
        )
    return render(request, 'experiment/experiment_request_form.html', {
        'form': form,
        'kilometer_formset': kilometer_formset,
        'file_formset': file_formset,
        'user': request.user,
    })

@login_required
def experiment_request_delete(request, pk):
    """حذف درخواست آزمایش"""
    experiment_request = get_object_or_404(models.ExperimentRequest, pk=pk)
    if request.method == 'POST':
        experiment_request.delete()
        messages.success(request, 'درخواست آزمایش با موفقیت حذف شد.')
        return redirect('experiment:experiment_request_list')
    return render(request, 'experiment/experiment_request_confirm_delete.html', {'experiment_request': experiment_request})

@login_required
def experiment_response_update(request, pk):
    """بروزرسانی پاسخ آزمایش"""
    experiment_response = get_object_or_404(models.ExperimentResponse, pk=pk)
    experiment_request = experiment_response.experiment_request
    
    if request.method == 'POST':
        form = forms.ExperimentResponseForm(request.POST, request.FILES, instance=experiment_response, experiment_request=experiment_request)
        kilometer_formset = ExperimentResponseKilometerFormSet(request.POST, prefix='kilometer', instance=experiment_response)
        file_formset = ExperimentResponseFileFormSet(request.POST, request.FILES, prefix='file', instance=experiment_response)
        if form.is_valid() and kilometer_formset.is_valid() and file_formset.is_valid():
            form.save()
            kilometer_formset.save()
            file_formset.save()
            messages.success(request, 'پاسخ آزمایش با موفقیت بروزرسانی شد.')
            return redirect('experiment:experiment_response_detail', pk=pk)
    else:
        form = forms.ExperimentResponseForm(instance=experiment_response, experiment_request=experiment_request)
        kilometer_formset = ExperimentResponseKilometerFormSet(prefix='kilometer', instance=experiment_response)
        file_formset = ExperimentResponseFileFormSet(prefix='file', instance=experiment_response)
    
    # آماده‌سازی context مشابه experiment_response_create
    layer_display_name = experiment_request.layer.layer_type.name
    siblings = experiment_request.project.projectlayer_set.filter(
        layer_type=experiment_request.layer.layer_type
    ).order_by('order_from_top')
    if siblings.count() > 1:
        layer_list = list(siblings)
        try:
            index = layer_list.index(experiment_request.layer) + 1
            layer_display_name = f"{layer_display_name} {index}"
        except ValueError:
            pass
    
    context = {
        'form': form,
        'kilometer_formset': kilometer_formset,
        'file_formset': file_formset,
        'asphalt_formset': asphalt_formset,
        'is_asphalt': is_asphalt,
        'experiment_request': experiment_request,
        'project': experiment_request.project,
        'layer': experiment_request.layer,
        'layer_display_name': layer_display_name,
        'experiment_types': experiment_request.experiment_type.all(),
        'experiment_subtypes': experiment_request.experiment_subtype.all(),
        'request_files': experiment_request.files.all(),
        'kilometer_ranges': experiment_request.kilometer_ranges.all(),
        'request_user': experiment_request.user,
        'response_user': request.user,
    }
    return render(request, 'experiment/experiment_response_form.html', context)

@login_required
def experiment_response_delete(request, pk):
    """حذف پاسخ آزمایش"""
    experiment_response = get_object_or_404(models.ExperimentResponse, pk=pk)
    if request.method == 'POST':
        experiment_response.delete()
        messages.success(request, 'پاسخ آزمایش با موفقیت حذف شد.')
        return redirect('experiment:experiment_response_list')
    return render(request, 'experiment/experiment_response_confirm_delete.html', {'experiment_response': experiment_response})

@login_required
def experiment_response_list(request):
    """نمایش لیست پاسخ‌های آزمایش"""
    experiment_responses = models.ExperimentResponse.objects.all()
    return render(request, 'experiment/experiment_response_list.html', {'experiment_responses': experiment_responses})

@login_required
def experiment_response_detail(request, pk):
    """نمایش جزئیات پاسخ آزمایش"""
    experiment_response = get_object_or_404(models.ExperimentResponse, pk=pk)
    return render(request, 'experiment/experiment_response_detail.html', {
        'experiment_response': experiment_response,
        'user': request.user
    })

@login_required
def experiment_approval_delete(request, pk):
    """حذف تاییدیه"""
    approval = get_object_or_404(models.ExperimentApproval, pk=pk)
    experiment_response = approval.experiment_response
    
    # بررسی اینکه آیا کاربر مجاز به حذف است
    if approval.approver != request.user and not request.user.is_superuser:
        messages.error(request, 'شما مجاز به حذف این تاییدیه نیستید.')
        return redirect('experiment:experiment_response_detail', pk=experiment_response.pk)
    
    if request.method == 'POST':
        approval.delete()
        messages.success(request, 'تاییدیه با موفقیت حذف شد.')
        return redirect('experiment:experiment_response_detail', pk=experiment_response.pk)
    
    return render(request, 'experiment/experiment_approval_confirm_delete.html', {
        'approval': approval,
        'experiment_response': experiment_response
    })

@login_required
@require_http_methods(["GET"])
def get_layers(request):
    """API برای دریافت لایه‌های پروژه"""
    project_id = request.GET.get('project_id')
    if project_id:
        layers = ProjectLayer.objects.filter(project_id=project_id).order_by('order_from_top')
        name_counts = {}
        for layer in layers:
            name = layer.layer_type.name
            name_counts[name] = name_counts.get(name, 0) + 1

        indices = {name: 0 for name in name_counts}
        data = []
        for layer in layers:
            name = layer.layer_type.name
            if name_counts[name] > 1:
                indices[name] += 1
                display_name = f"{name} {indices[name]}"
            else:
                display_name = name
            data.append({'id': layer.id, 'name': display_name})
        return JsonResponse({'layers': data})
    return JsonResponse({'layers': []})

@login_required
@require_http_methods(["GET"])
def get_subtypes(request):
    """API برای دریافت زیرنوع‌های آزمایش (پشتیبانی از چندتایی)"""
    experiment_type_ids = request.GET.getlist('experiment_type_id[]') or request.GET.getlist('experiment_type_id')
    if not experiment_type_ids:
        # اگر فقط یک مقدار به صورت رشته آمده باشد
        single_id = request.GET.get('experiment_type_id')
        if single_id:
            experiment_type_ids = [single_id]
    if experiment_type_ids:
        subtypes = models.ExperimentSubType.objects.filter(experiment_type_id__in=experiment_type_ids).distinct()
        data = [{'id': subtype.id, 'name': subtype.name} for subtype in subtypes]
        return JsonResponse({'subtypes': data})
    return JsonResponse({'subtypes': []})

@login_required
def get_project_layers(request):
    """دریافت لایه‌های پروژه برای AJAX"""
    project_id = request.GET.get('project_id')
    if project_id:
        layers = ProjectLayer.objects.filter(project_id=project_id)
        data = [{'id': layer.id, 'name': layer.name} for layer in layers]
        return JsonResponse({'layers': data})
    return JsonResponse({'layers': []})

@login_required
def get_experiment_types(request):
    """دریافت انواع آزمایش برای AJAX"""
    experiment_types = models.ExperimentType.objects.all()
    data = [{'id': exp_type.id, 'name': exp_type.name} for exp_type in experiment_types]
    return JsonResponse({'experiment_types': data})

@login_required
def get_experiment_subtypes(request):
    """دریافت زیرنوع‌های آزمایش برای AJAX"""
    experiment_type_id = request.GET.get('experiment_type_id')
    if experiment_type_id:
        subtypes = models.ExperimentSubType.objects.filter(experiment_type_id=experiment_type_id)
        data = [{'id': subtype.id, 'name': subtype.name} for subtype in subtypes]
        return JsonResponse({'subtypes': data})
    return JsonResponse({'subtypes': []})

@login_required
def get_concrete_places(request):
    """دریافت محل‌های بتن‌ریزی برای AJAX"""
    concrete_places = models.ConcretePlace.objects.all()
    data = [{'id': place.id, 'name': place.name} for place in concrete_places]
    return JsonResponse({'concrete_places': data})

@login_required
def asphalt_test_create(request, response_id):
    """ایجاد آزمایش آسفالت"""
    experiment_response = get_object_or_404(models.ExperimentResponse, pk=response_id)
    if request.method == 'POST':
        form = forms.AsphaltTestForm(request.POST)
        if form.is_valid():
            asphalt_test = form.save(commit=False)
            asphalt_test.experiment_response = experiment_response
            asphalt_test.save()
            messages.success(request, 'آزمایش آسفالت با موفقیت ثبت شد.')
            return redirect('experiment:experiment_response_detail', pk=response_id)
    else:
        form = forms.AsphaltTestForm()
    
    return render(request, 'experiment/asphalt_test_form.html', {
        'form': form,
        'experiment_response': experiment_response
    })

@login_required
def notification_list(request):
    """نمایش لیست اعلان‌ها"""
    notifications = models.Notification.objects.filter(user=request.user)
    return render(request, 'experiment/notification_list.html', {'notifications': notifications})

@login_required
def notification_mark_read(request, notification_id):
    """علامت‌گذاری اعلان به عنوان خوانده شده"""
    notification = get_object_or_404(models.Notification, pk=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    return JsonResponse({'status': 'success'})