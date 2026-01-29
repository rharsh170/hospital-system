from django.conf import settings
from django.db import models
from django.utils import timezone


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('PATIENT', 'Patient'),
        ('HOSPITAL_ADMIN', 'Hospital Admin'),
        ('PHARMACY_ADMIN', 'Pharmacy Admin'),
        ('OXYGEN_SUPPLIER', 'Oxygen Supplier'),
    ]
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='PATIENT')
    phone = models.CharField(max_length=20, blank=True)
    city = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f'{self.user.username} ({self.role})'


class Hospital(models.Model):
    name = models.CharField(max_length=255)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    rating = models.DecimalField(max_digits=2, decimal_places=1, default=3.0)
    contact_phone = models.CharField(max_length=20)
    emergency_contact = models.CharField(max_length=20)
    support_24_7 = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class HospitalBed(models.Model):
    BED_TYPE_CHOICES = [
        ('ICU', 'ICU'),
        ('GENERAL', 'General'),
        ('EMERGENCY', 'Emergency'),
    ]
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='beds')
    bed_type = models.CharField(max_length=20, choices=BED_TYPE_CHOICES)
    total_beds = models.PositiveIntegerField()
    available_beds = models.PositiveIntegerField()

    def __str__(self):
        return f'{self.hospital.name} - {self.bed_type}'


class Doctor(models.Model):
    SPECIALITY_CHOICES = [
        ('Cardiology', 'Cardiology'),
        ('Neurology', 'Neurology'),
        ('Orthopedics', 'Orthopedics'),
        ('General', 'General Physician'),
    ]
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='doctors')
    name = models.CharField(max_length=255)
    speciality = models.CharField(max_length=100, choices=SPECIALITY_CHOICES)
    experience_years = models.PositiveIntegerField()
    consultation_fee = models.DecimalField(max_digits=8, decimal_places=2)
    available_from = models.TimeField()
    available_to = models.TimeField()
    languages_spoken = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.name} - {self.speciality}'


class Appointment(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('CANCELLED', 'Cancelled'),
    ]
    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='appointments')
    date = models.DateField()
    time_slot = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Appointment with {self.doctor} on {self.date}'


class OxygenSupplier(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='oxygen_supplier')
    name = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    contact_phone = models.CharField(max_length=20)
    delivery_available = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class OxygenCylinderStock(models.Model):
    supplier = models.ForeignKey(OxygenSupplier, on_delete=models.CASCADE, related_name='stocks')
    capacity_litres = models.PositiveIntegerField()
    price_per_cylinder = models.DecimalField(max_digits=8, decimal_places=2)
    available_cylinders = models.PositiveIntegerField()

    def __str__(self):
        return f'{self.supplier.name} - {self.capacity_litres}L'


class OxygenBooking(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
    ]
    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='oxygen_bookings')
    stock = models.ForeignKey(OxygenCylinderStock, on_delete=models.CASCADE, related_name='bookings')
    quantity = models.PositiveIntegerField()
    delivery_address = models.TextField()
    scheduled_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Oxygen booking #{self.id} - {self.patient}'


class Pharmacy(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='pharmacy')
    name = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    address = models.TextField()
    contact_phone = models.CharField(max_length=20)

    def __str__(self):
        return self.name


class Medicine(models.Model):
    pharmacy = models.ForeignKey(Pharmacy, on_delete=models.CASCADE, related_name='medicines')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    stock = models.PositiveIntegerField()
    is_essential = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.name} ({self.pharmacy.name})'


class MedicineOrder(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('DISPATCHED', 'Dispatched'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
    ]
    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='medicine_orders')
    pharmacy = models.ForeignKey(Pharmacy, on_delete=models.CASCADE, related_name='orders')
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')

    def __str__(self):
        return f'Medicine order #{self.id}'


class MedicineOrderItem(models.Model):
    order = models.ForeignKey(MedicineOrder, on_delete=models.CASCADE, related_name='items')
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price_at_order = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return f'{self.medicine.name} x {self.quantity}'


class SupportRequest(models.Model):
    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('IN_PROGRESS', 'In Progress'),
        ('RESOLVED', 'Resolved'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=255)
    contact = models.CharField(max_length=50, blank=True)
    subject = models.CharField(max_length=255)
    description = models.TextField()
    is_emergency = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.subject


class Notification(models.Model):
    NOTIFICATION_TYPE_CHOICES = [
        ('BED', 'Bed Availability'),
        ('MEDICINE', 'Medicine Restock'),
        ('OXYGEN', 'Oxygen Restock'),
        ('APPOINTMENT', 'Appointment Reminder'),
        ('SUPPORT', 'Support Update'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPE_CHOICES)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f'Notification for {self.user.username}'
