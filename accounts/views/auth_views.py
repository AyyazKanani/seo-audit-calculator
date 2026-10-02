from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.cache import cache
from django.views.decorators.http import require_http_methods
from ..forms import UserRegisterForm, UserLoginForm

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_SECONDS = 300


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

    return render(request, "accounts/register.html", {"form": form, "next": request.GET.get("next", "")})


@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.user.is_authenticated:
        return redirect("core:home")

    cache_key = f"login_failures_{request.META.get('REMOTE_ADDR')}"
    failures = cache.get(cache_key, 0)

    if request.method == "POST":
        if failures >= MAX_FAILED_ATTEMPTS:
            messages.error(
                request,
                f"Too many failed attempts. Try again in {LOCKOUT_SECONDS // 60} minutes.",
            )
            return render(request, "accounts/login.html", {"form": UserLoginForm(), "next": request.GET.get("next", "")})

        form = UserLoginForm(request.POST)
        if form.is_valid():
            login_field = form.cleaned_data["login"]
            password = form.cleaned_data["password"]
            remember = form.cleaned_data["remember_me"]

            if "@" in login_field:
                user_match = User.objects.filter(email=login_field).first()
                username = user_match.username if user_match else login_field
            else:
                username = login_field

            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                cache.delete(cache_key)
                if not remember:
                    request.session.set_expiry(0)  # Session expires on browser close
                messages.success(request, f"Welcome back, {user.first_name or user.username}!")
                next_url = request.GET.get("next")
                if next_url and next_url.startswith("/") and not next_url.startswith("//"):
                    return redirect(next_url)
                return redirect("core:home")
            else:
                cache.set(
                    cache_key, failures + 1, LOCKOUT_SECONDS
                )
                messages.error(request, "Invalid username/email or password.")
    else:
        form = UserLoginForm()

    return render(request, "accounts/login.html", {"form": form, "next": request.GET.get("next", "")})


@login_required
@require_http_methods(["POST"])
def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("core:home")
