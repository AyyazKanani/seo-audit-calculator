"""
Pure scoring functions. No Django imports, no DB access.
Easy to test, reusable from views, services, APIs, or management commands.
"""

import re

from calculator.constants import (
    CONTENT_IDEAL_MAX,
    CONTENT_IDEAL_MIN,
    CONTENT_MIN_GOOD,
    CONTENT_MIN_THIN,
    CONTENT_TOO_LONG,
    DENSITY_IDEAL_MAX,
    DENSITY_IDEAL_MIN,
    DENSITY_OK_MAX,
    DENSITY_OK_MIN,
    DENSITY_WARN_MAX,
    DENSITY_WARN_MIN,
    META_ACCEPTABLE_MAX,
    META_ACCEPTABLE_MIN,
    META_IDEAL_MAX,
    META_IDEAL_MIN,
    SCORE_DENSITY_IDEAL,
    SCORE_DENSITY_LOW,
    SCORE_DENSITY_OK,
    SCORE_DENSITY_WARN,
    TITLE_ACCEPTABLE_MAX,
    TITLE_ACCEPTABLE_MIN,
    TITLE_IDEAL_MAX,
    TITLE_IDEAL_MIN,
    URL_MAX_ACCEPTABLE,
    URL_MAX_GOOD,
    WEIGHT_CONTENT,
    WEIGHT_KEYWORD,
    WEIGHT_META,
    WEIGHT_TITLE,
    WEIGHT_URL,
)


def _normalize(text: str | None) -> str:
    """Strip and collapse whitespace. Safe for None."""
    if not text:
        return ""
    return re.sub(r"\s+", " ", text.strip())


def _contains_keyword(text: str, keyword: str) -> bool:
    if not keyword:
        return False
    return _normalize(keyword).lower() in _normalize(text).lower()


def _starts_with_keyword(text: str, keyword: str) -> bool:
    if not keyword:
        return False
    return _normalize(text).lower().startswith(_normalize(keyword).lower())


# Pre-compiled for single-word density (performance)
_WORD_BOUNDARY_CACHE: dict[str, re.Pattern] = {}


def _word_pattern(keyword: str) -> re.Pattern:
    if keyword not in _WORD_BOUNDARY_CACHE:
        _WORD_BOUNDARY_CACHE[keyword] = re.compile(
            r"\b" + re.escape(keyword) + r"\b", re.IGNORECASE
        )
    return _WORD_BOUNDARY_CACHE[keyword]


def score_title(title: str | None, keyword: str | None) -> int:
    """Title: ideal 50-60 chars, contains keyword, 4-12 words, not ALL CAPS."""
    text = _normalize(title)
    if not text:
        return 0

    score = 0
    length = len(text)

    # Length (40 pts)
    if TITLE_IDEAL_MIN <= length <= TITLE_IDEAL_MAX:
        score += 40
    elif TITLE_ACCEPTABLE_MIN <= length < TITLE_IDEAL_MIN or TITLE_IDEAL_MAX < length <= TITLE_ACCEPTABLE_MAX:
        score += 25
    elif 10 <= length < TITLE_ACCEPTABLE_MIN or TITLE_ACCEPTABLE_MAX < length <= 80:
        score += 10

    # Keyword presence (30 pts)
    if _contains_keyword(text, keyword or ""):
        score += 30

    # Readability: 4-12 words, not shouting
    words = text.split()
    if 4 <= len(words) <= 12 and text != text.upper():
        score += 20

    # Starts with keyword bonus (10 pts)
    if _starts_with_keyword(text, keyword or ""):
        score += 10

    return min(score, 100)


def score_meta_description(description: str | None, keyword: str | None) -> int:
    """Meta description: ideal 120-160 chars, contains keyword."""
    text = _normalize(description)
    if not text:
        return 0

    score = 0
    length = len(text)

    # Length (40 pts)
    if META_IDEAL_MIN <= length <= META_IDEAL_MAX:
        score += 40
    elif META_ACCEPTABLE_MIN <= length < META_IDEAL_MIN or META_IDEAL_MAX < length <= META_ACCEPTABLE_MAX:
        score += 25
    elif 50 <= length < META_ACCEPTABLE_MIN or META_ACCEPTABLE_MAX < length <= 200:
        score += 10

    # Keyword presence (30 pts)
    if _contains_keyword(text, keyword or ""):
        score += 30

    # Sufficient content (20 pts)
    if len(text.split()) >= 10:
        score += 20

    # Starts with keyword bonus (10 pts)
    if _starts_with_keyword(text, keyword or ""):
        score += 10

    return min(score, 100)


