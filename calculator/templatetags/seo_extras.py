from django import template
from calculator.constants import grade_for_score

register = template.Library()


@register.filter
def grade_letter(score):
    """Return grade letter A/B/C/D for a numeric score. Usage: {{ score|grade_letter }}"""
    return grade_for_score(score)


@register.filter
def grade_lower(score):
    """Lowercased grade for CSS classes: a/b/c/d"""
    return grade_for_score(score).lower()
