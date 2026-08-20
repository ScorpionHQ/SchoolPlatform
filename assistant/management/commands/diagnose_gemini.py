import os
import sys

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Diagnose Gemini API connectivity on the server"

    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write("  GEMINI API DIAGNOSTIC")
        self.stdout.write("=" * 60)

        # 1. Check local_settings.py
        self.stdout.write("\n[1] Checking config/settings/local_settings.py ...")
        try:
            from config.settings import local_settings
            key = getattr(local_settings, "GEMINI_API_KEY", "NOT_FOUND")
            if key and key != "CHANGE_ME_ON_SERVER":
                self.stdout.write(self.style.SUCCESS(
                    f"  OK - local_settings.GEMINI_API_KEY = {key[:8]}...{key[-4:]} (len={len(key)})"
                ))
            else:
                self.stdout.write(self.style.ERROR(
                    f"  FAIL - GEMINI_API_KEY is placeholder or empty: '{key}'"
                ))
        except ImportError:
            self.stdout.write(self.style.ERROR(
                "  FAIL - local_settings.py not found or cannot be imported!"
            ))
        except Exception as exc:
            self.stdout.write(self.style.ERROR(
                f"  FAIL - Error reading local_settings.py: {exc}"
            ))

        # 2. Check Django settings
        self.stdout.write("\n[2] Checking Django settings.GEMINI_API_KEY ...")
        from django.conf import settings
        key = getattr(settings, "GEMINI_API_KEY", "")
        if key and len(key) > 10:
            self.stdout.write(self.style.SUCCESS(
                f"  OK - settings.GEMINI_API_KEY = {key[:8]}...{key[-4:]} (len={len(key)})"
            ))
        else:
            self.stdout.write(self.style.ERROR(
                f"  FAIL - settings.GEMINI_API_KEY is empty or too short: '{key}'"
            ))

        # 3. Check env var
        self.stdout.write("\n[3] Checking os.environ GEMINI_API_KEY ...")
        env_key = os.environ.get("GEMINI_API_KEY", "")
        if env_key and len(env_key) > 10:
            self.stdout.write(self.style.SUCCESS(
                f"  OK - env GEMINI_API_KEY = {env_key[:8]}...{env_key[-4:]} (len={len(env_key)})"
            ))
        else:
            self.stdout.write(self.style.WARNING(
                f"  WARN - env GEMINI_API_KEY is empty (not critical if local_settings.py works)"
            ))

        # 4. Check _api_available
        self.stdout.write("\n[4] Checking AssistantService._api_available() ...")
        try:
            from assistant.services import AssistantService
            available = AssistantService._api_available()
            if available:
                self.stdout.write(self.style.SUCCESS(
                    "  OK - _api_available() returns True"
                ))
            else:
                self.stdout.write(self.style.ERROR(
                    "  FAIL - _api_available() returns False (key is empty or placeholder)"
                ))
        except Exception as exc:
            self.stdout.write(self.style.ERROR(
                f"  FAIL - Error: {exc}"
            ))

        # 5. Test actual API call
        self.stdout.write("\n[5] Testing actual Gemini API call ...")
        if not key or len(key) < 10:
            self.stdout.write(self.style.ERROR(
                "  SKIP - No valid API key to test with"
            ))
        else:
            import json
            import urllib.request
            import urllib.error

            try:
                endpoint = (
                    "https://generativelanguage.googleapis.com/v1beta"
                    "/models/gemini-flash-latest:generateContent"
                )
                payload = {
                    "contents": [{"role": "user", "parts": [{"text": "Say hello in one word"}]}],
                    "generationConfig": {"maxOutputTokens": 10},
                }
                request = urllib.request.Request(
                    endpoint,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={
                        "Content-Type": "application/json",
                        "x-goog-api-key": key,
                    },
                    method="POST",
                )
                with urllib.request.urlopen(request, timeout=15) as response:
                    data = json.loads(response.read().decode("utf-8"))
                    text = ""
                    for c in data.get("candidates", []):
                        for p in (c.get("content") or {}).get("parts", []):
                            text += p.get("text", "")
                    if text.strip():
                        self.stdout.write(self.style.SUCCESS(
                            f"  OK - Gemini replied: '{text.strip()[:50]}'"
                        ))
                    else:
                        self.stdout.write(self.style.WARNING(
                            f"  WARN - Gemini returned empty text. Response: {json.dumps(data)[:200]}"
                        ))
            except urllib.error.HTTPError as exc:
                body = exc.read().decode("utf-8", "ignore")[:300]
                self.stdout.write(self.style.ERROR(
                    f"  FAIL - HTTP {exc.code}: {body}"
                ))
            except Exception as exc:
                self.stdout.write(self.style.ERROR(
                    f"  FAIL - {type(exc).__name__}: {exc}"
                ))

        # 6. Check model name
        self.stdout.write("\n[6] Checking model name ...")
        model = getattr(settings, "GEMINI_MODEL", "NOT_SET")
        self.stdout.write(f"  GEMINI_MODEL = {model}")

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("  DIAGNOSTIC COMPLETE")
        self.stdout.write("=" * 60)
