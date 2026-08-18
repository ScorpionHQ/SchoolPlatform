import io

from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext as _

from arabic_reshaper import arabic_reshaper
from bidi.algorithm import get_display
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
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


_REGISTERED_FONTS = {}


def _register_font(family, path):
    key = (family, path)

    if key not in _REGISTERED_FONTS:
        pdfmetrics.registerFont(TTFont(family, path))
        _REGISTERED_FONTS[key] = True

    return family


def _fonts():
    font_dir = settings.BASE_DIR / "static" / "fonts"

    regular = _register_font(
        "Amiri",
        str(font_dir / "Amiri-Regular.ttf"),
    )

    bold = _register_font(
        "Amiri-Bold",
        str(font_dir / "Amiri-Bold.ttf"),
    )

    return regular, bold


def _shape(text):
    return get_display(arabic_reshaper.reshape(str(text)))


def _money(amount):
    return "{:,.2f} {}".format(amount, _("IQD"))


def build_fee_prices_pdf(institution, fee_types):
    buffer = io.BytesIO()

    regular, bold = _fonts()

    title_style = ParagraphStyle(
        "Title",
        fontName=bold,
        fontSize=18,
        leading=26,
        alignment=TA_CENTER,
    )

    sub_style = ParagraphStyle(
        "Subtitle",
        fontName=regular,
        fontSize=11,
        leading=16,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#555555"),
    )

    header_style = ParagraphStyle(
        "Header",
        fontName=bold,
        fontSize=11,
        leading=16,
        alignment=TA_RIGHT,
        textColor=colors.white,
    )

    cell_style = ParagraphStyle(
        "Cell",
        fontName=regular,
        fontSize=10,
        leading=15,
        alignment=TA_RIGHT,
    )

    total_style = ParagraphStyle(
        "Total",
        fontName=bold,
        fontSize=11,
        leading=16,
        alignment=TA_RIGHT,
    )

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        title=_("Fee Price List - {institution}").format(
            institution=institution.name,
        ),
        author=institution.name,
    )

    today = timezone.localdate()

    story = [
        Paragraph(
            _shape(_("Fee Price List")),
            title_style,
        ),
        Paragraph(
            _shape(institution.name),
            sub_style,
        ),
        Paragraph(
            _shape(
                "{} {} - {} {}".format(
                    _("Generated on"),
                    today.isoformat(),
                    _("Academic year"),
                    today.year,
                )
            ),
            sub_style,
        ),
        Spacer(1, 10 * mm),
    ]

    header = [
        _("Fee name"),
        _("Amount"),
        _("Required"),
        _("Status"),
    ]

    rows = [
        [
            Paragraph(_shape(name), header_style)
            for name in header
        ]
    ]

    required_total = 0

    for fee_type in fee_types:

        if fee_type.is_required:
            required_total += fee_type.amount

        status = _("Active") if fee_type.is_active else _("Inactive")
        required = _("Required") if fee_type.is_required else _("Optional")

        rows.append(
            [
                Paragraph(_shape(fee_type.name), cell_style),
                Paragraph(_money(fee_type.amount), cell_style),
                Paragraph(_shape(required), cell_style),
                Paragraph(_shape(status), cell_style),
            ]
        )

    if fee_types:

        rows.append(
            [
                Paragraph(_shape(_("Total (required)")), total_style),
                Paragraph(_money(required_total), total_style),
                Paragraph("", total_style),
                Paragraph("", total_style),
            ]
        )

    table = Table(
        rows,
        colWidths=[
            78 * mm,
            50 * mm,
            28 * mm,
            24 * mm,
        ],
        repeatRows=1,
    )

    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1b6ca8")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ROWBACKGROUNDS", (0, 1), (-1, -2), [
                    colors.white,
                    colors.HexColor("#f2f6fa"),
                ]),
                ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#e8eef4")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#c9d4de")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    story.append(table)

    if not fee_types:

        story.append(
            Spacer(1, 8 * mm),
        )

        story.append(
            Paragraph(
                _shape(_("No active fee types to display.")),
                sub_style,
            )
        )

    doc.build(story)

    buffer.seek(0)

    return buffer
