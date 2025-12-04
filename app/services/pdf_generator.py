"""
PDF generation service for tailored resumes.

Converts resume text directly to PDF using reportlab.
"""

import io

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
except ImportError:
    A4 = None  # type: ignore
    getSampleStyleSheet = None  # type: ignore
    ParagraphStyle = None  # type: ignore
    cm = None  # type: ignore
    Paragraph = None  # type: ignore
    SimpleDocTemplate = None  # type: ignore
    Spacer = None  # type: ignore


def generate_pdf_from_text(resume_text: str) -> bytes:
    """
    Generate a PDF from resume text.

    Converts plain text resume to PDF with basic formatting.

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

    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        pdf_buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    story: list = []

    # Create custom styles
    heading_style = ParagraphStyle(
        "CustomHeading",
        parent=styles["Heading2"],
        fontSize=14,
        textColor=(44, 62, 80),  # #2c3e50
        spaceAfter=12,
        borderWidth=1,
        borderColor=(52, 152, 219),  # #3498db
        borderPadding=5,
    )

    normal_style = ParagraphStyle(
        "CustomNormal",
        parent=styles["Normal"],
        fontSize=11,
        leading=16,
        spaceAfter=6,
    )

    # Parse text into paragraphs
    lines = resume_text.splitlines()
    in_list = False

    for line in lines:
        line = line.strip()
        if not line:
            if in_list:
                story.append(Spacer(1, 6))
                in_list = False
            story.append(Spacer(1, 6))
            continue

        # Detect headers (all caps or lines ending with colon)
        if line.isupper() or line.endswith(":"):
            if in_list:
                story.append(Spacer(1, 6))
                in_list = False
            story.append(Paragraph(line, heading_style))
        # Detect bullet points
        elif line.startswith("- ") or line.startswith("* "):
            if not in_list:
                story.append(Spacer(1, 6))
                in_list = True
            bullet_text = f"• {line[2:]}"
            story.append(Paragraph(bullet_text, normal_style))
        else:
            if in_list:
                story.append(Spacer(1, 6))
                in_list = False
            story.append(Paragraph(line, normal_style))

    try:
        doc.build(story)
        return pdf_buffer.getvalue()
    except Exception as exc:
        raise RuntimeError(f"Error generating PDF: {exc}") from exc



