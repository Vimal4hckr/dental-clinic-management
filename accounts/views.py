from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render

from .forms import LoginForm, ProfileForm, SignUpForm
from .models import Role


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:redirect_dashboard')
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome to DentaCare, {user.first_name}! Your patient account is ready.')
            return redirect('accounts:redirect_dashboard')
    else:
        form = SignUpForm()
    return render(request, 'accounts/signup.html', {'form': form})


class AppLoginView(LoginView):
    template_name = 'accounts/login.html'
    authentication_form = LoginForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        messages.success(self.request, f'Welcome back, {form.get_user().display_name}!')
        return super().form_valid(form)


@login_required
def redirect_dashboard(request):
    """Send each user to the dashboard that matches their role."""
    role = request.user.role
    if request.user.is_superuser or role == Role.ADMIN:
        return redirect('manage_panel:dashboard')
    if role == Role.DENTIST:
        return redirect('clinic:dentist_dashboard')
    if role == Role.RECEPTIONIST:
        return redirect('clinic:receptionist_dashboard')
    return redirect('clinic:patient_dashboard')


@login_required
def profile_view(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated.')
            return redirect('accounts:profile')
    else:
        form = ProfileForm(instance=request.user)
    return render(request, 'accounts/profile.html', {'form': form})
