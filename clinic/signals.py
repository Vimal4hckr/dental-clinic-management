from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import DoctorProfile, PatientProfile


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def ensure_role_profile(sender, instance, created, **kwargs):
    """Automatically create the matching profile for dentists & patients."""
    role = getattr(instance, 'role', None)
    if role == 'patient':
        PatientProfile.objects.get_or_create(user=instance)
    elif role == 'dentist':
        DoctorProfile.objects.get_or_create(user=instance)
