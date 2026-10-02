"""
Views for the URL Analyzer.

Two views:
  1. analyzer_view      – form display + analysis (GET/POST)
  2. analyzer_result_view – cached result display (GET only, pk-based)
"""

from django.contrib import messages
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET

from calculator.models import SEOReport

from .fetcher import fetch_url
from .forms import URLAnalysisForm
from .parser import parse_html
from .scoring import build_report_data


def analyzer_view(request):
    """
    GET: show URL analysis form.
    POST: fetch → parse → score → show result (in-memory) and optionally save.
    """
    if request.method == "POST":
        form = URLAnalysisForm(request.POST)
        if form.is_valid():
            url = form.cleaned_data["url"]
            keyword = form.cleaned_data["target_keyword"]

            # Step 1: Fetch
            result = fetch_url(url)
            if result.error:
                messages.error(request, result.error)
                return render(request, "calculator/analyzer.html", {"form": form})

            # Step 2: Parse
            seo_data = parse_html(result.html, result.final_url, keyword)

            # Step 3: Score + recommendations
            report_data = build_report_data(seo_data, keyword)

            # Step 4: Save report if user is logged in
            report = None
            if request.user.is_authenticated:
                report = SEOReport(
                    user=request.user,
                    url=report_data["url"],
                    title=report_data["title"][:200] or report_data["url"][:200],
                    meta_description=report_data["meta_description"][:500] or "Auto-analyzed from URL",
                    content=seo_data.body_text[:50000],  # respect model max
                    target_keyword=keyword[:100] if keyword else "general",
                    title_score=report_data["title_score"],
                    meta_score=report_data["meta_score"],
                    url_score=report_data["url_score"],
                    keyword_density=report_data["keyword_density"],
                    content_score=report_data["content_score"],
                    overall_score=report_data["overall_score"],
                    word_count=report_data["word_count"],
                    recommendations=report_data["recommendations"],
                )
                report.save()

            # Pass data to result template
            context = {
                "report_data": report_data,
                "report": report,  # None if anonymous
                "from_analyzer": True,
            }
            return render(request, "calculator/analyzer_result.html", context)
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        form = URLAnalysisForm()

    return render(request, "calculator/analyzer.html", {"form": form})


@require_GET
def analyzer_result_view(request, pk: int):
    """
    Display a previously saved URL-analyzed report.
    Only accessible to the report owner (or anonymous if user is None).
    """
    report = get_object_or_404(SEOReport, pk=pk)
    if report.user_id is not None and report.user_id != getattr(request.user, "id", None):
        raise Http404("Report not found.")

    # Reconstruct report_data for the template
    from calculator.constants import grade_for_score

    report_data = {
        "url": report.url,
        "title": report.title,
        "meta_description": report.meta_description,
        "target_keyword": report.target_keyword,
        "title_score": report.title_score,
        "meta_score": report.meta_score,
        "url_score": report.url_score,
        "content_score": report.content_score,
        "keyword_density": report.keyword_density,
        "overall_score": report.overall_score,
        "word_count": report.word_count,
        "recommendations": report.recommendations,
        "is_url_analysis": True,
    }
    context = {
        "report_data": report_data,
        "report": report,
        "from_analyzer": True,
    }
    return render(request, "calculator/analyzer_result.html", context)
