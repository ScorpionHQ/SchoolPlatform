"""Build the editable Word version of the project report.

The report itself lives in docs/PROJECT_REPORT_AR.md. This script renders it
as a styled, fully right-to-left .docx: cover page, table of contents field,
brand-coloured headings, banded tables, callouts and code blocks.

Usage:

    python docs/build_report_docx.py
"""

import re
import sys
from pathlib import Path

from docx import Document
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from docx.opc.constants import RELATIONSHIP_TYPE as RT

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "docs" / "PROJECT_REPORT_AR.md"
TARGET = ROOT / "docs" / "PROJECT_REPORT_AR.docx"

BODY_FONT = "Segoe UI"
CODE_FONT = "Consolas"

PRIMARY = "6C5CE7"
PRIMARY_STRONG = "4737BF"
PRIMARY_LIGHT = "EFEDFC"
INK = "2B2833"
MUTED = "6B6779"
BORDER = "ECE9E3"
SURFACE = "F7F6F3"

BODY_SIZE = 10.5
TABLE_SIZE = 9
CODE_SIZE = 8

CONTENT_WIDTH_CM = 17.2

PPR_BIDI_SUCCESSORS = (
    "w:adjustRightInd",
    "w:snapToGrid",
    "w:spacing",
    "w:ind",
    "w:contextualSpacing",
    "w:mirrorIndents",
    "w:suppressOverlap",
    "w:jc",
    "w:textDirection",
    "w:textAlignment",
    "w:textboxTightWrap",
    "w:outlineLvl",
    "w:divId",
    "w:cnfStyle",
    "w:rPr",
    "w:sectPr",
    "w:pPrChange",
)


# --------------------------------------------------------------------------- #
# Low level helpers
# --------------------------------------------------------------------------- #


def rgb(value):
    return RGBColor.from_string(value)


def set_bidi(paragraph, enabled=True):
    pPr = paragraph._p.get_or_add_pPr()
    existing = pPr.find(qn("w:bidi"))

    if existing is not None:
        pPr.remove(existing)

    bidi = OxmlElement("w:bidi")

    if not enabled:
        bidi.set(qn("w:val"), "0")

    pPr.insert_element_before(bidi, *PPR_BIDI_SUCCESSORS)


def decorate_run(run, size=None, bold=None, italic=None, color=None, font=None):
    run.font.name = font or BODY_FONT

    if size is not None:
        run.font.size = Pt(size)

    if bold is not None:
        run.bold = bold

    if italic is not None:
        run.italic = italic

    if color is not None:
        run.font.color.rgb = rgb(color)

    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))

    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.insert(0, rFonts)

    rFonts.set(qn("w:cs"), font or BODY_FONT)

    if size is not None:
        sz_cs = OxmlElement("w:szCs")
        sz_cs.set(qn("w:val"), str(int(round(size * 2))))
        rPr.insert_element_before(
            sz_cs,
            "w:highlight",
            "w:u",
            "w:effect",
            "w:bdr",
            "w:shd",
            "w:fitText",
            "w:vertAlign",
            "w:rtl",
            "w:cs",
            "w:em",
            "w:lang",
            "w:eastAsianLayout",
            "w:specVanish",
            "w:oMath",
        )
        size_cs = rPr.findall(qn("w:szCs"))

        for extra in size_cs[:-1]:
            rPr.remove(extra)

    rtl = OxmlElement("w:rtl")
    rPr.insert_element_before(
        rtl,
        "w:cs",
        "w:em",
        "w:lang",
        "w:eastAsianLayout",
        "w:specVanish",
        "w:oMath",
    )
    rPr.insert_element_before(
        OxmlElement("w:cs"),
        "w:em",
        "w:lang",
        "w:eastAsianLayout",
        "w:specVanish",
        "w:oMath",
    )

    for tag in ("w:szCs", "w:rtl", "w:cs"):
        found = rPr.findall(qn(tag))

        for extra in found[1:]:
            rPr.remove(extra)

    return run


