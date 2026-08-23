"""
Lightweight, offline "AI" helpers.

These use transparent rule-based / heuristic logic so the whole app works
with NO external API keys. The design mimics an assistant so it is easy to
swap in a real LLM later (just replace the function bodies).
"""
import re
from datetime import date


# ---------------------------------------------------------------------------
# 1. Symptom triage
# ---------------------------------------------------------------------------
SYMPTOM_RULES = [
    {
        'keywords': ['bleeding', 'gum', 'gums', 'swollen', 'swelling'],
        'condition': 'Gingivitis / Gum disease',
        'urgency': 'Medium',
        'service': 'Scaling & Cleaning',
        'advice': 'Rinse with warm salt water and book a cleaning. Avoid hard brushing.',
    },
    {
        'keywords': ['severe', 'unbearable', 'sharp pain', 'throbbing', 'abscess', 'pus'],
        'condition': 'Possible dental abscess / infection',
        'urgency': 'High',
        'service': 'Emergency Consultation',
        'advice': 'This may need urgent care. Please book an emergency appointment today.',
    },
    {
        'keywords': ['cavity', 'hole', 'decay', 'black spot', 'sensitive', 'sensitivity', 'cold', 'hot', 'sweet'],
        'condition': 'Tooth decay / sensitivity',
        'urgency': 'Medium',
        'service': 'Cavity Filling',
        'advice': 'Use a desensitising toothpaste and schedule a filling to stop further decay.',
    },
    {
        'keywords': ['wisdom', 'back tooth', 'jaw pain', 'erupting'],
        'condition': 'Wisdom tooth trouble',
        'urgency': 'Medium',
        'service': 'Tooth Extraction',
        'advice': 'An X-ray will confirm alignment. Extraction may be advised if impacted.',
    },
    {
        'keywords': ['broken', 'chipped', 'cracked', 'knocked', 'fell', 'trauma', 'accident'],
        'condition': 'Fractured / broken tooth',
        'urgency': 'High',
        'service': 'Emergency Consultation',
        'advice': 'Keep any fragments in milk and see a dentist quickly to save the tooth.',
    },
    {
        'keywords': ['yellow', 'stain', 'stained', 'white', 'whiten', 'brighten'],
        'condition': 'Cosmetic discolouration',
        'urgency': 'Low',
        'service': 'Teeth Whitening',
        'advice': 'A professional whitening session is safe and effective for stains.',
    },
    {
        'keywords': ['crooked', 'align', 'braces', 'gap', 'spacing'],
        'condition': 'Alignment / orthodontic concern',
        'urgency': 'Low',
        'service': 'Orthodontic Consultation',
        'advice': 'Braces or aligners can help. Book an orthodontic assessment.',
    },
    {
        'keywords': ['bad breath', 'smell', 'halitosis'],
        'condition': 'Halitosis (bad breath)',
        'urgency': 'Low',
        'service': 'Scaling & Cleaning',
        'advice': 'Often caused by plaque. A cleaning plus tongue hygiene usually helps.',
    },
]

URGENCY_SCORE = {'Low': 25, 'Medium': 60, 'High': 90}


def symptom_triage(text):
    text_l = (text or '').lower()
    matches = []
    for rule in SYMPTOM_RULES:
        hits = sum(1 for kw in rule['keywords'] if kw in text_l)
        if hits:
            matches.append((hits, rule))
    if not matches:
        return {
            'matched': False,
            'condition': 'General check-up recommended',
            'urgency': 'Low',
            'urgency_score': 20,
            'service': 'General Consultation',
            'advice': 'We could not pinpoint a specific issue. A routine check-up is the safest next step.',
            'alternatives': [],
        }
    matches.sort(key=lambda x: x[0], reverse=True)
    best = matches[0][1]
    alternatives = [m[1]['condition'] for m in matches[1:3]]
    return {
        'matched': True,
        'condition': best['condition'],
        'urgency': best['urgency'],
        'urgency_score': URGENCY_SCORE[best['urgency']],
        'service': best['service'],
        'advice': best['advice'],
        'alternatives': alternatives,
    }


