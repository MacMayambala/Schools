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
    #path('accounts/add/', views.add_account, name='add_account'),
    path('reports/daily-collection/', views.daily_collection_report, name='daily_report'),
    path('statement/<int:student_id>/', views.student_statement, name='student_statement'),
    path('reports/export-excel/', views.export_collections_excel, name='export_excel'),
    path('settings/hub/', views.school_settings_hub, name='settings_hub'),
    path('invoice/<int:invoice_id>/print/', views.print_invoice, name='print_invoice'),
    path('momo-webhook/', views.momo_webhook, name='momo_webhook'),
    path('payment/<int:payment_id>/status/', views.check_payment_status, name='check_status'),
    path('bulk-sms-reminders/', views.bulk_sms_reminder_view, name='bulk_sms_reminders'),
    path('report/<int:student_id>/<str:term>/<str:year>/', 
         views.student_report_card, 
         name='student_report_card'),
    path('record-income/', views.record_income, name='record_income'),
    path('record-expense/', views.record_expense, name='record_expense'),


]