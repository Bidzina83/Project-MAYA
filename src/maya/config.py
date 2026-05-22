import os

# Configuration for Maya embedding provider
# Use environment variables to avoid committing secrets.

MAYA_EMBEDDING_PROVIDER = os.getenv("MAYA_EMBEDDING_PROVIDER", os.getenv("EMBEDDING_PROVIDER", "local")).lower()

# OpenAI / Azure OpenAI configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("MAYA_OPENAI_API_KEY")
OPENAI_API_TYPE = os.getenv("OPENAI_API_TYPE", "openai")  # 'openai' or 'azure'
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE")
OPENAI_API_VERSION = os.getenv("OPENAI_API_VERSION")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "text-embedding-3-small")
OPENAI_DEPLOYMENT = os.getenv("OPENAI_DEPLOYMENT")  # For Azure deployments

# Fallback embedding dimension (for local placeholder)
FALLBACK_DIM = int(os.getenv("MAYA_FALLBACK_DIM", "16"))
