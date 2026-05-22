Project MAYA — Embedding provider integration

This repository contains a minimal embedding wrapper and tests for Project MAYA.

Setup (recommended):
- Create a virtualenv and activate it
- pip install -r requirements-dev.txt
- Set OPENAI_API_KEY if you want to run live OpenAI integration tests

Environment variables
- MAYA_EMBEDDING_PROVIDER: 'local' (default) or 'openai' or 'azure'
- OPENAI_API_KEY: API key for OpenAI/Azure
- OPENAI_MODEL: model name (OpenAI) or deployment id (Azure)
- For Azure: OPENAI_API_BASE, OPENAI_API_VERSION, OPENAI_DEPLOYMENT

Files of interest:
- src/maya/embeddings.py — public entrypoint
- src/maya/adapters/openai_provider.py — OpenAI/Azure adapter
- tests/test_embeddings.py — placeholder unit test (local fallback)
- tests/test_openai_provider.py — live OpenAI integration test (skipped without OPENAI_API_KEY)
