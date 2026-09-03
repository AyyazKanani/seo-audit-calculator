from django.urls import path
from . import views

app_name = "calculator"

urlpatterns = [
    path("", views.calculator_view, name="calculator"),
    path("result/<int:pk>/", views.result_view, name="result"),
]
