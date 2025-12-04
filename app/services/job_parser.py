"""
Utilities for fetching and parsing job descriptions from URLs.

The parser extracts main content from HTML pages, stripping boilerplate
like navigation, headers, and footers.
"""

from typing import Final

import httpx
from bs4 import BeautifulSoup


_USER_AGENT: Final = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/91.0.4472.124 Safari/537.36"
)

_TIMEOUT_SECONDS: Final = 10


async def fetch_job_description_from_url(url: str) -> str:
    """
    Fetch a job description from a URL and extract the main text content.

    Args:
        url: The URL to fetch the job description from.

    Returns:
        Plain text content extracted from the page.

    Raises:
        httpx.HTTPError: If the HTTP request fails.
        ValueError: If the URL is invalid or the content cannot be parsed.
    """
    async with httpx.AsyncClient(
        timeout=_TIMEOUT_SECONDS,
        follow_redirects=True,
        headers={"User-Agent": _USER_AGENT},
    ) as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ValueError(f"Failed to fetch URL: {exc}") from exc

    return _extract_text_from_html(response.text)


def _extract_text_from_html(html_content: str) -> str:
    """
    Extract main text content from HTML, removing boilerplate.

    Uses BeautifulSoup to parse HTML and extract text from likely
    content containers (main, article, div with job-related classes).
    Falls back to body text if no specific containers are found.
    """
    soup = BeautifulSoup(html_content, "lxml")

    # Remove script and style elements
    for element in soup(["script", "style", "nav", "header", "footer"]):
        element.decompose()

    # Try to find main content containers
    content_selectors = [
        "main",
        "article",
        '[class*="job"]',
        '[class*="description"]',
        '[id*="job"]',
        '[id*="description"]',
        ".content",
        "#content",
    ]

    text_parts: list[str] = []

    for selector in content_selectors:
        elements = soup.select(selector)
        if elements:
            for elem in elements:
                text = elem.get_text(separator="\n", strip=True)
                if text and len(text) > 100:  # Minimum content length
                    text_parts.append(text)
                    break
            if text_parts:
                break

    # Fallback to body text if no specific containers found
    if not text_parts:
        body = soup.find("body")
        if body:
            text = body.get_text(separator="\n", strip=True)
            if text:
                text_parts.append(text)

    if not text_parts:
        raise ValueError("Could not extract meaningful content from the page")

    # Join and clean up whitespace
    result = "\n\n".join(text_parts)
    # Remove excessive blank lines
    lines = [line.strip() for line in result.splitlines() if line.strip()]
    return "\n".join(lines)

