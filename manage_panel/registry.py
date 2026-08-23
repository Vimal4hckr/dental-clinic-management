"""A tiny generic-CRUD registry so admins can manage models from a custom,
branded panel (NOT the default Django admin)."""
from django.forms import modelform_factory

from clinic.forms import CTRL
from clinic.models import InventoryItem, Review, Service


def _styled_form(model, fields):
    form = modelform_factory(model, fields=fields)

    class Styled(form):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            for f in self.fields.values():
                w = f.widget
                cls = w.attrs.get('class', '')
                w.attrs['class'] = (cls + ' ' + CTRL).strip()
    return Styled


class Resource:
    def __init__(self, slug, model, label, label_plural, icon,
                 list_display, form_fields, search_fields=None):
        self.slug = slug
        self.model = model
        self.label = label
        self.label_plural = label_plural
        self.icon = icon
        self.list_display = list_display  # list of (header, attr)
        self.form_fields = form_fields
        self.search_fields = search_fields or []

    def form_class(self):
        return _styled_form(self.model, self.form_fields)

    def value(self, obj, attr):
        val = getattr(obj, attr, '')
        if callable(val):
            val = val()
        return val

    def count(self):
        return self.model.objects.count()


RESOURCES = {
    'services': Resource(
        'services', Service, 'Service', 'Services', 'bi-clipboard2-pulse',
        list_display=[('Name', 'name'), ('Price', 'price'),
                      ('Duration (min)', 'duration_minutes'), ('Active', 'is_active')],
        form_fields=['name', 'description', 'price', 'duration_minutes', 'icon',
                     'image', 'is_active'],
        search_fields=['name'],
    ),
    'inventory': Resource(
        'inventory', InventoryItem, 'Inventory Item', 'Inventory', 'bi-box-seam',
        list_display=[('Name', 'name'), ('Category', 'category'),
                      ('Qty', 'quantity'), ('Reorder', 'reorder_level'),
                      ('Unit Price', 'unit_price')],
        form_fields=['name', 'category', 'quantity', 'unit', 'reorder_level',
                     'unit_price', 'supplier', 'icon'],
        search_fields=['name', 'category'],
    ),
    'reviews': Resource(
        'reviews', Review, 'Review', 'Reviews', 'bi-star',
        list_display=[('Patient', 'patient'), ('Dentist', 'dentist'),
                      ('Rating', 'rating'), ('Public', 'is_public')],
        form_fields=['patient', 'dentist', 'rating', 'comment', 'is_public'],
    ),
}


def get_resource(slug):
    return RESOURCES.get(slug)