def score_url(url: str | None, keyword: str | None) -> int:
    """URL: short, hyphenated, lowercased, contains keyword slug."""
    raw = _normalize(url)
    if not raw:
        return 0

    score = 0
    lowered = raw.lower()
    keyword_norm = _normalize(keyword) if keyword else ""
    keyword_slug = keyword_norm.lower().replace(" ", "-") if keyword_norm else ""

    # Keyword in URL (30 pts full slug, 20 partial)
    if keyword_slug and keyword_slug in lowered:
        score += 30
    elif keyword_norm and keyword_norm.lower() in lowered:
        score += 20

    # Length
    if len(raw) < URL_MAX_GOOD:
        score += 20
    elif len(raw) < URL_MAX_ACCEPTABLE:
        score += 10

    # Hyphens preferred, no underscores, lowercased, no spaces
    if "-" in raw and "_" not in raw:
        score += 15
    if raw == lowered and " " not in raw:
        score += 15

    # Clean URL: no query/hash
    if "?" not in raw and "&" not in raw and "#" not in raw:
        score += 10

    # Sensible segments 1-4
    segments = [s for s in raw.strip("/").split("/") if s]
    if 1 <= len(segments) <= 4:
        score += 10

    return min(score, 100)


def calculate_keyword_density(content: str | None, keyword: str | None) -> float:
    """Keyword density as percent of total words."""
    text = _normalize(content)
    kw = _normalize(keyword)
    if not text or not kw:
        return 0.0

    words = text.split()
    if not words:
        return 0.0

    content_lower = text.lower()
    keyword_lower = kw.lower()

    # Multi-word phrase vs single word
    if " " in keyword_lower:
        count = content_lower.count(keyword_lower)
        density = (count * len(keyword_lower.split()) / len(words)) * 100
    else:
        count = len(_word_pattern(keyword_lower).findall(content_lower))
        density = (count / len(words)) * 100

    return round(density, 2)


def score_keyword_density(density: float) -> int:
    """Map density to 0-100. 1-2.5% is ideal."""
    if DENSITY_IDEAL_MIN <= density <= DENSITY_IDEAL_MAX:
        return SCORE_DENSITY_IDEAL
    if DENSITY_OK_MIN <= density < DENSITY_IDEAL_MIN or DENSITY_IDEAL_MAX < density <= DENSITY_OK_MAX:
        return SCORE_DENSITY_OK
    if DENSITY_WARN_MIN <= density < DENSITY_OK_MIN or DENSITY_OK_MAX < density <= DENSITY_WARN_MAX:
        return SCORE_DENSITY_WARN
    if density > 0:
        return SCORE_DENSITY_LOW
    return 0


def score_content(content: str | None, keyword: str | None, density: float) -> int:
    """Content: word count + density + keyword in first 100 words."""
    text = _normalize(content)
    if not text:
        return 0

    score = 0
    words = text.split()
    word_count = len(words)

    # Word count (40 pts)
    if CONTENT_IDEAL_MIN <= word_count <= CONTENT_IDEAL_MAX:
        score += 40
    elif CONTENT_MIN_GOOD <= word_count < CONTENT_IDEAL_MIN or CONTENT_IDEAL_MAX < word_count <= CONTENT_TOO_LONG:
        score += 25
    elif CONTENT_MIN_THIN <= word_count < CONTENT_MIN_GOOD:
        score += 10

    # Density quality (30 pts)
    kd_score = score_keyword_density(density)
    if kd_score == SCORE_DENSITY_IDEAL:
        score += 30
    elif kd_score == SCORE_DENSITY_OK:
        score += 15
    elif kd_score == SCORE_DENSITY_WARN:
        score += 8
    elif kd_score == SCORE_DENSITY_LOW:
        score += 3

    # Keyword early in content (20 pts)
    first_100 = " ".join(words[:100]).lower()
    if keyword and _normalize(keyword).lower() in first_100:
        score += 20

    # Keyword present at all (10 pts)
    if _contains_keyword(text, keyword or ""):
        score += 10

    return min(score, 100)


def calculate_overall_score(
    title_score: int,
    meta_score: int,
    url_score: int,
    content_score: int,
    keyword_score: int,
) -> int:
    """Weighted average. Weights defined in constants.py."""
    weighted = (
        title_score * WEIGHT_TITLE
        + meta_score * WEIGHT_META
        + url_score * WEIGHT_URL
        + content_score * WEIGHT_CONTENT
        + keyword_score * WEIGHT_KEYWORD
    )
    return round(weighted)