def shade(element, fill):
    """Apply background colour to a paragraph, cell or table."""

    if element.tag == qn("w:tc"):
        container = element.get_or_add_tcPr()
        target = container
        successors = ("w:noWrap", "w:tcMar", "w:textDirection", "w:tcFitText", "w:vAlign", "w:hideMark")
    elif element.tag == qn("w:tr"):
        container = element.get_or_add_trPr()
        target = container
        successors = ("w:cantSplit", "w:trHeight", "w:tblHeader", "w:tblCellSpacing")
    else:
        container = element.get_or_add_pPr()
        target = container
        successors = (
            "w:tabs",
            "w:suppressAutoHyphens",
            "w:kinsoku",
            "w:wordWrap",
            "w:overflowPunct",
            "w:topLinePunct",
            "w:autoSpaceDE",
            "w:autoSpaceDN",
            "w:bidi",
            "w:adjustRightInd",
            "w:snapToGrid",
            "w:spacing",
            "w:ind",
            "w:contextualSpacing",
            "w:mirrorIndents",
            "w:suppressOverlap",
            "w:jc",
            "w:textDirection",
            "w:textAlignment",
            "w:textboxTightWrap",
            "w:outlineLvl",
            "w:divId",
            "w:cnfStyle",
            "w:rPr",
            "w:sectPr",
            "w:pPrChange",
        )

    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    target.insert_element_before(shd, *successors)


def borders(element, **edges):
    """edges: top=('single', 4, 'ECE9E3')"""

    if element.tag == qn("w:tbl"):
        container = element.tblPr
        wrapper = OxmlElement("w:tblBorders")
        successors = (
            "w:shd",
            "w:tblLayout",
            "w:tblCellMar",
            "w:tblLook",
            "w:tblCaption",
            "w:tblDescription",
            "w:tblPrChange",
        )
    elif element.tag == qn("w:p"):
        container = element.get_or_add_pPr()
        wrapper = OxmlElement("w:pBdr")
        successors = (
            "w:shd",
            "w:tabs",
            "w:suppressAutoHyphens",
            "w:kinsoku",
            "w:wordWrap",
            "w:overflowPunct",
            "w:topLinePunct",
            "w:autoSpaceDE",
            "w:autoSpaceDN",
            "w:bidi",
            "w:adjustRightInd",
            "w:snapToGrid",
            "w:spacing",
            "w:ind",
            "w:contextualSpacing",
            "w:mirrorIndents",
            "w:suppressOverlap",
            "w:jc",
            "w:textDirection",
            "w:textAlignment",
            "w:textboxTightWrap",
            "w:outlineLvl",
            "w:divId",
            "w:cnfStyle",
            "w:rPr",
            "w:sectPr",
            "w:pPrChange",
        )
    else:
        container = element.get_or_add_tcPr()
        wrapper = OxmlElement("w:tcBorders")
        successors = (
            "w:shd",
            "w:noWrap",
            "w:tcMar",
            "w:textDirection",
            "w:tcFitText",
            "w:vAlign",
            "w:hideMark",
        )

    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        value = edges.get(edge)

        if value is None:
            continue

        style, size, color = value
        item = OxmlElement(f"w:{edge}")
        item.set(qn("w:val"), style)
        item.set(qn("w:sz"), str(size))
        item.set(qn("w:space"), "0")
        item.set(qn("w:color"), color)
        wrapper.append(item)

    container.insert_element_before(wrapper, *successors)


def prepend(paragraph, text, size=None, bold=None, color=None, font=None):
    """Insert text at the start of a paragraph (headings keep their marker)."""

    run = paragraph.add_run(text)
    return decorate_run(run, size=size, bold=bold, color=color, font=font)


def paragraph(doc, text="", style=None, align=WD_ALIGN_PARAGRAPH.JUSTIFY, size=BODY_SIZE,
              bold=None, color=None, space_before=0, space_after=4,
              line_spacing=1.45, right_indent=None, first_line_indent=None,
              keep_with_next=False, bidi=True, font=None):
    para = doc.add_paragraph(style=style)

    if text:
        decorate_run(para.add_run(text), size=size, bold=bold, color=color, font=font)

    fmt = para.paragraph_format
    fmt.alignment = align
    fmt.space_before = Pt(space_before)
    fmt.space_after = Pt(space_after)
    fmt.line_spacing = line_spacing

    if right_indent is not None:
        fmt.right_indent = Cm(right_indent)

    if first_line_indent is not None:
        fmt.first_line_indent = Cm(first_line_indent)

    fmt.keep_with_next = keep_with_next

    if bidi:
        set_bidi(para, True)

    return para


