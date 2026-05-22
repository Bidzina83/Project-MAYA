import os
from typing import List

try:
    # openai 2.x uses the new OpenAI client
    from openai import OpenAI
except Exception:
    OpenAI = None

from .. import config


def embed_text_openai(text: str) -> List[float]:
    """Embed text using OpenAI (or Azure OpenAI) via openai>=1.0 client.

    Uses the new OpenAI client API: client = OpenAI(); client.embeddings.create(...)

    Raises RuntimeError on missing configuration or missing client.
    """
    if not text:
        return [0.0]

    if OpenAI is None:
        raise RuntimeError("openai package (new client) is not installed in the environment")

    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("MAYA_OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set")

    api_type = os.getenv("OPENAI_API_TYPE", "openai").lower()
    model = os.getenv("OPENAI_MODEL", config.OPENAI_MODEL)

    # Build client kwargs
    client_kwargs = {"api_key": api_key}

    if api_type == "azure":
        api_base = os.getenv("OPENAI_API_BASE") or config.OPENAI_API_BASE
        api_version = os.getenv("OPENAI_API_VERSION") or config.OPENAI_API_VERSION
        deployment = os.getenv("OPENAI_DEPLOYMENT") or config.OPENAI_DEPLOYMENT or model
        if not api_base:
            raise RuntimeError("OPENAI_API_BASE must be set for Azure OpenAI")
        if not api_version:
            raise RuntimeError("OPENAI_API_VERSION must be set for Azure OpenAI")
        client_kwargs.update({"api_base": api_base, "api_type": "azure", "api_version": api_version})
        client = OpenAI(**client_kwargs)
        resp = client.embeddings.create(model=deployment, input=text)
    else:
        # Standard OpenAI
        client = OpenAI(**client_kwargs)
        resp = client.embeddings.create(model=model, input=text)

    emb = resp.data[0].embedding
    return [float(x) for x in emb]
