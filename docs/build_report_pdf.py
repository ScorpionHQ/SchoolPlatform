"""Build the Arabic project report PDF from docs/PROJECT_REPORT_AR.md.

Markdown is turned into a print-ready RTL HTML page which Chrome prints to
PDF, so Arabic shaping, bidi and table layout are handled by the browser
instead of being re-implemented. A second pass stamps the running header and
the page numbers, which CSS cannot express in Chrome.

Usage:

    python docs/build_report_pdf.py

Chrome or Edge is discovered automatically; set CHROME_PATH to override.
"""

import base64
import html
import io
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "docs" / "PROJECT_REPORT_AR.md"
HTML_TARGET = ROOT / "docs" / "PROJECT_REPORT_AR.html"
PDF_TARGET = ROOT / "docs" / "PROJECT_REPORT_AR.pdf"
FONT_DIR = ROOT / "static" / "fonts"

PRIMARY = "#6C5CE7"
PRIMARY_STRONG = "#4737BF"
PRIMARY_LIGHT = "#EFEDFC"
INK = "#2B2833"
MUTED = "#6B6779"
BORDER = "#ECE9E3"
SURFACE = "#F7F6F3"

CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
]


# --------------------------------------------------------------------------- #
# Markdown -> HTML
# --------------------------------------------------------------------------- #


def escape(text):
    return html.escape(text, quote=False)


def inline(text):
    """Inline Markdown on already escaped text."""

    text = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        lambda match: f'<a href="{match.group(2)}">{match.group(1)}</a>',
        text,
    )
    text = re.sub(
        r"&lt;(https?://[^&]+?)&gt;",
        lambda match: f'<a href="{match.group(1)}">{match.group(1)}</a>',
        text,
    )
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    return text


def render_table(rows):
    header, *body = rows
    out = ['<table><thead><tr>']

    for cell in header:
        out.append(f"<th>{inline(escape(cell))}</th>")

    out.append("</tr></thead><tbody>")

    for row in body:
        out.append("<tr>")

        for cell in row:
            out.append(f"<td>{inline(escape(cell))}</td>")

        out.append("</tr>")

    out.append("</tbody></table>")
    return "".join(out)


def build_html_body(lines):
    parts = []
    paragraph = []
    counter = {"list": None}

    def flush_paragraph():
        if paragraph:
            text = " ".join(paragraph).strip()
            paragraph.clear()

            if text:
                parts.append(f"<p>{inline(escape(text))}</p>")

    def close_list():
        if counter["list"]:
            parts.append(f"</{counter['list']}>")
            counter["list"] = None

    index = 0

    while index < len(lines):
        line = lines[index].rstrip()

        if line.startswith("```"):
            flush_paragraph()
            close_list()
            block = []
            index += 1

            while index < len(lines) and not lines[index].startswith("```"):
                block.append(lines[index])
                index += 1

            code = escape("\n".join(block))
            parts.append(f"<pre><code>{code}</code></pre>")
            index += 1
            continue

        if line.strip() in {"---", "***", "___"}:
            flush_paragraph()
            close_list()
            parts.append('<hr class="rule">')
            index += 1
            continue

        if line.startswith("|"):
            flush_paragraph()
            close_list()
            rows = []

            while index < len(lines) and lines[index].startswith("|"):
                cells = [
                    cell.strip() for cell in lines[index].strip().strip("|").split("|")
                ]

                if not all(re.fullmatch(r":?-{2,}:?", cell) for cell in cells if cell):
                    rows.append(cells)

                index += 1

            if rows:
                parts.append(render_table(rows))

            continue

        if line.startswith(">"):
            flush_paragraph()
            close_list()
            quoted = []

            while index < len(lines) and lines[index].startswith(">"):
                quoted.append(lines[index].lstrip("> ").rstrip())
                index += 1

            parts.append(
                f'<div class="callout">{inline(escape(" ".join(quoted)))}</div>'
            )
            continue

        heading = re.match(r"^(#{2,4})\s+(.*)$", line)

        if heading:
            flush_paragraph()
            close_list()
            level = len(heading.group(1))
            parts.append(
                f"<h{level}>{inline(escape(heading.group(2)))}</h{level}>"
            )
            index += 1
            continue

        item = re.match(r"^\s*([-*+]|\d+\.)\s+(.*)$", line)

        if item:
            flush_paragraph()
            wanted = "ul" if item.group(1) in {"-", "*", "+"} else "ol"

            if counter["list"] != wanted:
                close_list()
                parts.append(f"<{wanted}>")
                counter["list"] = wanted

            parts.append(f"<li>{inline(escape(item.group(2)))}</li>")
            index += 1
            continue

        if not line.strip():
            flush_paragraph()
            close_list()
            index += 1
            continue

        paragraph.append(line.strip())
        index += 1

    flush_paragraph()
    close_list()
    return "\n".join(parts)


# --------------------------------------------------------------------------- #
# Page shell
# --------------------------------------------------------------------------- #


