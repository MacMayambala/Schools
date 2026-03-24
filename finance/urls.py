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
]