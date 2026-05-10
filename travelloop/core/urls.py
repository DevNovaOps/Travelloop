from django.urls import path
from . import views

urlpatterns = [
    # ── Page views ──
    path('', views.page_index, name='index'),
    path('login/', views.page_login, name='login'),
    path('register/', views.page_register, name='register'),
    path('forgot-password/', views.page_forgot_password, name='forgot_password'),
    path('verify-otp/', views.page_verify_otp, name='verify_otp'),
    path('reset-password/', views.page_reset_password, name='reset_password'),
    path('dashboard/', views.page_dashboard, name='dashboard'),
    path('trips/', views.page_trips, name='trips'),
    path('create-trip/', views.page_create_trip, name='create_trip'),
    path('build-itinerary/', views.page_build_itinerary, name='build_itinerary'),
    path('itinerary-view/', views.page_itinerary_view, name='itinerary_view'),
    path('profile/', views.page_profile, name='profile'),
    path('search/', views.page_search, name='search'),
    path('community/', views.page_community, name='community'),
    path('packing/', views.page_packing, name='packing'),
    path('notes/', views.page_notes, name='notes'),
    path('admin-panel/', views.page_admin_panel, name='admin_panel'),

    # ── Auth APIs ──
    path('api/register/', views.api_register, name='api_register'),
    path('api/login/', views.api_login, name='api_login'),
    path('api/logout/', views.api_logout, name='api_logout'),
    path('api/forgot-password/', views.api_forgot_password, name='api_forgot_password'),
    path('api/verify-otp/', views.api_verify_otp, name='api_verify_otp'),
    path('api/reset-password/', views.api_reset_password, name='api_reset_password'),

    # ── Profile API ──
    path('api/profile/', views.api_profile, name='api_profile'),

    # ── Dashboard Stats ──
    path('api/dashboard/stats/', views.api_dashboard_stats, name='api_dashboard_stats'),

    # ── Trips API ──
    path('api/trips/', views.api_trips, name='api_trips'),
    path('api/trips/<int:trip_id>/', views.api_trip_detail, name='api_trip_detail'),

    # ── Itinerary Sections API ──
    path('api/trips/<int:trip_id>/sections/', views.api_sections, name='api_sections'),
    path('api/trips/<int:trip_id>/sections/<int:section_id>/', views.api_section_detail, name='api_section_detail'),

    # ── Activities API ──
    path('api/trips/<int:trip_id>/sections/<int:section_id>/activities/', views.api_activities, name='api_activities'),

    # ── Packing API ──
    path('api/trips/<int:trip_id>/packing/', views.api_packing, name='api_packing'),
    path('api/trips/<int:trip_id>/packing/<int:item_id>/', views.api_packing_toggle, name='api_packing_toggle'),

    # ── Notes API ──
    path('api/trips/<int:trip_id>/notes/', views.api_notes, name='api_notes'),
    path('api/trips/<int:trip_id>/notes/<int:note_id>/', views.api_note_detail, name='api_note_detail'),

    # ── Community API ──
    path('api/community/', views.api_community, name='api_community'),
    path('api/community/<int:post_id>/like/', views.api_community_like, name='api_community_like'),

    # ── Destinations / Search API ──
    path('api/destinations/', views.api_destinations, name='api_destinations'),

    # ── Admin APIs ──
    path('api/admin/users/', views.api_admin_users, name='api_admin_users'),
    path('api/admin/users/<int:user_id>/toggle/', views.api_admin_toggle_user, name='api_admin_toggle_user'),
    path('api/admin/stats/', views.api_admin_stats, name='api_admin_stats'),

    # ── Notifications API ──
    path('api/notifications/', views.api_notifications, name='api_notifications'),

    # ── Health ──
    path('api/health/', views.api_health, name='api_health'),

    # ── Invoice Page ──
    path('invoices/', views.page_invoices, name='invoices'),

    # ── AI API ──
    path('api/ai/suggest/', views.api_ai_suggest, name='api_ai_suggest'),

    # ── Invoice / Expense APIs ──
    path('api/invoices/', views.api_invoices, name='api_invoices'),
    path('api/invoices/<int:invoice_id>/', views.api_invoice_detail, name='api_invoice_detail'),
    path('api/invoices/<int:invoice_id>/items/', views.api_expense_item, name='api_expense_item'),
    path('api/invoices/<int:invoice_id>/items/<int:item_id>/', views.api_expense_item_delete, name='api_expense_item_delete'),

    # ── Payment APIs ──
    path('api/payment/create/', views.api_payment_create, name='api_payment_create'),
    path('api/payment/verify/', views.api_payment_verify, name='api_payment_verify'),
]
