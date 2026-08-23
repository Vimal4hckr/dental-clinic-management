import json

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.decorators import role_required, staff_required
from aiassistant.engine import no_show_risk, risk_band

from . import analytics
from .forms import (AppointmentForm, InventoryItemForm, InvoiceForm,
                    InvoiceItemFormSet, PatientBookingForm, PaymentForm,
                    PrescriptionForm, PrescriptionItemFormSet, ReviewForm,
                    ToothRecordForm, TreatmentRecordForm)
from .models import (Appointment, AppointmentStatus, InventoryItem, Invoice,
                     Payment, Prescription, Service, ToothRecord,
                     TreatmentRecord)

User = get_user_model()


def _j(obj):
    return json.dumps(obj)


# ===========================================================================
# DASHBOARDS
# ===========================================================================
@role_required('dentist')
def dentist_dashboard(request):
    me = request.user
    today = timezone.localdate()
    my_appts = Appointment.objects.filter(dentist=me)
    context = {
        'today_appointments': my_appts.filter(date=today).order_by('time'),
        'upcoming': my_appts.filter(date__gte=today).exclude(
            status__in=['completed', 'cancelled']).order_by('date', 'time')[:6],
        'patients_count': my_appts.values('patient').distinct().count(),
        'treatments_count': TreatmentRecord.objects.filter(dentist=me).count(),
        'completed_count': my_appts.filter(status='completed').count(),
        'pending_count': my_appts.filter(status='pending').count(),
        'recent_treatments': TreatmentRecord.objects.filter(dentist=me)[:6],
        'appts_month_json': _j(analytics.appointments_per_month()),
        'treatment_dist_json': _j(analytics.treatment_distribution()),
        'status_json': _j(analytics.appointments_by_status()),
    }
    return render(request, 'clinic/dashboard_dentist.html', context)


@role_required('receptionist')
def receptionist_dashboard(request):
    today = timezone.localdate()
    appts = Appointment.objects.all()
    context = {
        'today_appointments': appts.filter(date=today).order_by('time'),
        'pending': appts.filter(status='pending').order_by('date', 'time')[:8],
        'total_today': appts.filter(date=today).count(),
        'pending_count': appts.filter(status='pending').count(),
        'confirmed_count': appts.filter(status='confirmed').count(),
        'patients_count': User.objects.filter(role='patient').count(),
        'unpaid_invoices': Invoice.objects.exclude(status='paid').count(),
        'revenue_json': _j(analytics.revenue_by_month()),
        'status_json': _j(analytics.appointments_by_status()),
        'appts_month_json': _j(analytics.appointments_per_month()),
    }
    return render(request, 'clinic/dashboard_receptionist.html', context)


@role_required('patient')
def patient_dashboard(request):
    me = request.user
    today = timezone.localdate()
    appts = Appointment.objects.filter(patient=me)
    invoices = Invoice.objects.filter(patient=me)
    outstanding = sum((inv.balance for inv in invoices), 0)
    tooth_records = {t.tooth_number: t for t in ToothRecord.objects.filter(patient=me)}
    context = {
        'upcoming': appts.filter(date__gte=today).exclude(
            status__in=['completed', 'cancelled']).order_by('date', 'time'),
        'past': appts.filter(Q(date__lt=today) | Q(status__in=['completed', 'cancelled']))[:6],
        'appointments_count': appts.count(),
        'treatments_count': TreatmentRecord.objects.filter(patient=me).count(),
        'prescriptions_count': Prescription.objects.filter(patient=me).count(),
        'outstanding': outstanding,
        'invoices': invoices[:5],
        'tooth_records': tooth_records,
        'tooth_range_upper': range(1, 17),
        'tooth_range_lower': range(17, 33),
        'recent_treatments': TreatmentRecord.objects.filter(patient=me)[:5],
        'prescriptions': Prescription.objects.filter(patient=me)[:5],
    }
    return render(request, 'clinic/dashboard_patient.html', context)


# ===========================================================================
# APPOINTMENTS
# ===========================================================================
@login_required
def appointment_list(request):
    user = request.user
    qs = Appointment.objects.select_related('patient', 'dentist', 'service')
    if user.is_patient():
        qs = qs.filter(patient=user)
    elif user.is_dentist():
        qs = qs.filter(dentist=user)
    status = request.GET.get('status')
    if status:
        qs = qs.filter(status=status)
    search = request.GET.get('q')
    if search:
        qs = qs.filter(Q(patient__first_name__icontains=search) |
                       Q(patient__last_name__icontains=search) |
                       Q(reason__icontains=search))
    return render(request, 'clinic/appointment_list.html', {
        'appointments': qs,
        'statuses': AppointmentStatus.choices,
        'current_status': status,
        'search': search or '',
    })


