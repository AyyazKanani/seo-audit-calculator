from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.views.decorators.http import require_http_methods
from ..forms import UserRegisterForm, UserLoginForm


@require_http_methods(["GET", "POST"])
def register_view(request):
    if request.user.is_authenticated:
        return redirect("core:home")

    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful! Welcome aboard.")
            return redirect("core:home")
        messages.error(request, "Please correct the errors below.")
    else:
        form = UserRegisterForm()

    return render(request, "accounts/register.html", {"form": form})


@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.user.is_authenticated:
        return redirect("core:home")

    if request.method == "POST":
        form = UserLoginForm(request.POST)
        if form.is_valid():
            login_field = form.cleaned_data["login"]
            password = form.cleaned_data["password"]
            remember = form.cleaned_data["remember_me"]

            # Support login with username or email
            if "@" in login_field:
                username = (
                    User.objects.filter(email=login_field).first().username
                    if User.objects.filter(email=login_field).exists()
                    else login_field
                )
            else:
                username = login_field

            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                if not remember:
                    request.session.set_expiry(0)  # Session expires on browser close
                messages.success(request, f"Welcome back, {user.first_name or user.username}!")
                next_url = request.GET.get("next")
                if next_url and next_url.startswith("/") and not next_url.startswith("//"):
                    return redirect(next_url)
                return redirect("core:home")
            else:
                messages.error(request, "Invalid username/email or password.")
    else:
        form = UserLoginForm()

    return render(request, "accounts/login.html", {"form": form})


@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("core:home")
