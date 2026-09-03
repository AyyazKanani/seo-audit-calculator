from django.urls import path
from . import views

app_name = "assistant"

urlpatterns = [
    path("", views.assistant_view, name="chat"),
    path("send/", views.send_message, name="send"),
    path("clear/", views.clear_chat, name="clear"),
]
