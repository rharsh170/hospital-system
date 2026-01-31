from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import (
    Appointment,
    BedBooking,
    CartItem,
    MedicineOrder,
    MedicineOrderItem,
    OxygenBooking,
    SupportRequest,
    UserProfile,
)


class PatientRegistrationForm(UserCreationForm):
    phone = forms.CharField(required=False)
    city = forms.CharField(required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'phone', 'city', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.role = 'PATIENT'
            profile.phone = self.cleaned_data.get('phone')
            profile.city = self.cleaned_data.get('city')
            profile.save()
        return user


class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['date', 'time_slot']


class OxygenBookingForm(forms.ModelForm):
    class Meta:
        model = OxygenBooking
        fields = ['quantity', 'delivery_address', 'scheduled_date', 'time_slot', 'payment_option']
        widgets = {
            'scheduled_date': forms.DateInput(attrs={'type': 'date'}),
            'time_slot': forms.TimeInput(attrs={'type': 'time'}),
        }


class MedicineOrderItemForm(forms.ModelForm):
    class Meta:
        model = MedicineOrderItem
        fields = ['quantity']


class CartAddItemForm(forms.ModelForm):
    """
    Simple form used on the medicine listing page to add packs to cart.
    """

    class Meta:
        model = CartItem
        fields = ['quantity']


class MedicineOrderContactForm(forms.ModelForm):
    """
    Captures patient contact phone and delivery address at checkout.
    """

    class Meta:
        model = MedicineOrder
        fields = ['contact_phone', 'shipping_address']


class SupportRequestForm(forms.ModelForm):
    class Meta:
        model = SupportRequest
        fields = ['name', 'contact', 'subject', 'description', 'is_emergency']

class BedBookingForm(forms.ModelForm):
    class Meta:
        model = BedBooking
        fields = ['booking_date', 'time_slot', 'payment_option']
        widgets = {
            'booking_date': forms.DateInput(attrs={'type': 'date'}),
            'time_slot': forms.TimeInput(attrs={'type': 'time'}),
        }
