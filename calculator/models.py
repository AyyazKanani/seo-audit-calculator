from django.conf import settings
from django.db import models
from django.db.models import Q
from django.urls import reverse

from .constants import GRADE_RANGES, grade_for_score


class SEOReportQuerySet(models.QuerySet):
    """Reusable filters — keeps views thin and consistent."""

    def for_user(self, user):
        return self.filter(user=user)

    def search(self, query: str):
        query = (query or "").strip()
        if not query:
            return self
        return self.filter(Q(title__icontains=query) | Q(target_keyword__icontains=query))

    def with_grade(self, grade: str):
        grade = (grade or "").strip().upper()
        # Accept labels like "Excellent" as well
        from .constants import GRADE_LABEL_TO_CODE

        if grade in GRADE_LABEL_TO_CODE:
            grade = GRADE_LABEL_TO_CODE[grade]
        if grade not in GRADE_RANGES:
            return self
        low, high = GRADE_RANGES[grade]
        return self.filter(overall_score__gte=low, overall_score__lte=high)


class SEOReport(models.Model):
    """
    Stores every SEO calculation. Inputs are saved verbatim,
    scores are computed via calculator.services before save.
    """

    class Grade(models.TextChoices):
        A = "A", "Excellent"
        B = "B", "Good"
        C = "C", "Needs Work"
        D = "D", "Poor"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="seo_reports",
        help_text="Owner of the report. Null for anonymous audits.",
        db_index=True,
    )

    # ---- Inputs ----
    url = models.CharField(
        max_length=500,
        help_text="Page URL or slug (e.g. /blog/seo-tips)",
    )
    title = models.CharField(max_length=200, help_text="Page title tag", db_index=True)
    meta_description = models.CharField(
        max_length=500,
        help_text="Meta description tag",
    )
    content = models.TextField(help_text="Main page content / body text")
    target_keyword = models.CharField(
        max_length=100,
        help_text="Primary keyword to optimize for",
        db_index=True,
    )

    # ---- Computed ----
    title_score = models.PositiveSmallIntegerField(default=0)
    meta_score = models.PositiveSmallIntegerField(default=0)
    url_score = models.PositiveSmallIntegerField(default=0)
    keyword_density = models.FloatField(default=0.0, help_text="Density in %")
    content_score = models.PositiveSmallIntegerField(default=0)
    overall_score = models.PositiveSmallIntegerField(default=0, db_index=True)

    recommendations = models.JSONField(default=list, blank=True)

    word_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = SEOReportQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "SEO Report"
        verbose_name_plural = "SEO Reports"
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["overall_score"]),
        ]

    def __str__(self) -> str:
        return f"Report #{self.pk} - {self.overall_score}/100 - {self.target_keyword}"

    def get_absolute_url(self) -> str:
        return reverse("calculator:result", kwargs={"pk": self.pk})

    @property
    def grade(self) -> str:
        """Letter grade derived from overall_score."""
        return grade_for_score(self.overall_score)

    @property
    def grade_label(self) -> str:
        return self.Grade(self.grade).label
