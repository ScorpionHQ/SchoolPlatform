# -*- coding: utf-8 -*-
"""Merge Arabic translations into django.po and compile django.mo."""
import io
import os
import sys

import polib

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "tools"))
from ar_translations import AR  # noqa: E402

PO_PATH = os.path.join(BASE, "locale", "ar", "LC_MESSAGES", "django.po")
MO_PATH = os.path.join(BASE, "locale", "ar", "LC_MESSAGES", "django.mo")

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

po = polib.pofile(PO_PATH)
by_id = {e.msgid: e for e in po}

added = updated = 0
for msgid, msgstr in AR.items():
    if msgid in by_id:
        e = by_id[msgid]
        if not e.translated() or e.msgstr != msgstr:
            e.msgstr = msgstr
            updated += 1
    else:
        po.append(polib.POEntry(msgid=msgid, msgstr=msgstr))
        added += 1

# sanity: placeholders preserved
bad = []
for msgid, msgstr in AR.items():
    for ph in ["%(", "{"]:
        if ph in msgid and ph not in msgstr:
            bad.append(msgid)
if bad:
    print("PLACEHOLDER ISSUES:")
    for b in bad:
        print("  ", b)

po.save(PO_PATH)
po.save_as_mofile(MO_PATH)
print(f"added={added} updated={updated}")
print(f"total entries={len(po)}")
missing = [e.msgid for e in po if not e.translated()]
print("untranslated remaining:", len(missing))
for m in missing[:50]:
    print("   UNTRANSLATED:", m)
print("OK")
