import json

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, JsonResponse
from django.shortcuts import render
from django.utils.translation import gettext as _

from .fileutils import (
    extract_text,
    human_size,
    is_allowed,
    is_pdf,
    truncate,
)
from .models import Attachment, Conversation, Message
from .pdf import build_report
from .services import AssistantService


@login_required
def chat_page(request):

    conversation = (
        Conversation.objects
        .filter(user=request.user)
        .order_by("-updated_at")
        .first()
    )

    messages = []

    if conversation:
        messages = conversation.messages.all()

    conversations = (
        Conversation.objects
        .filter(user=request.user)[:10]
    )

    return render(
        request,
        "assistant/chat.html",
        {
            "conversation": conversation,
            "current_pk": conversation.pk if conversation else None,
            "messages": messages,
            "conversations": conversations,
            "max_files": getattr(settings, "ASSISTANT_MAX_FILES", 10),
            "max_file_size_mb": getattr(
                settings, "ASSISTANT_MAX_FILE_SIZE_MB", 20
            ),
            "allowed_extensions": settings.ASSISTANT_ALLOWED_EXTENSIONS,
        },
    )


def _get_conversation(request, conversation_id=None):

    if conversation_id:
        conversation = (
            Conversation.objects
            .filter(pk=conversation_id, user=request.user)
            .first()
        )
        if conversation:
            return conversation

    return Conversation.objects.create(user=request.user)


def _user_attachments(request, ids):
    """Fetch attachments belonging to the current user, preserving order."""
    ids = list(dict.fromkeys(ids or []))
    if not ids:
        return []
    attachments = list(
        Attachment.objects.filter(
            pk__in=ids,
            user=request.user,
        )
    )
    order = {pk: index for index, pk in enumerate(ids)}
    attachments.sort(key=lambda item: order.get(item.pk, 0))
    return attachments


