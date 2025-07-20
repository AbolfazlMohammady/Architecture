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
        project_id = self.request.GET.get('project')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['projects'] = models.Project.objects.all()
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

class ExperimentResponseCreateView(LoginRequiredMixin, generic.CreateView):
    model = models.ExperimentResponse
    form_class = forms.ExperimentResponseForm
    template_name = 'experiment/experiment_response_form.html'
    success_url = reverse_lazy('experiment:experiment_request_list')

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
    experiment_requests = models.ExperimentRequest.objects.all()
    projects = models.Project.objects.all()
    
    # فیلتر بر اساس پروژه
    project_id = request.GET.get('project')
    if project_id:
        experiment_requests = experiment_requests.filter(project_id=project_id)
    
    # فیلتر بر اساس وضعیت
    status = request.GET.get('status')
    if status:
        experiment_requests = experiment_requests.filter(status=status)
    
    # فیلتر بر اساس جستجو
    search = request.GET.get('search')
    if search and search.strip() and search != 'None':
        experiment_requests = experiment_requests.filter(
            Q(description__icontains=search) | Q(project__name__icontains=search)
        )
    
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
        if form.is_valid():
            experiment_request = form.save(commit=False)
            experiment_request.user = request.user
            experiment_request.save()
            
            # ایجاد اعلان برای مدیر کنترل کیفیت
            if experiment_request.project.quality_control_manager:
                models.Notification.objects.create(
                    user=experiment_request.project.quality_control_manager,
                    experiment_request=experiment_request,
                    message=f'یک درخواست آزمایش جدید از {request.user.get_full_name()} برای شما ارسال شده است.'
                )
            
            messages.success(request, 'درخواست آزمایش با موفقیت ثبت شد.')
            return redirect('experiment:experiment_request_list')
    else:
        form = forms.ExperimentRequestForm(user=request.user)
    
    return render(request, 'experiment/experiment_request_form.html', {'form': form})

@login_required
def experiment_request_edit(request, pk):
    experiment_request = get_object_or_404(models.ExperimentRequest, pk=pk)
    if request.method == 'POST':
        form = forms.ExperimentRequestForm(request.POST, request.FILES, instance=experiment_request)
        if form.is_valid():
            form.save()
            return redirect('experiment:experiment_request_list')
    else:
        form = forms.ExperimentRequestForm(instance=experiment_request)
    
    return render(request, 'experiment/experiment_request_form.html', {
        'form': form
    })

@login_required
def experiment_request_detail(request, pk):
    experiment_request = get_object_or_404(models.ExperimentRequest, pk=pk)
    experiment_responses = models.ExperimentResponse.objects.filter(experiment_request=experiment_request)
    return render(request, 'experiment/experiment_request_detail.html', {
        'experiment_request': experiment_request,
        'experiment_responses': experiment_responses
    })

@login_required
def experiment_response_create(request, pk):
    experiment_request = get_object_or_404(models.ExperimentRequest, pk=pk)
    if request.method == 'POST':
        form = forms.ExperimentResponseForm(request.POST, request.FILES)
        if form.is_valid():
            experiment_response = form.save(commit=False)
            experiment_response.experiment_request = experiment_request
            experiment_response.user = self.request.user
            experiment_response.save()
            
            # ایجاد اعلان برای درخواست کننده
            models.Notification.objects.create(
                user=experiment_request.user,
                experiment_request=experiment_request,
                message=f'پاسخ آزمایش شما برای پروژه {experiment_request.project.name} ثبت شد.'
            )
            
            messages.success(request, 'پاسخ آزمایش با موفقیت ثبت شد.')
            return redirect('experiment:experiment_response_detail', pk=experiment_response.pk)
    else:
        form = forms.ExperimentResponseForm()
    return render(request, 'experiment/experiment_response_form.html', {
        'form': form,
        'experiment_request': experiment_request
    })