def font_face(family, filename, weight):
    data = base64.b64encode((FONT_DIR / filename).read_bytes()).decode("ascii")
    return (
        "@font-face {"
        f'font-family: "{family}";'
        f"src: url(data:font/ttf;base64,{data}) format('truetype');"
        f"font-weight: {weight}; font-style: normal;"
        "}"
    )


CSS = """
@page { size: A4; margin: 17mm 15mm 19mm; }
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: "Amiri", "Segoe UI", sans-serif;
  font-size: 10.4pt;
  line-height: 1.78;
  color: #2B2833;
  direction: rtl;
  text-align: right;
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}
a { color: #4737BF; text-decoration: none; }
p { margin: 0 0 3.6mm; text-align: justify; text-justify: inter-word; }
h2 {
  font-size: 15.5pt; color: #4737BF; margin: 8mm 0 3mm;
  padding-bottom: 1.6mm; border-bottom: 0.5mm solid #EFEDFC;
  break-after: avoid;
}
h3 { font-size: 12pt; color: #4737BF; margin: 6mm 0 2mm; break-after: avoid; }
ul, ol { margin: 0 0 3.6mm; padding-right: 7mm; }
li { margin-bottom: 1.2mm; }
table {
  width: 100%; border-collapse: collapse; margin: 2.5mm 0 4.5mm;
  font-size: 9.2pt; line-height: 1.55; break-inside: auto;
}
thead { display: table-header-group; }
tr { break-inside: avoid; }
th {
  background: #6C5CE7; color: #fff; font-weight: 700;
  padding: 1.8mm 2mm; border: 0.25mm solid #6C5CE7; text-align: right;
}
td {
  padding: 1.6mm 2mm; border: 0.25mm solid #ECE9E3; vertical-align: top;
  word-break: break-word;
}
tbody tr:nth-child(even) td { background: #F7F6F3; }
code {
  font-family: "Cascadia Mono", Consolas, monospace; font-size: 8.6pt;
  background: #F7F6F3; padding: 0.3mm 1.2mm; border-radius: 1mm;
  direction: ltr; unicode-bidi: embed;
}
pre {
  background: #F7F6F3; border: 0.25mm solid #ECE9E3; border-radius: 1.5mm;
  padding: 3mm 3.5mm; margin: 2.5mm 0 4.5mm; break-inside: avoid;
  direction: ltr; text-align: left; line-height: 1.45;
  white-space: pre-wrap;
}
pre code { background: none; padding: 0; font-size: 8.2pt; }
.callout {
  background: #EFEDFC; border-right: 1mm solid #6C5CE7;
  padding: 2.6mm 3.5mm; margin: 3mm 0 4mm; border-radius: 1mm;
  color: #4A4560; font-size: 9.6pt;
}
hr.rule { border: none; border-top: 0.25mm solid #ECE9E3; margin: 5mm 0; }
strong { font-weight: 700; color: #2B2833; }

/* cover */
.cover {
  height: 246mm; position: relative;
  display: flex; flex-direction: column;
  break-after: page;
}
.cover-band {
  background: #2B2833; color: #fff;
  margin: -17mm -15mm 0; padding: 34mm 15mm 16mm;
  border-bottom: 2mm solid #6C5CE7;
  text-align: center;
}
.cover-band .product { font-size: 27pt; font-weight: 700; margin: 0; }
.cover-band .tagline { font-size: 14pt; color: #C9BFFB; margin: 6mm 0 0; }
.cover-band .kind { font-size: 11pt; color: #9C93C7; margin: 4mm 0 0; }
.cover-body { text-align: center; padding-top: 20mm; }
.cover-body h1 {
  font-size: 17pt; font-weight: 700; margin: 0 0 8mm; color: #2B2833;
}
.cover-meta { font-size: 10.5pt; color: #6B6779; line-height: 2; }
.cover-meta .url {
  font-family: "Cascadia Mono", Consolas, monospace; font-size: 10pt;
  color: #4737BF; direction: ltr; display: inline-block;
}
.stats { display: flex; gap: 4mm; justify-content: center; margin-top: 16mm; }
.stat {
  background: #EFEDFC; border-radius: 2.5mm; padding: 5mm 3mm;
  width: 36mm; text-align: center;
}
.stat b { display: block; font-size: 19pt; color: #4737BF; line-height: 1.2; }
.stat span { font-size: 8.4pt; color: #6B6779; }
.cover-foot {
  margin-top: auto; border-top: 0.25mm solid #ECE9E3; padding-top: 4mm;
  text-align: center; font-size: 8.8pt; color: #6B6779;
}
.cover-foot .brand { color: #6C5CE7; font-weight: 700; display: block; margin-top: 2mm; }
"""


