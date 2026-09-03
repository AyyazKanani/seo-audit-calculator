import re

from django import forms
from django.core.exceptions import ValidationError

from .models import SEOReport


class SEOReportForm(forms.ModelForm):
    class Meta:
        model = SEOReport
        fields = ["url", "title", "meta_description", "content", "target_keyword"]
        widgets = {
            "url": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "https://example.com/blog/seo-tips",
                }
            ),
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Best SEO Tips for 2026 - Rank Higher on Google",
                }
            ),
            "meta_description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Discover actionable SEO tips to boost your rankings, improve page speed, and drive organic traffic...",
                }
            ),
            "content": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 8,
                    "placeholder": "Paste your page content here (at least 150 words recommended)...",
                }
            ),
            "target_keyword": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "seo tips",
                }
            ),
        }
        labels = {
            "url": "Page URL",
            "title": "Title Tag",
            "meta_description": "Meta Description",
            "content": "Page Content",
            "target_keyword": "Target Keyword",
        }
        help_texts = {
            "url": "Include the full URL or slug",
            "title": "50–60 characters is ideal",
            "meta_description": "120–160 characters is ideal",
            "content": "Main body text. More words = better analysis",
            "target_keyword": "Single keyword or short phrase",
        }

    def clean_url(self) -> str:
        url = (self.cleaned_data.get("url") or "").strip()
        if not url:
            raise ValidationError("URL is required.")
        # Allow slugs without scheme, but block javascript: and data:
        if re.match(r"^(javascript|data):", url, re.IGNORECASE):
            raise ValidationError("Invalid URL.")
        if " " in url:
            raise ValidationError("URL cannot contain spaces. Use hyphens instead.")
        # Normalize: collapse whitespace already stripped, limit length
        if len(url) > 500:
            raise ValidationError("URL is too long (max 500 characters).")
        return url

    def clean_title(self) -> str:
        title = (self.cleaned_data.get("title") or "").strip()
        if not title:
            raise ValidationError("Title is required.")
        title = re.sub(r"\s+", " ", title)
        if len(title) > 200:
            raise ValidationError("Title is too long (max 200 characters).")
        return title

    def clean_meta_description(self) -> str:
        meta = (self.cleaned_data.get("meta_description") or "").strip()
        if not meta:
            raise ValidationError("Meta description is required.")
        meta = re.sub(r"\s+", " ", meta)
        if len(meta) > 500:
            raise ValidationError("Meta description is too long (max 500 characters).")
        return meta

    def clean_target_keyword(self) -> str:
        kw = (self.cleaned_data.get("target_keyword") or "").strip()
        if not kw:
            raise ValidationError("Target keyword is required.")
        kw = re.sub(r"\s+", " ", kw)
        if len(kw) < 2:
            raise ValidationError("Keyword is too short.")
        if len(kw) > 100:
            raise ValidationError("Keyword is too long (max 100 characters).")
        return kw

    def clean_content(self) -> str:
        content = (self.cleaned_data.get("content") or "").strip()
        if not content:
            raise ValidationError("Content is required.")
        # Normalize line breaks but keep paragraph intent
        content = re.sub(r"[ \t]+", " ", content)
        if len(content.split()) < 10:
            raise ValidationError("Content is too short. Add at least 10 words.")
        if len(content) > 50000:
            raise ValidationError("Content is too long (max 50,000 characters).")
        return content
