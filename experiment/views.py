from django.shortcuts import render, redirect, get_object_or_404
from django.views import generic
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from . import models, forms
from project.models import ProjectLayer

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
    template_name = 'experiment/experiment-response-form.html'
    success_url = reverse_lazy('experiment:experiment-request-list')

    def get_initial(self):
        initial = super().get_initial()
        experiment_request_id = self.kwargs.get('pk')
        if experiment_request_id:
            initial['experiment_request'] = get_object_or_404(models.ExperimentRequest, pk=experiment_request_id)
        return initial

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
def get_layers(request):
    project_id = request.GET.get('project')
    if project_id:
        layers = ProjectLayer.objects.filter(project_id=project_id).select_related('layer_type')
        data = [{'id': layer.id, 'name': layer.layer_type.name} for layer in layers]
        return JsonResponse(data, safe=False)
    return JsonResponse([], safe=False)

@login_required
def get_subtypes(request):
    experiment_type_id = request.GET.get('experiment_type')
    print(f"Received experiment_type_id: {experiment_type_id}")
    
    if experiment_type_id:
        try:
            subtypes = models.ExperimentSubType.objects.filter(experiment_type_id=experiment_type_id)
            print(f"Found {subtypes.count()} subtypes")
            data = [{'id': subtype.id, 'name': subtype.name} for subtype in subtypes]
            print(f"Returning data: {data}")
            return JsonResponse(data, safe=False)
        except Exception as e:
            print(f"Error in get_subtypes: {str(e)}")
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse([], safe=False)

@login_required
def experiment_request_list(request):
    """نمایش لیست درخواست‌های آزمایش"""
    # دریافت پارامترهای فیلتر
    project_id = request.GET.get('project')
    status = request.GET.get('status')
    search_query = request.GET.get('search')

    # شروع با تمام درخواست‌ها
    experiment_requests = models.ExperimentRequest.objects.all()

    # اعمال فیلتر پروژه
    if project_id:
        experiment_requests = experiment_requests.filter(project_id=project_id)

    # اعمال فیلتر وضعیت
    if status:
        try:
            status = int(status)
            experiment_requests = experiment_requests.filter(status=status)
        except (ValueError, TypeError):
            pass

    # اعمال جستجو در توضیحات
    if search_query:
        experiment_requests = experiment_requests.filter(description__icontains=search_query)

    # مرتب‌سازی بر اساس تاریخ درخواست (نزولی)
    experiment_requests = experiment_requests.order_by('-request_date')

    # دریافت لیست پروژه‌ها برای فیلتر
    projects = models.Project.objects.all()

    context = {
        'experiment_requests': experiment_requests,
        'projects': projects,
    }
    return render(request, 'experiment/experiment_request_list.html', context)

@login_required
def experiment_request_create(request):
    if request.method == 'POST':
        form = forms.ExperimentRequestForm(request.POST, request.FILES)
        if form.is_valid():
            experiment_request = form.save(commit=False)
            experiment_request.user = request.user
            experiment_request.save()
            return redirect('experiment:experiment_request_list')
    else:
        form = forms.ExperimentRequestForm()
    return render(request, 'experiment/experiment_request_form.html', {'form': form})

@login_required
def experiment_request_detail(request, pk):
    experiment_request = get_object_or_404(models.ExperimentRequest, pk=pk)
    return render(request, 'experiment/experiment_request_detail.html', {'request': experiment_request})

@login_required
def experiment_response_create(request, pk):
    experiment_request = get_object_or_404(models.ExperimentRequest, pk=pk)
    if request.method == 'POST':
        form = forms.ExperimentResponseForm(request.POST, request.FILES)
        if form.is_valid():
            response = form.save(commit=False)
            response.experiment_request = experiment_request
            response.responder = request.user
            response.save()
            return redirect('experiment:experiment_request_list')
    else:
        form = forms.ExperimentResponseForm()
    return render(request, 'experiment/experiment_response_form.html', {'form': form, 'request': experiment_request})

@login_required
def experiment_approval_create(request, pk):
    experiment_request = get_object_or_404(models.ExperimentRequest, pk=pk)
    if request.method == 'POST':
        form = forms.ExperimentApprovalForm(request.POST)
        if form.is_valid():
            approval = form.save(commit=False)
            approval.experiment_request = experiment_request
            approval.approver = request.user
            approval.save()
            return redirect('experiment:experiment_request_list')
    else:
        form = forms.ExperimentApprovalForm()
    return render(request, 'experiment/experiment_approval_form.html', {'form': form, 'request': experiment_request})
