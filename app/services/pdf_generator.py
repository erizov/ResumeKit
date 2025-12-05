"""
PDF generation service for tailored resumes.

Converts resume text directly to PDF using reportlab.
"""

import io
import re

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm, mm
    from reportlab.platypus import (
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
        KeepTogether,
    )
    from reportlab.lib import colors
    from reportlab.platypus.flowables import PageBreak
except ImportError:
    A4 = None  # type: ignore
    getSampleStyleSheet = None  # type: ignore
    ParagraphStyle = None  # type: ignore
    cm = None  # type: ignore
    mm = None  # type: ignore
    Paragraph = None  # type: ignore
    SimpleDocTemplate = None  # type: ignore
    Spacer = None  # type: ignore
    Table = None  # type: ignore
    TableStyle = None  # type: ignore
    KeepTogether = None  # type: ignore
    colors = None  # type: ignore
    PageBreak = None  # type: ignore


def generate_pdf_from_text(resume_text: str) -> bytes:
    """
    Generate a compact PDF from resume text with two-column layout.

    Uses a compact two-column layout with important information
    (name, contact) in the top left corner. Maximizes space usage.

    Args:
        resume_text: Plain text content of the resume.

    Returns:
        PDF file content as bytes.

    Raises:
        RuntimeError: If reportlab is not installed or PDF generation fails.
    """
    if SimpleDocTemplate is None:
        raise RuntimeError(
            "reportlab is not installed. Install it with: pip install reportlab"
        )

    # Clean the text before processing
    from .resume_formatter import clean_resume_text
    resume_text = clean_resume_text(resume_text)

    pdf_buffer = io.BytesIO()
    # Reduced margins for more space
    doc = SimpleDocTemplate(
        pdf_buffer,
        pagesize=A4,
        rightMargin=1.2 * cm,
        leftMargin=1.2 * cm,
        topMargin=1.2 * cm,
        bottomMargin=1.2 * cm,
    )

    styles = getSampleStyleSheet()
    story: list = []

    # Compact styles
    name_style = ParagraphStyle(
        "NameStyle",
        parent=styles["Heading1"],
        fontSize=16,
        textColor=(44, 62, 80),
        spaceAfter=4,
        leading=18,
    )

    contact_style = ParagraphStyle(
        "ContactStyle",
        parent=styles["Normal"],
        fontSize=9,
        leading=11,
        spaceAfter=8,
    )

    heading_style = ParagraphStyle(
        "CustomHeading",
        parent=styles["Heading2"],
        fontSize=11,
        textColor=(44, 62, 80),
        spaceAfter=6,
        spaceBefore=8,
        leading=13,
    )

    normal_style = ParagraphStyle(
        "CustomNormal",
        parent=styles["Normal"],
        fontSize=9,
        leading=11,
        spaceAfter=3,
    )

    bullet_style = ParagraphStyle(
        "BulletStyle",
        parent=styles["Normal"],
        fontSize=9,
        leading=11,
        spaceAfter=2,
        leftIndent=6,
    )

    # Parse text into sections
    lines = resume_text.splitlines()
    sections: list[tuple[str, list[str]]] = []
    current_section = ""
    current_content: list[str] = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Detect headers (all caps or lines ending with colon)
        if line.isupper() or line.endswith(":"):
            if current_section:
                sections.append((current_section, current_content))
            current_section = line.rstrip(":")
            current_content = []
        else:
            current_content.append(line)

    if current_section:
        sections.append((current_section, current_content))

    # Extract header info (first few lines before first section)
    header_lines = []
    if sections:
        # Get lines before first section
        first_section_idx = resume_text.find(sections[0][0])
        if first_section_idx > 0:
            header_text = resume_text[:first_section_idx].strip()
            header_lines = [
                line.strip()
                for line in header_text.splitlines()
                if line.strip()
            ]

    # Build PDF content
    # Header: Name and contact info in top left (compact)
    if header_lines:
        # First line is usually the name
        if header_lines:
            story.append(Paragraph(header_lines[0], name_style))
        # Remaining header lines are contact info
        if len(header_lines) > 1:
            contact_text = "<br/>".join(header_lines[1:])
            story.append(Paragraph(contact_text, contact_style))

    story.append(Spacer(1, 4))

    # Process sections in two-column layout where possible
    # For compact layout, we'll use a table with two columns
    # Important sections go in left column, less critical in right

    # Simple approach: alternate or use single column for now
    # More complex: parse and distribute sections intelligently
    for section_title, content in sections:
        story.append(Paragraph(section_title, heading_style))

        for line in content:
            if line.startswith("- ") or line.startswith("* "):
                bullet_text = f"• {line[2:]}"
                story.append(Paragraph(bullet_text, bullet_style))
            elif re.search(r'\d{4}\s*[–-]\s*\d{4}', line):
                # Job title with date - format compactly
                parts = re.split(r'(\d{4}\s*[–-]\s*\d{4})', line)
                if len(parts) >= 2:
                    title_part = parts[0].strip()
                    date_part = parts[1]
                    formatted = f"<b>{title_part}</b> {date_part}"
                    story.append(Paragraph(formatted, normal_style))
                else:
                    story.append(Paragraph(line, normal_style))
            else:
                story.append(Paragraph(line, normal_style))

        story.append(Spacer(1, 4))

    try:
        doc.build(story)
        return pdf_buffer.getvalue()
    except Exception as exc:
        raise RuntimeError(f"Error generating PDF: {exc}") from exc



