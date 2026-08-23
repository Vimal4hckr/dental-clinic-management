from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone

User = settings.AUTH_USER_MODEL


# ----------------------------------------------------------------------------
# Profiles
# ----------------------------------------------------------------------------
class DoctorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor_profile')
    specialization = models.CharField(max_length=120, default='General Dentistry')
    license_no = models.CharField(max_length=60, blank=True)
    experience_years = models.PositiveIntegerField(default=1)
    consultation_fee = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('300.00'))
    available_days = models.CharField(max_length=120, default='Mon, Tue, Wed, Thu, Fri')
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=Decimal('4.5'))
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"Dr. {self.user.display_name} · {self.specialization}"


class BloodGroup(models.TextChoices):
    A_POS = 'A+', 'A+'
    A_NEG = 'A-', 'A-'
    B_POS = 'B+', 'B+'
    B_NEG = 'B-', 'B-'
    O_POS = 'O+', 'O+'
    O_NEG = 'O-', 'O-'
    AB_POS = 'AB+', 'AB+'
    AB_NEG = 'AB-', 'AB-'


class PatientProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient_profile')
    patient_code = models.CharField(max_length=20, unique=True, blank=True)
    blood_group = models.CharField(max_length=3, choices=BloodGroup.choices, blank=True)
    emergency_contact = models.CharField(max_length=20, blank=True, default='0000000000')
    allergies = models.CharField(max_length=255, blank=True, default='None')
    medical_history = models.TextField(blank=True, default='No significant history.')
    registered_on = models.DateField(default=timezone.now)

    def save(self, *args, **kwargs):
        if not self.patient_code:
            last = PatientProfile.objects.order_by('-id').first()
            next_id = (last.id + 1) if last else 1
            self.patient_code = f"PT-{next_id:05d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.patient_code} · {self.user.display_name}"


# ----------------------------------------------------------------------------
# Services offered
# ----------------------------------------------------------------------------
class Service(models.Model):
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('500.00'))
    duration_minutes = models.PositiveIntegerField(default=30)
    icon = models.CharField(max_length=60, default='bi-tooth',
                            help_text='Bootstrap icon class, e.g. bi-tooth')
    image = models.ImageField(upload_to='services/', blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


# ----------------------------------------------------------------------------
# Appointments
# ----------------------------------------------------------------------------
class AppointmentStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    CONFIRMED = 'confirmed', 'Confirmed'
    COMPLETED = 'completed', 'Completed'
    CANCELLED = 'cancelled', 'Cancelled'
    NO_SHOW = 'no_show', 'No Show'


class Appointment(models.Model):
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appointments',
                                limit_choices_to={'role': 'patient'})
    dentist = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='doctor_appointments',
                                limit_choices_to={'role': 'dentist'})
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateField()
    time = models.TimeField()
    status = models.CharField(max_length=15, choices=AppointmentStatus.choices,
                              default=AppointmentStatus.PENDING)
    reason = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    no_show_risk = models.PositiveIntegerField(default=0, help_text='AI-estimated no-show risk %')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-time']

    @property
    def is_upcoming(self):
        return self.date >= timezone.localdate() and self.status in (
            AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED)

    @property
    def status_color(self):
        return {
            'pending': 'warning',
            'confirmed': 'info',
            'completed': 'success',
            'cancelled': 'secondary',
            'no_show': 'danger',
        }.get(self.status, 'secondary')

    def __str__(self):
        return f"{self.patient.display_name} · {self.date} {self.time}"


# ----------------------------------------------------------------------------
# Tooth chart
# ----------------------------------------------------------------------------
class ToothCondition(models.TextChoices):
    HEALTHY = 'healthy', 'Healthy'
    CAVITY = 'cavity', 'Cavity'
    FILLED = 'filled', 'Filled'
    ROOT_CANAL = 'root_canal', 'Root Canal'
    CROWN = 'crown', 'Crown'
    MISSING = 'missing', 'Missing'


class ToothRecord(models.Model):
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tooth_records')
    tooth_number = models.PositiveIntegerField(help_text='1-32 (universal numbering)')
    condition = models.CharField(max_length=15, choices=ToothCondition.choices,
                                 default=ToothCondition.HEALTHY)
    note = models.CharField(max_length=200, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('patient', 'tooth_number')
        ordering = ['tooth_number']

    @property
    def condition_color(self):
        return {
            'healthy': '#22c55e',
            'cavity': '#ef4444',
            'filled': '#3b82f6',
            'root_canal': '#f59e0b',
            'crown': '#a855f7',
            'missing': '#94a3b8',
        }.get(self.condition, '#22c55e')

    def __str__(self):
        return f"Tooth {self.tooth_number} · {self.get_condition_display()}"


# ----------------------------------------------------------------------------
# Treatments
# ----------------------------------------------------------------------------
class TreatmentRecord(models.Model):
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='treatments')
    dentist = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                related_name='performed_treatments')
    appointment = models.ForeignKey(Appointment, on_delete=models.SET_NULL, null=True, blank=True)
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True)
    tooth_number = models.PositiveIntegerField(null=True, blank=True)
    description = models.TextField(blank=True)
    cost = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    date = models.DateField(default=timezone.now)
    is_completed = models.BooleanField(default=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.service} for {self.patient.display_name}"