# ---------------------------------------------------------------------------
# 2. Chatbot (intent based)
# ---------------------------------------------------------------------------
CHATBOT_INTENTS = [
    (['hi', 'hello', 'hey', 'good morning', 'good evening'],
     "Hello! I'm DentaBot 🦷 — your virtual dental assistant. Ask me about appointments, services, timings or prices."),
    (['appointment', 'book', 'booking', 'schedule'],
     "You can book an appointment from your dashboard → 'Book Appointment'. Choose a dentist, service, date and time. Would you like me to point you there?"),
    (['timing', 'time', 'open', 'hours', 'close'],
     "Our clinic is open Mon–Sat, 9:00 AM to 8:00 PM. Sundays are for emergencies only."),
    (['price', 'cost', 'fee', 'charge', 'how much'],
     "Prices depend on the service. Cleaning starts around ₹500, fillings ₹800, and whitening ₹3000. Try the AI Cost Estimator for a tailored quote."),
    (['pain', 'hurt', 'ache', 'emergency'],
     "Sorry you're in pain! For severe pain, book an Emergency Consultation. You can also use the Symptom Checker for quick guidance."),
    (['location', 'address', 'where'],
     "We're at DentaCare Clinic, Smile Street, Dental City. Parking is available on-site."),
    (['insurance', 'claim'],
     "We accept most major insurance providers and offer UPI, card and cash payments."),
    (['whiten', 'whitening', 'clean', 'braces', 'implant', 'root canal', 'filling'],
     "Yes, we offer that! Check the Services page for details, duration and pricing."),
    (['thanks', 'thank you', 'thankyou', 'bye'],
     "You're welcome! Take care of that smile 😄. Feel free to ask anything else."),
]


def chatbot_response(message):
    msg = (message or '').lower().strip()
    if not msg:
        return "Please type a question and I'll do my best to help!"
    for keywords, reply in CHATBOT_INTENTS:
        if any(kw in msg for kw in keywords):
            return reply
    return ("I'm still learning! I can help with appointments, services, timings, "
            "pricing, location and payments. Try rephrasing, or contact the front desk.")


# ---------------------------------------------------------------------------
# 3. No-show risk predictor
# ---------------------------------------------------------------------------
def no_show_risk(appointment):
    """Heuristic 0-100 risk score for an appointment being a no-show."""
    risk = 20
    patient = appointment.patient
    history = patient.appointments.all()
    past_no_shows = history.filter(status='no_show').count()
    past_total = history.count()
    if past_total:
        risk += int((past_no_shows / past_total) * 40)
    # Longer lead time -> slightly higher risk
    lead = (appointment.date - date.today()).days
    if lead > 14:
        risk += 15
    elif lead > 7:
        risk += 8
    # Early morning slots are missed more often
    if appointment.time and appointment.time.hour < 10:
        risk += 10
    # Missing phone number -> hard to remind
    if not patient.phone or patient.phone.strip('0') == '':
        risk += 10
    return max(5, min(risk, 95))


def risk_band(score):
    if score >= 66:
        return ('High', 'danger')
    if score >= 40:
        return ('Medium', 'warning')
    return ('Low', 'success')


# ---------------------------------------------------------------------------
# 4. Cost estimator
# ---------------------------------------------------------------------------
COMPLEXITY_MULTIPLIER = {'simple': 1.0, 'moderate': 1.4, 'complex': 1.9}


def estimate_cost(base_price, complexity='simple', teeth=1, insurance=False):
    base = float(base_price or 0)
    mult = COMPLEXITY_MULTIPLIER.get(complexity, 1.0)
    subtotal = base * mult * max(1, int(teeth))
    tax = subtotal * 0.05
    total = subtotal + tax
    covered = total * 0.5 if insurance else 0
    return {
        'base': round(base, 2),
        'multiplier': mult,
        'teeth': int(teeth),
        'subtotal': round(subtotal, 2),
        'tax': round(tax, 2),
        'insurance_covered': round(covered, 2),
        'total': round(total - covered, 2),
        'low': round((total - covered) * 0.9, 2),
        'high': round((total - covered) * 1.15, 2),
    }
