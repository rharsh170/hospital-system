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

    path('hospitals/', views.hospital_list, name='hospital_list'),
    path('hospitals/<int:pk>/', views.hospital_detail, name='hospital_detail'),

    path('doctors/search/', views.doctor_search, name='doctor_search'),
    path('doctors/<int:pk>/', views.doctor_detail, name='doctor_detail'),
    path('doctors/<int:doctor_id>/book/', views.book_appointment, name='book_appointment'),

    path('oxygen/', views.oxygen_list, name='oxygen_list'),
    path('oxygen/booking/<int:stock_id>/', views.oxygen_booking_create, name='oxygen_booking_create'),

    path('medicines/search/', views.medicine_search, name='medicine_search'),
    path('medicines/order/<int:medicine_id>/', views.medicine_order_create, name='medicine_order_create'),

    path('notifications/', views.notifications_list, name='notifications_list'),
    path('notifications/<int:pk>/read/', views.notification_mark_read, name='notification_mark_read'),

    path('emergency-contacts/', views.emergency_contacts, name='emergency_contacts'),
    path('support-request/', views.support_request_create, name='support_request_create'),
]

