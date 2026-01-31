from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .forms import (
    AppointmentForm,
    BedBookingForm,
    CartAddItemForm,
    MedicineOrderContactForm,
    MedicineOrderItemForm,
    OxygenBookingForm,
    PatientRegistrationForm,
    SupportRequestForm,
)
from .models import (
    Appointment,
    BedBooking,
    Cart,
    CartItem,
    Doctor,
    Hospital,
    HospitalBed,
    Medicine,
    MedicineOrder,
    MedicineOrderItem,
    Notification,
    OxygenBooking,
    OxygenCylinderStock,
    OxygenSupplier,
    Pharmacy,
    SupportRequest,
    UserProfile,
)


def home(request):
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


@require_POST
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
                # Allow staff/superusers to bypass explicit role assignment.
                if request.user.is_staff or request.user.is_superuser:
                    return view_func(request, *args, **kwargs)
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

    if role == 'PATIENT':
        return redirect('patient_dashboard')
    elif role == 'ADMIN':
        return redirect('admin_dashboard')
    elif role == 'HOSPITAL_ADMIN':
        return redirect('hospital_admin_dashboard')
    elif role == 'PHARMACY_ADMIN':
        return redirect('pharmacy_admin_dashboard')
    elif role == 'OXYGEN_SUPPLIER':
        return redirect('oxygen_supplier_dashboard')
    elif request.user.is_staff or request.user.is_superuser:
        return redirect('admin_dashboard')
    else:
        # Fallback for users with no profile and no staff status (shouldn't happen with default PATIENT role)
        return redirect('patient_dashboard')


@login_required
@role_required(['PATIENT'])
def patient_dashboard(request):
    appointments = request.user.appointments.select_related('doctor').order_by('-created_at')[:5]
    medicine_orders = request.user.medicine_orders.select_related('pharmacy').order_by('-created_at')[:5]
    oxygen_bookings = request.user.oxygen_bookings.select_related('stock').order_by('-created_at')[:5]
    notifications = request.user.notifications.order_by('-created_at')[:10]
    bed_bookings = request.user.bed_bookings.select_related('hospital_bed__hospital').order_by('-created_at')[:5]
    return render(request, 'core/dashboards/patient_dashboard.html', {
        'appointments': appointments,
        'medicine_orders': medicine_orders,
        'oxygen_bookings': oxygen_bookings,
        'notifications': notifications,
        'bed_bookings': bed_bookings,
    })


