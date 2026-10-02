"""
HTML parser for SEO element extraction.

Reads raw HTML and returns a structured dict of SEO signals.
No scoring logic here — pure extraction.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup


@dataclass
class SEOData:
    """All SEO signals extracted from a page."""
    # Title
    title: str = ""
    title_length: int = 0

    # Meta
    meta_description: str = ""
    meta_description_length: int = 0
    canonical_url: str = ""
    robots_meta: str = ""          # e.g. "noindex, nofollow"

    # Headings
    h1_count: int = 0
    h1_texts: list[str] = field(default_factory=list)
    h2_count: int = 0

    # Images
    image_count: int = 0
    images_missing_alt: int = 0
    images_missing_alt_src: list[str] = field(default_factory=list)

    # Links
    internal_links: int = 0
    external_links: int = 0

    # Content
    word_count: int = 0
    body_text: str = ""            # cleaned body text

    # Security / protocol
    is_https: bool = False

    # Keyword
    keyword_found: bool = False
    keyword_in_title: bool = False
    keyword_in_meta: bool = False
    keyword_in_h1: bool = False
    keyword_in_url: bool = False
    keyword_density: float = 0.0

    # Raw URL info
    final_url: str = ""
    url_path: str = ""


def _clean_text(soup: BeautifulSoup) -> str:
    """Extract visible text, strip non-content tags, collapse whitespace."""
    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()
    text = soup.get_text(separator=" ", strip=True)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _count_words(text: str) -> int:
    if not text:
        return 0
    return len(text.split())


def parse_html(html: str, url: str, target_keyword: str = "") -> SEOData:
    """
    Parse HTML and return SEOData with all extracted elements.

    Parameters:
        html: raw HTML string
        url: final URL after any redirects
        target_keyword: optional keyword to check presence / density
    """
    soup = BeautifulSoup(html, "html.parser")
    data = SEOData()
    data.final_url = url

    parsed_url = urlparse(url)
    data.is_https = parsed_url.scheme == "https"
    data.url_path = parsed_url.path

    # ---- Title ----
    title_tag = soup.find("title")
    if title_tag:
        data.title = re.sub(r"\s+", " ", title_tag.get_text(strip=True))
    data.title_length = len(data.title)

    # ---- Meta description ----
    meta_desc = soup.find("meta", attrs={"name": re.compile(r"^description$", re.I)})
    if meta_desc and meta_desc.get("content"):
        data.meta_description = re.sub(r"\s+", " ", meta_desc["content"].strip())
    data.meta_description_length = len(data.meta_description)

    # ---- Canonical ----
    canonical = soup.find("link", attrs={"rel": re.compile(r"^canonical$", re.I)})
    if canonical and canonical.get("href"):
        data.canonical_url = canonical["href"].strip()

    # ---- Robots meta ----
    robots_meta = soup.find("meta", attrs={"name": re.compile(r"^robots$", re.I)})
    if robots_meta and robots_meta.get("content"):
        data.robots_meta = robots_meta["content"].strip()

    # ---- Headings ----
    h1_tags = soup.find_all("h1")
    data.h1_count = len(h1_tags)
    data.h1_texts = [re.sub(r"\s+", " ", h.get_text(strip=True)) for h in h1_tags[:5]]
    data.h2_count = len(soup.find_all("h2"))

    # ---- Images ----
    img_tags = soup.find_all("img")
    data.image_count = len(img_tags)
    for img in img_tags:
        alt = img.get("alt")
        src = img.get("src", "")
        if alt is None or alt.strip() == "":
            data.images_missing_alt += 1
            if len(data.images_missing_alt_src) < 10:
                data.images_missing_alt_src.append(src[:200])

    # ---- Links ----
    base_domain = parsed_url.netloc.lower()
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"].strip()
        if not href or href.startswith("#") or href.startswith("javascript:"):
            continue
        # Resolve relative URLs
        abs_url = urljoin(url, href)
        link_parsed = urlparse(abs_url)
        link_domain = link_parsed.netloc.lower()
        if link_domain == base_domain:
            data.internal_links += 1
        elif link_domain:
            data.external_links += 1

    # ---- Body text / word count ----
    data.body_text = _clean_text(soup)
    data.word_count = _count_words(data.body_text)

    # ---- Keyword checks ----
    kw = (target_keyword or "").strip()
    if kw:
        kw_lower = kw.lower()
        data.keyword_found = kw_lower in data.body_text.lower()
        data.keyword_in_title = kw_lower in data.title.lower()
        data.keyword_in_meta = kw_lower in data.meta_description.lower()
        data.keyword_in_h1 = any(kw_lower in h.lower() for h in data.h1_texts)
        data.keyword_in_url = kw_lower in url.lower()

        # Density
        if data.word_count > 0:
            body_lower = data.body_text.lower()
            if " " in kw_lower:
                count = body_lower.count(kw_lower)
                data.keyword_density = round((count * len(kw.split()) / data.word_count) * 100, 2)
            else:
                pattern = re.compile(r"\b" + re.escape(kw_lower) + r"\b", re.I)
                count = len(pattern.findall(body_lower))
                data.keyword_density = round((count / data.word_count) * 100, 2)

    return data
