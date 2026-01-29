from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import (
    AppointmentForm,
    OxygenBookingForm,
    PatientRegistrationForm,
    MedicineOrderItemForm,
    SupportRequestForm,
)
from .models import (
    Appointment,
    Doctor,
    Hospital,
    HospitalBed,
    Medicine,
    MedicineOrder,
    Notification,
    OxygenBooking,
    OxygenCylinderStock,
    OxygenSupplier,
    Pharmacy,
    SupportRequest,
    UserProfile,
)


def home(request):
    """
    Entry point for end-users.
    If not authenticated, always send them to login first.
    Once authenticated, send them to the appropriate dashboard.
    """
    if not request.user.is_authenticated:
        return redirect('login')
    return redirect('dashboard')


def register(request):
    if request.method == 'POST':
        form = PatientRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Registration successful. Please log in.')
            return redirect('login')
    else:
        form = PatientRegistrationForm()
    return render(request, 'core/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid credentials')
    return render(request, 'core/login.html')


def logout_view(request):
    logout(request)
    return redirect('home')


def role_required(allowed_roles):
    def decorator(view_func):
        @login_required
        def _wrapped(request, *args, **kwargs):
            try:
                role = request.user.userprofile.role
            except UserProfile.DoesNotExist:
                messages.error(request, 'Role not assigned. Contact admin.')
                return redirect('home')
            if role not in allowed_roles:
                messages.error(request, 'You are not authorized to view this page.')
                return redirect('dashboard')
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator


@login_required
def dashboard(request):
    try:
        role = request.user.userprofile.role
    except UserProfile.DoesNotExist:
        role = None

    if role == 'HOSPITAL_ADMIN':
        return redirect('hospital_admin_dashboard')
    elif role == 'PHARMACY_ADMIN':
        return redirect('pharmacy_admin_dashboard')
    elif role == 'OXYGEN_SUPPLIER':
        return redirect('oxygen_supplier_dashboard')
    else:
        return redirect('patient_dashboard')


@login_required
@role_required(['PATIENT'])
def patient_dashboard(request):
    appointments = request.user.appointments.select_related('doctor').order_by('-created_at')[:5]
    medicine_orders = request.user.medicine_orders.select_related('pharmacy').order_by('-created_at')[:5]
    oxygen_bookings = request.user.oxygen_bookings.select_related('stock').order_by('-created_at')[:5]
    notifications = request.user.notifications.order_by('-created_at')[:10]
    return render(request, 'core/dashboards/patient_dashboard.html', {
        'appointments': appointments,
        'medicine_orders': medicine_orders,
        'oxygen_bookings': oxygen_bookings,
        'notifications': notifications,
    })


@login_required
@role_required(['HOSPITAL_ADMIN'])
def hospital_admin_dashboard(request):
    hospitals = Hospital.objects.all()
    appointments = Appointment.objects.select_related('doctor', 'patient').order_by('-created_at')[:10]
    return render(request, 'core/dashboards/hospital_admin_dashboard.html', {
        'hospitals': hospitals,
        'appointments': appointments,
    })


@login_required
@role_required(['PHARMACY_ADMIN'])
def pharmacy_admin_dashboard(request):
    pharmacy = getattr(request.user, 'pharmacy', None)
    medicines = pharmacy.medicines.all() if pharmacy else Medicine.objects.none()
    orders = pharmacy.orders.order_by('-created_at')[:10] if pharmacy else MedicineOrder.objects.none()
    return render(request, 'core/dashboards/pharmacy_admin_dashboard.html', {
        'pharmacy': pharmacy,
        'medicines': medicines,
        'orders': orders,
    })


@login_required
@role_required(['OXYGEN_SUPPLIER'])
def oxygen_supplier_dashboard(request):
    supplier = getattr(request.user, 'oxygen_supplier', None)
    stocks = supplier.stocks.all() if supplier else OxygenCylinderStock.objects.none()
    bookings_flat = OxygenBooking.objects.filter(stock__supplier=supplier).order_by('-created_at')[:20] if supplier else OxygenBooking.objects.none()
    return render(request, 'core/dashboards/oxygen_supplier_dashboard.html', {
        'supplier': supplier,
        'stocks': stocks,
        'bookings': bookings_flat,
    })


def hospital_list(request):
    city = request.GET.get('city')
    bed_type = request.GET.get('bed_type')
    min_rating = request.GET.get('min_rating')

    hospitals = Hospital.objects.all()

    if city:
        hospitals = hospitals.filter(city__icontains=city)
    if min_rating:
        hospitals = hospitals.filter(rating__gte=min_rating)
    if bed_type:
        hospitals = hospitals.filter(beds__bed_type=bed_type).distinct()

    context = {
        'hospitals': hospitals.prefetch_related('beds'),
        'selected_city': city or '',
        'selected_bed_type': bed_type or '',
        'selected_min_rating': min_rating or '',
    }

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        data = []
        for hospital in context['hospitals']:
            beds = []
            for b in hospital.beds.all():
                beds.append({
                    'bed_type': b.bed_type,
                    'total_beds': b.total_beds,
                    'available_beds': b.available_beds,
                })
            data.append({
                'name': hospital.name,
                'city': hospital.city,
                'rating': float(hospital.rating),
                'beds': beds,
            })
        return JsonResponse({'hospitals': data})
    return render(request, 'core/hospitals/hospital_list.html', context)


