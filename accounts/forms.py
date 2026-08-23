from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import Gender, Role

User = get_user_model()

INPUT = 'form-control-app'


class BootstrapMixin:
    """Adds consistent CSS classes + placeholders to every field."""

    def _style(self):
        for name, field in self.fields.items():
            widget = field.widget
            css = INPUT
            if isinstance(widget, forms.CheckboxInput):
                css = 'form-check-input-app'
            elif isinstance(widget, forms.Select):
                css = INPUT + ' select-app'
            existing = widget.attrs.get('class', '')
            widget.attrs['class'] = (existing + ' ' + css).strip()
            if not widget.attrs.get('placeholder') and not isinstance(widget, (forms.Select, forms.CheckboxInput)):
                widget.attrs['placeholder'] = field.label or name.replace('_', ' ').title()


class SignUpForm(BootstrapMixin, UserCreationForm):
    first_name = forms.CharField(max_length=50)
    last_name = forms.CharField(max_length=50, required=False)
    email = forms.EmailField()
    phone = forms.CharField(max_length=20, required=False)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'phone',
                  'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style()

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = Role.PATIENT  # public sign-ups are always patients
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data.get('last_name', '')
        user.phone = self.cleaned_data.get('phone') or '0000000000'
        if commit:
            user.save()
        return user


class LoginForm(BootstrapMixin, AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style()
        self.fields['username'].widget.attrs['placeholder'] = 'Username'
        self.fields['password'].widget.attrs['placeholder'] = 'Password'


class ProfileForm(BootstrapMixin, forms.ModelForm):
    date_of_birth = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone', 'gender',
                  'date_of_birth', 'address', 'bio', 'avatar')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style()


class StaffUserForm(BootstrapMixin, forms.ModelForm):
    """Used by admins to create/edit any user (any role)."""
    password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(),
        help_text='Leave blank to keep the current password when editing.'
    )
    date_of_birth = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'phone',
                  'role', 'gender', 'date_of_birth', 'address', 'avatar',
                  'is_active')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style()

    def save(self, commit=True):
        user = super().save(commit=False)
        pwd = self.cleaned_data.get('password')
        if pwd:
            user.set_password(pwd)
        if commit:
            user.save()
        return user
