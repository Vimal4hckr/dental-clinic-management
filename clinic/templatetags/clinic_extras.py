from django import template

register = template.Library()


@register.filter
def get_item(mapping, key):
    """Look up a value in a dict by (possibly non-string) key."""
    if mapping is None:
        return None
    try:
        return mapping.get(key)
    except AttributeError:
        return None


@register.filter
def currency(value):
    try:
        return f"₹{float(value):,.0f}"
    except (TypeError, ValueError):
        return f"₹{value}"


@register.filter
def sub(a, b):
    try:
        return a - b
    except TypeError:
        return a
