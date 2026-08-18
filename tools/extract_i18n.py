# -*- coding: utf-8 -*-
"""Extract all translatable msgids from templates + python, merge with existing
ar/django.po, and report missing translations."""
import glob
import io
import os
import re
import sys

import polib

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PO_PATH = os.path.join(BASE, "locale", "ar", "LC_MESSAGES", "django.po")


def norm_blocktext(s):
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def extract_templates():
    msgs = {}
    for p in glob.glob(os.path.join(BASE, "templates", "**", "*.html"), recursive=True):
        data = io.open(p, encoding="utf-8").read()
        for m in re.finditer(r"{%\s*trans\s+[\"']([^\"']+)[\"']\s*%}", data):
            msgs.setdefault(m.group(1), set()).add(os.path.basename(p))
        for m in re.finditer(
            r"{%\s*blocktrans\b(?:[^%]*?)\s*%}(.*?){%\s*endblocktrans\s*%}",
            data,
            re.S,
        ):
            t = norm_blocktext(m.group(1))
            if t:
                msgs.setdefault(t, set()).add(os.path.basename(p))
    return msgs


def extract_python():
    msgs = {}
    files = [
        p
        for p in glob.glob(os.path.join(BASE, "**", "*.py"), recursive=True)
        if "venv" not in p
        and "migrations" not in p
        and "tools" not in p
        and "staticfiles" not in p
    ]
    for p in files:
        data = io.open(p, encoding="utf-8").read()
        # concatenated adjacent strings inside _(...)
        for m in re.finditer(r"\b_\(\s*((?:[\"'][^\"']*[\"']\s*)+)\)", data):
            parts = re.findall(r"[\"']([^\"']*)[\"']", m.group(1))
            if parts:
                t = "".join(parts)
                if t.strip():
                    msgs.setdefault(t, set()).add(os.path.basename(p))
        for m in re.finditer(r"\bngettext\([\"']([^\"']+)[\"']\s*,\s*[\"']([^\"']+)[\"']", data):
            for t in (m.group(1), m.group(2)):
                if t.strip():
                    msgs.setdefault(t, set()).add(os.path.basename(p))
    return msgs


def main():
    t = extract_templates()
    py = extract_python()
    all_src = {}
    for k, v in t.items():
        all_src.setdefault(k, set()).update(v)
    for k, v in py.items():
        all_src.setdefault(k, set()).update(v)

    po = polib.pofile(PO_PATH)
    have = {e.msgid: e for e in po if e.translated()}

    missing = []
    for k in sorted(all_src):
        if k not in have:
            missing.append(k)

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    print("TOTAL UNIQUE MSGIDS:", len(all_src))
    print("IN PO (translated):", len(have))
    print("MISSING:", len(missing))
    print("=" * 60)
    for k in missing:
        print("MISSING:", k)
    print("=" * 60)
    # also dump all msgids to file for the translator
    out = os.path.join(BASE, "tools", "msgids.txt")
    with io.open(out, "w", encoding="utf-8") as fh:
        for k in sorted(all_src):
            fh.write(k + "\n")
    print("wrote", out)


if __name__ == "__main__":
    main()