# ----------------------------------------------------------------------------
# Prescriptions
# ----------------------------------------------------------------------------
class Prescription(models.Model):
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='prescriptions')
    dentist = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                related_name='written_prescriptions')
    appointment = models.ForeignKey(Appointment, on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateField(default=timezone.now)
    diagnosis = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"Rx #{self.id} · {self.patient.display_name}"


class PrescriptionItem(models.Model):
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE, related_name='items')
    medicine = models.CharField(max_length=120)
    dosage = models.CharField(max_length=60, default='1 tablet')
    frequency = models.CharField(max_length=60, default='Twice a day')
    duration = models.CharField(max_length=60, default='5 days')
    instructions = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return self.medicine


# ----------------------------------------------------------------------------
# Billing
# ----------------------------------------------------------------------------
class InvoiceStatus(models.TextChoices):
    UNPAID = 'unpaid', 'Unpaid'
    PARTIAL = 'partial', 'Partially Paid'
    PAID = 'paid', 'Paid'


class Invoice(models.Model):
    number = models.CharField(max_length=20, unique=True, blank=True)
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='invoices')
    appointment = models.ForeignKey(Appointment, on_delete=models.SET_NULL, null=True, blank=True)
    issued_date = models.DateField(default=timezone.now)
    due_date = models.DateField(null=True, blank=True)
    tax_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('5.00'))
    discount = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    status = models.CharField(max_length=10, choices=InvoiceStatus.choices,
                              default=InvoiceStatus.UNPAID)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['-issued_date', '-id']

    def save(self, *args, **kwargs):
        if not self.number:
            last = Invoice.objects.order_by('-id').first()
            next_id = (last.id + 1) if last else 1
            self.number = f"INV-{next_id:05d}"
        super().save(*args, **kwargs)

    @property
    def subtotal(self):
        return sum((item.line_total for item in self.items.all()), Decimal('0.00'))

    @property
    def tax_amount(self):
        return (self.subtotal * self.tax_percent / Decimal('100')).quantize(Decimal('0.01'))

    @property
    def total(self):
        return (self.subtotal + self.tax_amount - self.discount).quantize(Decimal('0.01'))

    @property
    def amount_paid(self):
        return sum((p.amount for p in self.payments.all()), Decimal('0.00'))

    @property
    def balance(self):
        return (self.total - self.amount_paid).quantize(Decimal('0.01'))

    def recalculate_status(self):
        paid = self.amount_paid
        if paid <= 0:
            self.status = InvoiceStatus.UNPAID
        elif paid < self.total:
            self.status = InvoiceStatus.PARTIAL
        else:
            self.status = InvoiceStatus.PAID
        self.save(update_fields=['status'])

    @property
    def status_color(self):
        return {'unpaid': 'danger', 'partial': 'warning', 'paid': 'success'}.get(self.status, 'secondary')

    def __str__(self):
        return self.number


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    description = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))

    @property
    def line_total(self):
        return (self.unit_price * self.quantity).quantize(Decimal('0.01'))

    def __str__(self):
        return self.description


class PaymentMethod(models.TextChoices):
    CASH = 'cash', 'Cash'
    CARD = 'card', 'Card'
    UPI = 'upi', 'UPI'
    INSURANCE = 'insurance', 'Insurance'


class Payment(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    method = models.CharField(max_length=10, choices=PaymentMethod.choices, default=PaymentMethod.CASH)
    paid_on = models.DateField(default=timezone.now)
    reference = models.CharField(max_length=60, blank=True)

    class Meta:
        ordering = ['-paid_on']

    def __str__(self):
        return f"{self.amount} for {self.invoice.number}"


# ----------------------------------------------------------------------------
# Inventory
# ----------------------------------------------------------------------------
class InventoryItem(models.Model):
    name = models.CharField(max_length=120)
    category = models.CharField(max_length=60, default='General')
    quantity = models.IntegerField(default=0)
    unit = models.CharField(max_length=20, default='pcs')
    reorder_level = models.IntegerField(default=10)
    unit_price = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    supplier = models.CharField(max_length=120, blank=True)
    icon = models.CharField(max_length=60, default='bi-box-seam')

    class Meta:
        ordering = ['name']

    @property
    def is_low(self):
        return self.quantity <= self.reorder_level

    def __str__(self):
        return self.name


# ----------------------------------------------------------------------------
# Reviews / feedback
# ----------------------------------------------------------------------------
class Review(models.Model):
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    dentist = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_reviews',
                                null=True, blank=True)
    rating = models.PositiveSmallIntegerField(default=5)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_public = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.rating}★ by {self.patient.display_name}"
