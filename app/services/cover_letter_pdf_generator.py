"""
PDF generation service for cover letters.

Converts cover letter text to PDF using reportlab with professional formatting.
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


def generate_cover_letter_pdf(cover_letter_text: str) -> bytes:
    """
    Generate a PDF from cover letter text.

    Formats cover letter with professional styling suitable for
    business correspondence.

    Args:
        cover_letter_text: Plain text content of the cover letter.

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
        rightMargin=2.5 * cm,
        leftMargin=2.5 * cm,
        topMargin=2.5 * cm,
        bottomMargin=2.5 * cm,
    )

    styles = getSampleStyleSheet()
    story: list = []

    # Professional cover letter styles
    normal_style = ParagraphStyle(
        "CoverLetterNormal",
        parent=styles["Normal"],
        fontSize=11,
        leading=16,
        spaceAfter=12,
        alignment=0,  # Left aligned
    )

    # Parse text into paragraphs
    paragraphs = cover_letter_text.split("\n\n")
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            story.append(Spacer(1, 12))
            continue

        # Check if it's a signature line (usually at the end)
        if para.startswith("С уважением") or para.startswith("Sincerely") or para.startswith("Best regards"):
            story.append(Spacer(1, 24))  # Extra space before signature
            story.append(Paragraph(para, normal_style))
        else:
            story.append(Paragraph(para, normal_style))

    try:
        doc.build(story)
        return pdf_buffer.getvalue()
    except Exception as exc:
        raise RuntimeError(f"Error generating cover letter PDF: {exc}") from exc

