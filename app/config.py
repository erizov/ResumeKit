"""
Configuration helpers for the ResumeKit backend.

Values are read from environment variables so that secrets are not
hard-coded in the source tree. A separate .env file can be used in
development together with a dotenv loader if desired.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env file if it exists
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True)
    print(f"[Config] Loaded .env from: {env_path.absolute()}")
else:
    print(f"[Config] Warning: .env file not found at: {env_path.absolute()}")


OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
OPENAI_API_BASE: str | None = os.getenv(
    "OPENAI_API_BASE", "https://api.openai.com/v1"
)
# Flag to force enabling/disabling OpenAI usage
RESUMEKIT_USE_OPENAI: str = os.getenv("RESUMEKIT_USE_OPENAI", "")

AUTH_SECRET_KEY: str | None = os.getenv("AUTH_SECRET_KEY")
# Token expiration in hours (default: 10 hours)
AUTH_TOKEN_EXPIRE_HOURS: float = float(
    os.getenv("AUTH_TOKEN_EXPIRE_HOURS", "10")
)
# Keep for backward compatibility, but prefer AUTH_TOKEN_EXPIRE_HOURS
AUTH_TOKEN_EXPIRE_MINUTES: int = int(
    os.getenv("AUTH_TOKEN_EXPIRE_MINUTES", str(int(AUTH_TOKEN_EXPIRE_HOURS * 60)))
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

# OpenAI model configuration
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")  # Default to GPT-4 Omni mini


