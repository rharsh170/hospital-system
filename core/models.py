from django.conf import settings
from django.db import models
from django.utils import timezone


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('PATIENT', 'Patient'),
        ('HOSPITAL_ADMIN', 'Hospital Admin'),
        ('PHARMACY_ADMIN', 'Pharmacy Admin'),
        ('OXYGEN_SUPPLIER', 'Oxygen Supplier'),
        ('ADMIN', 'Platform Admin'),
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
    hospital_type = models.CharField(
        max_length=100,
        blank=True,
        help_text="e.g. Multispeciality, Cardiac Center, Children’s Hospital",
    )
    established_year = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Year the hospital was established",
    )
    website = models.URLField(blank=True)
    image_url = models.URLField(
        blank=True,
        help_text="Optional hero/cover image shown on the hospital detail page",
    )
    rating = models.DecimalField(max_digits=2, decimal_places=1, default=3.0)
    contact_phone = models.CharField(max_length=20)
    emergency_contact = models.CharField(max_length=20)
    support_24_7 = models.BooleanField(default=True)
    specialties_offered = models.CharField(
        max_length=255,
        blank=True,
        help_text="Comma-separated list of key specialties (Cardiology, Neurology, etc.)",
    )

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
    qualification = models.CharField(
        max_length=255,
        blank=True,
        help_text="e.g. MBBS, MD (Cardiology)",
    )
    rating = models.DecimalField(
        max_digits=2,
        decimal_places=1,
        default=4.5,
        help_text="Average patient rating out of 5",
    )
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
    PAYMENT_CHOICES = [
        ('CASH', 'Cash on Delivery / Pickup'),
        ('INSURANCE', 'Insurance / TPA'),
        ('ONLINE', 'Online Payment'),
    ]
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
    time_slot = models.TimeField(help_text="Expected delivery/pickup time", null=True, blank=True)
    payment_option = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='CASH')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Oxygen Booking #{self.id} for {self.patient.username} - {self.stock.capacity_litres}L from {self.stock.supplier.name}'


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
    brand = models.CharField(max_length=255, blank=True)
    form = models.CharField(
        max_length=50,
        blank=True,
        help_text="e.g. Tablet, Syrup, Injection",
    )
    strength = models.CharField(
        max_length=50,
        blank=True,
        help_text="e.g. 500 mg, 5 mg/ml",
    )
    pack_size = models.PositiveIntegerField(
        default=1,
        help_text="Number of units (e.g. tablets) per pack",
    )
    price = models.DecimalField(max_digits=8, decimal_places=2)
    stock = models.PositiveIntegerField()
    is_essential = models.BooleanField(default=True)
    image_url = models.URLField(
        blank=True,
        help_text="Optional image for advanced medicine cards",
    )

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
    contact_phone = models.CharField(max_length=20, blank=True)
    shipping_address = models.TextField(blank=True)

    def __str__(self):
        return f'Medicine order #{self.id}'


class MedicineOrderItem(models.Model):
    order = models.ForeignKey(MedicineOrder, on_delete=models.CASCADE, related_name='items')
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price_at_order = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return f'{self.medicine.name} x {self.quantity}'


class Cart(models.Model):
    """
    Lightweight e‑commerce cart for medicine packs.
    Tied to an authenticated user; items are converted into MedicineOrder
    records on checkout.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='carts',
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f'Cart #{self.id} for {self.user.username}'

    def total_items(self):
        return sum(item.quantity for item in self.items.all())

    def total_price(self):
        return sum(item.subtotal for item in self.items.select_related('medicine'))


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('cart', 'medicine')

    def __str__(self):
        return f'{self.medicine.name} x {self.quantity} (cart #{self.cart_id})'

    @property
    def subtotal(self):
        return self.quantity * self.medicine.price


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


class BedBooking(models.Model):
    PAYMENT_CHOICES = [
        ('CASH', 'Cash at Hospital'),
        ('INSURANCE', 'Insurance / TPA'),
        ('ONLINE', 'Online Payment'),
    ]
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('CANCELLED', 'Cancelled'),
    ]
    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bed_bookings')
    hospital_bed = models.ForeignKey(HospitalBed, on_delete=models.CASCADE, related_name='bookings')
    booking_date = models.DateField()
    time_slot = models.TimeField(help_text="Expected arrival time")
    payment_option = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='CASH')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Bed Booking #{self.id} for {self.patient.username} at {self.hospital_bed.hospital.name}'
