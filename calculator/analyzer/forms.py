import re

from django import forms
from django.core.exceptions import ValidationError


class URLAnalysisForm(forms.Form):
    """Minimal form: URL + optional keyword for the URL analyzer."""

    url = forms.URLField(
        required=True,
        label="Website URL",
        help_text="Enter the full URL including https://",
        widget=forms.TextInput(
            attrs={
                "class": "form-control form-control-lg",
                "placeholder": "https://example.com",
                "autocomplete": "url",
            }
        ),
    )
    target_keyword = forms.CharField(
        required=False,
        label="Target Keyword (optional)",
        help_text="Optional — to check keyword presence on the page",
        max_length=100,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "seo tips",
            }
        ),
    )

    def clean_url(self) -> str:
        url = (self.cleaned_data.get("url") or "").strip()
        if not url:
            raise ValidationError("Please enter a URL.")
        # Reject javascript: / data: early
        if re.match(r"^(javascript|data|vbscript):", url, re.I):
            raise ValidationError("Invalid URL.")
        if len(url) > 2048:
            raise ValidationError("URL is too long (max 2048 characters).")
        return url

    def clean_target_keyword(self) -> str:
        kw = (self.cleaned_data.get("target_keyword") or "").strip()
        if kw and len(kw) < 2:
            raise ValidationError("Keyword is too short.")
        return kw
