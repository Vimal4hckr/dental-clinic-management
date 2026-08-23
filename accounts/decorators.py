from functools import wraps

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect


def role_required(*roles):
    """Allow access only to users whose role is in `roles` (superuser always allowed)."""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.info(request, 'Please sign in to continue.')
                return redirect('accounts:login')
            if request.user.is_superuser or request.user.role in roles:
                return view_func(request, *args, **kwargs)
            raise PermissionDenied('You do not have access to this area.')
        return _wrapped
    return decorator


def admin_required(view_func):
    return role_required('admin')(view_func)


def staff_required(view_func):
    """Admin, dentist or receptionist (i.e. clinic staff)."""
    return role_required('admin', 'dentist', 'receptionist')(view_func)
