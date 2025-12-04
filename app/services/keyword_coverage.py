"""
Keyword coverage analysis for matching resume skills with job requirements.

Extracts keywords from job descriptions and resumes, then computes
coverage metrics and identifies missing skills.
"""

import re
from typing import Final

# Common technology keywords to normalize
_TECH_NORMALIZATIONS: Final = {
    "python": "Python",
    "java": "Java",
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "react": "React",
    "vue": "Vue",
    "angular": "Angular",
    "fastapi": "FastAPI",
    "django": "Django",
    "flask": "Flask",
    "spring": "Spring",
    "spring boot": "Spring Boot",
    "postgresql": "PostgreSQL",
    "postgres": "PostgreSQL",
    "mysql": "MySQL",
    "mongodb": "MongoDB",
    "redis": "Redis",
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "k8s": "Kubernetes",
    "aws": "AWS",
    "azure": "Azure",
    "gcp": "GCP",
    "git": "Git",
    "github": "GitHub",
    "gitlab": "GitLab",
    "ci/cd": "CI/CD",
    "cicd": "CI/CD",
    "rest": "REST",
    "graphql": "GraphQL",
    "microservices": "Microservices",
    "api": "API",
    "sql": "SQL",
    "nosql": "NoSQL",
    "linux": "Linux",
    "unix": "Unix",
    "agile": "Agile",
    "scrum": "Scrum",
}


def extract_keywords(text: str) -> set[str]:
    """
    Extract technology and skill keywords from text.

    Uses simple pattern matching to find common technology names,
    programming languages, frameworks, and tools.
    """
    text_lower = text.lower()

    # Normalize common variations
    normalized_text = text_lower
    for variant, standard in _TECH_NORMALIZATIONS.items():
        normalized_text = normalized_text.replace(variant, standard.lower())

    keywords: set[str] = set()

    # Extract normalized keywords
    for variant, standard in _TECH_NORMALIZATIONS.items():
        if variant in text_lower or standard.lower() in text_lower:
            keywords.add(standard)

    # Extract common patterns (words that look like technologies)
    # Match capitalized words, acronyms, and common tech terms
    tech_patterns = [
        r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b",  # Capitalized words
        r"\b[A-Z]{2,}\b",  # Acronyms
        r"\b\w+\.(js|ts|py|java|go|rs|rb)\b",  # File extensions
    ]

    for pattern in tech_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            if isinstance(match, tuple):
                match = match[0]
            if len(match) > 2:  # Filter out very short matches
                keywords.add(match)

    # Also extract from structured resume if available
    # (This would be enhanced if we have StructuredResume data)

    return keywords


def compute_coverage(
    resume_text: str, job_description: str
) -> dict[str, any]:
    """
    Compute keyword coverage between resume and job description.

    Returns:
        Dictionary with:
        - matched: list of keywords found in both
        - missing: list of keywords in JD but not in resume
        - score: coverage score (0.0 to 1.0)
    """
    resume_keywords = extract_keywords(resume_text)
    jd_keywords = extract_keywords(job_description)

    matched = sorted(resume_keywords.intersection(jd_keywords))
    missing = sorted(jd_keywords - resume_keywords)

    # Coverage score: percentage of JD keywords found in resume
    score = (
        len(matched) / len(jd_keywords) if jd_keywords else 0.0
    )

    return {
        "matched": matched,
        "missing": missing,
        "score": round(score, 2),
        "total_jd_keywords": len(jd_keywords),
        "total_resume_keywords": len(resume_keywords),
    }

