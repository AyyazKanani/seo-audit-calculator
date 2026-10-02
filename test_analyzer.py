"""
Manual test script for the URL Analyzer — runs all 6 test cases.
Run: python test_analyzer.py
"""
import os
import sys
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "seo_audit.settings")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.test import RequestFactory
from calculator.analyzer.fetcher import fetch_url, _validate_url, _validate_hostname
from calculator.analyzer.parser import parse_html
from calculator.analyzer.scoring import build_report_data
from calculator.analyzer.views import analyzer_view

factory = RequestFactory()

def separator(title):
    print(f"\n{'='*60}")
    print(f"  TEST: {title}")
    print(f"{'='*60}")

def test_validate_url():
    separator("URL Validation (pre-fetch)")
    cases = [
        ("https://example.com", True),
        ("http://example.com", True),
        ("ftp://example.com", False),
        ("javascript:alert(1)", False),
        ("", False),
        ("https://localhost:8000", False),
        ("https://127.0.0.1", False),
        ("https://192.168.1.1", False),
        ("https://10.0.0.1", False),
        ("https://169.254.169.254/metadata", False),
    ]
    for url, should_pass in cases:
        err, _ = _validate_url(url)
        passed = (err is None) == should_pass
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {url!r:45s} -> err={err!r}")

def test_fetch_normal():
    separator("1. Normal public HTTPS website")
    result = fetch_url("https://httpbin.org/html")
    print(f"  status_code : {result.status_code}")
    print(f"  final_url   : {result.final_url}")
    print(f"  redirected  : {result.redirected}")
    print(f"  html length : {len(result.html)}")
    print(f"  error       : {result.error}")
    assert result.error == "", f"Unexpected error: {result.error}"
    assert result.status_code == 200
    assert len(result.html) > 100
    print("  PASS")

def test_fetch_invalid():
    separator("2. Invalid URL")
    result = fetch_url("https://this-domain-does-not-exist-xyz123.com")
    print(f"  error : {result.error}")
    assert result.error != ""
    print("  PASS")

def test_fetch_localhost():
    separator("3. Localhost URL")
    result = fetch_url("http://localhost:8000/admin/")
    print(f"  error : {result.error}")
    assert result.error != ""
    assert "private" in result.error.lower() or "internal" in result.error.lower()
    print("  PASS")

def test_fetch_private_ip():
    separator("4. Private/Internal IP")
    for url in ["http://192.168.1.1/", "http://10.0.0.1/", "http://127.0.0.1/"]:
        result = fetch_url(url)
        print(f"  {url:30s} -> error: {result.error}")
        assert result.error != ""
    print("  PASS")

def test_fetch_redirect():
    separator("5. URL that redirects (to HTML)")
    result = fetch_url("https://httpbin.org/redirect-to?url=https://httpbin.org/html")
    print(f"  final_url   : {result.final_url}")
    print(f"  redirected  : {result.redirected}")
    print(f"  status_code : {result.status_code}")
    print(f"  error       : {result.error}")
    # Should succeed (follows redirect to HTML)
    assert result.error == "", f"Unexpected error: {result.error}"
    assert result.redirected
    print("  PASS")

def test_fetch_non_html():
    separator("6. Non-HTML URL")
    result = fetch_url("https://httpbin.org/image/png")
    print(f"  content-type check : error={result.error!r}")
    assert result.error != ""
    print("  PASS")

def test_full_flow():
    separator("FULL PIPELINE: fetch -> parse -> score -> recommendations")
    result = fetch_url("https://httpbin.org/html")
    assert result.error == ""
    data = parse_html(result.html, result.final_url, "motor")
    report = build_report_data(data, "motor")
    print(f"  title               : {report['title']!r}")
    print(f"  title_score         : {report['title_score']}")
    print(f"  meta_score          : {report['meta_score']}")
    print(f"  url_score           : {report['url_score']}")
    print(f"  content_score       : {report['content_score']}")
    print(f"  overall_score       : {report['overall_score']}")
    print(f"  word_count          : {report['word_count']}")
    print(f"  recommendations ({len(report['recommendations'])}):")
    for i, tip in enumerate(report['recommendations'][:5], 1):
        print(f"    {i}. {tip[:80]}")
    print("  PASS")

def test_view_returns_200():
    separator("VIEW: GET /calculator/analyze/ returns 200")
    from django.test import Client
    client = Client()
    response = client.get("/calculator/analyze/")
    print(f"  status_code : {response.status_code}")
    assert response.status_code == 200
    content = response.content.decode()
    assert "Analyze Website URL" in content
    print("  PASS")

def test_view_rejects_localhost():
    separator("VIEW: POST with localhost URL shows error")
    from django.test import Client
    client = Client()
    response = client.post("/calculator/analyze/", {
        "url": "http://localhost:8000/",
        "target_keyword": "",
    })
    print(f"  status_code : {response.status_code}")
    assert response.status_code == 200  # re-renders form with error
    content = response.content.decode()
    assert "private" in content.lower() or "internal" in content.lower() or "error" in content.lower()
    print("  PASS")


if __name__ == "__main__":
    test_validate_url()
    test_fetch_normal()
    test_fetch_invalid()
    test_fetch_localhost()
    test_fetch_private_ip()
    test_fetch_redirect()
    test_fetch_non_html()
    test_full_flow()
    test_view_returns_200()
    test_view_rejects_localhost()
    print(f"\n{'='*60}")
    print("  ALL TESTS PASSED")
    print(f"{'='*60}")
