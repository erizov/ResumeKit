"""
Utility functions for cleaning and formatting resume text.
"""

import re


def clean_resume_text(text: str) -> str:
    """
    Clean resume text by removing separators and excessive empty lines.

    Args:
        text: Raw resume text

    Returns:
        Cleaned resume text
    """
    # Remove "--" separators and divider lines
    lines = text.splitlines()
    cleaned_lines = []
    
    for line in lines:
        # Skip lines that are only dashes, underscores, or separators
        stripped = line.strip()
        if re.match(r'^[-_=]{3,}$', stripped):
            continue
        
        # Remove "--" from the beginning or end of lines
        cleaned = re.sub(r'^[-]{2,}\s*', '', line)
        cleaned = re.sub(r'\s*[-]{2,}$', '', cleaned)
        
        cleaned_lines.append(cleaned)
    
    # Remove excessive empty lines (keep max 1 empty line between content)
    result_lines = []
    prev_empty = False
    
    for line in cleaned_lines:
        is_empty = not line.strip()
        
        if is_empty:
            if not prev_empty:
                result_lines.append("")
                prev_empty = True
        else:
            result_lines.append(line)
            prev_empty = False
    
    # Remove leading and trailing empty lines
    while result_lines and not result_lines[0].strip():
        result_lines.pop(0)
    while result_lines and not result_lines[-1].strip():
        result_lines.pop()
    
    return "\n".join(result_lines)


def format_dates_on_right(text: str) -> str:
    """
    Format job titles and dates on the same line with dates aligned to the right.

    Attempts to detect patterns like:
    - "Job Title" followed by "1998 – 2002" on next line
    - "Job Title  1998 – 2002" on same line

    Args:
        text: Resume text

    Returns:
        Text with dates formatted on the right side of job titles
    """
    lines = text.splitlines()
    result_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        # Check if current line looks like a job title and next line has dates
        if i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            # Pattern: dates like "1998 – 2002" or "1998-2002"
            date_pattern = r'^\d{4}\s*[–-]\s*\d{4}$'
            
            if re.match(date_pattern, next_line):
                # Combine title and date on same line
                # Use spaces to align date to right (approximate)
                combined = f"{line}  {next_line}"
                result_lines.append(combined)
                i += 2  # Skip both lines
                continue
        
        # Check if line already has date pattern at the end
        date_at_end = re.search(r'\s+(\d{4}\s*[–-]\s*\d{4})$', line)
        if date_at_end:
            # Already formatted, keep as is
            result_lines.append(line)
        else:
            result_lines.append(line)
        
        i += 1
    
    return "\n".join(result_lines)

