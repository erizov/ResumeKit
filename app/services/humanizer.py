"""
Text humanization service to make AI-generated content more natural.

Reduces AI stigmas and patterns that make content appear machine-generated.
"""

import re
import random


# Common AI stigma phrases to avoid or replace
AI_STIGMA_PHRASES = {
    "leverage": ["use", "apply", "employ", "work with"],
    "utilize": ["use", "employ", "apply"],
    "robust": ["strong", "reliable", "solid", "effective"],
    "cutting-edge": ["modern", "latest", "current", "advanced"],
    "state-of-the-art": ["modern", "advanced", "latest"],
    "seamlessly": ["smoothly", "effectively", "efficiently"],
    "synergy": ["cooperation", "collaboration", "teamwork"],
    "paradigm": ["approach", "model", "framework"],
    "proactive": ["forward-thinking", "active", "initiative-driven"],
    "game-changer": ["breakthrough", "innovation", "advancement"],
    "touch base": ["contact", "reach out", "connect"],
    "circle back": ["return to", "follow up on", "revisit"],
    "deep dive": ["detailed analysis", "thorough review", "close look"],
}

# Common AI patterns to detect and vary
AI_PATTERNS = [
    # Overly formal openings
    (r"^Dear Sir or Madam,", ["Dear Hiring Manager,", "Dear Team,"]),
    (r"^I am writing to express", ["I am interested in", "I would like to apply for"]),
    
    # Repetitive sentence starters
    (r"(I am|I have|I can)\s", None),  # Will track frequency
    
    # Buzzword overuse indicators
    (r"\b(leverage|utilize|robust|seamlessly)\b", None),
]


def humanize_text(
    text: str,
    language: str = "en",
    apply_variations: bool = True,
) -> str:
    """
    Humanize AI-generated text by reducing stigmas and adding natural variations.
    
    Args:
        text: Text to humanize
        language: Language code (en, ru)
        apply_variations: Whether to apply random variations
        
    Returns:
        Humanized text
    """
    if not text:
        return text
    
    # For Russian text, use different approach
    if language == "ru":
        return _humanize_russian(text, apply_variations)
    
    # English humanization
    humanized = text
    
    # 1. Replace AI stigma phrases with natural alternatives
    if apply_variations:
        humanized = _replace_stigma_phrases(humanized)
    
    # 2. Add natural imperfections (occasional slight variations)
    if apply_variations:
        humanized = _add_natural_variations(humanized)
    
    # 3. Vary sentence structure
    humanized = _vary_sentence_structure(humanized)
    
    # 4. Remove excessive enthusiasm markers
    humanized = _reduce_enthusiasm(humanized)
    
    return humanized


def _replace_stigma_phrases(text: str) -> str:
    """
    Replace common AI stigma phrases with natural alternatives.
    """
    result = text
    
    for stigma, alternatives in AI_STIGMA_PHRASES.items():
        # Case-insensitive replacement with random alternative
        pattern = re.compile(r'\b' + stigma + r'\b', re.IGNORECASE)
        
        # Find all occurrences
        matches = list(pattern.finditer(result))
        
        # Replace each occurrence with a random alternative
        for match in reversed(matches):  # Reverse to maintain positions
            replacement = random.choice(alternatives)
            # Match the case of original
            if match.group().isupper():
                replacement = replacement.upper()
            elif match.group()[0].isupper():
                replacement = replacement.capitalize()
            
            result = result[:match.start()] + replacement + result[match.end():]
    
    return result


def _add_natural_variations(text: str) -> str:
    """
    Add natural variations to make text less perfect.
    
    Occasionally:
    - Use contractions
    - Add minor stylistic variations
    - Break up overly perfect patterns
    """
    result = text
    
    # Occasionally use contractions (but not too many)
    contractions = {
        "I am": "I'm",
        "I have": "I've",
        "I would": "I'd",
        "cannot": "can't",
        "do not": "don't",
        "will not": "won't",
    }
    
    # Apply contractions randomly (30% chance per occurrence)
    for formal, casual in contractions.items():
        pattern = re.compile(r'\b' + re.escape(formal) + r'\b', re.IGNORECASE)
        matches = list(pattern.finditer(result))
        
        for match in reversed(matches):
            if random.random() < 0.3:  # 30% chance
                result = result[:match.start()] + casual + result[match.end():]
    
    return result


def _vary_sentence_structure(text: str) -> str:
    """
    Vary sentence structure to avoid repetitive patterns.
    """
    lines = text.split('\n')
    
    # Track sentence starters to detect repetition
    sentence_starters = []
    for line in lines:
        line = line.strip()
        if line and len(line) > 10:
            # Get first 2-3 words
            words = line.split()[:3]
            if words:
                starter = ' '.join(words)
                sentence_starters.append(starter)
    
    # If too many sentences start the same way, it's an AI pattern
    # This is just detection - the LLM prompt should handle prevention
    
    return text