def add_hyperlink(paragraph, url, text, size=TABLE_SIZE, color=PRIMARY_STRONG):
    part = paragraph.part
    r_id = part.relate_to(url, RT.HYPERLINK, is_external=True)

    hyperlink = OxmlElement("w:hyperlink")
    hyperlink.set(qn("r:id"), r_id)

    run = OxmlElement("w:r")
    rPr = OxmlElement("w:rPr")

    run_style = OxmlElement("w:rStyle")
    run_style.set(qn("w:val"), "Hyperlink")
    rPr.append(run_style)

    run_fonts = OxmlElement("w:rFonts")
    run_fonts.set(qn("w:ascii"), BODY_FONT)
    run_fonts.set(qn("w:hAnsi"), BODY_FONT)
    run_fonts.set(qn("w:cs"), BODY_FONT)
    rPr.append(run_fonts)

    size_el = OxmlElement("w:sz")
    size_el.set(qn("w:val"), str(int(size * 2)))
    rPr.append(size_el)

    size_cs = OxmlElement("w:szCs")
    size_cs.set(qn("w:val"), str(int(size * 2)))
    rPr.append(size_cs)

    color_el = OxmlElement("w:color")
    color_el.set(qn("w:val"), color)
    rPr.append(color_el)

    run.append(rPr)

    text_el = OxmlElement("w:t")
    text_el.text = text
    text_el.set(qn("xml:space"), "preserve")
    run.append(text_el)

    hyperlink.append(run)
    paragraph._p.append(hyperlink)
    return hyperlink


INLINE = re.compile(r"\*\*(.+?)\*\*|`([^`]+)`|\[([^\]]+)\]\(([^)]+)\)|<(https?://[^>]+)>")


def rich(paragraph, text, size=BODY_SIZE, color=None, bold_color=None):
    """Render inline Markdown (bold, code, links) inside a paragraph."""

    position = 0

    for match in INLINE.finditer(text):
        if match.start() > position:
            decorate_run(
                paragraph.add_run(text[position:match.start()]),
                size=size,
                color=color,
            )

        if match.group(1) is not None:
            decorate_run(
                paragraph.add_run(match.group(1)),
                size=size,
                bold=True,
                color=bold_color or INK,
            )
        elif match.group(2) is not None:
            decorate_run(
                paragraph.add_run(match.group(2)),
                size=size - 0.8,
                color=PRIMARY_STRONG,
                font=CODE_FONT,
            )
        else:
            label = match.group(3) or match.group(5)
            url = match.group(4) or match.group(5)
            add_hyperlink(paragraph, url, label, size=size)

        position = match.end()

    if position < len(text):
        decorate_run(paragraph.add_run(text[position:]), size=size, color=color)


# --------------------------------------------------------------------------- #
# Blocks
# --------------------------------------------------------------------------- #


