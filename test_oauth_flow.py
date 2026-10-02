"""
Tests for the Google OAuth login flow fix.
Run: python test_oauth_flow.py
"""
import os
import sys
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "seo_audit.settings")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.test import Client
from django.contrib.auth.models import User


def sep(title):
    print(f"\n{'='*60}")
    print(f"  TEST: {title}")
    print(f"{'='*60}")


def read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def test_no_popup_login():
    sep("Login template has NO window.open")
    c = read("templates/accounts/login.html")
    assert "window.open" not in c
    assert "return false;" not in c
    assert "googleLogin" not in c
    print("  PASS")


def test_no_popup_register():
    sep("Register template has NO window.open")
    c = read("templates/accounts/register.html")
    assert "window.open" not in c
    assert "return false;" not in c
    assert "googleLogin" not in c
    print("  PASS")


def test_next_in_login():
    sep("Login template passes next to Google OAuth")
    c = read("templates/accounts/login.html")
    assert "next=" in c
    assert "next|default:" in c
    print("  PASS")


def test_next_in_register():
    sep("Register template passes next to Google OAuth")
    c = read("templates/accounts/register.html")
    assert "next=" in c
    assert "next|default:" in c
    print("  PASS")


def test_views_pass_next():
    sep("Auth views pass next to template context")
    c = read("accounts/views/auth_views.py")
    assert '"next": request.GET.get("next", "")' in c
    print("  PASS")


def test_email_login_handles_next():
    sep("Email/password login handles next parameter")
    c = read("accounts/views/auth_views.py")
    assert 'next_url = request.GET.get("next")' in c
    assert "return redirect(next_url)" in c
    print("  PASS")


def test_settings_unchanged():
    sep("Key settings unchanged")
    c = read("seo_audit/settings.py")
    assert 'LOGIN_REDIRECT_URL = "dashboard:dashboard"' in c
    assert 'SOCIALACCOUNT_LOGIN_ON_GET = True' in c
    assert 'SOCIALACCOUNT_AUTO_SIGNUP = True' in c
    print("  PASS")


def test_assistant_unchanged():
    sep("AI Assistant code unchanged")
    c = read("assistant/views.py")
    assert "@login_required" in c
    assert "assistant_view" in c
    assert "send_message" in c
    assert "clear_chat" in c
    print("  PASS")


def test_homepage_cta():
    sep("Homepage CTA links correct")
    c = read("templates/core/home.html")
    assert "calculator:calculator" in c
    assert "assistant:chat" in c
    print("  PASS")


def test_navbar_links():
    sep("Navbar links correct")
    c = read("templates/base.html")
    assert "calculator:calculator" in c
    assert "calculator:analyzer" in c
    assert "assistant:chat" in c
    print("  PASS")


def test_socialaccount_page():
    sep("Socialaccount intermediate page intact")
    c = read("templates/socialaccount/login.html")
    assert "Sign in via Google" in c
    assert 'method="post"' in c
    print("  PASS")


def test_login_with_next():
    sep("GET /accounts/login/?next=/calculator/ passes next to template")
    client = Client()
    r = client.get("/accounts/login/", {"next": "/calculator/"})
    assert r.status_code == 200
    assert "next=/calculator/" in r.content.decode()
    print("  PASS")


def test_login_without_next():
    sep("GET /accounts/login/ uses default /dashboard/")
    client = Client()
    r = client.get("/accounts/login/")
    assert r.status_code == 200
    assert "next=/dashboard/" in r.content.decode()
    print("  PASS")


def test_register_with_next():
    sep("GET /accounts/register/?next=/calculator/ passes next")
    client = Client()
    r = client.get("/accounts/register/", {"next": "/calculator/"})
    assert r.status_code == 200
    assert "next=/calculator/" in r.content.decode()
    print("  PASS")


def test_assistant_requires_login():
    sep("Assistant view redirects unauthenticated to login")
    client = Client()
    r = client.get("/assistant/")
    assert r.status_code == 302
    assert "/accounts/login/" in r.url
    assert "next=" in r.url
    print("  PASS")


def test_calculator_works():
    sep("Calculator view works without login")
    client = Client()
    r = client.get("/calculator/")
    assert r.status_code == 200
    print("  PASS")


if __name__ == "__main__":
    test_no_popup_login()
    test_no_popup_register()
    test_next_in_login()
    test_next_in_register()
    test_views_pass_next()
    test_email_login_handles_next()
    test_settings_unchanged()
    test_assistant_unchanged()
    test_homepage_cta()
    test_navbar_links()
    test_socialaccount_page()
    test_login_with_next()
    test_login_without_next()
    test_register_with_next()
    test_assistant_requires_login()
    test_calculator_works()
    print(f"\n{'='*60}")
    print("  ALL TESTS PASSED")
    print(f"{'='*60}")
