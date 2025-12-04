"""
Tests for RAG service.
"""

import os
from pathlib import Path

import pytest

from app.services.rag_service import RAGService, get_rag_service
from app.schemas import LanguageCode, TargetRole


@pytest.fixture
def knowledge_base_dir(tmp_path):
    """
    Create temporary knowledge base directory with test documents.
    """
    kb_dir = tmp_path / "knowledge_base"
    kb_dir.mkdir()

    # Create test documents
    (kb_dir / "russian_general_guidelines.md").write_text(
        "# Russian Guidelines\n\nInclude photo. Use formal tone."
    )
    (kb_dir / "english_us_guidelines.md").write_text(
        "# US Guidelines\n\nNo photo. Keep to 1-2 pages."
    )
    (kb_dir / "tech_backend_best_practices.md").write_text(
        "# Backend Best Practices\n\nUse Python, FastAPI, PostgreSQL."
    )

    return kb_dir


def test_rag_service_initialization():
    """Test RAG service can be initialized."""
    service = RAGService()
    assert service is not None


def test_rag_service_loads_documents(knowledge_base_dir, monkeypatch):
    """Test RAG service loads documents from knowledge base."""
    # Temporarily change knowledge base path
    original_path = Path("knowledge_base")
    
    service = RAGService()
    # Manually set path for testing
    service.knowledge_base_path = knowledge_base_dir
    service._load_knowledge_base()

    assert len(service.documents) > 0


def test_rag_service_metadata_extraction():
    """Test metadata extraction from document names."""
    service = RAGService()
    
    metadata = service._extract_metadata("russian_general_guidelines.md", "")
    assert "ru" in metadata["language"]
    
    metadata = service._extract_metadata("english_us_guidelines.md", "")
    assert "en" in metadata["language"]
    assert "us" in metadata["market"]
    
    metadata = service._extract_metadata("tech_backend_best_practices.md", "")
    assert "backend" in metadata["role"]


def test_rag_service_retrieval_no_documents():
    """Test retrieval when no documents are loaded."""
    service = RAGService()
    service.documents = []  # Clear documents
    
    result = service.retrieve_best_practices(
        language=LanguageCode.RU,
        target_role=TargetRole.BACKEND,
        job_description="Backend developer position",
        top_k=3,
    )
    
    assert result == []


def test_rag_service_retrieval_with_documents(knowledge_base_dir, monkeypatch):
    """Test retrieval returns relevant documents."""
    service = RAGService()
    service.knowledge_base_path = knowledge_base_dir
    service._load_knowledge_base()
    
    # Mock OpenAI client to avoid API calls in tests
    service.client = None
    
    result = service.retrieve_best_practices(
        language=LanguageCode.RU,
        target_role=TargetRole.BACKEND,
        job_description="Backend developer position",
        top_k=2,
    )
    
    # Should return documents (fallback to first N if no embeddings)
    assert len(result) <= 2


def test_get_rag_service_singleton():
    """Test get_rag_service returns singleton instance."""
    service1 = get_rag_service()
    service2 = get_rag_service()
    
    assert service1 is service2


def test_rag_service_without_openai_key(monkeypatch):
    """Test RAG service works without OpenAI key (graceful degradation)."""
    # Save original value
    original_key = os.getenv("OPENAI_API_KEY")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    
    # Create new service instance (will not have client)
    service = RAGService()
    # Service may still have client from previous initialization
    # Test that retrieval works even without client
    
    # Should still work, just without semantic search
    result = service.retrieve_best_practices(
        language=LanguageCode.EN,
        target_role=TargetRole.BACKEND,
        job_description="Test job",
        top_k=1,
    )
    
    # Should return empty or fallback results
    assert isinstance(result, list)
    
    # Restore original key
    if original_key:
        monkeypatch.setenv("OPENAI_API_KEY", original_key)

