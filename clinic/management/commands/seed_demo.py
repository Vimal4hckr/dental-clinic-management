import random
from datetime import date, time, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from aiassistant.engine import no_show_risk
from clinic.models import (Appointment, AppointmentStatus, DoctorProfile,
                           InventoryItem, Invoice, InvoiceItem, PatientProfile,
                           Payment, PaymentMethod, Prescription,
                           PrescriptionItem, Review, Service, ToothCondition,
                           ToothRecord, TreatmentRecord)

User = get_user_model()
random.seed(42)

# Privacy-safe demo data: all emails use example.com, phones are 0000000000.
DEMO_PHONE = '0000000000'

FIRST = ['John', 'Emma', 'Michael', 'Olivia', 'James', 'Sophia', 'David',
         'Ava', 'Daniel', 'Mia', 'Ravi', 'Priya', 'Arjun', 'Neha', 'Liam',
         'Isabella', 'Noah', 'Aria', 'Ethan', 'Zoya']
LAST = ['Sharma', 'Patel', 'Brown', 'Johnson', 'Davis', 'Wilson', 'Kumar',
        'Singh', 'Taylor', 'Anderson', 'Verma', 'Nair', 'Khan', 'Reddy']

SERVICES = [
    ('General Consultation', 'A thorough dental check-up and oral health assessment.', 300, 20, 'bi-clipboard2-pulse'),
    ('Scaling & Cleaning', 'Professional plaque and tartar removal for healthy gums.', 800, 40, 'bi-droplet'),
    ('Cavity Filling', 'Tooth-coloured composite fillings to restore decayed teeth.', 1200, 45, 'bi-tooth'),
    ('Root Canal', 'Painless root canal therapy to save infected teeth.', 4500, 90, 'bi-diagram-3'),
    ('Tooth Extraction', 'Safe removal of damaged or impacted teeth.', 1500, 40, 'bi-scissors'),
    ('Teeth Whitening', 'Brighten your smile with professional whitening.', 3000, 60, 'bi-stars'),
    ('Dental Crown', 'Durable crowns to restore shape and strength.', 6000, 75, 'bi-gem'),
    ('Orthodontic Consultation', 'Assessment for braces and aligners.', 500, 30, 'bi-bounding-box'),
    ('Emergency Consultation', 'Urgent care for dental pain and trauma.', 700, 30, 'bi-heart-pulse'),
]

MEDICINES = [
    ('Amoxicillin 500mg', '1 capsule', 'Three times a day', '5 days', 'After meals'),
    ('Ibuprofen 400mg', '1 tablet', 'Twice a day', '3 days', 'For pain relief'),
    ('Chlorhexidine Mouthwash', '10 ml', 'Twice a day', '7 days', 'Rinse, do not swallow'),
    ('Paracetamol 650mg', '1 tablet', 'As needed', '3 days', 'Max 3 per day'),
    ('Metronidazole 400mg', '1 tablet', 'Three times a day', '5 days', 'Avoid alcohol'),
]

INVENTORY = [
    ('Latex Gloves (Box)', 'Consumables', 45, 'box', 20, 250, 'bi-hand-index'),
    ('Face Masks (Box)', 'Consumables', 30, 'box', 15, 300, 'bi-mask'),
    ('Composite Filling Kit', 'Materials', 12, 'kit', 5, 3500, 'bi-tooth'),
    ('Local Anesthetic', 'Pharmacy', 8, 'vial', 10, 180, 'bi-eyedropper'),
    ('Dental Burs Set', 'Instruments', 6, 'set', 4, 1200, 'bi-gear'),
    ('X-Ray Films', 'Consumables', 60, 'pcs', 25, 40, 'bi-image'),
    ('Suction Tips', 'Consumables', 18, 'pack', 20, 150, 'bi-funnel'),
    ('Fluoride Gel', 'Materials', 14, 'tube', 8, 220, 'bi-droplet-half'),
]

REVIEW_COMMENTS = [
    'Amazing experience! The dentist was gentle and explained everything.',
    'Booked online in seconds and the clinic was spotless. Highly recommend.',
    'Painless root canal — I was so nervous but the team was fantastic.',
    'Great value and the AI cost estimator was surprisingly accurate!',
    'My kids love coming here. Friendly staff and modern equipment.',
    'Whitening results were incredible. Five stars!',
]


