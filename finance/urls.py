from django.urls import path
from . import views

app_name = 'finance'

urlpatterns = [
    path('dashboard/', views.finance_dashboard, name='dashboard'),
    path('bulk-bill/', views.run_bulk_billing, name='bulk_bill'),
    path('payment/<int:invoice_id>/', views.record_payment, name='record_payment'),
    path('receipt/<int:payment_id>/', views.receipt_detail, name='receipt_detail'),
    path('reports/defaulters/', views.defaulters_report, name='defaulters_report'),
    path('accounts/', views.account_list, name='account_list'),
    path('accounts/add/', views.account_list, name='add_account'),
    path('reports/daily-collection/', views.daily_collection_report, name='daily_report'),
    path('statement/<int:student_id>/', views.student_statement, name='student_statement'),
    path('reports/export-excel/', views.export_collections_excel, name='export_excel'),
    path('settings/hub/', views.school_settings_hub, name='settings_hub'),
    path('invoice/<int:invoice_id>/print/', views.print_invoice, name='print_invoice'),
    path('momo-webhook/', views.momo_webhook, name='momo_webhook'),
    path('payment/<int:payment_id>/status/', views.check_payment_status, name='check_status'),

]