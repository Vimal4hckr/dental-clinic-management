"""Reusable analytics helpers that power the dashboard charts."""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db.models import Count, Sum
from django.utils import timezone

from .models import (Appointment, AppointmentStatus, Invoice, Payment,
                     TreatmentRecord)

User = get_user_model()

MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']


def _last_12_months():
    today = timezone.localdate().replace(day=1)
    months = []
    y, m = today.year, today.month
    for _ in range(12):
        months.append((y, m))
        m -= 1
        if m == 0:
            m = 12
            y -= 1
    return list(reversed(months))


def revenue_by_month():
    """Total collected payments per month for the last 12 months."""
    labels, data = [], []
    payments = Payment.objects.values_list('paid_on', 'amount')
    bucket = {}
    for paid_on, amount in payments:
        key = (paid_on.year, paid_on.month)
        bucket[key] = bucket.get(key, Decimal('0')) + amount
    for (y, m) in _last_12_months():
        labels.append(f"{MONTHS[m - 1]} {str(y)[2:]}")
        data.append(float(bucket.get((y, m), 0)))
    return {'labels': labels, 'data': data}


def appointments_by_status():
    rows = (Appointment.objects.values('status')
            .annotate(c=Count('id')).order_by())
    mapping = {r['status']: r['c'] for r in rows}
    labels, data = [], []
    for value, label in AppointmentStatus.choices:
        labels.append(label)
        data.append(mapping.get(value, 0))
    return {'labels': labels, 'data': data}


def appointments_per_month():
    labels, data = [], []
    rows = Appointment.objects.values_list('date', flat=True)
    bucket = {}
    for d in rows:
        key = (d.year, d.month)
        bucket[key] = bucket.get(key, 0) + 1
    for (y, m) in _last_12_months():
        labels.append(f"{MONTHS[m - 1]} {str(y)[2:]}")
        data.append(bucket.get((y, m), 0))
    return {'labels': labels, 'data': data}


def treatment_distribution():
    rows = (TreatmentRecord.objects.values('service__name')
            .annotate(c=Count('id')).order_by('-c')[:6])
    return {
        'labels': [r['service__name'] or 'Other' for r in rows],
        'data': [r['c'] for r in rows],
    }


def patient_growth():
    labels, data = [], []
    patients = User.objects.filter(role='patient').values_list('date_joined', flat=True)
    bucket = {}
    for dj in patients:
        d = timezone.localtime(dj).date()
        key = (d.year, d.month)
        bucket[key] = bucket.get(key, 0) + 1
    running = 0
    for (y, m) in _last_12_months():
        running += bucket.get((y, m), 0)
        labels.append(f"{MONTHS[m - 1]} {str(y)[2:]}")
        data.append(running)
    return {'labels': labels, 'data': data}


def admin_kpis():
    total_revenue = Payment.objects.aggregate(s=Sum('amount'))['s'] or Decimal('0')
    outstanding = Decimal('0')
    for inv in Invoice.objects.all():
        outstanding += inv.balance
    return {
        'total_patients': User.objects.filter(role='patient').count(),
        'total_dentists': User.objects.filter(role='dentist').count(),
        'total_appointments': Appointment.objects.count(),
        'appointments_today': Appointment.objects.filter(date=timezone.localdate()).count(),
        'total_revenue': total_revenue,
        'outstanding': outstanding,
        'total_treatments': TreatmentRecord.objects.count(),
        'pending_appointments': Appointment.objects.filter(
            status=AppointmentStatus.PENDING).count(),
    }