def style_document(doc):
    normal = doc.styles["Normal"]
    normal.font.name = BODY_FONT
    normal.font.size = Pt(BODY_SIZE)

    rPr = normal.element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))

    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.insert(0, rFonts)

    for key in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rFonts.set(qn(key), BODY_FONT)

    pPr = normal.element.get_or_add_pPr()
    set_bidi_on_element(pPr)

    for name, size, color in (
        ("Heading 1", 15.5, PRIMARY_STRONG),
        ("Heading 2", 12, PRIMARY_STRONG),
    ):
        style = doc.styles[name]
        style.font.name = BODY_FONT
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = rgb(color)
        style.paragraph_format.space_before = Pt(14 if name == "Heading 1" else 10)
        style.paragraph_format.space_after = Pt(6 if name == "Heading 1" else 3)
        style.paragraph_format.keep_with_next = True
        style.paragraph_format.line_spacing = 1.2
        style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        set_bidi_on_element(style.element.get_or_add_pPr())

        heading_rPr = style.element.get_or_add_rPr()
        heading_fonts = heading_rPr.find(qn("w:rFonts"))

        if heading_fonts is None:
            heading_fonts = OxmlElement("w:rFonts")
            heading_rPr.insert(0, heading_fonts)

        for key in ("w:ascii", "w:hAnsi", "w:cs"):
            heading_fonts.set(qn(key), BODY_FONT)

        if name == "Heading 1":
            pBdr = OxmlElement("w:pBdr")
            bottom = OxmlElement("w:bottom")
            bottom.set(qn("w:val"), "single")
            bottom.set(qn("w:sz"), "6")
            bottom.set(qn("w:space"), "4")
            bottom.set(qn("w:color"), PRIMARY)
            pBdr.append(bottom)
            style.element.get_or_add_pPr().insert_element_before(
                pBdr,
                "w:shd",
                "w:tabs",
                "w:suppressAutoHyphens",
                "w:kinsoku",
                "w:wordWrap",
                "w:overflowPunct",
                "w:topLinePunct",
                "w:autoSpaceDE",
                "w:autoSpaceDN",
                "w:bidi",
                "w:adjustRightInd",
                "w:snapToGrid",
                "w:spacing",
                "w:ind",
                "w:contextualSpacing",
                "w:mirrorIndents",
                "w:suppressOverlap",
                "w:jc",
                "w:textDirection",
                "w:textAlignment",
                "w:textboxTightWrap",
                "w:outlineLvl",
                "w:divId",
                "w:cnfStyle",
                "w:rPr",
                "w:sectPr",
                "w:pPrChange",
            )

    section = doc.sections[0]
    section.page_width = Cm(21)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(2.0)
    section.bottom_margin = Cm(2.0)
    section.left_margin = Cm(1.9)
    section.right_margin = Cm(1.9)
    section.header_distance = Cm(1.0)
    section.footer_distance = Cm(1.0)
    section.different_first_page_header_footer = True


def set_bidi_on_element(pPr):
    bidi = OxmlElement("w:bidi")
    pPr.insert_element_before(bidi, *PPR_BIDI_SUCCESSORS)


def add_header_footer(doc):
    section = doc.sections[0]

    header = section.header.paragraphs[0]
    header.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_bidi(header)
    decorate_run(header.add_run("SchoolPlatform â€” Ø§Ù„ØªÙ‚Ø±ÙŠØ± Ø§Ù„Ø´Ø§Ù…Ù„  Â·  Ø§Ù„Ø¥ØµØ¯Ø§Ø± 1.0"), size=8, color=MUTED)
    borders(header._p, bottom=("single", 4, BORDER))

    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_bidi(footer)
    decorate_run(footer.add_run("ØµÙØ­Ø© "), size=8, color=MUTED)

    field(footer, "PAGE")
    decorate_run(footer.add_run(" Ù…Ù† "), size=8, color=MUTED)
    field(footer, "NUMPAGES")


def field(paragraph, instruction):
    run = paragraph.add_run()
    decorate_run(run, size=8, color=MUTED)

    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = f" {instruction} "
    separate = OxmlElement("w:fldChar")
    separate.set(qn("w:fldCharType"), "separate")
    text = OxmlElement("w:t")
    text.text = "1"
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")

    for element in (begin, instr, separate, text, end):
        run._r.append(element)


def cell_text(cell, text, size=TABLE_SIZE, bold=False, color=INK, align=WD_ALIGN_PARAGRAPH.RIGHT):
    cell.text = ""
    para = cell.paragraphs[0]
    para.paragraph_format.space_before = Pt(1)
    para.paragraph_format.space_after = Pt(1)
    para.paragraph_format.line_spacing = 1.2
    para.alignment = align
    set_bidi(para)
    rich(para, text, size=size, color=color, bold_color=color if bold else None)

    if bold:
        for run in para.runs:
            run.bold = True


def strip_markup(text):
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"<(https?://[^>]+)>", r"\1", text)
    text = text.replace("**", "").replace("__", "")
    text = re.sub(r"`([^`]*)`", r"\1", text)
    return " ".join(text.split()).strip()


