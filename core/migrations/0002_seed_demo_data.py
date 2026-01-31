from django.db import migrations
import datetime


def seed_demo_data(apps, schema_editor):
    Hospital = apps.get_model('core', 'Hospital')
    Doctor = apps.get_model('core', 'Doctor')
    Pharmacy = apps.get_model('core', 'Pharmacy')
    Medicine = apps.get_model('core', 'Medicine')
    User = apps.get_model('auth', 'User')
    UserProfile = apps.get_model('core', 'UserProfile')

    # Hospitals
    cities = ['Pune', 'Mumbai', 'Delhi', 'Bengaluru', 'Hyderabad', 'Chennai']
    for i in range(30):
        city = cities[i % len(cities)]
        hospital, _ = Hospital.objects.get_or_create(
            name=f'CURA Demo Hospital {i + 1}',
            defaults={
                'address': f'{i + 1} Demo Street, {city}',
                'city': city,
                'state': 'India',
                'hospital_type': 'Multispeciality' if i % 2 == 0 else 'General',
                'established_year': 1990 + (i % 20),
                'rating': 3.5 + (i % 15) / 10,
                'contact_phone': f'+91-99999{i:05d}',
                'emergency_contact': f'+91-88888{i:05d}',
                'support_24_7': True,
                'specialties_offered': 'Cardiology, Neurology, Orthopedics',
            },
        )

    hospitals = list(Hospital.objects.all()[:10])
    if not hospitals:
        return

    # Doctors
    specialities = ['Cardiology', 'Neurology', 'Orthopedics', 'General']
    languages = ['English, Hindi', 'English, Marathi', 'English, Kannada', 'English, Telugu']
    for i in range(30):
        hospital = hospitals[i % len(hospitals)]
        Doctor.objects.get_or_create(
            name=f'Dr Demo {i + 1}',
            hospital=hospital,
            defaults={
                'speciality': specialities[i % len(specialities)],
                'experience_years': 3 + (i % 20),
                'consultation_fee': 300 + (i * 10),
                'available_from': datetime.time(9, 0),
                'available_to': datetime.time(17, 0),
                'languages_spoken': languages[i % len(languages)],
                'city': hospital.city,
                'is_active': True,
            },
        )

    # Pharmacy / medicines
    pharmacy_user, _ = User.objects.get_or_create(
        username='demo_pharmacy_admin',
        defaults={'email': 'demo_pharmacy@example.com'},
    )
    UserProfile.objects.get_or_create(
        user=pharmacy_user,
        defaults={'role': 'PHARMACY_ADMIN', 'city': 'Pune'},
    )
    pharmacy, _ = Pharmacy.objects.get_or_create(
        user=pharmacy_user,
        defaults={
            'name': 'CURA Demo Pharmacy',
            'city': 'Pune',
            'address': '1 Demo Pharma Street, Pune',
            'contact_phone': '+91-77777-00000',
        },
    )

    brands = ['CURA Life', 'HealthPlus', 'MedTrust', 'CareWell', 'HealFast']
    forms = ['Tablet', 'Syrup', 'Capsule']
    strengths = ['250 mg', '500 mg', '650 mg']
    base_names = [
        'Paracetamol 650 mg Tablet',
        'Ibuprofen 400 mg Tablet',
        'Amoxicillin 500 mg Capsule',
        'Azithromycin 500 mg Tablet',
        'Cetirizine 10 mg Tablet',
        'Pantoprazole 40 mg Tablet',
        'Metformin 500 mg Tablet',
        'Atorvastatin 10 mg Tablet',
        'Losartan 50 mg Tablet',
        'Vitamin D3 60k IU Capsule',
    ]

    for i in range(30):
        base = base_names[i % len(base_names)]
        batch_suffix = (i // len(base_names)) + 1
        name = f'{base} (Pack {batch_suffix})'
        Medicine.objects.get_or_create(
            pharmacy=pharmacy,
            name=name,
            defaults={
                'description': 'Sample medicine entry for testing CURA search and ordering.',
                'brand': brands[i % len(brands)],
                'form': forms[i % len(forms)],
                'strength': strengths[i % len(strengths)],
                'pack_size': 10 + (i % 3) * 10,
                'price': 50 + (i * 5),
                'stock': 20 + (i * 2),
                'is_essential': i % 2 == 0,
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_doctor_qualification_doctor_rating_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_demo_data, migrations.RunPython.noop),
    ]

