"""
Modular PDF generator for SEO reports.
Uses reportlab Platypus for precise, professional layout.
View layer only calls generate_report_pdf(report) -> bytes.
"""

import io

from django.utils import timezone
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.lib import colors

# Brand palette — matches site dark theme but PDF is light for print
PRIMARY = HexColor("#6366F1")
PRIMARY_DARK = HexColor("#4F46E5")
SUCCESS = HexColor("#16A34A")
LIME = HexColor("#65A30D")
WARNING = HexColor("#D97706")
DANGER = HexColor("#DC2626")
TEXT = HexColor("#0F172A")
MUTED = HexColor("#64748B")
BORDER = HexColor("#E2E8F0")
SURFACE = HexColor("#F8FAFC")

GRADE_COLORS = {
    "A": SUCCESS,
    "B": LIME,
    "C": WARNING,
    "D": DANGER,
}
GRADE_LABELS = {"A": "Excellent", "B": "Good", "C": "Needs Improvement", "D": "Poor"}
GRADE_BG = {
    "A": HexColor("#DCFCE7"),
    "B": HexColor("#ECFCCB"),
    "C": HexColor("#FEF3C7"),
    "D": HexColor("#FEE2E2"),
}
GRADE_BORDER = {
    "A": HexColor("#86EFAC"),
    "B": HexColor("#A3E635"),
    "C": HexColor("#FCD34D"),
    "D": HexColor("#FCA5A5"),
}


def _grade_for(score: int) -> str:
    from calculator.constants import grade_for_score

    return grade_for_score(score)