@login_required
def appointment_create(request):
    user = request.user
    patient_mode = user.is_patient()
    FormClass = PatientBookingForm if patient_mode else AppointmentForm
    if request.method == 'POST':
        form = FormClass(request.POST)
        if form.is_valid():
            appt = form.save(commit=False)
            if patient_mode:
                appt.patient = user
                appt.status = AppointmentStatus.PENDING
            appt.save()
            appt.no_show_risk = no_show_risk(appt)
            appt.save(update_fields=['no_show_risk'])
            messages.success(request, 'Appointment booked successfully!')
            return redirect('clinic:appointment_list')
    else:
        form = FormClass()
    return render(request, 'clinic/form_page.html',
                  {'form': form, 'title': 'Book Appointment'})


@staff_required
def appointment_update(request, pk):
    appt = get_object_or_404(Appointment, pk=pk)
    if request.method == 'POST':
        form = AppointmentForm(request.POST, instance=appt)
        if form.is_valid():
            appt = form.save()
            appt.no_show_risk = no_show_risk(appt)
            appt.save(update_fields=['no_show_risk'])
            messages.success(request, 'Appointment updated.')
            return redirect('clinic:appointment_list')
    else:
        form = AppointmentForm(instance=appt)
    return render(request, 'clinic/form_page.html',
                  {'form': form, 'title': f'Edit Appointment #{appt.id}'})


@login_required
def appointment_detail(request, pk):
    appt = get_object_or_404(
        Appointment.objects.select_related('patient', 'dentist', 'service'), pk=pk)
    user = request.user
    if user.is_patient() and appt.patient_id != user.id:
        raise PermissionDenied
    if user.is_dentist() and appt.dentist_id != user.id:
        raise PermissionDenied
    band, color = risk_band(appt.no_show_risk)
    return render(request, 'clinic/appointment_detail.html',
                  {'appt': appt, 'risk_band': band, 'risk_color': color})


@staff_required
def appointment_set_status(request, pk, status):
    appt = get_object_or_404(Appointment, pk=pk)
    if status in dict(AppointmentStatus.choices):
        appt.status = status
        appt.save(update_fields=['status'])
        messages.success(request, f'Appointment marked as {appt.get_status_display()}.')
    return redirect(request.META.get('HTTP_REFERER', 'clinic:appointment_list'))


@login_required
def appointment_cancel(request, pk):
    appt = get_object_or_404(Appointment, pk=pk)
    user = request.user
    if user.is_patient() and appt.patient_id != user.id:
        raise PermissionDenied
    appt.status = AppointmentStatus.CANCELLED
    appt.save(update_fields=['status'])
    messages.info(request, 'Appointment cancelled.')
    return redirect(request.META.get('HTTP_REFERER', 'clinic:appointment_list'))


@staff_required
def appointment_delete(request, pk):
    appt = get_object_or_404(Appointment, pk=pk)
    if request.method == 'POST':
        appt.delete()
        messages.success(request, 'Appointment deleted.')
        return redirect('clinic:appointment_list')
    return render(request, 'clinic/confirm_delete.html',
                  {'object': appt, 'title': 'Delete Appointment',
                   'cancel_url': 'clinic:appointment_list'})


# ===========================================================================
# PATIENTS
# ===========================================================================
@staff_required
def patient_list(request):
    search = request.GET.get('q', '')
    patients = User.objects.filter(role='patient').select_related('patient_profile')
    if search:
        patients = patients.filter(Q(first_name__icontains=search) |
                                   Q(last_name__icontains=search) |
                                   Q(email__icontains=search))
    return render(request, 'clinic/patient_list.html',
                  {'patients': patients, 'search': search})


@staff_required
def patient_detail(request, pk):
    patient = get_object_or_404(User, pk=pk, role='patient')
    tooth_records = {t.tooth_number: t for t in ToothRecord.objects.filter(patient=patient)}
    return render(request, 'clinic/patient_detail.html', {
        'patient': patient,
        'appointments': Appointment.objects.filter(patient=patient)[:8],
        'treatments': TreatmentRecord.objects.filter(patient=patient)[:8],
        'prescriptions': Prescription.objects.filter(patient=patient)[:8],
        'invoices': Invoice.objects.filter(patient=patient)[:8],
        'tooth_records': tooth_records,
        'tooth_range_upper': range(1, 17),
        'tooth_range_lower': range(17, 33),
        'conditions': ToothRecord._meta.get_field('condition').choices,
    })


