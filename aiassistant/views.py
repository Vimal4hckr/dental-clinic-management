from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from clinic.models import Service

from . import engine


def symptom_checker(request):
    result = None
    symptoms = ''
    if request.method == 'POST':
        symptoms = request.POST.get('symptoms', '')
        result = engine.symptom_triage(symptoms)
    return render(request, 'aiassistant/symptom_checker.html',
                  {'result': result, 'symptoms': symptoms})


def chatbot(request):
    return render(request, 'aiassistant/chatbot.html')


@require_POST
def chatbot_api(request):
    message = request.POST.get('message', '')
    reply = engine.chatbot_response(message)
    return JsonResponse({'reply': reply})


def cost_estimator(request):
    result = None
    services = Service.objects.filter(is_active=True)
    selected = None
    if request.method == 'POST':
        try:
            service = Service.objects.get(pk=request.POST.get('service'))
        except (Service.DoesNotExist, ValueError):
            service = None
        selected = service.id if service else None
        base = service.price if service else request.POST.get('base_price', 0)
        complexity = request.POST.get('complexity', 'simple')
        teeth = request.POST.get('teeth', 1)
        insurance = request.POST.get('insurance') == 'on'
        result = engine.estimate_cost(base, complexity, teeth, insurance)
        result['service'] = service
    return render(request, 'aiassistant/cost_estimator.html',
                  {'result': result, 'services': services, 'selected': selected})


@login_required
def hub(request):
    """Landing page linking all AI tools."""
    return render(request, 'aiassistant/hub.html')
