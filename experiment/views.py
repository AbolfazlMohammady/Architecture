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
def experiment_request_list(request):
    experiment_requests = models.ExperimentRequest.objects.all()
    return render(request, 'experiment/experiment_request_list.html', {
        'experiment_requests': experiment_requests
    })

@login_required
def experiment_request_create(request):
    if request.method == 'POST':
        form = forms.ExperimentRequestForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('experiment:experiment_request_list')
    else:
        form = forms.ExperimentRequestForm()
    
    return render(request, 'experiment/experiment_request_form.html', {
        'form': form
    })

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
    return render(request, 'experiment/experiment_request_detail.html', {
        'experiment_request': experiment_request
    })

@login_required
def experiment_response_create(request, pk):
    """ایجاد پاسخ آزمایش"""
    experiment_request = get_object_or_404(models.ExperimentRequest, pk=pk)
    if request.method == 'POST':
        form = forms.ExperimentResponseForm(request.POST, request.FILES)
        if form.is_valid():
            experiment_response = form.save(commit=False)
            experiment_response.experiment_request = experiment_request
            experiment_response.save()
            messages.success(request, 'پاسخ آزمایش با موفقیت ثبت شد.')
            return redirect('experiment:experiment_response_detail', pk=experiment_response.pk)
    else:
        form = forms.ExperimentResponseForm()
    return render(request, 'experiment/experiment_response_form.html', {'form': form, 'experiment_request': experiment_request})

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
    """ویرایش نوع آزمایش"""
    experiment_type = get_object_or_404(models.ExperimentType, pk=pk)
    if request.method == 'POST':
        form = forms.ExperimentTypeForm(request.POST, instance=experiment_type)
        if form.is_valid():
            form.save()
            messages.success(request, 'نوع آزمایش با موفقیت ویرایش شد.')
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
    return render(request, 'experiment/experiment_type_confirm_delete.html', {'object': experiment_type})

@login_required
def experiment_subtype_list(request):
    """لیست زیرگروه‌های آزمایش"""
    subtypes = models.ExperimentSubType.objects.all().order_by('experiment_type__name', 'name')
    return render(request, 'experiment/experiment_subtype_list.html', {'subtypes': subtypes})

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
    """ویرایش زیرگروه آزمایش"""
    subtype = get_object_or_404(models.ExperimentSubType, pk=pk)
    if request.method == 'POST':
        form = forms.ExperimentSubTypeForm(request.POST, instance=subtype)
        if form.is_valid():
            form.save()
            messages.success(request, 'زیرگروه آزمایش با موفقیت ویرایش شد.')
            return redirect('experiment:experiment_subtype_list')
    else:
        form = forms.ExperimentSubTypeForm(instance=subtype)
    return render(request, 'experiment/experiment_subtype_form.html', {'form': form})

@login_required
def experiment_subtype_delete(request, pk):
    """حذف زیرگروه آزمایش"""
    subtype = get_object_or_404(models.ExperimentSubType, pk=pk)
    if request.method == 'POST':
        subtype.delete()
        messages.success(request, 'زیرگروه آزمایش با موفقیت حذف شد.')
        return redirect('experiment:experiment_subtype_list')
    return render(request, 'experiment/experiment_subtype_confirm_delete.html', {'object': subtype})

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
    """ویرایش محل بتن‌ریزی"""
    concrete_place = get_object_or_404(models.ConcretePlace, pk=pk)
    if request.method == 'POST':
        form = forms.ConcretePlaceForm(request.POST, instance=concrete_place)
        if form.is_valid():
            form.save()
            messages.success(request, 'محل بتن‌ریزی با موفقیت ویرایش شد.')
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
    return render(request, 'experiment/concrete_place_confirm_delete.html', {'object': concrete_place})

@login_required
def experiment_request_update(request, pk):
    """ویرایش درخواست آزمایش"""
    experiment_request = get_object_or_404(models.ExperimentRequest, pk=pk)
    if request.method == 'POST':
        form = forms.ExperimentRequestForm(request.POST, request.FILES, instance=experiment_request)
        if form.is_valid():
            form.save()
            messages.success(request, 'درخواست آزمایش با موفقیت ویرایش شد.')
            return redirect('experiment:experiment_request_detail', pk=experiment_request.pk)
    else:
        form = forms.ExperimentRequestForm(instance=experiment_request)
    return render(request, 'experiment/experiment_request_form.html', {'form': form})

