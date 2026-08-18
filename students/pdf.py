"""PDF generation for student login credentials.

Generates a downloadable PDF listing each created student's name,
login code and temporary password, with full Arabic (RTL) support
using the Amiri font bundled with the project.
"""

import logging
from datetime import datetime

from django.conf import settings
from django.utils.translation import gettext as _

logger = logging.getLogger(__name__)

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import (
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )
except ImportError:  # pragma: no cover
    arabic_reshaper = None
    get_display = None
    pdfmetrics = None
    TTFont = None
    SimpleDocTemplate = None
    Paragraph = None
    Table = None
    TableStyle = None
    Spacer = None
    colors = None
    A4 = None
    mm = None
    ParagraphStyle = None
    getSampleStyleSheet = None
    TA_CENTER = "center"

BRAND = "#4F46E5"
BRAND_DARK = "#3730A3"
INK = "#111827"
MUTED = "#6B7280"
LINE = "#E5E7EB"
BG = "#F8FAFC"

_PRIMARY_FONT = "Helvetica"
_BOLD_FONT = "Helvetica-Bold"


def _fonts_dir():
    for base in (settings.BASE_DIR, settings.BASE_DIR / "staticfiles"):
        candidate = base / "static" / "fonts"
        if candidate.exists():
            return candidate
        candidate = base / "fonts"
        if candidate.exists():
            return candidate
    candidate = settings.BASE_DIR / "static" / "fonts"
    if candidate.exists():
        return candidate
    return None


def _register_fonts():
    """Register the bundled Amiri font. Falls back to Helvetica."""
    global _PRIMARY_FONT, _BOLD_FONT

    if TTFont is None:
        return

    fonts_dir = _fonts_dir()

    if fonts_dir is None:
        return

    regular = fonts_dir / "Amiri-Regular.ttf"
    bold = fonts_dir / "Amiri-Bold.ttf"

    try:
        pdfmetrics.registerFont(TTFont("Amiri", str(regular)))
        if bold.exists():
            pdfmetrics.registerFont(TTFont("Amiri-Bold", str(bold)))
        else:
            pdfmetrics.registerFont(TTFont("Amiri-Bold", str(regular)))
        _PRIMARY_FONT = "Amiri"
        _BOLD_FONT = "Amiri-Bold"
    except Exception as exc:  # pragma: no cover
        logger.warning("Could not register Amiri font: %s", exc)


def _has_arabic(text):
    return any("\u0600" <= char <= "\u06FF" for char in text)


def _arabic(text):
    """Shape and reorder text for correct Arabic rendering."""
    if not text:
        return text
    text = str(text)
    if not _has_arabic(text):
        return text
    if arabic_reshaper is None or get_display is None:
        return text
    reshaped = arabic_reshaper.reshape(text)
    return get_display(reshaped)


def _footer(canvas, document):
    canvas.saveState()

    width, height = A4

    canvas.setStrokeColor(LINE)
    canvas.setLineWidth(0.5)
    canvas.line(20 * mm, 18 * mm, width - 20 * mm, 18 * mm)

    canvas.setFont(_PRIMARY_FONT, 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(
        20 * mm,
        14 * mm,
        _arabic("SchoolPlatform"),
    )
    canvas.drawRightString(
        width - 20 * mm,
        14 * mm,
        f"{document.page}",
    )

    canvas.restoreState()


def _header(canvas, document):
    canvas.saveState()

    width, height = A4

    canvas.setFillColor(BRAND)
    canvas.rect(0, height - 30 * mm, width, 30 * mm, stroke=0, fill=1)

    canvas.setFillColor(colors.white)
    canvas.setFont(_BOLD_FONT, 16)
    canvas.drawString(
        20 * mm,
        height - 17 * mm,
        _arabic(_("Student Login Credentials")),
    )

    canvas.setFont(_PRIMARY_FONT, 9)
    canvas.setFillColor(colors.HexColor("#E0E7FF"))
    canvas.drawRightString(
        width - 20 * mm,
        height - 17 * mm,
        "SchoolPlatform",
    )

    canvas.restoreState()


def _on_page(canvas, document):
    _header(canvas, document)
    _footer(canvas, document)


def build_credentials_pdf(
    stream,
    *,
    institution,
    credentials,
    generated_at=None,
):
    """Write a PDF with student login credentials into ``stream``.

    Arguments:
        stream: binary file-like object.
        institution: display name of the school/institution.
        credentials: list of dicts with keys {name, code, password}.
        generated_at: datetime object (defaults to now).
    """
    if SimpleDocTemplate is None:  # pragma: no cover
        raise RuntimeError("reportlab is not installed on this server.")

    _register_fonts()

    now = generated_at or datetime.now()

    credentials = credentials or []

    styles = getSampleStyleSheet()

    h1 = ParagraphStyle(
        "CredentialsTitle",
        parent=styles["Title"],
        fontName=_BOLD_FONT,
        fontSize=20,
        leading=26,
        textColor=INK,
        spaceAfter=2 * mm,
    )
    sub = ParagraphStyle(
        "CredentialsSub",
        parent=styles["Normal"],
        fontName=_PRIMARY_FONT,
        fontSize=10,
        leading=15,
        textColor=MUTED,
        spaceAfter=6 * mm,
    )
    cell = ParagraphStyle(
        "CredentialsCell",
        parent=styles["Normal"],
        fontName=_PRIMARY_FONT,
        fontSize=9.5,
        leading=13,
        textColor=INK,
        alignment=TA_CENTER,
    )
    cell_head = ParagraphStyle(
        "CredentialsCellHead",
        parent=cell,
        fontName=_BOLD_FONT,
        textColor=colors.white,
    )
    note = ParagraphStyle(
        "CredentialsNote",
        parent=styles["Normal"],
        fontName=_PRIMARY_FONT,
        fontSize=9.5,
        leading=15,
        textColor=BRAND_DARK,
        spaceBefore=6 * mm,
    )

    def p(text, style):
        return Paragraph(_arabic(str(text)), style)

    document = SimpleDocTemplate(
        stream,
        pagesize=A4,
        topMargin=40 * mm,
        bottomMargin=25 * mm,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        title=str(_("Student Login Credentials")),
        author="SchoolPlatform",
    )

    elements = []

    elements.append(p(_("Student Login Credentials"), h1))

    meta_lines = " | ".join(
        part for part in (
            _arabic(institution),
            now.strftime("%Y-%m-%d %H:%M"),
            _("A total of {count} students").format(
                count=len(credentials),
            ),
        ) if part
    )
    elements.append(p(meta_lines, sub))

    table_data = [
        [
            p(_("No."), cell_head),
            p(_("Student Name"), cell_head),
            p(_("Login Code"), cell_head),
            p(_("Temporary Password"), cell_head),
        ]
    ]

    for index, item in enumerate(credentials, start=1):
        table_data.append(
            [
                p(index, cell),
                p(item.get("name", ""), cell),
                p(item.get("code", ""), cell),
                p(item.get("password", ""), cell),
            ]
        )

    table = Table(
        table_data,
        colWidths=[15 * mm, 80 * mm, 45 * mm, 50 * mm],
        repeatRows=1,
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), BRAND),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, LINE),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BG]),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    elements.append(table)

    elements.append(
        p(
            _(
                "Students must change their password on their "
                "first login."
            ),
            note,
        )
    )

    elements.append(Spacer(1, 6 * mm))
    elements.append(
        p(
            _(
                "This document was generated automatically by the "
                "SchoolPlatform."
            ),
            sub,
        )
    )

    document.build(elements, onFirstPage=_on_page, onLaterPages=_on_page)

    return document