def hospital_detail(request, pk):
    hospital = get_object_or_404(Hospital, pk=pk)
    beds = hospital.beds.all()
    doctors = hospital.doctors.all()
    return render(request, 'core/hospitals/hospital_detail.html', {
        'hospital': hospital,
        'beds': beds,
        'doctors': doctors,
    })


def doctor_search(request):
    speciality = request.GET.get('speciality')
    city = request.GET.get('city')
    doctors = Doctor.objects.filter(is_active=True)

    if speciality:
        doctors = doctors.filter(speciality__iexact=speciality)
    if city:
        doctors = doctors.filter(city__icontains=city)

    return render(request, 'core/doctors/doctor_search.html', {
        'doctors': doctors.select_related('hospital'),
        'selected_speciality': speciality or '',
        'selected_city': city or '',
    })


def doctor_detail(request, pk):
    doctor = get_object_or_404(Doctor, pk=pk)
    return render(request, 'core/doctors/doctor_detail.html', {'doctor': doctor})


@login_required
@role_required(['PATIENT'])
def book_appointment(request, doctor_id):
    doctor = get_object_or_404(Doctor, id=doctor_id, is_active=True)
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.patient = request.user
            appointment.doctor = doctor
            appointment.save()
            Notification.objects.create(
                user=request.user,
                message=f'Appointment booked with Dr. {doctor.name} on {appointment.date}.',
                notification_type='APPOINTMENT',
            )
            messages.success(request, 'Appointment booked successfully.')
            return redirect('patient_dashboard')
    else:
        form = AppointmentForm()
    return render(request, 'core/doctors/book_appointment.html', {
        'doctor': doctor,
        'form': form,
    })


def oxygen_list(request):
    city = request.GET.get('city')
    suppliers = OxygenSupplier.objects.all().select_related('user')
    if city:
        suppliers = suppliers.filter(city__icontains=city)
    suppliers = suppliers.prefetch_related('stocks')
    return render(request, 'core/oxygen/oxygen_list.html', {
        'suppliers': suppliers,
        'selected_city': city or '',
    })


@login_required
@role_required(['PATIENT'])
def oxygen_booking_create(request, stock_id):
    stock = get_object_or_404(OxygenCylinderStock, id=stock_id)
    if request.method == 'POST':
        form = OxygenBookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.patient = request.user
            booking.stock = stock
            if booking.quantity > stock.available_cylinders:
                messages.error(request, 'Not enough cylinders available.')
            else:
                booking.save()
                stock.available_cylinders -= booking.quantity
                stock.save()
                Notification.objects.create(
                    user=request.user,
                    message=f'Oxygen booking #{booking.id} created.',
                    notification_type='OXYGEN',
                )
                messages.success(request, 'Oxygen booking created.')
                return redirect('patient_dashboard')
    else:
        form = OxygenBookingForm()
    return render(request, 'core/oxygen/oxygen_booking_form.html', {
        'stock': stock,
        'form': form,
    })


def medicine_search(request):
    name = request.GET.get('name')
    city = request.GET.get('city')
    medicines = Medicine.objects.select_related('pharmacy').all()

    if name:
        medicines = medicines.filter(name__icontains=name)
    if city:
        medicines = medicines.filter(pharmacy__city__icontains=city)

    return render(request, 'core/medicines/medicine_search.html', {
        'medicines': medicines,
        'selected_name': name or '',
        'selected_city': city or '',
    })


@login_required
@role_required(['PATIENT'])
def medicine_order_create(request, medicine_id):
    medicine = get_object_or_404(Medicine, id=medicine_id)
    if request.method == 'POST':
        item_form = MedicineOrderItemForm(request.POST)
        if item_form.is_valid():
            quantity = item_form.cleaned_data['quantity']
            if quantity > medicine.stock:
                messages.error(request, 'Not enough stock.')
            else:
                order = MedicineOrder.objects.create(
                    patient=request.user,
                    pharmacy=medicine.pharmacy,
                    status='PENDING',
                )
                MedicineOrderItem.objects.create(
                    order=order,
                    medicine=medicine,
                    quantity=quantity,
                    price_at_order=medicine.price,
                )
                medicine.stock -= quantity
                medicine.save()
                Notification.objects.create(
                    user=request.user,
                    message=f'Medicine order #{order.id} created.',
                    notification_type='MEDICINE',
                )
                messages.success(request, 'Medicine order placed.')
                return redirect('patient_dashboard')
    else:
        item_form = MedicineOrderItemForm()
    return render(request, 'core/medicines/medicine_order_form.html', {
        'medicine': medicine,
        'item_form': item_form,
    })


@login_required
def notifications_list(request):
    notifications = request.user.notifications.order_by('-created_at')
    return render(request, 'core/notifications/notification_list.html', {
        'notifications': notifications,
    })


@login_required
@require_POST
def notification_mark_read(request, pk):
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.is_read = True
    notification.save()
    return redirect('notifications_list')


def emergency_contacts(request):
    return render(request, 'core/support/emergency_contacts.html')


def support_request_create(request):
    if request.method == 'POST':
        form = SupportRequestForm(request.POST)
        if form.is_valid():
            support = form.save(commit=False)
            if request.user.is_authenticated:
                support.user = request.user
            support.save()
            if support.user:
                Notification.objects.create(
                    user=support.user,
                    message=f'Support request \"{support.subject}\" received.',
                    notification_type='SUPPORT',
                )
            messages.success(request, 'Support request submitted. Our team will contact you soon.')
            return redirect('home')
    else:
        form = SupportRequestForm()
    return render(request, 'core/support/support_request_form.html', {'form': form})