@login_required
def experiment_request_delete(request, pk):
    """حذف درخواست آزمایش"""
    experiment_request = get_object_or_404(models.ExperimentRequest, pk=pk)
    if request.method == 'POST':
        experiment_request.delete()
        messages.success(request, 'درخواست آزمایش با موفقیت حذف شد.')
        return redirect('experiment:experiment_request_list')
    return render(request, 'experiment/experiment_request_confirm_delete.html', {'object': experiment_request})

@login_required
def experiment_response_update(request, pk):
    """ویرایش پاسخ آزمایش"""
    experiment_response = get_object_or_404(models.ExperimentResponse, pk=pk)
    if request.method == 'POST':
        form = forms.ExperimentResponseForm(request.POST, request.FILES, instance=experiment_response)
        if form.is_valid():
            form.save()
            messages.success(request, 'پاسخ آزمایش با موفقیت ویرایش شد.')
            return redirect('experiment:experiment_response_detail', pk=experiment_response.pk)
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
    return render(request, 'experiment/experiment_response_confirm_delete.html', {'object': experiment_response})

@login_required
def experiment_response_list(request):
    """لیست پاسخ‌های آزمایش"""
    responses = models.ExperimentResponse.objects.all().order_by('-response_date')
    return render(request, 'experiment/experiment_response_list.html', {'responses': responses})

@login_required
def experiment_response_detail(request, pk):
    """جزئیات پاسخ آزمایش"""
    response = get_object_or_404(models.ExperimentResponse, pk=pk)
    return render(request, 'experiment/experiment_response_detail.html', {'response': response})

@login_required
@require_http_methods(["GET"])
def get_layers(request):
    project_id = request.GET.get('project_id')
    if not project_id:
        return JsonResponse({'error': 'Project ID is required'}, status=400)
    
    try:
        project = models.Project.objects.get(pk=project_id)
        layers = project.projectlayer_set.all()
        data = [{'id': layer.id, 'name': layer.layer_type.name} for layer in layers]
        return JsonResponse(data, safe=False)
    except models.Project.DoesNotExist:
        return JsonResponse({'error': 'Project not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_http_methods(["GET"])
def get_subtypes(request):
    experiment_type_id = request.GET.get('experiment_type_id')
    if not experiment_type_id:
        return JsonResponse({'error': 'Experiment Type ID is required'}, status=400)
    
    try:
        experiment_type = models.ExperimentType.objects.get(pk=experiment_type_id)
        subtypes = experiment_type.experimentsubtype_set.all()
        data = [{'id': subtype.id, 'name': subtype.name} for subtype in subtypes]
        return JsonResponse(data, safe=False)
    except models.ExperimentType.DoesNotExist:
        return JsonResponse({'error': 'Experiment Type not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def get_project_layers(request):
    """دریافت لیست لایه‌های پروژه برای بارگذاری پویا"""
    try:
        project_id = request.GET.get('project')
        if not project_id:
            return JsonResponse({'error': 'Project ID is required'}, status=400)
            
        layers = ProjectLayer.objects.filter(project_id=project_id).order_by('name')
        data = [{'id': layer.id, 'name': layer.name} for layer in layers]
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
def get_experiment_types(request):
    """دریافت لیست انواع آزمایش برای بارگذاری پویا"""
    try:
        experiment_types = models.ExperimentType.objects.all().order_by('name')
        data = [{'id': et.id, 'name': et.name} for et in experiment_types]
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
def get_experiment_subtypes(request):
    """دریافت لیست زیرگروه‌های آزمایش برای بارگذاری پویا"""
    try:
        experiment_type_id = request.GET.get('experiment_type')
        if not experiment_type_id:
            return JsonResponse({'error': 'Experiment Type ID is required'}, status=400)
            
        subtypes = models.ExperimentSubType.objects.filter(experiment_type_id=experiment_type_id).order_by('name')
        data = [{'id': st.id, 'name': st.name} for st in subtypes]
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
def get_concrete_places(request):
    """دریافت لیست محل‌های بتن‌ریزی برای بارگذاری پویا"""
    try:
        places = models.ConcretePlace.objects.all().order_by('name')
        data = [{'id': p.id, 'name': p.name} for p in places]
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