def add_table(doc, rows):
    columns = max(len(row) for row in rows)
    rows = [row + [""] * (columns - len(row)) for row in rows]
    header, *body = rows

    weights = []

    for index in range(columns):
        longest = max(len(strip_markup(row[index])) for row in rows)
        weights.append(max(9, min(longest, 52)))

    total = sum(weights)
    widths = [CONTENT_WIDTH_CM * weight / total for weight in weights]

    minimum = 2.2
    deficit = sum(minimum - width for width in widths if width < minimum)

    if deficit:
        widths = [max(width, minimum) for width in widths]
        room = sum(width - minimum for width in widths)
        widths = [
            width - (width - minimum) * deficit / room if width > minimum else width
            for width in widths
        ]

    table = doc.add_table(rows=len(rows), cols=columns)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False

    tblPr = table._tbl.tblPr
    bidi = OxmlElement("w:bidiVisual")
    tblPr.append(bidi)

    borders(
        table._tbl,
        top=("single", 4, BORDER),
        bottom=("single", 4, BORDER),
        left=("single", 4, BORDER),
        right=("single", 4, BORDER),
        insideH=("single", 4, BORDER),
        insideV=("single", 4, BORDER),
    )

    for row_index, row in enumerate(rows):
        is_header = row_index == 0
        table_row = table.rows[row_index]

        trPr = table_row._tr.get_or_add_trPr()
        cant_split = OxmlElement("w:cantSplit")
        trPr.append(cant_split)

        if is_header:
            trPr.append(OxmlElement("w:tblHeader"))

        for column_index, value in enumerate(row):
            cell = table.cell(row_index, column_index)
            cell.width = Cm(widths[column_index])

            if is_header:
                shade(cell._tc, PRIMARY)
                cell_text(cell, value, bold=True, color="FFFFFF", align=WD_ALIGN_PARAGRAPH.RIGHT)
            else:
                if row_index % 2 == 0:
                    shade(cell._tc, SURFACE)

                cell_text(cell, value)

            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER

    spacer = doc.add_paragraph()
    spacer.paragraph_format.space_after = Pt(2)
    spacer.paragraph_format.space_before = Pt(0)
    spacer.paragraph_format.line_spacing = 1.0
    set_bidi(spacer)


def add_code(doc, lines):
    table = doc.add_table(rows=1, cols=1)
    table.autofit = False
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    cell = table.cell(0, 0)
    cell.width = Cm(CONTENT_WIDTH_CM)
    shade(cell._tc, SURFACE)
    borders(
        cell._tc,
        top=("single", 4, BORDER),
        bottom=("single", 4, BORDER),
        left=("single", 4, BORDER),
        right=("single", 4, BORDER),
    )

    cell.text = ""
    first = True

    for line in lines:
        para = cell.paragraphs[0] if first else cell.add_paragraph()
        first = False
        para.paragraph_format.space_before = Pt(0)
        para.paragraph_format.space_after = Pt(0)
        para.paragraph_format.line_spacing = 1.15
        para.alignment = WD_ALIGN_PARAGRAPH.LEFT
        set_bidi(para, False)
        run = para.add_run(line.rstrip() or " ")
        decorate_run(run, size=CODE_SIZE, font=CODE_FONT, color=INK)

    spacer = doc.add_paragraph()
    spacer.paragraph_format.space_after = Pt(2)
    spacer.paragraph_format.line_spacing = 1.0
    set_bidi(spacer)


def add_callout(doc, text):
    table = doc.add_table(rows=1, cols=1)
    table.autofit = False
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    cell = table.cell(0, 0)
    cell.width = Cm(CONTENT_WIDTH_CM)
    shade(cell._tc, PRIMARY_LIGHT)
    borders(
        cell._tc,
        right=("single", 18, PRIMARY),
        top=("single", 2, PRIMARY_LIGHT),
        bottom=("single", 2, PRIMARY_LIGHT),
        left=("single", 2, PRIMARY_LIGHT),
    )

    cell.text = ""
    para = cell.paragraphs[0]
    para.paragraph_format.space_before = Pt(3)
    para.paragraph_format.space_after = Pt(3)
    para.paragraph_format.line_spacing = 1.4
    para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    set_bidi(para)
    rich(para, text, size=9.6, color="4A4560", bold_color=INK)

    spacer = doc.add_paragraph()
    spacer.paragraph_format.space_after = Pt(2)
    spacer.paragraph_format.line_spacing = 1.0
    set_bidi(spacer)


