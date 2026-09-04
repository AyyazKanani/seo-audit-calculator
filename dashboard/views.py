from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Max, Min, Q
from django.shortcuts import render

from calculator.constants import grade_for_score
from calculator.models import SEOReport


@login_required
def dashboard_view(request):
    """
    Optimized dashboard: 2 queries total.
    1) Single aggregate for all stats + distribution
    2) Recent 5 reports (only needed fields)
    """
    base_qs = SEOReport.objects.for_user(request.user)

    # Single aggregate query for all summary cards + distribution
    stats = base_qs.aggregate(
        total=Count("id"),
        avg_score=Avg("overall_score"),
        best_score=Max("overall_score"),
        worst_score=Min("overall_score"),
        excellent=Count("id", filter=Q(overall_score__gte=80)),
        good=Count("id", filter=Q(overall_score__gte=60, overall_score__lt=80)),
        needs=Count("id", filter=Q(overall_score__gte=40, overall_score__lt=60)),
        poor=Count("id", filter=Q(overall_score__lt=40)),
    )

    total = stats["total"] or 0
    avg_score = round(stats["avg_score"]) if stats["avg_score"] is not None else 0
    best_score = stats["best_score"] or 0
    worst_score = stats["worst_score"] or 0

    # Distribution with percentages (avoid extra query)
    distribution = []
    if total > 0:
        for label, count, color, grade in [
            ("Excellent", stats["excellent"], "success", "A"),
            ("Good", stats["good"], "lime", "B"),
            ("Needs Improvement", stats["needs"], "warning", "C"),
            ("Poor", stats["poor"], "danger", "D"),
        ]:
            pct = round((count / total) * 100) if total else 0
            distribution.append(
                {"label": label, "count": count, "pct": pct, "color": color, "grade": grade}
            )
    else:
        distribution = [
            {"label": "Excellent", "count": 0, "pct": 0, "color": "success", "grade": "A"},
            {"label": "Good", "count": 0, "pct": 0, "color": "lime", "grade": "B"},
            {"label": "Needs Improvement", "count": 0, "pct": 0, "color": "warning", "grade": "C"},
            {"label": "Poor", "count": 0, "pct": 0, "color": "danger", "grade": "D"},
        ]

    # Recent 5 — only needed columns (avoid fetching large `content` field)
    recent_reports = base_qs.only("title", "target_keyword", "overall_score", "created_at", "url").order_by("-created_at")[:5]

    # Stat cards config for reusable include — DRY, easy to extend
    def _grade_lower(score: int) -> str:
        return grade_for_score(score).lower() if total else ""

    stat_cards = [
        {"label": "Total Audits", "value": total, "suffix": "", "icon": "bi-collection", "bg": "bg-indigo", "badge_label": "Total", "badge_grade": "", "delay": 50},
        {"label": "Average Score", "value": avg_score, "suffix": "/100", "icon": "bi-graph-up", "bg": "bg-cyan", "badge_label": "Avg", "badge_grade": "", "delay": 80},
        {"label": "Best Score", "value": best_score, "suffix": "/100", "icon": "bi-trophy", "bg": "bg-green", "badge_label": str(best_score), "badge_grade": _grade_lower(best_score), "delay": 110},
        {"label": "Worst Score", "value": worst_score, "suffix": "/100", "icon": "bi-flag", "bg": "bg-amber", "badge_label": str(worst_score), "badge_grade": _grade_lower(worst_score), "delay": 140},
    ]

    context = {
        "total_audits": total,
        "avg_score": avg_score,
        "best_score": best_score,
        "worst_score": worst_score,
        "stat_cards": stat_cards,
        "distribution": distribution,
        "recent_reports": recent_reports,
        "has_reports": total > 0,
    }
    return render(request, "dashboard/dashboard.html", context)
