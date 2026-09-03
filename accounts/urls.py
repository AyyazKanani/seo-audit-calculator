from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from .views import auth_views as av
from .views import profile_views as pv
from .views import password_views as pwv
from .forms import BootstrapPasswordResetForm, BootstrapSetPasswordForm

app_name = "accounts"

urlpatterns = [
    path("register/", av.register_view, name="register"),
    path("login/", av.login_view, name="login"),
    path("logout/", av.logout_view, name="logout"),
    path("profile/", pv.profile_view, name="profile"),
    path("profile/edit/", pv.edit_profile_view, name="edit_profile"),
    path("password/change/", pwv.change_password_view, name="change_password"),
    path(
        "password/reset/",
        auth_views.PasswordResetView.as_view(
            template_name="accounts/password_reset.html",
            email_template_name="accounts/emails/password_reset_email.html",
            subject_template_name="accounts/emails/password_reset_subject.txt",
            form_class=BootstrapPasswordResetForm,
            success_url=reverse_lazy("accounts:password_reset_done"),
        ),
        name="password_reset",
    ),
    path(
        "password/reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="accounts/password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    path(
        "password/reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="accounts/password_reset_confirm.html",
            form_class=BootstrapSetPasswordForm,
            success_url=reverse_lazy("accounts:password_reset_complete"),
        ),
        name="password_reset_confirm",
    ),
    path(
        "password/reset/complete/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="accounts/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
]
