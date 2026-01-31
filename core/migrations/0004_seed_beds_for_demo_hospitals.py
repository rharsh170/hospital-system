from django.db import migrations


def seed_beds(apps, schema_editor):
    Hospital = apps.get_model('core', 'Hospital')
    HospitalBed = apps.get_model('core', 'HospitalBed')

    bed_types = ['ICU', 'GENERAL', 'EMERGENCY']
    for hospital in Hospital.objects.all():
        # If beds already exist for this hospital, skip.
        if HospitalBed.objects.filter(hospital=hospital).exists():
            continue
        for bt in bed_types:
            total = 20 if bt == 'GENERAL' else 10
            available = total // 2
            HospitalBed.objects.create(
                hospital=hospital,
                bed_type=bt,
                total_beds=total,
                available_beds=available,
            )


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_seed_demo_data'),
    ]

    operations = [
        migrations.RunPython(seed_beds, migrations.RunPython.noop),
    ]