def page_break(doc):
    para = doc.add_paragraph()
    para.paragraph_format.space_after = Pt(0)
    set_bidi(para)
    para.add_run().add_break(WD_BREAK.PAGE)
    return para


def add_cover(doc):
    band = doc.add_table(rows=1, cols=1)
    band.autofit = False
    band.alignment = WD_TABLE_ALIGNMENT.CENTER

    cell = band.cell(0, 0)
    cell.width = Cm(CONTENT_WIDTH_CM)
    shade(cell._tc, INK)
    borders(
        cell._tc,
        bottom=("single", 24, PRIMARY),
        top=("single", 2, INK),
        left=("single", 2, INK),
        right=("single", 2, INK),
    )

    cell.text = ""

    titles = [
        ("Ù…Ù†ØµØ© SchoolPlatform", 28, "FFFFFF", True, 10, 3),
        ("Ù†Ø¸Ø§Ù… Ø¥Ø¯Ø§Ø±Ø© Ù…Ø¯Ø±Ø³ÙŠØ© Ø³Ø­Ø§Ø¨ÙŠ Ù…ØªØ¹Ø¯Ø¯ Ø§Ù„Ù…Ø¤Ø³Ø³Ø§Øª", 14, "C9BFFB", False, 4, 2),
        ("ØªÙ‚Ø±ÙŠØ± ÙÙ†ÙŠ ÙˆØªØ¬Ø§Ø±ÙŠ Ø´Ø§Ù…Ù„", 11, "9C93C7", False, 4, 10),
    ]

    for index, (text, size, color, bold, space_before, space_after) in enumerate(titles):
        para = cell.paragraphs[0] if index == 0 else cell.add_paragraph()
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        para.paragraph_format.space_before = Pt(space_before)
        para.paragraph_format.space_after = Pt(space_after)
        para.paragraph_format.line_spacing = 1.2
        set_bidi(para)
        decorate_run(para.add_run(text), size=size, bold=bold, color=color)

    paragraph(doc, "", space_after=0, line_spacing=1.0)

    paragraph(
        doc,
        "Ø§Ù„Ù…Ù…ÙŠØ²Ø§Øª Â· Ø·Ø±ÙŠÙ‚Ø© Ø§Ù„Ø¹Ù…Ù„ Â· Ø§Ù„Ø£Ù‡Ø¯Ø§Ù Â· Ø®Ø·Ø© Ø§Ù„ØªØ³Ù„ÙŠÙ…",
        align=WD_ALIGN_PARAGRAPH.CENTER,
        size=17,
        bold=True,
        color=INK,
        space_before=18,
        space_after=10,
        line_spacing=1.2,
    )

    paragraph(
        doc,
        "Ù†Ø³Ø®Ø© Ø­ÙŠÙ‘Ø© ØªØ¹Ù…Ù„ Ø§Ù„Ø¢Ù† Ø¹Ù„Ù‰ Ø§Ù„Ø¥Ù†ØªØ±Ù†Øª",
        align=WD_ALIGN_PARAGRAPH.CENTER,
        size=10.5,
        color=MUTED,
        space_after=2,
    )

    link_para = doc.add_paragraph()
    link_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    link_para.paragraph_format.space_after = Pt(2)
    set_bidi(link_para, False)
    add_hyperlink(
        link_para,
        "https://schoolplatform-iq.vercel.app",
        "https://schoolplatform-iq.vercel.app",
        size=10.5,
    )

    paragraph(
        doc,
        "Ø§Ù„Ø¥ØµØ¯Ø§Ø± 1.0 â€” 4 Ù†ÙˆÙÙ…Ø¨Ø± 2026",
        align=WD_ALIGN_PARAGRAPH.CENTER,
        size=10.5,
        color=MUTED,
        space_after=16,
    )

    stats = [
        ("313", "Ø§Ø®ØªØ¨Ø§Ø±Ø§Ù‹ Ù†Ø§Ø¬Ø­Ø§Ù‹"),
        ("14", "ÙˆØ­Ø¯Ø© ÙˆØ¸ÙŠÙÙŠØ©"),
        ("18", "Ø¬Ø¯ÙˆÙ„ Ø¨ÙŠØ§Ù†Ø§Øª"),
        ("0", "ØªÙƒÙ„ÙØ© ØªØ´ØºÙŠÙ„ Ø´Ù‡Ø±ÙŠØ©"),
    ]

    table = doc.add_table(rows=1, cols=len(stats))
    table.autofit = False
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    for index, (value, label) in enumerate(stats):
        cell = table.cell(0, index)
        cell.width = Cm(CONTENT_WIDTH_CM / len(stats) - 0.3)
        shade(cell._tc, PRIMARY_LIGHT)
        borders(
            cell._tc,
            top=("single", 8, "FFFFFF"),
            bottom=("single", 8, "FFFFFF"),
            left=("single", 8, "FFFFFF"),
            right=("single", 8, "FFFFFF"),
        )
        cell.text = ""

        top = cell.paragraphs[0]
        top.alignment = WD_ALIGN_PARAGRAPH.CENTER
        top.paragraph_format.space_before = Pt(10)
        top.paragraph_format.space_after = Pt(0)
        set_bidi(top)
        decorate_run(top.add_run(value), size=20, bold=True, color=PRIMARY_STRONG)

        bottom = cell.add_paragraph()
        bottom.alignment = WD_ALIGN_PARAGRAPH.CENTER
        bottom.paragraph_format.space_after = Pt(10)
        bottom.paragraph_format.space_before = Pt(0)
        set_bidi(bottom)
        decorate_run(bottom.add_run(label), size=8.5, color=MUTED)

    paragraph(doc, "", space_after=0, line_spacing=1.0)

    note = paragraph(
        doc,
        "ÙˆØ«ÙŠÙ‚Ø© Ù…ÙØ¹Ø¯Ù‘Ø© Ù„Ù„Ø¹Ø±Ø¶ Ø¹Ù„Ù‰ Ø§Ù„Ø´Ø±ÙƒØ© Ø§Ù„Ù…Ø´ØªØ±ÙŠØ© â€” Ø¬Ù…ÙŠØ¹ Ø§Ù„Ø­Ù‚ÙˆÙ‚ Ù…Ø­ÙÙˆØ¸Ø©",
        align=WD_ALIGN_PARAGRAPH.CENTER,
        size=9,
        color=MUTED,
        space_before=24,
        space_after=2,
    )
    borders(note._p, top=("single", 4, BORDER))

    paragraph(
        doc,
        "SchoolPlatform",
        align=WD_ALIGN_PARAGRAPH.CENTER,
        size=9,
        bold=True,
        color=PRIMARY,
        space_after=0,
    )


