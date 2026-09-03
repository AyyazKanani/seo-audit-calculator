import re

from .base import BaseAIProvider


_RESPONSES: dict[str, str] = {
    "title": (
        "**Title Tag — Quick Guide**\n"
        "- Keep 50–60 characters so Google doesn't truncate.\n"
        "- Put your main keyword near the start.\n"
        "- Make it unique per page and compelling for clicks.\n"
        "- Example: `Best SEO Tips for 2026 — Rank Higher on Google`"
    ),
    "meta description": (
        "**Meta Description — Quick Guide**\n"
        "- Aim for 120–160 characters.\n"
        "- Include the target keyword naturally + a call-to-action.\n"
        "- Each page needs a unique description for better CTR."
    ),
    "meta": (
        "**Meta Description — Quick Guide**\n"
        "- Aim for 120–160 characters.\n"
        "- Include the target keyword naturally + a call-to-action.\n"
        "- Each page needs a unique description for better CTR."
    ),
    "keyword": (
        "**Keywords — Beginner Tips**\n"
        "- Pick 1 primary keyword per page (e.g. `seo tips`).\n"
        "- Use it in title, first 100 words, one heading, and URL slug.\n"
        "- Keep density 1–2.5% — avoid stuffing."
    ),
    "backlink": (
        "**Backlinks — What Matters**\n"
        "- One link from a trusted site beats 10 low-quality links.\n"
        "- Earn them with useful content, not buying.\n"
        "- Track with Search Console → Links report."
    ),
    "content": (
        "**Content — What Google Loves**\n"
        "- Aim 600–1500 words for competitive topics.\n"
        "- Answer the search intent in the first paragraph.\n"
        "- Use headings (H2/H3) to structure topics."
    ),
    "heading": (
        "**Headings (H1–H3) — Structure**\n"
        "- One H1 per page containing the keyword.\n"
        "- H2s for main sections, H3s for sub-points.\n"
        "- Keep headings descriptive, not clever."
    ),
    "url": (
        "**URLs — Clean & Short**\n"
        "- Use lowercase + hyphens: `/blog/seo-tips/`\n"
        "- Keep under 75 chars, include keyword.\n"
        "- Avoid `?id=123` parameters."
    ),
    "page speed": (
        "**Page Speed — Fast Wins**\n"
        "- Optimize images (WebP, lazy-load).\n"
        "- Minify CSS/JS, enable caching.\n"
        "- Test with PageSpeed Insights — aim Core Web Vitals green."
    ),
    "speed": (
        "**Page Speed — Fast Wins**\n"
        "- Optimize images (WebP, lazy-load).\n"
        "- Minify CSS/JS, enable caching.\n"
        "- Test with PageSpeed Insights."
    ),
    "image": (
        "**Images — SEO Checklist**\n"
        "- Compress + use WebP, add `alt` text with keyword where relevant.\n"
        "- Use descriptive file names: `seo-tips-cover.webp`."
    ),
    "alt": (
        "**Images — SEO Checklist**\n"
        "- Compress + use WebP, add `alt` text with keyword where relevant.\n"
        "- Use descriptive file names."
    ),
}

_FALLBACK = (
    "I can help with SEO topics like **title, meta description, keywords, backlinks, content, headings, URLs, page speed, and images**.\n\n"
    "Try asking: *How do I write a good title?* or *What is keyword density?*\n"
    "Your question was: \"{prompt}\" — Could you rephrase with one of those keywords?"
)


class DummyProvider(BaseAIProvider):
    """Keyword-matched predefined responses. No external API."""

    def get_response(self, prompt: str, history: list[dict] | None = None) -> str:
        text = (prompt or "").lower()
        # Normalize: keep letters, numbers, spaces
        text = re.sub(r"[^a-z0-9 ]+", " ", text)

        # Longest keys first so "meta description" beats "meta"
        for key in sorted(_RESPONSES, key=len, reverse=True):
            if key in text:
                return _RESPONSES[key]

        return _FALLBACK.format(prompt=prompt.strip()[:120])
