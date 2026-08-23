from .models import ROLE_THEMES, Role


def theme_context(request):
    """Expose the active theme (based on the logged-in user's role) to templates."""
    user = getattr(request, 'user', None)
    if user is not None and user.is_authenticated:
        theme = user.theme
    else:
        theme = {
            'name': 'theme-public',
            'label': 'DentaCare',
            'primary': '#2563eb',
            'accent': '#06b6d4',
            'gradient': 'linear-gradient(135deg, #2563eb 0%, #06b6d4 100%)',
            'icon': 'bi-hospital',
        }
    return {
        'active_theme': theme,
        'all_roles': Role,
        'brand_name': 'DentaCare',
    }
