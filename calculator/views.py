from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from .forms import SEOReportForm
from .models import SEOReport
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
    return render(request, "calculator/result.html", {"report": report})
