"""Deploy the project to Vercel with a token, without a Git integration.

Git integration is the normal way to deploy, but it needs a GitHub login
connection on the Vercel account. This script does the same job with the REST
API, so a Git push can deploy from a GitHub Actions workflow.

Required environment variables:

    VERCEL_TOKEN        personal token from https://vercel.com/account/tokens

Optional:

    VERCEL_PROJECT_ID   prj_... (defaults to the SchoolPlatform project)
    VERCEL_TEAM_ID      team_... when the project belongs to a team
    VERCEL_PROJECT_NAME project name, used as the deployment name
    VERCEL_WORKERS      parallel uploads, default 8

Usage:

    python deploy/vercel_deploy.py
"""

import concurrent.futures
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

API = "https://api.vercel.com"

ROOT = Path(__file__).resolve().parent.parent

PROJECT_ID = os.environ.get(
    "VERCEL_PROJECT_ID",
    "prj_KUKYs6FB4vYas7Y8VbQYw5OvYnLH",
)

TEAM_ID = os.environ.get("VERCEL_TEAM_ID", "team_KYTFCN2nSc7JVVVc1JLltrdD")

PROJECT_NAME = os.environ.get("VERCEL_PROJECT_NAME", "schoolplatform")

WORKERS = int(os.environ.get("VERCEL_WORKERS", "8"))

SKIP_DIRS = {
    ".git",
    ".github",
    ".vercel",
    "staticfiles",
    "media",
    "node_modules",
    "venv",
    ".venv",
    "env",
    "__pycache__",
    ".idea",
    ".vscode",
}

SKIP_FILES = {
    "cookies.txt",
    "db.sqlite3",
    ".env",
    ".env.local",
    ".env.production",
}

SKIP_SUFFIXES = (".pyc", ".log")

POLL_SECONDS = 10

POLL_LIMIT = 90


def token():

    value = os.environ.get("VERCEL_TOKEN", "").strip()

    if not value:
        sys.exit("error: VERCEL_TOKEN is not set")

    return value


def query(extra=""):

    parts = []

    if TEAM_ID:
        parts.append(f"teamId={TEAM_ID}")

    if extra:
        parts.append(extra)

    return ("?" + "&".join(parts)) if parts else ""


def call(method, path, payload=None, extra="", raw=None, headers=None):

    data = None

    if raw is not None:
        data = raw

    elif payload is not None:
        data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(API + path + query(extra), data=data, method=method)

    request.add_header("Authorization", f"Bearer {token()}")

    request.add_header("Accept", "application/json")

    if raw is not None:
        request.add_header("Content-Type", "application/octet-stream")
    elif payload is not None:
        request.add_header("Content-Type", "application/json")

    for key, value in (headers or {}).items():
        request.add_header(key, value)

    try:

        with urllib.request.urlopen(request, timeout=90) as response:

            body = response.read()

            return json.loads(body) if body else {}

    except urllib.error.HTTPError as error:

        detail = error.read().decode("utf-8", "replace")[:500]

        raise RuntimeError(f"{method} {path} -> {error.code}: {detail}") from error

    except urllib.error.URLError as error:

        raise RuntimeError(f"{method} {path} -> network error: {error.reason}") from error

    except OSError as error:

        raise RuntimeError(f"{method} {path} -> socket error: {error}") from error


def collect_files():
    """Every file that belongs in the deployment, with its content."""

    files = []

    for path in sorted(ROOT.rglob("*")):

        if not path.is_file():
            continue

        relative = path.relative_to(ROOT)

        if any(part in SKIP_DIRS for part in relative.parts):
            continue

        if path.name in SKIP_FILES:
            continue

        if path.name.startswith(".env."):
            continue

        if path.name.endswith(SKIP_SUFFIXES):
            continue

        files.append((relative.as_posix(), path.read_bytes()))

    return files


def upload(item):
    """Send one file; the digest makes repeat uploads idempotent."""

    relative, content, digest = item

    for attempt in range(1, 4):

        try:

            call(
                "POST",
                "/v2/files",
                raw=content,
                headers={"x-vercel-digest": digest},
            )

            return relative, digest

        except Exception as error:

            # 409 means the server already has this content.
            if "-> 409" in str(error):
                return relative, digest

            if attempt == 3:
                raise RuntimeError(f"{relative}: {error}") from error

            time.sleep(2 * attempt)

    return relative, digest


def main():

    files = collect_files()

    total = sum(len(content) for _, content in files)

    print(f"files={len(files)} totalMB={total / (1024 * 1024):.1f}")

    unique = {}

    for relative, content in files:

        digest = hashlib.sha1(content).hexdigest()

        unique.setdefault(digest, (relative, content, digest))

    print(f"unique={len(unique)} workers={WORKERS}")

    done = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as pool:

        for relative, digest in pool.map(upload, unique.values()):

            done += 1

            if done % 50 == 0:
                print(f"uploaded={done}/{len(unique)}")

    print(f"uploaded={done}")

    manifest = [
        {"file": relative, "sha": hashlib.sha1(content).hexdigest(), "size": len(content)}
        for relative, content in files
    ]

    deployment = call(
        "POST",
        "/v13/deployments",
        {
            "name": PROJECT_NAME,
            "project": PROJECT_ID,
            "target": "production",
            "files": manifest,
            "projectSettings": {"framework": "django"},
        },
        extra="forceNew=1",
    )

    deployment_id = deployment["id"]

    print(f"deployment={deployment_id}", flush=True)

    for _ in range(POLL_LIMIT):

        time.sleep(POLL_SECONDS)

        state = call("GET", f"/v13/deployments/{deployment_id}")

        print(f"state={state.get('readyState')}", flush=True)

        if state.get("readyState") == "READY":

            print(f"deployment_url=https://{state.get('url')}")

            print("DEPLOY_OK")

            return 0

        if state.get("readyState") in {"ERROR", "CANCELED"}:

            print(f"BUILD_FAILED {state.get('errorMessage')}")

            return 3

    print("TIMEOUT")

    return 4


if __name__ == "__main__":
    sys.exit(main())
