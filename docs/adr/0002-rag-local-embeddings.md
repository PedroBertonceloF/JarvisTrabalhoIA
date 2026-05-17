# 2. Local Embeddings and Vector Storage for RAG

Date: 2026-05-17

## Status

Accepted

## Context

The system requires a RAG (Retrieval-Augmented Generation) implementation to allow the assistant to answer questions based on academic materials. The specification requires chunking, generating embeddings, and retrieval. It explicitly states that free tools are allowed.

While the LLM is mandated to be Gemma 12B via a specific API, the embedding model and vector database are not specified. We need a solution that is free, easy to set up, and reliable.

## Decision

We will use:
- **Embedding Model:** `sentence-transformers/all-MiniLM-L6-v2` (run locally).
- **Vector Database:** `ChromaDB` (running in local persistent mode).

## Consequences

**Positive:**
- Completely free and open-source.
- Runs entirely locally, removing the need for external API keys for embeddings.
- `all-MiniLM-L6-v2` is fast and lightweight, suitable for academic texts on standard hardware.
- `ChromaDB` handles local persistence easily without requiring a separate database server installation.

**Negative:**
- Generating embeddings locally requires some CPU/RAM resources, though `MiniLM` is very lightweight.
- The repository will need to manage the local ChromaDB database directory (needs to be ignored in `.gitignore`).