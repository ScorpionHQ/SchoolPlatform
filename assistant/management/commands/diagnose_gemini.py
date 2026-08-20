import json
import os
import urllib.error
import urllib.request

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Diagnose Gemini API connectivity on the server"

    def _api_call(self, key, model, payload, timeout=20):
        endpoint = (
            f"https://generativelanguage.googleapis.com/v1beta"
            f"/models/{model}:generateContent"
        )
        request = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": key,
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))

    def _extract_text(self, data):
        for c in data.get("candidates", []):
            parts = (c.get("content") or {}).get("parts") or []
            text = "".join(p.get("text", "") for p in parts).strip()
            if text:
                return text
        return None

    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write("  GEMINI API DIAGNOSTIC v2")
        self.stdout.write("=" * 60)

        # 1. Check local_settings.py
        self.stdout.write("\n[1] local_settings.py ...")
        try:
            from config.settings import local_settings
            key = getattr(local_settings, "GEMINI_API_KEY", "NOT_FOUND")
            if key and key != "CHANGE_ME_ON_SERVER":
                self.stdout.write(self.style.SUCCESS(
                    f"  OK - key = {key[:8]}...{key[-4:]} (len={len(key)})"
                ))
            else:
                self.stdout.write(self.style.ERROR(
                    f"  FAIL - placeholder or empty: '{key}'"
                ))
                return
        except ImportError:
            self.stdout.write(self.style.ERROR(
                "  FAIL - file not found or cannot import!"
            ))
            return
        except Exception as exc:
            self.stdout.write(self.style.ERROR(f"  FAIL - {exc}"))
            return

        # 2. Check Django settings
        self.stdout.write("\n[2] Django settings.GEMINI_API_KEY ...")
        from django.conf import settings
        key = getattr(settings, "GEMINI_API_KEY", "")
        if key and len(key) > 10:
            self.stdout.write(self.style.SUCCESS(
                f"  OK - key = {key[:8]}...{key[-4:]} (len={len(key)})"
            ))
        else:
            self.stdout.write(self.style.ERROR(
                f"  FAIL - empty or too short: '{key}'"
            ))
            return

        model = getattr(settings, "GEMINI_MODEL", "gemini-flash-latest")
        self.stdout.write(f"  Model = {model}")

        # 3. _api_available
        self.stdout.write("\n[3] _api_available() ...")
        try:
            from assistant.services import AssistantService
            if AssistantService._api_available():
                self.stdout.write(self.style.SUCCESS("  OK - True"))
            else:
                self.stdout.write(self.style.ERROR("  FAIL - False"))
                return
        except Exception as exc:
            self.stdout.write(self.style.ERROR(f"  FAIL - {exc}"))
            return

        # 4. Simple call WITHOUT search, high token budget
        self.stdout.write(f"\n[4] Simple call ({model}, no search, 256 tokens) ...")
        payload_simple = {
            "contents": [{"role": "user", "parts": [{"text": "قل مرحبا بword واحد فقط"}]}],
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 256,
            },
        }
        try:
            data = self._api_call(key, model, payload_simple)
            text = self._extract_text(data)
            feedback = data.get("promptFeedback") or {}
            block = feedback.get("blockReason")
            usage = data.get("usageMetadata") or {}
            candidates = data.get("candidates") or []
            content_raw = (candidates[0].get("content") or {}) if candidates else {}

            self.stdout.write(f"  promptFeedback = {json.dumps(feedback)}")
            self.stdout.write(f"  usage = {json.dumps(usage)}")
            self.stdout.write(f"  content raw = {json.dumps(content_raw)[:200]}")

            if block:
                self.stdout.write(self.style.ERROR(
                    f"  BLOCKED by safety: {block}"
                ))
            elif text:
                self.stdout.write(self.style.SUCCESS(
                    f"  OK - replied: '{text[:60]}'"
                ))
            else:
                self.stdout.write(self.style.ERROR(
                    f"  FAIL - empty text, full response: {json.dumps(data)[:400]}"
                ))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", "ignore")[:300]
            self.stdout.write(self.style.ERROR(f"  FAIL - HTTP {exc.code}: {body}"))
        except Exception as exc:
            self.stdout.write(self.style.ERROR(f"  FAIL - {type(exc).__name__}: {exc}"))

        # 5. Call WITH google_search tool (like the real assistant)
        self.stdout.write(f"\n[5] Call WITH google_search tool ({model}, 256 tokens) ...")
        payload_search = {
            "contents": [{"role": "user", "parts": [{"text": "قل مرحبا بword واحد فقط"}]}],
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 256,
            },
            "tools": [{"google_search": {}}],
        }
        try:
            data = self._api_call(key, model, payload_search)
            text = self._extract_text(data)
            feedback = data.get("promptFeedback") or {}
            block = feedback.get("blockReason")
            usage = data.get("usageMetadata") or {}
            candidates = data.get("candidates") or []
            content_raw = (candidates[0].get("content") or {}) if candidates else {}

            self.stdout.write(f"  promptFeedback = {json.dumps(feedback)}")
            self.stdout.write(f"  usage = {json.dumps(usage)}")
            self.stdout.write(f"  content raw = {json.dumps(content_raw)[:200]}")

            if block:
                self.stdout.write(self.style.ERROR(
                    f"  BLOCKED by safety: {block}"
                ))
            elif text:
                self.stdout.write(self.style.SUCCESS(
                    f"  OK - replied: '{text[:60]}'"
                ))
            else:
                self.stdout.write(self.style.ERROR(
                    f"  FAIL - empty text, full response: {json.dumps(data)[:400]}"
                ))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", "ignore")[:300]
            self.stdout.write(self.style.ERROR(f"  FAIL - HTTP {exc.code}: {body}"))
        except Exception as exc:
            self.stdout.write(self.style.ERROR(f"  FAIL - {type(exc).__name__}: {exc}"))

        # 6. Test with gemini-2.5-flash as fallback
        if model != "gemini-2.5-flash":
            self.stdout.write(f"\n[6] Fallback test (gemini-2.5-flash, no search, 256 tokens) ...")
            payload_fb = {
                "contents": [{"role": "user", "parts": [{"text": "قل مرحبا بword واحد فقط"}]}],
                "generationConfig": {
                    "temperature": 0.3,
                    "maxOutputTokens": 256,
                },
            }
            try:
                data = self._api_call(key, "gemini-2.5-flash", payload_fb)
                text = self._extract_text(data)
                feedback = data.get("promptFeedback") or {}
                block = feedback.get("blockReason")

                if block:
                    self.stdout.write(self.style.ERROR(
                        f"  BLOCKED by safety: {block}"
                    ))
                elif text:
                    self.stdout.write(self.style.SUCCESS(
                        f"  OK - replied: '{text[:60]}'"
                    ))
                else:
                    self.stdout.write(self.style.ERROR(
                        f"  FAIL - empty, response: {json.dumps(data)[:400]}"
                    ))
            except urllib.error.HTTPError as exc:
                body = exc.read().decode("utf-8", "ignore")[:300]
                self.stdout.write(self.style.ERROR(f"  FAIL - HTTP {exc.code}: {body}"))
            except Exception as exc:
                self.stdout.write(self.style.ERROR(f"  FAIL - {type(exc).__name__}: {exc}"))
        else:
            self.stdout.write("\n[6] Skipping fallback (already using gemini-2.5-flash)")

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("  DIAGNOSTIC COMPLETE")
        self.stdout.write("=" * 60)
