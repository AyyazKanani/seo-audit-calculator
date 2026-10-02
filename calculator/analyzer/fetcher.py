"""
Secure URL fetcher with full SSRF protection.

Checks performed before every request:
  1. Scheme must be http:// or https://
  2. Hostname must not be loopback / localhost / private / reserved
  3. DNS-resolved IP must not be loopback / private / reserved
  4. Redirect destination IPs are re-checked (redirect bypass prevention)
  5. Response limited to MAX_RESPONSE_SIZE bytes
  6. Only text/html content-type accepted
  7. Reasonable timeout enforced

All exceptions are caught and returned as user-friendly error strings.
"""

from __future__ import annotations

import ipaddress
import socket
from dataclasses import dataclass
from urllib.parse import urlparse

import requests

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
REQUEST_TIMEOUT = 10            # seconds
MAX_RESPONSE_BYTES = 5 * 1024 * 1024   # 5 MB
USER_AGENT = (
    "SEOAuditBot/1.0 "
    "(+https://seo-audit-calc.local; bot for on-page SEO analysis)"
)
ALLOWED_SCHEMES = {"http", "https"}
ALLOWED_CONTENT_PREFIXES = ("text/html", "application/xhtml")

# RFC 5735 / RFC 6890 reserved ranges that must never be fetched
_PRIVATE_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),       # loopback
    ipaddress.ip_network("10.0.0.0/8"),        # Class A private
    ipaddress.ip_network("172.16.0.0/12"),     # Class B private
    ipaddress.ip_network("192.168.0.0/16"),    # Class C private
    ipaddress.ip_network("169.254.0.0/16"),    # link-local
    ipaddress.ip_network("::1/128"),           # IPv6 loopback
    ipaddress.ip_network("fc00::/7"),          # IPv6 ULA
    ipaddress.ip_network("fe80::/10"),         # IPv6 link-local
    ipaddress.ip_network("0.0.0.0/8"),         # "this" network
]


# ---------------------------------------------------------------------------
# Data class for fetch results
# ---------------------------------------------------------------------------
@dataclass
class FetchResult:
    """Returned by fetch_url. On failure `error` is set, rest is empty."""
    final_url: str = ""
    html: str = ""
    status_code: int = 0
    error: str = ""
    redirected: bool = False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _is_private_ip(ip_str: str) -> bool:
    """Return True if ip_str belongs to a loopback / private / reserved range."""
    try:
        addr = ipaddress.ip_address(ip_str)
    except ValueError:
        return True  # unparseable → treat as unsafe
    return any(addr in net for net in _PRIVATE_NETWORKS)


def _validate_hostname(hostname: str) -> str | None:
    """
    Resolve hostname and verify *every* resulting IP is public.
    Returns error string on failure, None on success.
    """
    if not hostname:
        return "No hostname provided."
    low = hostname.lower()
    blocked_names = {
        "localhost", "localhost.localdomain",
        "metadata.google.internal",
        "169.254.169.254",  # cloud metadata endpoint
    }
    if low in blocked_names:
        return "Access to internal hostnames is not allowed."
    try:
        infos = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
    except socket.gaierror:
        return f"Could not resolve hostname '{hostname}'."
    if not infos:
        return f"No DNS records found for '{hostname}'."
    for family, _, _, _, sockaddr in infos:
        ip = sockaddr[0]
        if _is_private_ip(ip):
            return (
                f"Hostname '{hostname}' resolves to a private/internal IP ({ip}). "
                "Only public URLs can be analyzed."
            )
    return None


def _validate_url(url: str) -> tuple[str | None, str]:
    """
    Parse and validate the URL before any network call.
    Returns (error, normalised_url). error is None on success.
    """
    url = url.strip()
    if not url:
        return ("Please enter a URL.", "")
    # Reject dangerous schemes early
    if "://" not in url:
        # Try adding https://
        url = "https://" + url
    try:
        parsed = urlparse(url)
    except Exception:
        return ("Invalid URL format.", "")
    scheme = (parsed.scheme or "").lower()
    if scheme not in ALLOWED_SCHEMES:
        return (
            f"Only http:// and https:// URLs are accepted (got '{scheme}://').",
            "",
        )
    hostname = parsed.hostname
    if not hostname:
        return ("URL has no valid hostname.", "")
    err = _validate_hostname(hostname)
    if err:
        return (err, "")
    return (None, url)


def _check_response_ip(url: str, response: requests.Response) -> str | None:
    """
    After a request completes, verify the *actual* connected IP wasn't
    redirected to a private range. Returns error or None.
    """
    history_urls = [r.url for r in response.history] + [response.url]
    for h_url in history_urls:
        h_parsed = urlparse(h_url)
        h_host = h_parsed.hostname
        if not h_host:
            continue
        err = _validate_hostname(h_host)
        if err:
            return f"Redirect target blocked: {err}"
    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def fetch_url(url: str) -> FetchResult:
    """
    Fetch a URL safely. Returns a FetchResult with either `html` or `error`.
    """
    err, normalised = _validate_url(url)
    if err:
        return FetchResult(error=err)

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html, application/xhtml+xml;q=0.9, */*;q=0.1",
        "Accept-Language": "en-US,en;q=0.9",
    }

    try:
        resp = requests.get(
            normalised,
            headers=headers,
            timeout=REQUEST_TIMEOUT,
            allow_redirects=True,
            stream=True,  # read in chunks to enforce size limit
        )
    except requests.exceptions.TooManyRedirects:
        return FetchResult(error="Too many redirects. The site seems to loop.", final_url=normalised)
    except requests.exceptions.ConnectionError:
        return FetchResult(error="Could not connect to the website. Check the URL and try again.", final_url=normalised)
    except requests.exceptions.Timeout:
        return FetchResult(error=f"The website took too long to respond (>{REQUEST_TIMEOUT}s).", final_url=normalised)
    except requests.exceptions.SSLError:
        return FetchResult(error="SSL/TLS certificate error. The site may have an invalid certificate.", final_url=normalised)
    except requests.exceptions.RequestException:
        return FetchResult(error="Failed to fetch the URL. Please check the address and try again.", final_url=normalised)

    # Check content-type before reading body
    content_type = resp.headers.get("Content-Type", "")
    if not any(content_type.lower().startswith(p) for p in ALLOWED_CONTENT_PREFIXES):
        resp.close()
        return FetchResult(
            error=(
                f"This URL does not return HTML (Content-Type: {content_type or 'unknown'}). "
                "Only web pages can be analyzed."
            ),
            final_url=resp.url,
            status_code=resp.status_code,
        )

    # Read body with size limit
    chunks: list[bytes] = []
    total = 0
    for chunk in resp.iter_content(chunk_size=65536):
        total += len(chunk)
        if total > MAX_RESPONSE_BYTES:
            resp.close()
            return FetchResult(
                error=f"Response too large (>{MAX_RESPONSE_BYTES // (1024*1024)} MB). Cannot analyze this page.",
                final_url=resp.url,
                status_code=resp.status_code,
            )
        chunks.append(chunk)
    resp.close()

    html = b"".join(chunks).decode(resp.encoding or "utf-8", errors="replace")

    # Re-check IPs after redirects
    ip_err = _check_response_ip(normalised, resp)
    if ip_err:
        return FetchResult(error=ip_err, final_url=resp.url, status_code=resp.status_code)

    redirected = len(resp.history) > 0

    return FetchResult(
        final_url=resp.url,
        html=html,
        status_code=resp.status_code,
        redirected=redirected,
    )
