"""
DOCX generation service for tailored resumes.

Converts resume text to DOCX format using python-docx.
"""

import io

try:
    from docx import Document
    from docx.shared import Cm, Pt
    from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
except ImportError:
    Document = None  # type: ignore


def generate_docx_from_text(resume_text: str) -> bytes:
    """
    Generate a DOCX file from resume text.

    Converts plain text resume to DOCX with basic formatting.

    Args:
        resume_text: Plain text content of the resume.

    Returns:
        DOCX file content as bytes.

    Raises:
        RuntimeError: If python-docx is not installed or DOCX generation fails.
    """
    if Document is None:
        raise RuntimeError(
            "python-docx is not installed. Install it with: pip install python-docx"
        )

    doc = Document()
    
    # Set default font
    style = doc.styles["Normal"]
    font = style.font
    font.name = "Calibri"
    font.size = Pt(11)

    # Parse text into paragraphs
    lines = resume_text.splitlines()
    
    for line in lines:
        line = line.strip()
        if not line:
            # Add empty paragraph for spacing
            doc.add_paragraph()
            continue

        # Detect headers (all caps or lines ending with colon)
        if line.isupper() or line.endswith(":"):
            p = doc.add_paragraph(line)
            p.style = "Heading 2"
            p.runs[0].font.size = Pt(14)
            p.runs[0].bold = True
        # Detect bullet points
        elif line.startswith("- ") or line.startswith("* "):
            p = doc.add_paragraph(line[2:], style="List Bullet")
        else:
            doc.add_paragraph(line)

    # Save to bytes buffer
    doc_buffer = io.BytesIO()
    doc.save(doc_buffer)
    doc_buffer.seek(0)
    return doc_buffer.getvalue()