def generate_report_pdf(report) -> bytes:
    """
    Build a branded PDF for a single SEOReport instance.
    Returns bytes ready for HttpResponse.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=14 * mm,
        bottomMargin=16 * mm,
        title=f"SEO Report - {report.title[:40]}",
        author="SEO Audit Calculator",
    )

    styles = getSampleStyleSheet()

    # Custom styles
    s_title = ParagraphStyle("TitleCustom", parent=styles["Title"], fontSize=22, leading=26, textColor=TEXT, spaceAfter=2, alignment=1)
    s_h2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=13, leading=16, textColor=PRIMARY_DARK, spaceBefore=14, spaceAfter=6, borderPadding=(0, 0, 4))
    s_h3 = ParagraphStyle("H3", parent=styles["Heading3"], fontSize=10, leading=12, textColor=MUTED, spaceAfter=4)
    s_body = ParagraphStyle("Body", parent=styles["Normal"], fontSize=9.5, leading=14, textColor=TEXT, spaceAfter=4)
    s_small = ParagraphStyle("Small", parent=styles["Normal"], fontSize=8, leading=10, textColor=MUTED, spaceAfter=2)
    s_bullet = ParagraphStyle("Bullet", parent=s_body, leftIndent=12, bulletIndent=6, spaceAfter=3)
    s_score = ParagraphStyle("Score", parent=styles["Normal"], fontSize=32, leading=32, textColor=TEXT, alignment=1, spaceAfter=2)
    s_grade = ParagraphStyle("Grade", parent=styles["Normal"], fontSize=10, leading=12, textColor=MUTED, alignment=1)

    grade = _grade_for(report.overall_score)
    grade_color = GRADE_COLORS[grade]
    grade_label = GRADE_LABELS[grade]
    generated = timezone.localtime(report.created_at).strftime("%b %d, %Y %H:%M")

    story = []

    # --- Header band ---
    header_data = [
        [Paragraph('<b>SEO Audit Calculator</b>', ParagraphStyle("hdr", parent=s_small, textColor=PRIMARY_DARK, fontSize=9)), Paragraph(f'<font color="#64748B">Generated: {generated}</font>', ParagraphStyle("hdr2", parent=s_small, alignment=2))],
    ]
    header_table = Table(header_data, colWidths=[95 * mm, 85 * mm])
    header_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
    story.append(header_table)
    # thin line
    line = Table([[""]], colWidths=[180 * mm])
    line.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, -1), 0.6, PRIMARY)]))
    story.append(line)
    story.append(Spacer(1, 6 * mm))

    # Title block
    story.append(Paragraph("SEO Audit Report", s_title))
    story.append(Paragraph(f'<font color="#64748B">{report.url}</font>', ParagraphStyle("url", parent=s_small, alignment=1)))
    story.append(Spacer(1, 5 * mm))

    # Overall score card
    overall_data = [
        [Paragraph(f'<font size="32"><b>{report.overall_score}</b></font><font size="11" color="#64748B"> / 100</font>', s_score)],
        [Paragraph(f'<b>Grade {grade} — {grade_label}</b>', s_grade)],
        [Paragraph(f'Target keyword: <b>{report.target_keyword}</b> &nbsp;•&nbsp; {report.word_count} words', ParagraphStyle("kw", parent=s_small, alignment=1))],
    ]
    overall_table = Table(overall_data, colWidths=[180 * mm])
    overall_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), GRADE_BG[grade]),
        ("BOX", (0, 0), (-1, -1), 0.8, GRADE_BORDER[grade]),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, GRADE_BORDER[grade]),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(overall_table)
    story.append(Spacer(1, 6 * mm))

    # Scores table
    story.append(Paragraph("Scores Breakdown", s_h2))
    score_rows = [
        [Paragraph("<b>Metric</b>", s_small), Paragraph("<b>Score</b>", s_small), Paragraph("<b>Details</b>", s_small)],
        [Paragraph("Title Tag", s_body), Paragraph(f"{report.title_score}/100", s_body), Paragraph(f"{len(report.title)} chars", s_small)],
        [Paragraph("Meta Description", s_body), Paragraph(f"{report.meta_score}/100", s_body), Paragraph(f"{len(report.meta_description)} chars", s_small)],
        [Paragraph("URL Structure", s_body), Paragraph(f"{report.url_score}/100", s_body), Paragraph(f"{len(report.url)} chars", s_small)],
        [Paragraph("Content Quality", s_body), Paragraph(f"{report.content_score}/100", s_body), Paragraph(f"{report.word_count} words", s_small)],
        [Paragraph("Keyword Density", s_body), Paragraph(f"{report.keyword_density}%", s_body), Paragraph(f"Ideal 1–2.5% for “{report.target_keyword}”", s_small)],
    ]
    t = Table(score_rows, colWidths=[55 * mm, 25 * mm, 100 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#F1F5F9")),
        ("TEXTCOLOR", (0, 0), (-1, 0), MUTED),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (1, 0), (1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.4, BORDER),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, SURFACE]),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(t)
    story.append(Spacer(1, 6 * mm))

    # Website Title section
    story.append(Paragraph("Website Title", s_h2))
    story.append(Paragraph(report.title, s_body))
    story.append(Spacer(1, 3 * mm))

    # Recommendations
    story.append(Paragraph("Recommendations", s_h2))
    if report.recommendations:
        for tip in report.recommendations:
            # Escape for Paragraph XML
            safe = tip.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            story.append(Paragraph(safe, s_bullet, bulletText="•"))
    else:
        story.append(Paragraph("No recommendations — your page looks well optimized.", s_body))

    story.append(Spacer(1, 8 * mm))
    # Footer note
    story.append(Paragraph(f"Generated on {generated} • SEO Audit Calculator • Report #{report.pk}", ParagraphStyle("footer", parent=s_small, alignment=1, textColor=MUTED)))

    # Build with footer page numbers
    def _footer(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(BORDER)
        canvas.setLineWidth(0.5)
        canvas.line(doc.leftMargin, doc.bottomMargin - 6, doc.width + doc.leftMargin, doc.bottomMargin - 6)
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(MUTED)
        canvas.drawCentredString(doc.width / 2 + doc.leftMargin, doc.bottomMargin - 12, f"SEO Audit Calculator — Confidential • Page {doc.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf
