"""
Configuration helpers for the ResumeKit backend.

Values are read from environment variables so that secrets are not
hard-coded in the source tree. A separate .env file can be used in
development together with a dotenv loader if desired.
"""

import os


OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
OPENAI_API_BASE: str | None = os.getenv(
    "OPENAI_API_BASE", "https://api.openai.com/v1"
)

AUTH_SECRET_KEY: str | None = os.getenv("AUTH_SECRET_KEY")
AUTH_TOKEN_EXPIRE_MINUTES: int = int(
    os.getenv("AUTH_TOKEN_EXPIRE_MINUTES", "30")
)
AUTH_LOGIN: str | None = os.getenv("AUTH_LOGIN")
AUTH_PASSWORD: str | None = os.getenv("AUTH_PASSWORD")

# Rate limiting configuration
RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() in {
    "true",
    "1",
    "yes",
}

# RAG (Retrieval-Augmented Generation) configuration
RAG_ENABLED = os.getenv("RAG_ENABLED", "true").lower() in {
    "true",
    "1",
    "yes",
}
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "3"))  # Number of documents to retrieve