def build_html(body):
    return f"""<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
<meta charset="utf-8">
<title>التقرير الشامل — SchoolPlatform</title>
<style>
{font_face("Amiri", "Amiri-Regular.ttf", 400)}
{font_face("Amiri", "Amiri-Bold.ttf", 700)}
{CSS}
</style>
</head>
<body>
<section class="cover">
  <div class="cover-band">
    <p class="product">منصة SchoolPlatform</p>
    <p class="tagline">نظام إدارة مدرسية سحابي متعدد المؤسسات</p>
    <p class="kind">تقرير فني وتجاري شامل</p>
  </div>
  <div class="cover-body">
    <h1>المميزات · طريقة العمل · الأهداف · خطة التسليم</h1>
    <div class="cover-meta">
      نسخة حيّة تعمل الآن على الإنترنت<br>
      <span class="url">https://schoolplatform-iq.vercel.app</span><br>
      الإصدار 1.0 — 4 نوفمبر 2026
    </div>
    <div class="stats">
      <div class="stat"><b>313</b><span>اختباراً ناجحاً</span></div>
      <div class="stat"><b>14</b><span>وحدة وظيفية</span></div>
      <div class="stat"><b>18</b><span>جدول بيانات</span></div>
      <div class="stat"><b>0</b><span>تكلفة تشغيل شهرية</span></div>
    </div>
  </div>
  <div class="cover-foot">
    وثيقة مُعدّة للعرض على الشركة المشترية — جميع الحقوق محفوظة
    <span class="brand">SchoolPlatform</span>
  </div>
</section>
{body}
</body>
</html>
"""


# --------------------------------------------------------------------------- #
# Chrome / PDF
# --------------------------------------------------------------------------- #


def find_chrome():
    import os

    override = os.environ.get("CHROME_PATH")

    if override and Path(override).exists():
        return override

    for candidate in CHROME_CANDIDATES:
        if Path(candidate).exists():
            return candidate

    for name in ("chrome", "google-chrome", "chromium", "msedge"):

        found = shutil.which(name)

        if found:
            return found

    return None


def print_pdf(chrome, source, target):
    with tempfile.TemporaryDirectory() as profile:
        result = subprocess.run(
            [
                chrome,
                "--headless=new",
                "--disable-gpu",
                "--no-sandbox",
                "--no-pdf-header-footer",
                f"--user-data-dir={profile}",
                f"--print-to-pdf={target}",
                source.resolve().as_uri(),
            ],
            capture_output=True,
            text=True,
            timeout=240,
        )

    if not Path(target).exists():
        sys.exit(f"error: Chrome did not produce a PDF\n{result.stderr[-800:]}")


STAMP_FOOTER = "SchoolPlatform — التقرير الشامل"
STAMP_VERSION = "الإصدار 1.0"


def shape(text):
    from bidi.algorithm import get_display

    from arabic_reshaper import arabic_reshaper

    return get_display(arabic_reshaper.reshape(text))


def stamp(source, target):
    """Running header, footer rule and page numbers, cover excluded."""

    pdfmetrics.registerFont(TTFont("Amiri", str(FONT_DIR / "Amiri-Regular.ttf")))

    reader = PdfReader(str(source))
    writer = PdfWriter()
    total = len(reader.pages)

    for index, page in enumerate(reader.pages):
        if index:
            buffer = io.BytesIO()
            overlay = canvas.Canvas(buffer, pagesize=A4)
            width, height = A4

            overlay.setStrokeColor(colors.HexColor(BORDER))
            overlay.setLineWidth(0.6)
            overlay.line(15 * mm, 13.5 * mm, width - 15 * mm, 13.5 * mm)
            overlay.line(15 * mm, height - 11 * mm, width - 15 * mm, height - 11 * mm)

            overlay.setFillColor(colors.HexColor(MUTED))
            overlay.setFont("Amiri", 8)
            overlay.drawRightString(width - 15 * mm, height - 9.6 * mm, shape(STAMP_FOOTER))
            overlay.drawString(15 * mm, height - 9.6 * mm, shape(STAMP_VERSION))
            overlay.drawCentredString(width / 2, 9 * mm, f"{index + 1} / {total}")

            overlay.save()
            buffer.seek(0)
            page.merge_page(PdfReader(buffer).pages[0])

        writer.add_page(page)

    with open(target, "wb") as handle:
        writer.write(handle)


def main():
    if not SOURCE.exists():
        sys.exit(f"error: {SOURCE} is missing")

    chrome = find_chrome()

    if not chrome:
        sys.exit("error: Chrome or Edge is required to print the PDF")

    lines = SOURCE.read_text(encoding="utf-8").splitlines()

    # The document title and its metadata table are replaced by the cover.
    start = 0

    while start < len(lines) and not lines[start].startswith("## "):
        start += 1

    HTML_TARGET.write_text(build_html(build_html_body(lines[start:])), encoding="utf-8")

    with tempfile.TemporaryDirectory() as folder:
        draft = Path(folder) / "report.pdf"
        print_pdf(chrome, HTML_TARGET, draft)
        stamp(draft, PDF_TARGET)

    print(f"written {PDF_TARGET} ({PDF_TARGET.stat().st_size / 1024:.0f} KB)")
    print(f"written {HTML_TARGET}")


if __name__ == "__main__":
    main()
