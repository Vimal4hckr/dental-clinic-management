from django.urls import path

from . import views

app_name = 'clinic'

urlpatterns = [
    # Dashboards
    path('dentist/', views.dentist_dashboard, name='dentist_dashboard'),
    path('reception/', views.receptionist_dashboard, name='receptionist_dashboard'),
    path('me/', views.patient_dashboard, name='patient_dashboard'),

    # Appointments
    path('appointments/', views.appointment_list, name='appointment_list'),
    path('appointments/new/', views.appointment_create, name='appointment_create'),
    path('appointments/<int:pk>/', views.appointment_detail, name='appointment_detail'),
    path('appointments/<int:pk>/edit/', views.appointment_update, name='appointment_update'),
    path('appointments/<int:pk>/delete/', views.appointment_delete, name='appointment_delete'),
    path('appointments/<int:pk>/status/<str:status>/', views.appointment_set_status,
         name='appointment_set_status'),
    path('appointments/<int:pk>/cancel/', views.appointment_cancel, name='appointment_cancel'),

    # Patients
    path('patients/', views.patient_list, name='patient_list'),
    path('patients/<int:pk>/', views.patient_detail, name='patient_detail'),
    path('patients/<int:pk>/tooth/', views.tooth_update, name='tooth_update'),

    # Treatments
    path('treatments/', views.treatment_list, name='treatment_list'),
    path('treatments/new/', views.treatment_create, name='treatment_create'),
    path('treatments/<int:pk>/edit/', views.treatment_update, name='treatment_update'),
    path('treatments/<int:pk>/delete/', views.treatment_delete, name='treatment_delete'),

    # Prescriptions
    path('prescriptions/', views.prescription_list, name='prescription_list'),
    path('prescriptions/new/', views.prescription_create, name='prescription_create'),
    path('prescriptions/<int:pk>/', views.prescription_detail, name='prescription_detail'),
    path('prescriptions/<int:pk>/delete/', views.prescription_delete, name='prescription_delete'),

    # Invoices
    path('invoices/', views.invoice_list, name='invoice_list'),
    path('invoices/new/', views.invoice_create, name='invoice_create'),
    path('invoices/<int:pk>/', views.invoice_detail, name='invoice_detail'),
    path('invoices/<int:pk>/pay/', views.invoice_add_payment, name='invoice_add_payment'),
    path('invoices/<int:pk>/delete/', views.invoice_delete, name='invoice_delete'),

    # Inventory
    path('inventory/', views.inventory_list, name='inventory_list'),
    path('inventory/new/', views.inventory_create, name='inventory_create'),
    path('inventory/<int:pk>/edit/', views.inventory_update, name='inventory_update'),
    path('inventory/<int:pk>/delete/', views.inventory_delete, name='inventory_delete'),

    # Reviews
    path('reviews/new/', views.review_create, name='review_create'),
]
