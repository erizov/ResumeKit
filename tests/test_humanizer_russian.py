"""
Tests for Russian language humanization.
"""

import pytest

from app.services.humanizer import humanize_text, check_ai_score

# Set default timeout for all tests in this file (5 seconds)
pytestmark = pytest.mark.timeout(5)


class TestRussianHumanization:
    """Test Russian language-specific humanization."""

    def test_russian_stigma_replacement(self) -> None:
        """Test replacement of Russian AI stigma phrases."""
        text = "Я буду использовать инновационный подход для оптимизации эффективных решений."
        
        # Run multiple times due to randomness
        results = [humanize_text(text, language="ru") for _ in range(5)]
        
        # At least some should have replacements
        has_replacements = any(
            "применять" in r or "современный" in r or "улучшить" in r
            for r in results
        )
        assert has_replacements, "Should replace some Russian stigmas"

    def test_russian_formality_reduction(self) -> None:
        """Test reduction of excessive formality in Russian."""
        text = "Глубокоуважаемый господин, выражаю заинтересованность. С глубоким уважением."
        result = humanize_text(text, language="ru")
        
        # Should reduce formality
        assert "Глубокоуважаемый" not in result
        assert "Уважаемый" in result
        assert "С глубоким уважением" not in result

    def test_russian_ai_score(self) -> None:
        """Test AI score calculation for Russian text."""
        # High AI stigma text
        ai_text = (
            "Я буду использовать инновационный подход для оптимизации. "
            "Я имею глубокие знания. Я осуществляю реализацию. "
            "Я являюсь высококвалифицированным специалистом."
        )
        
        score = check_ai_score(ai_text, language="ru")
        
        # Should return valid score structure
        assert "score" in score
        assert "flags" in score
        assert "suggestions" in score
        assert isinstance(score["score"], (int, float))
        assert score["score"] >= 0

    def test_russian_natural_text(self) -> None:
        """Test that natural Russian text has low AI score."""
        natural_text = (
            "Работаю с Python больше 5 лет. Создавал несколько веб-приложений "
            "с использованием FastAPI. Мой опыт включает работу над backend-сервисами "
            "и базами данных."
        )
        
        score = check_ai_score(natural_text, language="ru")
        
        # Should have reasonable score
        assert score["score"] >= 0
        assert isinstance(score["flags"], list)

    def test_russian_humanization_preserves_content(self) -> None:
        """Test that humanization preserves key content in Russian."""
        text = "У меня 10 лет опыта работы с Python и Java в компании BNY Mellon."
        result = humanize_text(text, language="ru")
        
        # Should preserve key information
        assert "10 лет" in result or "10" in result
        assert "Python" in result
        assert "Java" in result
        assert "BNY Mellon" in result

    def test_russian_cover_letter_humanization(self) -> None:
        """Test humanization of Russian cover letter."""
        cover_letter = """Уважаемые господа,

Я буду использовать инновационный подход для эффективной реализации ваших проектов. 
Я имею глубокие знания в области backend-разработки. Я осуществляю оптимизацию 
высококачественных решений.

С глубоким уважением,
Евгений"""
        
        result = humanize_text(cover_letter, language="ru")
        
        # Should reduce AI patterns
        ai_phrases = ["использовать", "инновационный", "осуществляю", "высококачественных"]
        replaced_count = sum(1 for phrase in ai_phrases if phrase in result.lower())
        
        # Should have replaced at least some phrases
        assert replaced_count < len(ai_phrases)
        
        # Should reduce formality
        assert "С глубоким уважением" not in result