@login_required
def experiment_approval_create(request, response_id):
    experiment_response = get_object_or_404(models.ExperimentResponse, pk=response_id)
    if request.method == 'POST':
        form = forms.ExperimentApprovalForm(request.POST)
        if form.is_valid():
            approval = form.save(commit=False)
            approval.experiment_response = experiment_response
            approval.approver = request.user
            approval.save()
            
            # ایجاد اعلان برای کاربران مرتبط
            status_text = "تایید شد" if approval.status == models.ExperimentApproval.APPROVED else "رد شد"
            models.Notification.objects.create(
                user=experiment_response.experiment_request.user,
                experiment_request=experiment_response.experiment_request,
                message=f'پاسخ آزمایش شما توسط {request.user.get_full_name()} {status_text}.'
            )
            
            # اعلان برای مدیر کنترل کیفیت
            if experiment_response.experiment_request.project.quality_control_manager:
                models.Notification.objects.create(
                    user=experiment_response.experiment_request.project.quality_control_manager,
                    experiment_request=experiment_response.experiment_request,
                    message=f'پاسخ آزمایش برای پروژه {experiment_response.experiment_request.project.name} {status_text}.'
            )
            
            messages.success(request, 'تایید آزمایش با موفقیت ثبت شد.')
            return redirect('experiment:experiment_response_detail', pk=response_id)
    else:
        form = forms.ExperimentApprovalForm()
    return render(request, 'experiment/experiment_approval_form.html', {
        'form': form,
        'experiment_response': experiment_response
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

def dashboard_charts(request):
    """نمایش نمودارهای داشبورد با میانگین ضرایب پرداخت"""
    logger.info(f"Accessing dashboard_charts view by user: {request.user}")
    try:
        # محاسبه آمار کلی
        coefficients = models.PaymentCoefficient.objects.all()
        total_coefficients = coefficients.count()
        
        if total_coefficients > 0:
            average_coefficient = coefficients.aggregate(Avg('coefficient'))['coefficient__avg']
            best_coefficient = coefficients.aggregate(Max('coefficient'))['coefficient__max']
            worst_coefficient = coefficients.aggregate(Min('coefficient'))['coefficient__min']
        else:
            average_coefficient = 0
            best_coefficient = 0
            worst_coefficient = 0
        
        # محاسبه میانگین ضرایب پرداخت برای هر لایه
        asphalt_avg = models.PaymentCoefficient.objects.filter(layer='ASPHALT').aggregate(Avg('coefficient'))['coefficient__avg'] or 0
        base_avg = models.PaymentCoefficient.objects.filter(layer='BASE').aggregate(Avg('coefficient'))['coefficient__avg'] or 0
        subbase_avg = models.PaymentCoefficient.objects.filter(layer='SUBBASE').aggregate(Avg('coefficient'))['coefficient__avg'] or 0
        embankment_avg = models.PaymentCoefficient.objects.filter(layer='EMBANKMENT').aggregate(Avg('coefficient'))['coefficient__avg'] or 0
        
        # داده‌های نمودار توزیع
        distribution_labels = ['0.0-0.2', '0.2-0.4', '0.4-0.6', '0.6-0.8', '0.8-1.0', '1.0-1.2']
        distribution_data = []
        for i in range(6):
            start = i * 0.2
            end = (i + 1) * 0.2
            count = coefficients.filter(coefficient__gte=start, coefficient__lt=end).count()
            distribution_data.append(count)
        
        # داده‌های نمودار پروژه‌ها
        projects = models.Project.objects.all()
        project_labels = [project.name for project in projects]
        project_data = []
        for project in projects:
            avg = project.paymentcoefficient_set.aggregate(Avg('coefficient'))['coefficient__avg'] or 0
            project_data.append(round(avg, 2))
        
        # داده‌های نمودار لایه‌ها
        layer_labels = ['آسفالت گرم', 'اساس', 'زیراساس', 'خاکریزی']
        layer_data = [asphalt_avg, base_avg, subbase_avg, embankment_avg]
        
        logger.info(f"Calculated statistics - Total: {total_coefficients}, Avg: {average_coefficient}, Best: {best_coefficient}, Worst: {worst_coefficient}")
        
        context = {
            'total_coefficients': total_coefficients,
            'average_coefficient': round(average_coefficient, 2),
            'best_coefficient': round(best_coefficient, 2),
            'worst_coefficient': round(worst_coefficient, 2),
            'asphalt_avg': round(asphalt_avg, 2),
            'base_avg': round(base_avg, 2),
            'subbase_avg': round(subbase_avg, 2),
            'embankment_avg': round(embankment_avg, 2),
            'distribution_labels': distribution_labels,
            'distribution_data': distribution_data,
            'project_labels': project_labels,
            'project_data': project_data,
            'layer_labels': layer_labels,
            'layer_data': layer_data,
        }
        
        logger.info("Rendering dashboard_charts.html template")
        return render(request, 'experiment/dashboard_charts.html', context)
    except Exception as e:
        logger.error(f"Error in dashboard_charts: {str(e)}")
        messages.error(request, 'خطا در بارگذاری نمودارهای داشبورد')
        return render(request, 'experiment/dashboard_charts.html', {
            'total_coefficients': 0,
            'average_coefficient': 0,
            'best_coefficient': 0,
            'worst_coefficient': 0,
            'asphalt_avg': 0,
            'base_avg': 0,
            'subbase_avg': 0,
            'embankment_avg': 0,
            'distribution_labels': [],
            'distribution_data': [],
            'project_labels': [],
            'project_data': [],
            'layer_labels': [],
            'layer_data': [],
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
        if form.is_valid():
            form.save()
            messages.success(request, 'درخواست آزمایش با موفقیت بروزرسانی شد.')
            return redirect('experiment:experiment_request_list')
    else:
        form = forms.ExperimentRequestForm(instance=experiment_request, user=request.user)
    return render(request, 'experiment/experiment_request_form.html', {'form': form})

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
    if request.method == 'POST':
        form = forms.ExperimentResponseForm(request.POST, request.FILES, instance=experiment_response)
        if form.is_valid():
            form.save()
            messages.success(request, 'پاسخ آزمایش با موفقیت بروزرسانی شد.')
            return redirect('experiment:experiment_response_detail', pk=pk)
    else:
        form = forms.ExperimentResponseForm(instance=experiment_response)
    return render(request, 'experiment/experiment_response_form.html', {'form': form})

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
    return render(request, 'experiment/experiment_response_detail.html', {'experiment_response': experiment_response})

@login_required
@require_http_methods(["GET"])
def get_layers(request):
    """API برای دریافت لایه‌های پروژه"""
    project_id = request.GET.get('project_id')
    if project_id:
        layers = ProjectLayer.objects.filter(project_id=project_id)
        data = [{'id': layer.id, 'name': layer.name} for layer in layers]
        return JsonResponse({'layers': data})
    return JsonResponse({'layers': []})

@login_required
@require_http_methods(["GET"])
def get_subtypes(request):
    """API برای دریافت زیرنوع‌های آزمایش"""
    experiment_type_id = request.GET.get('experiment_type_id')
    if experiment_type_id:
        subtypes = models.ExperimentSubType.objects.filter(experiment_type_id=experiment_type_id)
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