class Command(BaseCommand):
    help = 'Seed the database with realistic, privacy-safe demo data.'

    def add_arguments(self, parser):
        parser.add_argument('--flush', action='store_true',
                            help='Delete existing demo data first.')

    def handle(self, *args, **options):
        if options['flush']:
            self.stdout.write('Flushing existing data...')
            for model in (Payment, InvoiceItem, Invoice, PrescriptionItem,
                          Prescription, TreatmentRecord, ToothRecord,
                          Appointment, Review, InventoryItem, Service):
                model.objects.all().delete()
            User.objects.exclude(is_superuser=True).delete()

        self.stdout.write('Creating users...')
        admin = self._user('admin', 'Admin', 'User', 'admin', is_staff=True, is_superuser=True)
        reception = self._user('reception', 'Riya', 'Front', 'receptionist')

        dentists = []
        for uname, fn, ln, spec in [
            ('drsmith', 'Sarah', 'Smith', 'General Dentistry'),
            ('drpatel', 'Anil', 'Patel', 'Orthodontics'),
            ('drjones', 'Emily', 'Jones', 'Endodontics'),
        ]:
            d = self._user(uname, fn, ln, 'dentist')
            prof, _ = DoctorProfile.objects.get_or_create(user=d)
            prof.specialization = spec
            prof.experience_years = random.randint(3, 20)
            prof.consultation_fee = Decimal(random.choice([300, 400, 500]))
            prof.rating = Decimal(str(round(random.uniform(4.2, 5.0), 1)))
            prof.license_no = f'DL-{random.randint(10000, 99999)}'
            prof.save()
            dentists.append(d)

        self.stdout.write('Creating services...')
        services = []
        for name, desc, price, dur, icon in SERVICES:
            s, _ = Service.objects.get_or_create(name=name, defaults={
                'description': desc, 'price': Decimal(price),
                'duration_minutes': dur, 'icon': icon})
            services.append(s)

        self.stdout.write('Creating patients (spread across 12 months)...')
        patients = []
        now = timezone.now()
        used = set()
        for i in range(24):
            fn = random.choice(FIRST)
            ln = random.choice(LAST)
            base = f'{fn.lower()}{ln.lower()}'
            uname = base
            n = 1
            while uname in used or User.objects.filter(username=uname).exists():
                n += 1
                uname = f'{base}{n}'
            used.add(uname)
            p = self._user(uname, fn, ln, 'patient')
            # spread joins over last 12 months for the growth chart
            days_ago = random.randint(0, 360)
            p.date_joined = now - timedelta(days=days_ago)
            p.gender = random.choice(['male', 'female'])
            p.date_of_birth = date(random.randint(1965, 2010), random.randint(1, 12), random.randint(1, 28))
            p.address = f'{random.randint(1, 200)} Demo Street, Sample City'
            p.save()
            prof, _ = PatientProfile.objects.get_or_create(user=p)
            prof.blood_group = random.choice(['A+', 'B+', 'O+', 'AB+', 'O-', 'A-'])
            prof.allergies = random.choice(['None', 'Penicillin', 'Latex', 'None', 'None'])
            prof.registered_on = p.date_joined.date()
            prof.save()
            patients.append(p)

        # give the first patient a friendly username
        john = patients[0]
        john.username = 'john'
        john.first_name, john.last_name = 'John', 'Sharma'
        john.save()

        self.stdout.write('Creating tooth charts...')
        conditions = [c[0] for c in ToothCondition.choices]
        for p in patients:
            for _ in range(random.randint(2, 8)):
                num = random.randint(1, 32)
                ToothRecord.objects.update_or_create(
                    patient=p, tooth_number=num,
                    defaults={'condition': random.choice(conditions)})

        self.stdout.write('Creating appointments, treatments, prescriptions...')
        statuses = [AppointmentStatus.COMPLETED] * 6 + \
                   [AppointmentStatus.CONFIRMED] * 2 + \
                   [AppointmentStatus.PENDING] * 2 + \
                   [AppointmentStatus.CANCELLED, AppointmentStatus.NO_SHOW]
        for p in patients:
            for _ in range(random.randint(1, 5)):
                dentist = random.choice(dentists)
                service = random.choice(services)
                days = random.randint(-330, 20)  # mostly past, some future
                appt_date = (now + timedelta(days=days)).date()
                if days > 0:
                    status = random.choice([AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED])
                else:
                    status = random.choice(statuses)
                appt = Appointment.objects.create(
                    patient=p, dentist=dentist, service=service,
                    date=appt_date,
                    time=time(random.randint(9, 18), random.choice([0, 15, 30, 45])),
                    status=status,
                    reason=random.choice(['Toothache', 'Routine check-up', 'Cleaning',
                                          'Sensitivity', 'Follow-up', 'Pain']))
                appt.no_show_risk = no_show_risk(appt)
                appt.save(update_fields=['no_show_risk'])

                if status == AppointmentStatus.COMPLETED:
                    cost = service.price * Decimal(str(round(random.uniform(0.9, 1.3), 2)))
                    TreatmentRecord.objects.create(
                        patient=p, dentist=dentist, appointment=appt, service=service,
                        tooth_number=random.randint(1, 32),
                        description=f'{service.name} completed successfully.',
                        cost=cost.quantize(Decimal('0.01')), date=appt_date)

                    if random.random() < 0.6:
                        rx = Prescription.objects.create(
                            patient=p, dentist=dentist, appointment=appt, date=appt_date,
                            diagnosis=random.choice(['Dental caries', 'Gingivitis',
                                                     'Post-extraction care', 'Pulpitis']))
                        for med in random.sample(MEDICINES, random.randint(1, 3)):
                            PrescriptionItem.objects.create(
                                prescription=rx, medicine=med[0], dosage=med[1],
                                frequency=med[2], duration=med[3], instructions=med[4])

                    # Invoice + payment
                    inv = Invoice.objects.create(
                        patient=p, appointment=appt, issued_date=appt_date,
                        due_date=appt_date + timedelta(days=15),
                        tax_percent=Decimal('5.00'))
                    InvoiceItem.objects.create(
                        invoice=inv, description=service.name, quantity=1,
                        unit_price=cost.quantize(Decimal('0.01')))
                    # 75% fully paid, 15% partial, 10% unpaid
                    roll = random.random()
                    if roll < 0.75:
                        Payment.objects.create(invoice=inv, amount=inv.total,
                                               method=random.choice(list(PaymentMethod.values)),
                                               paid_on=appt_date)
                    elif roll < 0.9:
                        Payment.objects.create(invoice=inv, amount=(inv.total / 2).quantize(Decimal('0.01')),
                                               method=random.choice(list(PaymentMethod.values)),
                                               paid_on=appt_date)
                    inv.recalculate_status()

        self.stdout.write('Creating inventory...')
        for name, cat, qty, unit, reorder, price, icon in INVENTORY:
            InventoryItem.objects.get_or_create(name=name, defaults={
                'category': cat, 'quantity': qty, 'unit': unit,
                'reorder_level': reorder, 'unit_price': Decimal(price),
                'supplier': 'DentSupply Co.', 'icon': icon})

        self.stdout.write('Creating reviews...')
        for _ in range(8):
            Review.objects.create(
                patient=random.choice(patients), dentist=random.choice(dentists),
                rating=random.randint(4, 5), comment=random.choice(REVIEW_COMMENTS))

        self.stdout.write(self.style.SUCCESS(
            '\nDemo data ready!\n'
            '  Admin login       : admin / demo1234\n'
            '  Dentist login     : drsmith / demo1234\n'
            '  Receptionist login: reception / demo1234\n'
            '  Patient login     : john / demo1234\n'))

    def _user(self, username, first, last, role, is_staff=False, is_superuser=False):
        user, created = User.objects.get_or_create(username=username, defaults={
            'first_name': first, 'last_name': last,
            'email': f'{username}@example.com', 'role': role,
            'phone': DEMO_PHONE, 'is_staff': is_staff, 'is_superuser': is_superuser,
        })
        if created:
            user.set_password('demo1234')
            user.save()
        return user
