from django.contrib import admin
from .models import (
    UserProfile,
    Hospital,
    HospitalBed,
    Doctor,
    Appointment,
    OxygenSupplier,
    OxygenCylinderStock,
    OxygenBooking,
    Pharmacy,
    Medicine,
    MedicineOrder,
    MedicineOrderItem,
    SupportRequest,
    Notification,
)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'city', 'phone')


class HospitalBedInline(admin.TabularInline):
    model = HospitalBed
    extra = 1


class DoctorInline(admin.TabularInline):
    model = Doctor
    extra = 1


@admin.register(Hospital)
class HospitalAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'state', 'rating', 'support_24_7')
    inlines = [HospitalBedInline, DoctorInline]


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('name', 'speciality', 'hospital', 'city', 'consultation_fee', 'is_active')
    list_filter = ('speciality', 'city', 'hospital')


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('patient', 'doctor', 'date', 'time_slot', 'status')
    list_filter = ('status', 'date')


class OxygenCylinderStockInline(admin.TabularInline):
    model = OxygenCylinderStock
    extra = 1


@admin.register(OxygenSupplier)
class OxygenSupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'contact_phone', 'delivery_available')
    inlines = [OxygenCylinderStockInline]


@admin.register(OxygenCylinderStock)
class OxygenCylinderStockAdmin(admin.ModelAdmin):
    list_display = ('supplier', 'capacity_litres', 'price_per_cylinder', 'available_cylinders')


@admin.register(OxygenBooking)
class OxygenBookingAdmin(admin.ModelAdmin):
    list_display = ('patient', 'stock', 'quantity', 'scheduled_date', 'status')
    list_filter = ('status',)


class MedicineInline(admin.TabularInline):
    model = Medicine
    extra = 1


@admin.register(Pharmacy)
class PharmacyAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'contact_phone')
    inlines = [MedicineInline]


@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = ('name', 'pharmacy', 'price', 'stock', 'is_essential')
    list_filter = ('is_essential',)


class MedicineOrderItemInline(admin.TabularInline):
    model = MedicineOrderItem
    extra = 0


@admin.register(MedicineOrder)
class MedicineOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'pharmacy', 'status', 'created_at')
    inlines = [MedicineOrderItemInline]


@admin.register(SupportRequest)
class SupportRequestAdmin(admin.ModelAdmin):
    list_display = ('subject', 'name', 'is_emergency', 'status', 'created_at')
    list_filter = ('is_emergency', 'status')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'notification_type', 'message', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read')
