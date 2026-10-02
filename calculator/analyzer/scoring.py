"""
Maps extracted SEOData to the existing scoring + recommendation system.

Adds URL-analyzer-specific recommendations for things the manual calculator
doesn't cover (H1, images, links, canonical, robots, HTTPS, etc.).
"""

from __future__ import annotations

from calculator.utils.scoring import (
    calculate_keyword_density,
    calculate_overall_score,
    score_content,
    score_keyword_density,
    score_meta_description,
    score_title,
    score_url,
)

from .parser import SEOData


def score_extracted(data: SEOData, keyword: str = "") -> dict:
    """
    Compute all scores from an SEOData object.
    Returns a dict matching the shape expected by the result template
    plus extra fields for analyzer-specific metrics.
    """
    # Build the "content" for density: use body text
    # But body_text can be huge — use first ~5000 words for density
    body_for_density = " ".join(data.body_text.split()[:5000])

    kw = (keyword or "").strip()

    # Re-run density via existing utility for consistency
    density = data.keyword_density

    title_score = score_title(data.title, kw)
    meta_score = score_meta_description(data.meta_description, kw)
    url_score = score_url(data.final_url, kw)
    keyword_score = score_keyword_density(density)
    content_score = score_content(body_for_density, kw, density)
    overall = calculate_overall_score(
        title_score, meta_score, url_score, content_score, keyword_score
    )

    return {
        "title_score": title_score,
        "meta_score": meta_score,
        "url_score": url_score,
        "keyword_density": density,
        "keyword_score": keyword_score,
        "content_score": content_score,
        "overall_score": overall,
        "word_count": data.word_count,
    }


def generate_analyzer_recommendations(data: SEOData, scores: dict, keyword: str = "") -> list[str]:
    """
    Generate recommendations combining standard scoring tips with
    analyzer-specific checks (H1, images, links, HTTPS, etc.).
    """
    tips: list[str] = []
    kw = (keyword or "").strip()

    # ---- Standard scoring-based tips (reuse existing logic) ----
    from calculator.utils.recommendations import generate_recommendations
    standard = generate_recommendations(
        url=data.final_url,
        title=data.title,
        meta_description=data.meta_description,
        content=data.body_text[:10000],  # limit for performance
        keyword=kw,
        title_score=scores["title_score"],
        meta_score=scores["meta_score"],
        url_score=scores["url_score"],
        content_score=scores["content_score"],
        keyword_density=scores["keyword_density"],
        keyword_score=scores["keyword_score"],
        word_count=scores["word_count"],
    )
    tips.extend(standard)

    # ---- Analyzer-specific: HTTPS ----
    if not data.is_https:
        tips.insert(0, "Enable HTTPS — it's a ranking signal and builds user trust.")

    # ---- Analyzer-specific: H1 ----
    if data.h1_count == 0:
        tips.insert(1, "Add an H1 tag — every page should have exactly one.")
    elif data.h1_count > 1:
        tips.insert(1, f"Found {data.h1_count} H1 tags. Use exactly one H1 per page.")

    # ---- Analyzer-specific: Canonical ----
    if not data.canonical_url:
        tips.append("Add a canonical URL tag (<link rel='canonical'>) to prevent duplicate content issues.")

    # ---- Analyzer-specific: Robots ----
    robots_lower = data.robots_meta.lower()
    if "noindex" in robots_lower:
        tips.append("⚠️  This page has 'noindex' — search engines won't include it in results.")
    if "nofollow" in robots_lower:
        tips.append("⚠️  This page has 'nofollow' — link equity won't pass through links on this page.")

    # ---- Analyzer-specific: Images ----
    if data.image_count == 0:
        tips.append("Add relevant images — visual content improves engagement and can rank in image search.")
    elif data.images_missing_alt > 0:
        tips.append(
            f"{data.images_missing_alt} of {data.image_count} images are missing alt text. "
            "Add descriptive alt attributes for accessibility and image SEO."
        )

    # ---- Analyzer-specific: Links ----
    if data.internal_links == 0 and data.external_links == 0:
        tips.append("Add internal links to help search engines discover and rank your content.")
    elif data.internal_links == 0:
        tips.append("Add internal links to connect this page to the rest of your site.")
    elif data.external_links == 0:
        tips.append("Consider adding outbound links to authoritative sources to boost credibility.")

    # ---- Analyzer-specific: Headings structure ----
    if data.h2_count == 0 and data.word_count > 300:
        tips.append("Add H2 subheadings to break up long content and improve readability.")

    # ---- Keyword specific (from parser checks) ----
    if data.keyword_density > 0:
        if not data.keyword_in_title:
            tips.append(f"Keyword not found in the title — include '{data.final_url}' in the <title> tag.")
        if not data.keyword_in_meta:
            tips.append(f"Keyword not found in meta description.")
        if not data.keyword_in_h1:
            tips.append(f"Keyword not found in H1 — include it in your main heading.")
    elif data.keyword_density == 0:
        tips.append("Target keyword not found anywhere on the page.")

    return tips


def build_report_data(data: SEOData, user_keyword: str = "") -> dict:
    """
    Top-level function: runs scoring + recommendations on extracted SEOData.
    Returns a dict ready for the result template context.
    """
    kw = (user_keyword or "").strip()
    scores = score_extracted(data, kw)
    recommendations = generate_analyzer_recommendations(data, scores, kw)

    return {
        # Scores
        **scores,
        "recommendations": recommendations,
        # Extracted data for display
        "url": data.final_url,
        "title": data.title,
        "meta_description": data.meta_description,
        "target_keyword": user_keyword,
        # Analyzer-specific fields (extra context)
        "h1_count": data.h1_count,
        "h1_texts": data.h1_texts,
        "h2_count": data.h2_count,
        "canonical_url": data.canonical_url,
        "robots_meta": data.robots_meta,
        "is_https": data.is_https,
        "image_count": data.image_count,
        "images_missing_alt": data.images_missing_alt,
        "images_missing_alt_src": data.images_missing_alt_src,
        "internal_links": data.internal_links,
        "external_links": data.external_links,
        "keyword_found": data.keyword_found,
        "keyword_in_title": data.keyword_in_title,
        "keyword_in_meta": data.keyword_in_meta,
        "keyword_in_h1": data.keyword_in_h1,
        "keyword_in_url": data.keyword_in_url,
        # Flag to tell template this is from URL analysis
        "is_url_analysis": True,
    }
