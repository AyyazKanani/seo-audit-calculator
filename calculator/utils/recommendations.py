"""
Generates actionable SEO recommendations from scores + inputs.
Pure function, no DB access. Uses thresholds from constants.py.
"""

from calculator.constants import (
    DENSITY_STUFFING,
    META_LONG_WARN,
    META_SHORT_WARN,
    TITLE_LONG_WARN,
    TITLE_SHORT_WARN,
    URL_MAX_GOOD,
)


def generate_recommendations(
    *,
    url: str,
    title: str,
    meta_description: str,
    content: str,
    keyword: str,
    title_score: int,
    meta_score: int,
    url_score: int,
    content_score: int,
    keyword_density: float,
    keyword_score: int,
    word_count: int,
) -> list[str]:
    tips: list[str] = []
    kw_norm = (keyword or "").strip()
    kw_lower = kw_norm.lower()

    # Title
    if not title or not title.strip():
        tips.append("Add a title tag — every page needs one for SEO.")
    else:
        length = len(title.strip())
        if length < TITLE_SHORT_WARN:
            tips.append(f"Title is too short ({length} chars). Aim for 50–60 characters.")
        elif length > TITLE_LONG_WARN:
            tips.append(f"Title is too long ({length} chars). Keep it 50–60 characters so it doesn't truncate.")
        if kw_norm and kw_lower not in title.lower():
            tips.append(f"Include your target keyword '{kw_norm}' in the title.")
        elif kw_norm and not title.lower().strip().startswith(kw_lower):
            tips.append(f"Try starting the title with your keyword '{kw_norm}' for extra relevance.")

    # Meta
    if not meta_description or not meta_description.strip():
        tips.append("Add a meta description to improve click-through rate from Google.")
    else:
        mlen = len(meta_description.strip())
        if mlen < META_SHORT_WARN:
            tips.append(f"Meta description is short ({mlen} chars). Expand to 120–160 characters.")
        elif mlen > META_LONG_WARN:
            tips.append(f"Meta description is long ({mlen} chars). Trim to 120–160 characters.")
        if kw_norm and kw_lower not in meta_description.lower():
            tips.append(f"Add keyword '{kw_norm}' naturally in the meta description.")

    # URL
    if url and "_" in url:
        tips.append("Use hyphens (-) instead of underscores (_) in URLs — Google prefers hyphens.")
    if url and url != url.lower():
        tips.append("Use lowercase letters in URLs for consistency and to avoid duplicate content.")
    if url and ("?" in url or "&" in url):
        tips.append("Avoid query parameters in URLs. Use clean, readable paths.")
    if url and len(url) >= URL_MAX_GOOD:
        tips.append(f"URL is long ({len(url)} chars). Shorter URLs tend to rank better — aim under 75 chars.")
    if kw_norm:
        slug = kw_lower.replace(" ", "-")
        if url and slug not in url.lower() and kw_lower not in url.lower():
            tips.append(f"Include keyword '{kw_norm}' in the URL slug (e.g. /{slug}/).")

    # Content
    if word_count < 300:
        tips.append(f"Content is thin ({word_count} words). Aim for at least 600 words for competitive topics.")
    elif word_count > 2000:
        tips.append(f"Content is very long ({word_count} words). Consider splitting into a series if depth hurts readability.")
    if kw_norm and kw_lower not in content.lower():
        tips.append(f"Keyword '{kw_norm}' not found in content. Add it naturally a few times.")
    else:
        if keyword_density == 0:
            tips.append("Keyword not found — add it to the content.")
        elif keyword_density < 0.5:
            tips.append(f"Keyword density is low ({keyword_density}%). Aim for 1–2.5% — add the keyword a few more times.")
        elif keyword_density > DENSITY_STUFFING:
            tips.append(f"Keyword density is high ({keyword_density}%). Reduce repetition to avoid keyword stuffing (ideal 1–2.5%).")
        first_100 = " ".join(content.split()[:100]).lower() if content else ""
        if kw_norm and kw_lower not in first_100:
            tips.append(f"Mention '{kw_norm}' within the first 100 words to signal relevance to Google.")

    # Score-based closing
    if title_score < 50 or meta_score < 50:
        tips.append("Fix title and meta first — they have the biggest impact on CTR in search results.")

    if not tips:
        tips.append("Great job! Your page looks well optimized. Keep monitoring rankings and refresh content regularly.")

    return tips