@staff_required
def tooth_update(request, pk):
    """Add/update a tooth record for a patient (dentist/staff)."""
    patient = get_object_or_404(User, pk=pk, role='patient')
    if request.method == 'POST':
        number = request.POST.get('tooth_number')
        condition = request.POST.get('condition')
        note = request.POST.get('note', '')
        if number and condition:
            ToothRecord.objects.update_or_create(
                patient=patient, tooth_number=number,
                defaults={'condition': condition, 'note': note})
            messages.success(request, f'Tooth {number} updated.')
    return redirect('clinic:patient_detail', pk=patient.pk)


# ===========================================================================
# TREATMENTS
# ===========================================================================
@login_required
def treatment_list(request):
    user = request.user
    qs = TreatmentRecord.objects.select_related('patient', 'dentist', 'service')
    if user.is_patient():
        qs = qs.filter(patient=user)
    elif user.is_dentist():
        qs = qs.filter(dentist=user)
    return render(request, 'clinic/treatment_list.html', {'treatments': qs})


@role_required('dentist', 'admin', 'receptionist')
def treatment_create(request):
    if request.method == 'POST':
        form = TreatmentRecordForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Treatment record added.')
            return redirect('clinic:treatment_list')
    else:
        initial = {}
        if request.user.is_dentist():
            initial['dentist'] = request.user
        form = TreatmentRecordForm(initial=initial)
    return render(request, 'clinic/form_page.html',
                  {'form': form, 'title': 'New Treatment Record'})


@role_required('dentist', 'admin', 'receptionist')
def treatment_update(request, pk):
    treatment = get_object_or_404(TreatmentRecord, pk=pk)
    if request.method == 'POST':
        form = TreatmentRecordForm(request.POST, instance=treatment)
        if form.is_valid():
            form.save()
            messages.success(request, 'Treatment updated.')
            return redirect('clinic:treatment_list')
    else:
        form = TreatmentRecordForm(instance=treatment)
    return render(request, 'clinic/form_page.html',
                  {'form': form, 'title': 'Edit Treatment'})


@role_required('dentist', 'admin')
def treatment_delete(request, pk):
    treatment = get_object_or_404(TreatmentRecord, pk=pk)
    if request.method == 'POST':
        treatment.delete()
        messages.success(request, 'Treatment deleted.')
        return redirect('clinic:treatment_list')
    return render(request, 'clinic/confirm_delete.html',
                  {'object': treatment, 'title': 'Delete Treatment',
                   'cancel_url': 'clinic:treatment_list'})


# ===========================================================================
# PRESCRIPTIONS
# ===========================================================================
@login_required
def prescription_list(request):
    user = request.user
    qs = Prescription.objects.select_related('patient', 'dentist')
    if user.is_patient():
        qs = qs.filter(patient=user)
    elif user.is_dentist():
        qs = qs.filter(dentist=user)
    return render(request, 'clinic/prescription_list.html', {'prescriptions': qs})


@role_required('dentist', 'admin')
def prescription_create(request):
    if request.method == 'POST':
        form = PrescriptionForm(request.POST)
        formset = PrescriptionItemFormSet(request.POST, prefix='items')
        if form.is_valid() and formset.is_valid():
            rx = form.save()
            formset.instance = rx
            formset.save()
            messages.success(request, 'Prescription created.')
            return redirect('clinic:prescription_detail', pk=rx.pk)
    else:
        initial = {'dentist': request.user} if request.user.is_dentist() else {}
        form = PrescriptionForm(initial=initial)
        formset = PrescriptionItemFormSet(prefix='items')
    return render(request, 'clinic/prescription_form.html',
                  {'form': form, 'formset': formset, 'title': 'New Prescription'})


@login_required
def prescription_detail(request, pk):
    rx = get_object_or_404(Prescription.objects.select_related('patient', 'dentist'), pk=pk)
    if request.user.is_patient() and rx.patient_id != request.user.id:
        raise PermissionDenied
    return render(request, 'clinic/prescription_detail.html', {'rx': rx})


