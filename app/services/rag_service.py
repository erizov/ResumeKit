"""
RAG (Retrieval-Augmented Generation) service for resume tailoring.

This service retrieves relevant best practices and guidelines from a
knowledge base to enhance resume tailoring prompts.
"""

import os
from pathlib import Path
from typing import List

import numpy as np
from openai import OpenAI

from ..config import OPENAI_API_KEY, OPENAI_API_BASE
from ..schemas import LanguageCode, TargetRole


class RAGService:
    """
    Service for retrieving relevant best practices from knowledge base.
    """

    def __init__(self):
        """
        Initialize RAG service.

        Loads knowledge base documents and creates embeddings if needed.
        """
        self.client = None
        if OPENAI_API_KEY:
            self.client = OpenAI(
                api_key=OPENAI_API_KEY,
                base_url=OPENAI_API_BASE
            )

        self.knowledge_base_path = Path("knowledge_base")
        self.embeddings_cache: dict[str, List[float]] = {}
        self.documents: List[dict] = []

        # Load knowledge base on initialization
        self._load_knowledge_base()

    def _load_knowledge_base(self) -> None:
        """
        Load all markdown documents from knowledge base directory.

        Each document is indexed with metadata for filtering.
        """
        if not self.knowledge_base_path.exists():
            # Knowledge base not set up yet, skip
            return

        for file_path in self.knowledge_base_path.glob("*.md"):
            try:
                content = file_path.read_text(encoding="utf-8")
                metadata = self._extract_metadata(file_path.name, content)

                self.documents.append(
                    {
                        "path": str(file_path),
                        "name": file_path.stem,
                        "content": content,
                        "metadata": metadata,
                    }
                )
            except Exception as e:
                print(f"Warning: Failed to load {file_path}: {e}")

    def _extract_metadata(
        self, filename: str, content: str
    ) -> dict[str, str | List[str]]:
        """
        Extract metadata from document filename and content.

        Returns metadata dict with language, market, industry, role, category.
        """
        metadata: dict[str, str | List[str]] = {
            "language": [],
            "market": [],
            "industry": [],
            "role": [],
            "category": "general",
        }

        filename_lower = filename.lower()

        # Extract language
        if "russian" in filename_lower:
            metadata["language"].append("ru")
        if "english" in filename_lower or "us" in filename_lower or "uk" in filename_lower:
            metadata["language"].append("en")

        # Extract market
        if "russian" in filename_lower:
            metadata["market"].append("ru")
        if "us" in filename_lower:
            metadata["market"].append("us")
        if "uk" in filename_lower:
            metadata["market"].append("uk")
        if "general" in filename_lower or not any(
            m in filename_lower for m in ["russian", "us", "uk"]
        ):
            metadata["market"].append("general")

        # Extract industry
        if "tech" in filename_lower:
            metadata["industry"].append("tech")
        if "backend" in filename_lower:
            metadata["industry"].append("tech")
            metadata["role"].append("backend")
        if "fullstack" in filename_lower:
            metadata["industry"].append("tech")
            metadata["role"].append("fullstack")
        if "gpt" in filename_lower or "engineer" in filename_lower:
            metadata["industry"].append("tech")
            metadata["role"].append("gpt_engineer")

        # Extract category
        if "guidelines" in filename_lower or "best_practices" in filename_lower:
            metadata["category"] = "guidelines"
        elif "ats" in filename_lower:
            metadata["category"] = "ats"
        elif "formatting" in filename_lower or "examples" in filename_lower:
            metadata["category"] = "formatting"
        else:
            metadata["category"] = "general"

        # Default to general if no specific matches
        if not metadata["language"]:
            metadata["language"] = ["general"]
        if not metadata["market"]:
            metadata["market"] = ["general"]
        if not metadata["industry"]:
            metadata["industry"] = ["general"]

        return metadata

    def _get_embedding(self, text: str) -> List[float]:
        """
        Get embedding for text using OpenAI API.

        Caches embeddings to avoid redundant API calls.
        """
        if not self.client:
            return []

        # Check cache
        cache_key = text[:100]  # Use first 100 chars as cache key
        if cache_key in self.embeddings_cache:
            return self.embeddings_cache[cache_key]

        try:
            response = self.client.embeddings.create(
                model="text-embedding-3-small",
                input=text,
            )
            embedding = response.data[0].embedding
            self.embeddings_cache[cache_key] = embedding
            return embedding
        except Exception as e:
            print(f"Warning: Failed to get embedding: {e}")
            return []

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors.
        """
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0

        vec1_np = np.array(vec1)
        vec2_np = np.array(vec2)

        dot_product = np.dot(vec1_np, vec2_np)
        norm1 = np.linalg.norm(vec1_np)
        norm2 = np.linalg.norm(vec2_np)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))

    def retrieve_best_practices(
        self,
        language: LanguageCode,
        target_role: TargetRole,
        job_description: str,
        top_k: int = 3,
    ) -> List[str]:
        """
        Retrieve relevant best practices based on language, role, and job description.

        Args:
            language: Target language for resume
            target_role: Target role (backend, fullstack, gpt_engineer)
            job_description: Job description text for semantic search
            top_k: Number of documents to retrieve

        Returns:
            List of relevant document contents (best practices)
        """
        if not self.documents:
            return []

        # Filter by metadata (exact match)
        language_str = language.value
        role_str = target_role.value

        filtered_docs = []
        for doc in self.documents:
            metadata = doc["metadata"]

            # Check language match
            language_match = (
                language_str in metadata.get("language", [])
                or "general" in metadata.get("language", [])
            )

            # Check role match
            role_match = (
                role_str in metadata.get("role", [])
                or "general" in metadata.get("role", [])
                or not metadata.get("role", [])
            )

            if language_match and role_match:
                filtered_docs.append(doc)

        # If no filtered docs, use all docs
        if not filtered_docs:
            filtered_docs = self.documents

        # Semantic search on job description
        if job_description and self.client:
            try:
                job_embedding = self._get_embedding(job_description[:1000])

                # Calculate similarity scores
                scored_docs = []
                for doc in filtered_docs:
                    # Use document title/name for embedding (faster)
                    doc_embedding = self._get_embedding(doc["name"] + " " + doc["content"][:500])
                    similarity = self._cosine_similarity(job_embedding, doc_embedding)
                    scored_docs.append((similarity, doc))

                # Sort by similarity and get top K
                scored_docs.sort(key=lambda x: x[0], reverse=True)
                top_docs = [doc for _, doc in scored_docs[:top_k]]

                return [doc["content"] for doc in top_docs]
            except Exception as e:
                print(f"Warning: Semantic search failed: {e}")

        # Fallback: return first top_k documents
        return [doc["content"] for doc in filtered_docs[:top_k]]


# Global RAG service instance
_rag_service: RAGService | None = None


def get_rag_service() -> RAGService:
    """
    Get or create global RAG service instance.
    """
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service

