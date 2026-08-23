from django.shortcuts import render

from clinic.models import Review, Service


def home(request):
    return render(request, 'pages/home.html', {
        'services': Service.objects.filter(is_active=True)[:6],
        'reviews': Review.objects.filter(is_public=True).select_related('patient')[:6],
    })


def about(request):
    return render(request, 'pages/about.html')


def services(request):
    return render(request, 'pages/services.html', {
        'services': Service.objects.filter(is_active=True),
    })


def contact(request):
    sent = False
    if request.method == 'POST':
        # Demo only: no email backend configured.
        sent = True
    return render(request, 'pages/contact.html', {'sent': sent})
