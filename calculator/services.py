"""
Service layer for SEO reports.

Views, APIs, and management commands should call these helpers
instead of reimplementing scoring logic.
"""

from django.db import transaction

from .models import SEOReport
from .utils import (
    calculate_keyword_density,
    calculate_overall_score,
    generate_recommendations,
    score_content,
    score_keyword_density,
    score_meta_description,
    score_title,
    score_url,
)


def compute_scores(data: dict) -> dict:
    """
    Compute all SEO scores from raw inputs.

    Expects keys: url, title, meta_description, content, target_keyword
    Returns dict with title_score, meta_score, url_score,
    keyword_density, keyword_score, content_score, overall_score, word_count
    """
    url = data.get("url", "") or ""
    title = data.get("title", "") or ""
    meta = data.get("meta_description", "") or ""
    content = data.get("content", "") or ""
    keyword = data.get("target_keyword", "") or ""

    title_score = score_title(title, keyword)
    meta_score = score_meta_description(meta, keyword)
    url_score = score_url(url, keyword)
    density = calculate_keyword_density(content, keyword)
    keyword_score = score_keyword_density(density)
    content_score = score_content(content, keyword, density)
    overall = calculate_overall_score(
        title_score, meta_score, url_score, content_score, keyword_score
    )
    word_count = len(content.strip().split()) if content.strip() else 0

    return {
        "title_score": title_score,
        "meta_score": meta_score,
        "url_score": url_score,
        "keyword_density": density,
        "keyword_score": keyword_score,
        "content_score": content_score,
        "overall_score": overall,
        "word_count": word_count,
    }


def build_recommendations(data: dict, scores: dict) -> list[str]:
    """Thin wrapper to keep call sites clean."""
    return generate_recommendations(
        url=data.get("url", "") or "",
        title=data.get("title", "") or "",
        meta_description=data.get("meta_description", "") or "",
        content=data.get("content", "") or "",
        keyword=data.get("target_keyword", "") or "",
        title_score=scores["title_score"],
        meta_score=scores["meta_score"],
        url_score=scores["url_score"],
        content_score=scores["content_score"],
        keyword_density=scores["keyword_density"],
        keyword_score=scores["keyword_score"],
        word_count=scores["word_count"],
    )


@transaction.atomic
def create_report(*, user, form_data: dict) -> SEOReport:
    """
    Create and save an SEOReport from validated form_data.
    `user` may be None for anonymous audits.
    """
    scores = compute_scores(form_data)
    recommendations = build_recommendations(form_data, scores)

    report = SEOReport(
        user=user if getattr(user, "is_authenticated", False) else None,
        url=form_data["url"],
        title=form_data["title"],
        meta_description=form_data["meta_description"],
        content=form_data["content"],
        target_keyword=form_data["target_keyword"].strip(),
        **{k: v for k, v in scores.items() if k != "keyword_score"},
        recommendations=recommendations,
    )
    # keyword_score is not stored (derived), only keyword_density is persisted
    report.save()
    return report