@role_required('dentist', 'admin')
def prescription_delete(request, pk):
    rx = get_object_or_404(Prescription, pk=pk)
    if request.method == 'POST':
        rx.delete()
        messages.success(request, 'Prescription deleted.')
        return redirect('clinic:prescription_list')
    return render(request, 'clinic/confirm_delete.html',
                  {'object': rx, 'title': 'Delete Prescription',
                   'cancel_url': 'clinic:prescription_list'})


# ===========================================================================
# INVOICES & PAYMENTS
# ===========================================================================
@login_required
def invoice_list(request):
    user = request.user
    qs = Invoice.objects.select_related('patient')
    if user.is_patient():
        qs = qs.filter(patient=user)
    return render(request, 'clinic/invoice_list.html', {'invoices': qs})


@role_required('receptionist', 'admin')
def invoice_create(request):
    if request.method == 'POST':
        form = InvoiceForm(request.POST)
        formset = InvoiceItemFormSet(request.POST, prefix='items')
        if form.is_valid() and formset.is_valid():
            invoice = form.save()
            formset.instance = invoice
            formset.save()
            invoice.recalculate_status()
            messages.success(request, f'Invoice {invoice.number} created.')
            return redirect('clinic:invoice_detail', pk=invoice.pk)
    else:
        form = InvoiceForm()
        formset = InvoiceItemFormSet(prefix='items')
    return render(request, 'clinic/invoice_form.html',
                  {'form': form, 'formset': formset, 'title': 'New Invoice'})


@login_required
def invoice_detail(request, pk):
    invoice = get_object_or_404(Invoice.objects.select_related('patient'), pk=pk)
    if request.user.is_patient() and invoice.patient_id != request.user.id:
        raise PermissionDenied
    payment_form = PaymentForm(initial={'amount': invoice.balance})
    return render(request, 'clinic/invoice_detail.html',
                  {'invoice': invoice, 'payment_form': payment_form})


@role_required('receptionist', 'admin')
def invoice_add_payment(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.invoice = invoice
            payment.save()
            invoice.recalculate_status()
            messages.success(request, 'Payment recorded.')
    return redirect('clinic:invoice_detail', pk=invoice.pk)


@role_required('receptionist', 'admin')
def invoice_delete(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    if request.method == 'POST':
        invoice.delete()
        messages.success(request, 'Invoice deleted.')
        return redirect('clinic:invoice_list')
    return render(request, 'clinic/confirm_delete.html',
                  {'object': invoice, 'title': 'Delete Invoice',
                   'cancel_url': 'clinic:invoice_list'})


# ===========================================================================
# INVENTORY
# ===========================================================================
@staff_required
def inventory_list(request):
    items = InventoryItem.objects.all()
    return render(request, 'clinic/inventory_list.html', {
        'items': items,
        'low_count': sum(1 for i in items if i.is_low),
        'total_value': items.aggregate(v=Sum('unit_price'))['v'] or 0,
    })


@staff_required
def inventory_create(request):
    if request.method == 'POST':
        form = InventoryItemForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Inventory item added.')
            return redirect('clinic:inventory_list')
    else:
        form = InventoryItemForm()
    return render(request, 'clinic/form_page.html',
                  {'form': form, 'title': 'Add Inventory Item'})


@staff_required
def inventory_update(request, pk):
    item = get_object_or_404(InventoryItem, pk=pk)
    if request.method == 'POST':
        form = InventoryItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, 'Inventory item updated.')
            return redirect('clinic:inventory_list')
    else:
        form = InventoryItemForm(instance=item)
    return render(request, 'clinic/form_page.html',
                  {'form': form, 'title': 'Edit Inventory Item'})


@staff_required
def inventory_delete(request, pk):
    item = get_object_or_404(InventoryItem, pk=pk)
    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Item deleted.')
        return redirect('clinic:inventory_list')
    return render(request, 'clinic/confirm_delete.html',
                  {'object': item, 'title': 'Delete Item',
                   'cancel_url': 'clinic:inventory_list'})


# ===========================================================================
# REVIEWS
# ===========================================================================
@role_required('patient')
def review_create(request):
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.patient = request.user
            review.save()
            messages.success(request, 'Thanks for your feedback!')
            return redirect('clinic:patient_dashboard')
    else:
        form = ReviewForm()
    return render(request, 'clinic/form_page.html',
                  {'form': form, 'title': 'Leave a Review'})