def add_toc(doc):
    paragraph(doc, "Ø§Ù„Ù…Ø­ØªÙˆÙŠØ§Øª", size=15.5, bold=True, color=PRIMARY_STRONG,
              space_before=0, space_after=8, line_spacing=1.2)

    holder = doc.add_paragraph()
    holder.paragraph_format.space_after = Pt(6)
    set_bidi(holder)

    run = holder.add_run()
    decorate_run(run, size=9, color=MUTED)

    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = ' TOC \\o "1-2" \\h \\z \\u '
    separate = OxmlElement("w:fldChar")
    separate.set(qn("w:fldCharType"), "separate")
    placeholder = OxmlElement("w:t")
    placeholder.text = "Ø§Ø¶ØºØ· Ø¨Ø²Ø± Ø§Ù„ÙØ£Ø±Ø© Ø§Ù„Ø£ÙŠÙ…Ù† Ù‡Ù†Ø§ Ø«Ù… Â«ØªØ­Ø¯ÙŠØ« Ø§Ù„Ø­Ù‚Ù„Â» Ù„Ø¨Ù†Ø§Ø¡ Ø§Ù„ÙÙ‡Ø±Ø³."
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")

    for element in (begin, instr, separate, placeholder, end):
        run._r.append(element)


# --------------------------------------------------------------------------- #
# Markdown driving
# --------------------------------------------------------------------------- #