@login_required
@staff_member_required
@require_POST
def admin_update_appointment_status(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    status = request.POST.get('status')
    valid_statuses = {choice[0] for choice in Appointment.STATUS_CHOICES}
    if status in valid_statuses:
        appointment.status = status
        appointment.save()
        Notification.objects.create(
            user=appointment.patient,
            message=f'Your appointment with Dr. {appointment.doctor.name} on {appointment.date} is now {status}.',
            notification_type='APPOINTMENT',
        )
        messages.success(request, 'Appointment status updated.')
    else:
        messages.error(request, 'Invalid status.')
    return redirect('admin_dashboard')


@login_required
@staff_member_required
@require_POST
def admin_update_medicine_order_status(request, pk):
    order = get_object_or_404(MedicineOrder, pk=pk)
    status = request.POST.get('status')
    valid_statuses = {choice[0] for choice in MedicineOrder.STATUS_CHOICES}
    if status in valid_statuses:
        order.status = status
        order.save()
        Notification.objects.create(
            user=order.patient,
            message=f'Medicine order #{order.id} status updated to {status}.',
            notification_type='MEDICINE',
        )
        messages.success(request, 'Medicine order status updated.')
    else:
        messages.error(request, 'Invalid status.')
    return redirect('admin_dashboard')


@login_required
@staff_member_required
@require_POST
def admin_update_oxygen_booking_status(request, pk):
    booking = get_object_or_404(OxygenBooking, pk=pk)
    status = request.POST.get('status')
    valid_statuses = {choice[0] for choice in OxygenBooking.STATUS_CHOICES}
    if status in valid_statuses:
        old_status = booking.status
        booking.status = status
        booking.save()
        
        # If approved, reduce available cylinders
        if status == 'CONFIRMED' and old_status != 'CONFIRMED':
            stock = booking.stock
            if stock.available_cylinders >= booking.quantity:
                stock.available_cylinders -= booking.quantity
                stock.save()
            else:
                messages.warning(request, f'Stock is insufficient, but booking was marked confirmed.')

        Notification.objects.create(
            user=booking.patient,
            message=f'Your oxygen booking from {booking.stock.supplier.name} is now {status}.',
            notification_type='OXYGEN',
        )
        messages.success(request, 'Oxygen booking status updated.')
    else:
        messages.error(request, 'Invalid status.')
    return redirect('admin_dashboard')


@login_required
@staff_member_required
@require_POST
def admin_update_support_request_status(request, pk):
    support = get_object_or_404(SupportRequest, pk=pk)
    status = request.POST.get('status')
    valid_statuses = {choice[0] for choice in SupportRequest.STATUS_CHOICES}
    if status in valid_statuses:
        support.status = status
        support.save()
        # Optional: notify linked user
        if support.user:
            Notification.objects.create(
                user=support.user,
                message=f'Your support request "{support.subject}" is now {status}.',
                notification_type='SUPPORT',
            )
        messages.success(request, 'Support request status updated.')
    else:
        messages.error(request, 'Invalid status.')
    return redirect('admin_dashboard')


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


@login_required
@staff_member_required
def admin_dashboard(request):
    # Fetch pending items for admin review
    appointments = Appointment.objects.filter(status='PENDING').select_related('doctor', 'patient').order_by('created_at')
    orders = MedicineOrder.objects.filter(status='PENDING').select_related('patient', 'pharmacy').order_by('created_at')
    oxygen_bookings = OxygenBooking.objects.filter(status='PENDING').select_related('patient', 'stock').order_by('created_at')
    support_requests = SupportRequest.objects.filter(status='OPEN').select_related('user').order_by('created_at')
    bed_bookings = BedBooking.objects.filter(status='PENDING').select_related('patient', 'hospital_bed__hospital').order_by('created_at')

    return render(request, 'core/dashboards/admin_dashboard.html', {
        'appointments': appointments,
        'orders': orders,
        'oxygen_bookings': oxygen_bookings,
        'support_requests': support_requests,
        'bed_bookings': bed_bookings,
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
                'id': hospital.id,
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


@login_required
@role_required(['PATIENT'])
def bed_booking_create(request, bed_id):
    bed = get_object_or_404(HospitalBed, id=bed_id)
    if bed.available_beds <= 0:
        messages.error(request, 'No beds of this type are currently available.')
        return redirect('hospital_detail', pk=bed.hospital.id)

    if request.method == 'POST':
        form = BedBookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.patient = request.user
            booking.hospital_bed = bed
            booking.save()
            
            # Reduce available beds temporarily? 
            # Usually for medical booking, we only reduce upon CONFIRMATION by admin.
            # But the user asked for "booking" visible in admin to approve.
            
            Notification.objects.create(
                user=request.user,
                message=f'Bed booking request for {bed.get_bed_type_display()} at {bed.hospital.name} submitted.',
                notification_type='BED',
            )
            messages.success(request, 'Bed booking request submitted. Waiting for admin approval.')
            return redirect('patient_dashboard')
    else:
        form = BedBookingForm()
    
    return render(request, 'core/hospitals/bed_booking_form.html', {
        'bed': bed,
        'form': form,
    })


@login_required
@staff_member_required
@require_POST
def admin_update_bed_booking_status(request, pk):
    booking = get_object_or_404(BedBooking, pk=pk)
    status = request.POST.get('status')
    valid_statuses = {choice[0] for choice in BedBooking.STATUS_CHOICES}
    if status in valid_statuses:
        old_status = booking.status
        booking.status = status
        booking.save()
        
        # If approved, reduce available beds
        if status == 'CONFIRMED' and old_status != 'CONFIRMED':
            bed = booking.hospital_bed
            if bed.available_beds > 0:
                bed.available_beds -= 1
                bed.save()
            else:
                messages.warning(request, f'Bed count is already 0, but booking was marked confirmed.')

        Notification.objects.create(
            user=booking.patient,
            message=f'Your bed booking at {booking.hospital_bed.hospital.name} is now {status}.',
            notification_type='BED',
        )
        messages.success(request, 'Bed booking status updated.')
    else:
        messages.error(request, 'Invalid status.')
    return redirect('admin_dashboard')


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
                Notification.objects.create(
                    user=request.user,
                    message=f'Oxygen booking request for {stock.capacity_litres}L from {stock.supplier.name} submitted.',
                    notification_type='OXYGEN',
                )
                messages.success(request, 'Oxygen booking request submitted. Waiting for approval.')
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

    add_form = CartAddItemForm()

    return render(
        request,
        'core/medicines/medicine_search.html',
        {
            'medicines': medicines,
            'selected_name': name or '',
            'selected_city': city or '',
            'cart_add_form': add_form,
        },
    )


@login_required
@role_required(['PATIENT'])
def medicine_order_create(request, medicine_id):
    medicine = get_object_or_404(Medicine, id=medicine_id)
    if request.method == 'POST':
        item_form = MedicineOrderItemForm(request.POST)
        contact_form = MedicineOrderContactForm(request.POST)
        if item_form.is_valid() and contact_form.is_valid():
            quantity = item_form.cleaned_data['quantity']
            if quantity > medicine.stock:
                messages.error(request, 'Not enough stock.')
            else:
                order = MedicineOrder.objects.create(
                    patient=request.user,
                    pharmacy=medicine.pharmacy,
                    status='PENDING',
                    contact_phone=contact_form.cleaned_data['contact_phone'],
                    shipping_address=contact_form.cleaned_data['shipping_address'],
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
                messages.success(request, 'Your order has been placed. You can track it from your dashboard.')
                return redirect('patient_dashboard')
    else:
        item_form = MedicineOrderItemForm()
        contact_form = MedicineOrderContactForm()
    return render(request, 'core/medicines/medicine_order_form.html', {
        'medicine': medicine,
        'item_form': item_form,
        'contact_form': contact_form,
    })


def _get_or_create_cart(user):
    cart, _ = Cart.objects.get_or_create(user=user, is_active=True)
    return cart


@login_required
@role_required(['PATIENT'])
@require_POST
def cart_add(request, medicine_id):
    medicine = get_object_or_404(Medicine, id=medicine_id)
    form = CartAddItemForm(request.POST)
    if form.is_valid():
        quantity = form.cleaned_data['quantity']
        if quantity <= 0:
            messages.error(request, 'Quantity must be at least 1 pack.')
            return redirect('medicine_search')

        cart = _get_or_create_cart(request.user)
        item, created = CartItem.objects.get_or_create(
            cart=cart,
            medicine=medicine,
            defaults={'quantity': quantity},
        )
        if not created:
            item.quantity += quantity
            item.save()

        messages.success(
            request,
            f'Added {quantity} pack(s) of {medicine.name} to your cart.',
        )
    else:
        messages.error(request, 'Could not add this medicine to the cart.')
    return redirect('cart_detail')


@login_required
@role_required(['PATIENT'])
def cart_detail(request):
    cart = (
        Cart.objects.filter(user=request.user, is_active=True)
        .prefetch_related('items__medicine__pharmacy')
        .first()
    )
    items = cart.items.all() if cart else []

    totals_by_pharmacy = {}
    if cart:
        for item in items:
            pharmacy = item.medicine.pharmacy
            totals_by_pharmacy.setdefault(pharmacy, 0)
            totals_by_pharmacy[pharmacy] += item.subtotal

    return render(
        request,
        'core/medicines/cart_detail.html',
        {
            'cart': cart,
            'items': items,
            'totals_by_pharmacy': totals_by_pharmacy,
        },
    )


@login_required
@role_required(['PATIENT'])
@require_POST
def cart_update(request, item_id):
    item = get_object_or_404(
        CartItem,
        id=item_id,
        cart__user=request.user,
        cart__is_active=True,
    )
    try:
        quantity = int(request.POST.get('quantity', '1'))
    except ValueError:
        quantity = 1

    if quantity <= 0:
        item.delete()
        messages.success(request, f'Removed {item.medicine.name} from your cart.')
    else:
        item.quantity = quantity
        item.save()
        messages.success(
            request,
            f'Updated {item.medicine.name} to {quantity} pack(s) in your cart.',
        )

    return redirect('cart_detail')


@login_required
@role_required(['PATIENT'])
@require_POST
def cart_remove(request, item_id):
    item = get_object_or_404(
        CartItem,
        id=item_id,
        cart__user=request.user,
        cart__is_active=True,
    )
    name = item.medicine.name
    item.delete()
    messages.success(request, f'Removed {name} from your cart.')
    return redirect('cart_detail')


@login_required
@role_required(['PATIENT'])
def cart_checkout(request):
    cart = (
        Cart.objects.filter(user=request.user, is_active=True)
        .prefetch_related('items__medicine__pharmacy')
        .first()
    )
    if not cart or not cart.items.exists():
        messages.error(request, 'Your cart is empty.')
        return redirect('medicine_search')

    items = list(cart.items.all())

    contact_form = MedicineOrderContactForm(request.POST or None)

    if request.method == 'POST':
        if not contact_form.is_valid():
            messages.error(request, 'Please provide a valid phone number and delivery address.')
        else:
            # Validate stock for each item
            for item in items:
                medicine = item.medicine
                if item.quantity > medicine.stock:
                    messages.error(
                        request,
                        f'Not enough stock for {medicine.name}. Available: {medicine.stock}',
                    )
                    return redirect('cart_detail')

            # Group items by pharmacy and create MedicineOrder(s)
            orders_created = []
            by_pharmacy = {}
            for item in items:
                by_pharmacy.setdefault(item.medicine.pharmacy, []).append(item)

            for pharmacy, pharmacy_items in by_pharmacy.items():
                order = MedicineOrder.objects.create(
                    patient=request.user,
                    pharmacy=pharmacy,
                    status='PENDING',
                    contact_phone=contact_form.cleaned_data['contact_phone'],
                    shipping_address=contact_form.cleaned_data['shipping_address'],
                )
                for item in pharmacy_items:
                    medicine = item.medicine
                    MedicineOrderItem.objects.create(
                        order=order,
                        medicine=medicine,
                        quantity=item.quantity,
                        price_at_order=medicine.price,
                    )
                    medicine.stock -= item.quantity
                    medicine.save()
                orders_created.append(order)

            # Clear cart
            cart.items.all().delete()
            cart.is_active = False
            cart.save()

            for order in orders_created:
                Notification.objects.create(
                    user=request.user,
                    message=f'Medicine order #{order.id} created from your cart.',
                    notification_type='MEDICINE',
                )

            messages.success(
                request,
                'Your order has been placed. You can track it from your dashboard.',
            )
            return redirect('patient_dashboard')

    # GET or invalid POST: show review/summary UI + contact form
    totals_by_pharmacy = {}
    for item in items:
        pharmacy = item.medicine.pharmacy
        totals_by_pharmacy.setdefault(pharmacy, 0)
        totals_by_pharmacy[pharmacy] += item.subtotal

    return render(
        request,
        'core/medicines/cart_detail.html',
        {
            'cart': cart,
            'items': items,
            'totals_by_pharmacy': totals_by_pharmacy,
            'is_checkout': True,
            'contact_form': contact_form,
        },
    )


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


def assistant_home(request):
    """
    Optional landing page (the assistant is also available site-wide via the widget).
    """
    return render(request, 'core/assistant/assistant.html')


def _assistant_live_stats(user):
    """
    'Real-time' here means live DB-backed numbers (not external APIs).
    Keep this cheap and safe to compute.
    """
    stats = {
        "hospitals": Hospital.objects.count(),
        "doctors_active": Doctor.objects.filter(is_active=True).count(),
        "oxygen_suppliers": OxygenSupplier.objects.count(),
        "medicines": Medicine.objects.count(),
        "server_time": timezone.localtime().strftime("%d %b %Y, %H:%M"),
    }
    if user and getattr(user, "is_authenticated", False):
        stats["your_unread_notifications"] = Notification.objects.filter(user=user, is_read=False).count()
    return stats


from django.conf import settings

@csrf_exempt
@require_POST
def assistant_api(request):
    """
    Intelligent Assistant powered by OpenAI (ChatGPT).
    Falls back to simple logic if no key is configured or API fails.
    """
    try:
        payload = request.POST or {}
        message = (payload.get("message") or "").strip()
    except Exception:
        message = ""

    if not message:
        return JsonResponse({"reply": "I'm listening. Ask me anything about CURA or healthcare resources."})

    # Fallback/Default suggestions
    default_suggestions = ["Show live stats", "How do I book?", "Emergency contacts", "Oxygen availability"]
    
    # Check for API Key
    api_key = getattr(settings, 'OPENAI_API_KEY', None)
    
    if not api_key:
        # Fallback to simple static logic if no key
        return _static_assistant_reply(request, message)

    try:
        import openai
        # 1. Get Live Context
        stats = _assistant_live_stats(request.user)
        user_context = f"User: {request.user.username}" if request.user.is_authenticated else "User: Guest"
        
        # 2. Construct System Prompt
        system_prompt = (
            "You are the CURA Assistant, an AI for a hospital resource platform. "
            "Your goal is to help users find beds, doctors, oxygen, and medicines. "
            "Be concise, professional, and helpful. "
            "Strictly use the following LIVE DATA to answer questions about availability. "
            "Do not make up numbers. "
            f"\n\nLIVE DATA CONTEXT:\n{stats}\n"
            f"\nUSER CONTEXT:\n{user_context}\n"
            "\nIf the user asks for actions (like booking), explain the steps on the website. "
            "For general medical advice, include a disclaimer that you are an AI and they should see a doctor."
        )

        # 3. Call OpenAI API
        client = openai.OpenAI(api_key=api_key)
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message},
            ],
            max_tokens=150,
            temperature=0.7,
        )
        
        reply_text = completion.choices[0].message.content.strip()
        
        return JsonResponse({
            "reply": reply_text,
            "suggestions": default_suggestions,
            "stats": stats
        })

    except Exception as e:
        # Log error in real app; here we just fall back
        print(f"OpenAI Error: {e}")
        return _static_assistant_reply(request, message)


def _static_assistant_reply(request, message):
    """
    Original static logic for fallback.
    """
    msg = message.lower()
    stats = _assistant_live_stats(request.user)

    def reply(text, suggestions=None):
        return JsonResponse({
            "reply": text,
            "suggestions": suggestions or ["How does CURA work?", "Where do I book a doctor?", "Show live stats", "Emergency help"],
            "stats": stats,
        })

    # Quick intents
    if any(k in msg for k in ["stats", "live data", "real time", "realtime", "updates", "update"]):
        return reply(
            "Here are your live platform stats (from the database):\n"
            f"- Hospitals: {stats['hospitals']}\n"
            f"- Active doctors: {stats['doctors_active']}\n"
            f"- Oxygen suppliers: {stats['oxygen_suppliers']}\n"
            f"- Medicines listed: {stats['medicines']}\n"
            + (f"- Your unread notifications: {stats.get('your_unread_notifications', 0)}\n" if "your_unread_notifications" in stats else "")
            + f"- Server time: {stats['server_time']}"
        , suggestions=["Hospital beds", "Doctors", "Medicines", "Oxygen"])

    if any(k in msg for k in ["how does", "how do", "workflow", "website work", "works", "use cura"]):
        return reply(
            "CURA is a single place to discover healthcare resources and take action:\n"
            "1) Dashboard: you see your latest activity (appointments, medicine orders, oxygen bookings, notifications).\n"
            "2) Resources: search hospitals (beds), doctors (appointments), medicines (orders), and oxygen suppliers (bookings).\n"
            "3) Notifications: CURA posts updates after you book/order.\n"
            "Tip: the numbers you see are live from the database and update as admins/suppliers change inventory or status."
        , suggestions=["Go to Dashboard", "Show live stats", "Emergency contacts", "24/7 Support"])

    if any(k in msg for k in ["doctor", "appointment", "book a doctor", "book doctor"]):
        return reply(
            "To book a doctor: open Resources → Doctors, filter by city/speciality, open a doctor profile, then choose a slot to book.\n"
            "After booking, you’ll see it on your Dashboard and in Notifications."
        , suggestions=["Search doctors", "View dashboard", "Show live stats"])

    if any(k in msg for k in ["hospital", "beds", "bed", "icu"]):
        return reply(
            "To find hospital beds: open Resources → Hospital beds and filter by city/bed type.\n"
            "Bed availability is shown per hospital and updates when hospital admins change it."
        , suggestions=["Hospital beds", "Emergency contacts", "Show live stats"])

    if any(k in msg for k in ["oxygen", "cylinder", "cylinders"]):
        return reply(
            "To book oxygen: open Resources → Oxygen, select a supplier, then book a cylinder capacity and quantity.\n"
            "Availability updates as suppliers adjust stock and as bookings are placed."
        , suggestions=["Oxygen", "Show live stats", "Emergency contacts"])

    if any(k in msg for k in ["medicine", "medicines", "pharmacy", "order"]):
        return reply(
            "To order medicines: open Resources → Medicines, filter by name/city, then place an order.\n"
            "Stock reduces when you order; you’ll get a notification update."
        , suggestions=["Medicines", "View dashboard", "Show live stats"])

    if any(k in msg for k in ["emergency", "ambulance", "112", "108", "police", "fire"]):
        return reply(
            "If this is an emergency, call the official numbers immediately:\n"
            "- National Emergency: 112\n- Ambulance: 102 / 108\n- Fire: 101\n- Police: 100\n"
            "Then use Emergency page → “Submit Support Request” for assistance and tracking inside CURA."
        , suggestions=["Open Emergency page", "Submit support request", "Show live stats"])

    # Fallback
    return reply(
        "I can guide you through CURA. Try asking about: hospital beds, booking doctors, medicines, oxygen, notifications, or type “stats”."
    )
