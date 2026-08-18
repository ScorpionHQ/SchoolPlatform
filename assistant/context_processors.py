from django.conf import settings
from django.templatetags.static import static

try:
    from django.contrib.staticfiles.finders import find
except ImportError:  # pragma: no cover
    find = None

from .services import AssistantService


def _avatar_url(path):
    try:
        return static(path)
    except Exception:
        return ""


def _avatar_exists(path):
    if not path or not find:
        return False
    try:
        return bool(find(path))
    except Exception:
        return False


def assistant_context(request):

    if not getattr(settings, "ASSISTANT_ENABLED", True):
        return {}

    user = getattr(request, "user", None)

    persona = AssistantService.persona_for(user)

    avatar_path = persona.get("avatar", "")

    config = {
        "name": persona.get("name", settings.ASSISTANT_NAME),
        "description": persona.get("description", ""),
        "avatar_url": _avatar_url(avatar_path),
        "avatar_exists": _avatar_exists(avatar_path),
    }

    emotion_prefix = persona.get("emotion_prefix", "")

    emotions = {}

    if emotion_prefix:

        for state in AssistantService.EMOTION_STATES:

            path = f"{emotion_prefix}/{state}.png"

            if _avatar_exists(path):

                emotions[state] = _avatar_url(path)

    config["emotions"] = emotions

    return {
        "assistant_config": config,
    }
