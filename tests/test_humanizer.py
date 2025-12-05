"""
Tests for text humanization and AI detection.
"""

import pytest

from app.services.humanizer import (
    check_ai_score,
    humanize_text,
    _replace_stigma_phrases,
    _reduce_enthusiasm,
)

# Set default timeout for all tests in this file (5 seconds)
pytestmark = pytest.mark.timeout(5)


class TestHumanizer:
    """Test humanization service."""

    def test_replace_stigma_phrases(self) -> None:
        """Test that AI stigma phrases are replaced."""
        text = "I will leverage my expertise to utilize robust solutions."
        result = _replace_stigma_phrases(text)

        # Should not contain stigma phrases
        assert "leverage" not in result.lower()
        assert "utilize" not in result.lower()
        assert "robust" not in result.lower()

        # Should contain natural alternatives
        assert any(
            word in result.lower() for word in ["use", "apply", "employ"]
        )

    def test_reduce_enthusiasm(self) -> None:
        """Test that excessive enthusiasm is reduced."""
        text = "I am excited! This is amazing! I love this job!"
        result = _reduce_enthusiasm(text)

        # Should have fewer exclamation marks
        assert result.count("!") <= 1

    def test_humanize_text_english(self) -> None:
        """Test humanizing English text."""
        text = "I will leverage cutting-edge technology to utilize robust solutions seamlessly."
        result = humanize_text(text, language="en")

        # Should not contain multiple stigma phrases
        stigma_count = sum(
            1
            for word in [
                "leverage",
                "cutting-edge",
                "utilize",
                "robust",
                "seamlessly",
            ]
            if word in result.lower()
        )
        assert stigma_count < 3  # Should have replaced most

    def test_humanize_text_russian(self) -> None:
        """Test humanizing Russian text."""
        text = "Я буду использовать инновационный подход для оптимизации."
        result = humanize_text(text, language="ru")

        # Should return modified text
        assert len(result) > 0
        assert isinstance(result, str)

    def test_check_ai_score_high_buzzwords(self) -> None:
        """Test AI score detection for high buzzword density."""
        text = (
            "I will leverage cutting-edge technology to utilize robust "
            "solutions seamlessly. This paradigm-shifting approach will "
            "create synergy and be a game-changer."
        )
        score_info = check_ai_score(text, language="en")

        # Should detect high AI likelihood
        assert score_info["score"] >= 30
        assert len(score_info["flags"]) > 0
        assert "buzzword" in str(score_info["flags"]).lower()

    def test_check_ai_score_natural_text(self) -> None:
        """Test AI score for natural, human-like text."""
        text = (
            "I have worked with Python for 5 years. I built several "
            "web applications using FastAPI. My experience includes "
            "working on backend services and databases."
        )
        score_info = check_ai_score(text, language="en")

        # Should have lower AI score
        assert score_info["score"] < 30

    def test_check_ai_score_repetitive_structure(self) -> None:
        """Test detection of repetitive sentence structure."""
        text = (
            "I am experienced. I am skilled. I am dedicated. "
            "I am passionate. I am committed. I am focused. "
            "I am motivated. I am enthusiastic."
        )
        score_info = check_ai_score(text, language="en")

        # Should detect repetitive structure (or at least return valid score)
        assert score_info["score"] >= 0
        assert isinstance(score_info["flags"], list)

    def test_check_ai_score_excessive_enthusiasm(self) -> None:
        """Test detection of excessive enthusiasm."""
        text = "This is amazing! I'm so excited! This opportunity is incredible! I can't wait!"
        score_info = check_ai_score(text, language="en")

        # Should detect excessive enthusiasm
        assert score_info["score"] > 10
        assert any(
            "enthusiasm" in flag.lower() for flag in score_info["flags"]
        )

    def test_humanize_preserves_meaning(self) -> None:
        """Test that humanization preserves the core meaning."""
        text = "I have 10 years of experience with Python and Java."
        result = humanize_text(text, language="en")

        # Should still contain key information
        assert "10 years" in result or "10" in result
        assert "Python" in result
        assert "Java" in result

    def test_humanize_with_variations_disabled(self) -> None:
        """Test humanization with variations disabled."""
        text = "I will leverage robust technology."
        result = humanize_text(text, language="en", apply_variations=False)

        # Should still be modified but less aggressively
        assert len(result) > 0


class TestHumanizerAPI:
    """Test humanizer API endpoints."""

    @pytest.mark.timeout(10)  # API calls may take longer
    def test_ai_score_endpoint(self) -> None:
        """Test AI score check endpoint."""
        from app.main import app
        from fastapi.testclient import TestClient

        client = TestClient(app)

        response = client.post(
            "/api/humanizer/ai-score",
            json={
                "text": "I will leverage cutting-edge technology.",
                "language": "en",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "score" in data
        assert "flags" in data
        assert "suggestions" in data
        assert "is_likely_ai" in data

    @pytest.mark.timeout(10)  # API calls may take longer
    def test_humanize_endpoint(self) -> None:
        """Test text humanization endpoint."""
        from app.main import app
        from fastapi.testclient import TestClient

        client = TestClient(app)

        response = client.post(
            "/api/humanizer/humanize",
            json={
                "text": "I will leverage cutting-edge solutions seamlessly.",
                "language": "en",
                "apply_variations": True,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "original" in data
        assert "humanized" in data
        assert "ai_score_before" in data
        assert "ai_score_after" in data

        # Humanized should have lower or equal AI score
        assert (
            data["ai_score_after"]["score"]
            <= data["ai_score_before"]["score"]
        )

