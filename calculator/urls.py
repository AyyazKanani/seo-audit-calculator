from django.urls import path
from . import views

app_name = "calculator"

urlpatterns = [
    path("", views.calculator_view, name="calculator"),
    path("reports/", views.report_list_view, name="reports"),
    path("reports/<int:pk>/delete/", views.report_delete_view, name="report_delete"),
    path("result/<int:pk>/", views.result_view, name="result"),
    path("result/<int:pk>/pdf/", views.report_pdf_view, name="report_pdf"),
]
