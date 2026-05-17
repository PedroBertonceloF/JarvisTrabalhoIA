# 3. LLM API Integration Strategy

Date: 2026-05-17

## Status

Accepted

## Context

The specification mandates the use of a specific Gemma 12B model hosted at an endpoint provided by the professor (`https://llm.liaufms.org/v1/gemma-3-12b-it`). However, for development, the team wants to work without relying on the production API to avoid hitting limits or if the endpoint is unavailable, while ensuring that switching to the production API requires zero architectural changes.

The provided endpoint uses an OpenAI-compatible API structure.

## Decision

We will use the official `openai` Python SDK as the sole client for LLM interactions. 

For the development environment, we will use **Ollama** running locally, which provides a drop-in OpenAI-compatible API on `http://localhost:11434/v1`. 

The configuration (Base URL, API Key, Model Name) will be strictly managed via environment variables (`.env` file).

## Consequences

**Positive:**
- **Zero-code switch:** Moving from development (Ollama) to production (Professor's API) requires changing only the `.env` file values.
- **No heavy abstractions:** By using the `openai` SDK directly, we avoid the overhead and complexity of large frameworks like LangChain if they aren't strictly necessary for the tool-calling logic.
- Local development is free and offline-capable.

**Negative:**
- Requires developers to have Ollama installed and a local model (e.g., `llama3` or `gemma`) pulled for local testing.