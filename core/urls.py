from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/patient/', views.patient_dashboard, name='patient_dashboard'),
    path('dashboard/hospital-admin/', views.hospital_admin_dashboard, name='hospital_admin_dashboard'),
    path('dashboard/pharmacy-admin/', views.pharmacy_admin_dashboard, name='pharmacy_admin_dashboard'),
    path('dashboard/oxygen-supplier/', views.oxygen_supplier_dashboard, name='oxygen_supplier_dashboard'),
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),

    path('hospitals/', views.hospital_list, name='hospital_list'),
    path('hospitals/<int:pk>/', views.hospital_detail, name='hospital_detail'),
    path('hospitals/book-bed/<int:bed_id>/', views.bed_booking_create, name='bed_booking_create'),

    path('doctors/search/', views.doctor_search, name='doctor_search'),
    path('doctors/<int:pk>/', views.doctor_detail, name='doctor_detail'),
    path('doctors/<int:doctor_id>/book/', views.book_appointment, name='book_appointment'),

    path('oxygen/', views.oxygen_list, name='oxygen_list'),
    path('oxygen/booking/<int:stock_id>/', views.oxygen_booking_create, name='oxygen_booking_create'),

    path('medicines/search/', views.medicine_search, name='medicine_search'),
    path('medicines/order/<int:medicine_id>/', views.medicine_order_create, name='medicine_order_create'),
    path('medicines/cart/', views.cart_detail, name='cart_detail'),
    path('medicines/cart/add/<int:medicine_id>/', views.cart_add, name='cart_add'),
    path('medicines/cart/update/<int:item_id>/', views.cart_update, name='cart_update'),
    path('medicines/cart/remove/<int:item_id>/', views.cart_remove, name='cart_remove'),
    path('medicines/cart/checkout/', views.cart_checkout, name='cart_checkout'),

    path('notifications/', views.notifications_list, name='notifications_list'),
    path('notifications/<int:pk>/read/', views.notification_mark_read, name='notification_mark_read'),

    path('emergency-contacts/', views.emergency_contacts, name='emergency_contacts'),
    path('support-request/', views.support_request_create, name='support_request_create'),

    # CURA Assistant (AI-like helper)
    path('assistant/', views.assistant_home, name='assistant_home'),
    path('assistant/api/', views.assistant_api, name='assistant_api'),

    # Admin quick actions for requests
    path('manage/appointments/<int:pk>/status/', views.admin_update_appointment_status, name='admin_update_appointment_status'),
    path('manage/medicine-orders/<int:pk>/status/', views.admin_update_medicine_order_status, name='admin_update_medicine_order_status'),
    path('manage/oxygen-bookings/<int:pk>/status/', views.admin_update_oxygen_booking_status, name='admin_update_oxygen_booking_status'),
    path('manage/bed-bookings/<int:pk>/status/', views.admin_update_bed_booking_status, name='admin_update_bed_booking_status'),
    path('manage/support-requests/<int:pk>/status/', views.admin_update_support_request_status, name='admin_update_support_request_status'),

    # --- ADMIN MANAGEMENT: DOCTORS ---
    path('manage/doctors/', views.manage_doctors, name='manage_doctors'),
    path('manage/doctors/create/', views.create_doctor, name='create_doctor'),
    path('manage/doctors/<int:pk>/edit/', views.edit_doctor, name='edit_doctor'),
    path('manage/doctors/<int:pk>/toggle/', views.toggle_doctor_status, name='toggle_doctor_status'),

]

