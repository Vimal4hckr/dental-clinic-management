from django.contrib.auth.models import AbstractUser
from django.db import models


class Role(models.TextChoices):
    ADMIN = 'admin', 'Administrator'
    DENTIST = 'dentist', 'Dentist'
    RECEPTIONIST = 'receptionist', 'Receptionist'
    PATIENT = 'patient', 'Patient'


class Gender(models.TextChoices):
    MALE = 'male', 'Male'
    FEMALE = 'female', 'Female'
    OTHER = 'other', 'Other'


# Theme metadata used to give every role a distinct look & feel.
ROLE_THEMES = {
    Role.ADMIN: {
        'name': 'theme-admin',
        'label': 'Admin Console',
        'primary': '#4f46e5',
        'accent': '#a855f7',
        'gradient': 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)',
        'icon': 'bi-shield-lock',
    },
    Role.DENTIST: {
        'name': 'theme-dentist',
        'label': 'Dentist Workspace',
        'primary': '#0d9488',
        'accent': '#22c55e',
        'gradient': 'linear-gradient(135deg, #0d9488 0%, #16a34a 100%)',
        'icon': 'bi-heart-pulse',
    },
    Role.RECEPTIONIST: {
        'name': 'theme-receptionist',
        'label': 'Front Desk',
        'primary': '#2563eb',
        'accent': '#06b6d4',
        'gradient': 'linear-gradient(135deg, #2563eb 0%, #06b6d4 100%)',
        'icon': 'bi-calendar2-week',
    },
    Role.PATIENT: {
        'name': 'theme-patient',
        'label': 'My Health',
        'primary': '#e11d48',
        'accent': '#f97316',
        'gradient': 'linear-gradient(135deg, #f43f5e 0%, #f97316 100%)',
        'icon': 'bi-emoji-smile',
    },
}


class User(AbstractUser):
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.PATIENT)
    phone = models.CharField(max_length=20, blank=True, default='0000000000')
    gender = models.CharField(max_length=10, choices=Gender.choices, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.CharField(max_length=255, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(blank=True)

    @property
    def theme(self):
        return ROLE_THEMES.get(self.role, ROLE_THEMES[Role.PATIENT])

    @property
    def initials(self):
        first = (self.first_name or self.username or '?')[:1]
        last = (self.last_name or '')[:1]
        return (first + last).upper()

    @property
    def display_name(self):
        full = self.get_full_name()
        return full if full else self.username

    def is_admin(self):
        return self.role == Role.ADMIN or self.is_superuser

    def is_dentist(self):
        return self.role == Role.DENTIST

    def is_receptionist(self):
        return self.role == Role.RECEPTIONIST

    def is_patient(self):
        return self.role == Role.PATIENT

    def __str__(self):
        return f"{self.display_name} ({self.get_role_display()})"