@login_required
def api_files_upload(request):

    if request.method != "POST":
        return JsonResponse(
            {"error": _("method not allowed")},
            status=405,
        )

    files = request.FILES.getlist("files")

    if not files:
        return JsonResponse(
            {"error": _("No files received")},
            status=400,
        )

    max_files = getattr(settings, "ASSISTANT_MAX_FILES", 10)

    if len(files) > max_files:
        return JsonResponse(
            {
                "error": _(
                    "You can upload up to %(count)s files at once."
                ) % {"count": max_files},
            },
            status=400,
        )

    max_bytes = (
        getattr(settings, "ASSISTANT_MAX_FILE_SIZE_MB", 20)
        * 1024
        * 1024
    )
    max_text_chars = getattr(
        settings, "ASSISTANT_MAX_FILE_TEXT_CHARS", 300000
    )

    conversation = _get_conversation(
        request,
        request.POST.get("conversation_id"),
    )

    created = []
    errors = []

    for uploaded in files:

        name = uploaded.name or "file"

        if not is_allowed(name):
            errors.append(
                {
                    "name": name,
                    "error": _("Unsupported file type."),
                }
            )
            continue

        if uploaded.size > max_bytes:
            errors.append(
                {
                    "name": name,
                    "error": _(
                        "File exceeds the %(size)s MB limit."
                    ) % {"size": max_bytes // (1024 * 1024)},
                }
            )
            continue

        if name.lower().endswith(".pdf") and not is_pdf(uploaded):
            errors.append(
                {
                    "name": name,
                    "error": _("This file is not a valid PDF."),
                }
            )
            continue

        try:
            text, kind = extract_text(uploaded, name)
        except ValueError as exc:
            errors.append({"name": name, "error": str(exc)})
            continue

        text = text[:max_text_chars]

        uploaded.seek(0)

        attachment = Attachment.objects.create(
            conversation=conversation,
            user=request.user,
            name=name,
            file=uploaded,
            kind=kind,
            size=uploaded.size,
            text=text,
        )

        created.append(
            {
                "id": attachment.pk,
                "name": attachment.name,
                "kind": attachment.kind,
                "size": attachment.size,
                "size_human": human_size(attachment.size),
                "conversation_id": conversation.pk,
            }
        )

    return JsonResponse(
        {
            "files": created,
            "errors": errors,
            "conversation_id": conversation.pk,
        },
        status=201 if created else 400,
    )


@login_required
def api_files_analyze(request):

    if request.method != "POST":
        return JsonResponse(
            {"error": _("method not allowed")},
            status=405,
        )

    try:
        body = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        body = {}

    attachments = _user_attachments(
        request,
        body.get("attachment_ids") or [],
    )

    if not attachments:
        return JsonResponse(
            {"error": _("No valid files selected")},
            status=400,
        )

    task = body.get("task") or "summarize"

    if task not in ("summarize", "analyze", "qa"):
        task = "summarize"

    question = (body.get("question") or "").strip()

    conversation = _get_conversation(
        request,
        body.get("conversation_id"),
    )

    user_message = Message.objects.create(
        conversation=conversation,
        role=Message.Role.USER,
        content=AssistantService.file_task_prompt(task, question),
    )

    reply, source, sources = AssistantService.get_file_reply(
        request.user,
        getattr(request, "current_institution", None),
        task,
        question,
        attachments,
    )

    Message.objects.create(
        conversation=conversation,
        role=Message.Role.ASSISTANT,
        content=reply,
        sources=sources,
    )

    return JsonResponse(
        {
            "reply": reply,
            "source": source,
            "sources": sources,
            "conversation_id": conversation.pk,
        }
    )


@login_required
def api_files_report(request):

    if request.method != "POST":
        return JsonResponse(
            {"error": _("method not allowed")},
            status=405,
        )

    try:
        body = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        body = {}

    attachments = _user_attachments(
        request,
        body.get("attachment_ids") or [],
    )

    if not attachments:
        return JsonResponse(
            {"error": _("No valid files selected")},
            status=400,
        )

    excerpt_chars = getattr(
        settings, "ASSISTANT_REPORT_EXCERPT_CHARS", 3000
    )

    files = [
        {
            "name": attachment.name,
            "kind": attachment.kind,
            "size": attachment.size,
            "excerpt": truncate(attachment.text or "", excerpt_chars),
        }
        for attachment in attachments
    ]

    institution = getattr(request, "current_institution", None)

    import io

    buffer = io.BytesIO()

    build_report(
        buffer,
        institution=institution.name if institution else None,
        user_name=(
            request.user.get_full_name() or request.user.username
        ),
        title=(body.get("title") or "").strip() or None,
        notes=body.get("notes") or "",
        files=files,
    )

    buffer.seek(0)

    return FileResponse(
        buffer,
        as_attachment=True,
        filename="assistant-report.pdf",
        content_type="application/pdf",
    )


@login_required
def api_chat(request):

    if request.method != "POST":
        return JsonResponse(
            {"error": _("method not allowed")},
            status=405,
        )

    try:
        body = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        body = {}

    question = (body.get("message") or "").strip()

    if not question:
        return JsonResponse(
            {"error": _("empty message")},
            status=400,
        )

    conversation = _get_conversation(
        request,
        body.get("conversation_id"),
    )

    attachment_ids = body.get("attachment_ids") or []

    Message.objects.create(
        conversation=conversation,
        role=Message.Role.USER,
        content=question,
    )

    if attachment_ids:

        attachments = _user_attachments(request, attachment_ids)

        reply, source, sources = AssistantService.get_file_reply(
            request.user,
            getattr(request, "current_institution", None),
            "qa",
            question,
            attachments,
        )

    else:

        reply, source, sources = AssistantService.get_reply(
            request.user,
            getattr(request, "current_institution", None),
            question,
            conversation=conversation,
        )

    emotion = AssistantService.detect_emotion(question)

    Message.objects.create(
        conversation=conversation,
        role=Message.Role.ASSISTANT,
        content=reply,
        sources=sources,
    )

    return JsonResponse(
        {
            "reply": reply,
            "source": source,
            "emotion": emotion,
            "sources": sources,
            "conversation_id": conversation.pk,
        }
    )