def heading(doc, text, level):
    style = "Heading 1" if level == 2 else "Heading 2"
    para = doc.add_paragraph(style=style)
    set_bidi(para)
    para.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    rich(para, text, size=15.5 if level == 2 else 12, bold_color=PRIMARY_STRONG)

    for run in para.runs:
        run.bold = True
        run.font.color.rgb = rgb(PRIMARY_STRONG)

    return para


def build(doc, lines):
    paragraph_buffer = []

    def flush():
        if not paragraph_buffer:
            return

        text = " ".join(paragraph_buffer)
        paragraph_buffer.clear()
        para = paragraph(doc, "", space_after=5, line_spacing=1.5)
        rich(para, text, size=BODY_SIZE)

    index = 0

    while index < len(lines):
        line = lines[index].rstrip()

        if line.startswith("```"):
            flush()
            block = []
            index += 1

            while index < len(lines) and not lines[index].startswith("```"):
                block.append(lines[index])
                index += 1

            add_code(doc, block)
            index += 1
            continue

        if line.strip() in {"---", "***", "___"}:
            flush()
            index += 1
            continue

        if line.startswith("|"):
            flush()
            rows = []

            while index < len(lines) and lines[index].startswith("|"):
                cells = [cell.strip() for cell in lines[index].strip().strip("|").split("|")]

                if not all(re.fullmatch(r":?-{2,}:?", cell) for cell in cells if cell):
                    rows.append(cells)

                index += 1

            if rows:
                add_table(doc, rows)

            continue

        if line.startswith(">"):
            flush()
            quoted = []

            while index < len(lines) and lines[index].startswith(">"):
                quoted.append(lines[index].lstrip("> ").rstrip())
                index += 1

            add_callout(doc, " ".join(quoted))
            continue

        match = re.match(r"^(#{2,4})\s+(.*)$", line)

        if match:
            flush()
            heading(doc, match.group(2), len(match.group(1)))
            index += 1
            continue

        item = re.match(r"^\s*([-*+]|\d+\.)\s+(.*)$", line)

        if item:
            flush()
            marker = "â€¢" if item.group(1) in {"-", "*", "+"} else item.group(1)
            para = paragraph(
                doc,
                "",
                space_after=2,
                line_spacing=1.45,
                right_indent=0.65,
                first_line_indent=-0.65,
            )
            decorate_run(para.add_run(f"{marker}  "), size=BODY_SIZE, color=PRIMARY_STRONG)
            rich(para, item.group(2), size=BODY_SIZE)
            index += 1
            continue

        if not line.strip():
            flush()
            index += 1
            continue

        paragraph_buffer.append(line.strip())
        index += 1

    flush()


def main():
    if not SOURCE.exists():
        sys.exit(f"error: {SOURCE} is missing")

    doc = Document()
    style_document(doc)
    add_header_footer(doc)
    add_cover(doc)
    page_break(doc)
    add_toc(doc)
    page_break(doc)

    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    start = 0

    while start < len(lines) and not lines[start].startswith("## "):
        start += 1

    build(doc, lines[start:])

    props = doc.core_properties
    props.title = "Ø§Ù„ØªÙ‚Ø±ÙŠØ± Ø§Ù„Ø´Ø§Ù…Ù„ â€” SchoolPlatform"
    props.subject = "Ù†Ø¸Ø§Ù… Ø¥Ø¯Ø§Ø±Ø© Ù…Ø¯Ø±Ø³ÙŠØ© Ø³Ø­Ø§Ø¨ÙŠ"
    props.author = "SchoolPlatform"
    props.keywords = "Ù…Ø¯Ø±Ø³Ø©, Ø¥Ø¯Ø§Ø±Ø©, Django, ØªÙ‚Ø±ÙŠØ±"
    props.comments = "ØªÙ‚Ø±ÙŠØ± ÙÙ†ÙŠ ÙˆØªØ¬Ø§Ø±ÙŠ Ø´Ø§Ù…Ù„"

    doc.save(str(TARGET))
    print(f"written {TARGET} ({TARGET.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()

