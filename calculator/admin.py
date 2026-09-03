from django.contrib import admin
from .models import SEOReport


@admin.register(SEOReport)
class SEOReportAdmin(admin.ModelAdmin):
    list_display = ("id", "target_keyword", "overall_score", "grade", "user", "created_at")
    list_filter = ("created_at",)
    search_fields = ("url", "title", "target_keyword", "user__username")
    readonly_fields = (
        "title_score",
        "meta_score",
        "url_score",
        "keyword_density",
        "content_score",
        "overall_score",
        "word_count",
        "recommendations",
        "created_at",
        "updated_at",
    )
    ordering = ("-created_at",)
