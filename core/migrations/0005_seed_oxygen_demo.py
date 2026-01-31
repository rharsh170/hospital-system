from django.db import migrations


def seed_oxygen_demo(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    UserProfile = apps.get_model('core', 'UserProfile')
    OxygenSupplier = apps.get_model('core', 'OxygenSupplier')
    OxygenCylinderStock = apps.get_model('core', 'OxygenCylinderStock')

    supplier_user, _ = User.objects.get_or_create(
        username='demo_oxygen_supplier',
        defaults={'email': 'demo_oxygen@example.com'},
    )
    UserProfile.objects.get_or_create(
        user=supplier_user,
        defaults={'role': 'OXYGEN_SUPPLIER', 'city': 'Pune'},
    )

    supplier, _ = OxygenSupplier.objects.get_or_create(
        user=supplier_user,
        defaults={
            'name': 'CURA Oxygen Services',
            'city': 'Pune',
            'contact_phone': '+91-76666-00000',
            'delivery_available': True,
        },
    )

    capacities = [5, 10, 15, 20, 30, 40, 47, 50, 60, 80]
    base_price = 800

    for idx, cap in enumerate(capacities):
        OxygenCylinderStock.objects.get_or_create(
            supplier=supplier,
            capacity_litres=cap,
            defaults={
                'price_per_cylinder': base_price + idx * 150,
                'available_cylinders': 5 + idx,
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_seed_beds_for_demo_hospitals'),
    ]

    operations = [
        migrations.RunPython(seed_oxygen_demo, migrations.RunPython.noop),
    ]

