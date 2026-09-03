import json

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from .models import ChatMessage
from .services.factory import get_ai_provider


@login_required
def assistant_view(request):
    # Only last 100 to keep page fast; ordered for chat flow
    messages = ChatMessage.objects.filter(user=request.user).order_by("created_at")[:100]
    return render(request, "assistant/chat.html", {"messages": messages})


@login_required
@require_POST
def send_message(request):
    try:
        data = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON."}, status=400)

    prompt = (data.get("message") or "").strip()
    if not prompt:
        return JsonResponse({"error": "Message cannot be empty."}, status=400)
    if len(prompt) > 2000:
        return JsonResponse({"error": "Message too long (max 2000)."}, status=400)

    # Build history *before* saving current turn — provider gets prior context only
    history_qs = ChatMessage.objects.filter(user=request.user).order_by("-created_at")[:9]
    history = [{"role": m.role, "content": m.content} for m in reversed(list(history_qs))]

    # Atomic: both turns saved together or not at all
    with transaction.atomic():
        ChatMessage.objects.create(user=request.user, role=ChatMessage.Role.USER, content=prompt)
        provider = get_ai_provider()
        reply = provider.get_response(prompt, history=history)
        ChatMessage.objects.create(user=request.user, role=ChatMessage.Role.ASSISTANT, content=reply)

    return JsonResponse({"reply": reply})


@login_required
@require_POST
def clear_chat(request):
    ChatMessage.objects.filter(user=request.user).delete()
    return JsonResponse({"ok": True})
