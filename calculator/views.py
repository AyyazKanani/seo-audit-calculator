from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from .forms import SEOReportForm
from .models import SEOReport
from .pdf import generate_report_pdf
from .services import create_report


def calculator_view(request):
    """
    Thin view: validates form and delegates calculation to services.create_report.
    No scoring logic here — keeps views testable and reusable.
    """
    if request.method == "POST":
        form = SEOReportForm(request.POST)
        if form.is_valid():
            report: SEOReport = create_report(
                user=request.user,
                form_data=form.cleaned_data,
            )
            messages.success(request, f"Report saved — Overall score {report.overall_score}/100")
            return redirect(report.get_absolute_url())
        messages.error(request, "Please fix the errors below.")
    else:
        form = SEOReportForm()

    return render(request, "calculator/calculator.html", {"form": form})


def result_view(request, pk: int):
    report = get_object_or_404(SEOReport, pk=pk)
    # Protect: if report belongs to someone, only owner can view
    if report.user_id is not None and report.user_id != getattr(request.user, "id", None):
        raise Http404("Report not found.")
    return render(request, "calculator/result.html", {"report": report})


@login_required
def report_list_view(request):
    """
    Private history for logged-in user.
    Supports ?q= search (title or keyword) and ?grade= filter (A/B/C/D).
    Paginated 9 per page. Uses single source GRADE_RANGES.
    """
    from calculator.constants import GRADE_LABEL_TO_CODE, GRADE_RANGES

    qs = SEOReport.objects.filter(user=request.user)

    q = (request.GET.get("q") or "").strip()[:100]
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(target_keyword__icontains=q))

    grade = (request.GET.get("grade") or "").strip().upper()
    if grade in GRADE_LABEL_TO_CODE:
        grade = GRADE_LABEL_TO_CODE[grade]
    if grade in GRADE_RANGES:
        low, high = GRADE_RANGES[grade]
        qs = qs.filter(overall_score__gte=low, overall_score__lte=high)
    else:
        grade = ""  # normalize invalid value

    paginator = Paginator(qs, 9)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "reports": page_obj.object_list,
        "q": q,
        "grade": grade,
        "total_count": paginator.count,
        "page_range": paginator.get_elided_page_range(page_obj.number, on_each_side=2, on_ends=1),
    }
    return render(request, "calculator/report_list.html", context)


@login_required
@require_POST
def report_delete_view(request, pk: int):
    report = get_object_or_404(SEOReport, pk=pk, user=request.user)
    report.delete()
    messages.success(request, "Report deleted.")
    return redirect("calculator:reports")


@login_required
@require_GET
def report_pdf_view(request, pk: int):
    # Single query enforces ownership — no separate check needed (IDOR-safe)
    report = get_object_or_404(SEOReport, pk=pk, user=request.user)
    pdf_bytes = generate_report_pdf(report)
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    date_str = timezone.localtime(report.created_at).strftime("%Y-%m-%d")
    response["Content-Disposition"] = f'attachment; filename="seo-report-{date_str}.pdf"'
    return response