def _reduce_enthusiasm(text: str) -> str:
    """
    Reduce excessive enthusiasm markers that are AI stigmas.
    """
    result = text
    
    # Limit exclamation marks (max 1 per paragraph)
    paragraphs = result.split('\n\n')
    processed = []
    
    for para in paragraphs:
        # Count exclamation marks
        exclaim_count = para.count('!')
        
        if exclaim_count > 1:
            # Replace all but the first with periods
            parts = para.split('!')
            processed_para = parts[0] + '!'
            for part in parts[1:]:
                if part.strip():
                    processed_para += '.' + part
            processed.append(processed_para)
        else:
            processed.append(para)
    
    result = '\n\n'.join(processed)
    
    # Reduce excessive capitalization
    result = re.sub(r'\b([A-Z]{3,})\b', lambda m: m.group().capitalize(), result)
    
    return result


def _humanize_russian(text: str, apply_variations: bool) -> str:
    """
    Humanize Russian text with language-specific patterns.
    """
    result = text
    
    # Russian AI stigma phrases - more comprehensive list
    russian_stigmas = {
        "использовать": ["применять", "работать с", "применить"],
        "эффективный": ["результативный", "продуктивный", "успешный", "действенный"],
        "инновационный": ["современный", "передовой", "новый", "актуальный"],
        "оптимизировать": ["улучшить", "доработать", "усовершенствовать", "настроить"],
        "осуществлять": ["выполнять", "проводить", "делать"],
        "реализовать": ["выполнить", "сделать", "создать"],
        "уникальный": ["особенный", "отличительный", "своеобразный"],
        "квалифицированный": ["опытный", "компетентный", "знающий"],
        "высококачественный": ["качественный", "надежный", "хороший"],
        "многофункциональный": ["универсальный", "гибкий"],
    }
    
    if apply_variations:
        for stigma, alternatives in russian_stigmas.items():
            pattern = re.compile(r'\b' + stigma + r'\b', re.IGNORECASE)
            matches = list(pattern.finditer(result))
            
            for match in reversed(matches):
                if random.random() < 0.5:  # 50% chance of replacement
                    replacement = random.choice(alternatives)
                    # Try to match case
                    if match.group()[0].isupper():
                        replacement = replacement.capitalize()
                    result = result[:match.start()] + replacement + result[match.end():]
    
    # Reduce excessive formality (common AI patterns in Russian)
    result = result.replace("Глубокоуважаемый", "Уважаемый")
    result = result.replace("С глубоким уважением", "С уважением")
    result = result.replace("выражаю заинтересованность", "меня заинтересовала")
    result = result.replace("хотел бы выразить", "хочу выразить")
    result = result.replace("имею глубокие знания", "имею хорошие знания")
    
    # Reduce repetitive "я" at sentence starts (common AI pattern)
    lines = result.split('\n')
    processed_lines = []
    for line in lines:
        # Don't modify every line, just occasionally
        if line.strip().lower().startswith('я ') and random.random() < 0.3:
            # Sometimes remove "я" or rephrase
            processed_lines.append(line)
        else:
            processed_lines.append(line)
    
    result = '\n'.join(processed_lines)
    
    return result


def check_ai_score(text: str, language: str = "en") -> dict:
    """
    Calculate an AI detection score for the text.
    
    Returns a dict with:
    - score: 0-100, where higher = more AI-like
    - flags: List of detected AI patterns
    - suggestions: List of improvement suggestions
    """
    flags = []
    suggestions = []
    score = 0
    
    if language == "en":
        # Check for buzzword density
        buzzwords = [
            "leverage", "utilize", "robust", "cutting-edge", "state-of-the-art",
            "seamlessly", "synergy", "paradigm", "proactive", "game-changer"
        ]
        
        word_count = len(text.split())
        buzzword_count = sum(
            len(re.findall(r'\b' + word + r'\b', text, re.IGNORECASE))
            for word in buzzwords
        )
        
        if word_count > 0:
            buzzword_density = buzzword_count / word_count
            if buzzword_density > 0.05:  # More than 5% buzzwords
                score += 30
                flags.append("High buzzword density")
                suggestions.append("Replace buzzwords with natural language")
        
        # Check for repetitive sentence starters
        sentences = re.split(r'[.!?]+', text)
        sentence_starters = [s.strip()[:10] for s in sentences if s.strip()]
        if len(sentence_starters) > 3:
            unique_starters = len(set(sentence_starters))
            if unique_starters / len(sentence_starters) < 0.6:
                score += 20
                flags.append("Repetitive sentence structure")
                suggestions.append("Vary sentence beginnings")
        
        # Check for excessive exclamation marks
        exclaim_count = text.count('!')
        if exclaim_count > 2:
            score += 15
            flags.append("Excessive enthusiasm markers")
            suggestions.append("Reduce exclamation marks")
        
        # Check for overly perfect grammar indicators
        if re.search(r'Dear Sir or Madam', text):
            score += 10
            flags.append("Overly formal opening")
            suggestions.append("Use more natural greeting")
    
    return {
        "score": min(score, 100),
        "flags": flags,
        "suggestions": suggestions,
        "is_likely_ai": score > 50,
    }

