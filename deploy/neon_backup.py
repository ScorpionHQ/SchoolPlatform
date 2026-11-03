"""Snapshot the Neon database by creating a copy-on-write branch.

A Neon branch is an instant, cheap copy of the data at a point in time. The
free plan keeps them without extra compute, and restoring is a matter of
pointing ``DATABASE_URL`` at the backup branch (or copying it back).

Usage:

    set NEON_API_KEY=napi_...
    set NEON_PROJECT_ID=frosty-dawn-46163110
    python deploy/neon_backup.py

Optional:

    NEON_BACKUP_KEEP   number of snapshots to keep (default 5)
    NEON_BACKUP_PREFIX prefix used in branch names (default backup-)
"""

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

API = "https://console.neon.tech/api/v2"

PREFIX = os.environ.get("NEON_BACKUP_PREFIX", "backup-")

KEEP = int(os.environ.get("NEON_BACKUP_KEEP", "5"))


def fail(message):
    print(f"error: {message}", file=sys.stderr)
    sys.exit(1)


def call(method, path, payload=None):
    token = os.environ.get("NEON_API_KEY", "").strip()

    if not token:
        fail("NEON_API_KEY is not set")

    data = json.dumps(payload).encode("utf-8") if payload is not None else None

    request = urllib.request.Request(
        API + path,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
    )

    try:

        with urllib.request.urlopen(request, timeout=60) as response:

            body = response.read()

            return json.loads(body) if body else {}

    except urllib.error.HTTPError as error:

        detail = error.read().decode("utf-8", "replace")[:400]

        fail(f"{method} {path} returned {error.code}: {detail}")

    except urllib.error.URLError as error:

        fail(f"{method} {path} failed: {error.reason}")


def main():

    project = os.environ.get("NEON_PROJECT_ID", "").strip()

    if not project:
        fail("NEON_PROJECT_ID is not set")

    branches = call("GET", f"/projects/{project}/branches").get("branches", [])

    primary = next((b for b in branches if b.get("primary")), None)

    if not primary:
        fail("the project has no primary branch")

    name = PREFIX + datetime.now(timezone.utc).strftime("%Y%m%d-%H%M")

    created = call(
        "POST",
        f"/projects/{project}/branches",
        {"branch": {"name": name, "parent_id": primary["id"]}},
    ).get("branch", {})

    print(f"created {name} ({created.get('id', 'unknown')})")

    backups = sorted(
        (b for b in branches if str(b.get("name", "")).startswith(PREFIX)),
        key=lambda b: b.get("created_at", ""),
        reverse=True,
    )

    for old in backups[KEEP:]:

        call("DELETE", f"/projects/{project}/branches/{old['id']}")

        print(f"pruned {old['name']}")

    print(f"kept {min(len(backups) + 1, KEEP)} snapshot(s)")


if __name__ == "__main__":
    main()
