# Implementation Plan: Jarvis Acadêmico

## Overview
We are building "Jarvis Acadêmico", an AI-powered academic assistant for students. It integrates an LLM (Gemma 12B via OpenAI API, using Ollama for local dev) with RAG (local ChromaDB + sentence-transformers) for querying study materials. It also manages a schedule (Agenda) and tasks (Tarefas), and includes active learning features like Review Sessions and Study Recommendations. The UI will be built with Streamlit.

## Architecture Decisions
- **UI Framework:** Streamlit (ADR 0001) for rapid, Python-native GUI development.
- **RAG Stack:** ChromaDB + `sentence-transformers/all-MiniLM-L6-v2` locally (ADR 0002) for free and local vector storage.
- **LLM Integration:** OpenAI Python SDK, allowing zero-code switching between local Ollama during development and the Professor's API for production via `.env` (ADR 0003).

## Task List

### Phase 1: Foundation & Project Setup
- [ ] **Task 1: Initialize Project & Dependencies**
  - Create `requirements.txt` with `streamlit`, `openai`, `chromadb`, `sentence-transformers`, `python-dotenv`, `pandas` (if needed for CSV/SQLite).
  - Setup `.env.example` with `OPENAI_BASE_URL`, `OPENAI_API_KEY`, `MODEL_NAME`.
  - Create the basic directory structure (`src/`, `data/`, `docs/`).
- [ ] **Task 2: Basic Streamlit UI Shell**
  - Create `src/app.py`.
  - Implement the basic Streamlit chat interface (`st.chat_message`, `st.chat_input`).
  - Add a sidebar for basic navigation or file uploading placeholders.

### Checkpoint: Foundation
- [ ] Can run `streamlit run src/app.py`.
- [ ] UI shows a chat interface.

### Phase 2: Core Data & LLM
- [ ] **Task 3: Local Storage Setup (Agenda/Tarefas)**
  - Implement `src/storage.py` using SQLite (or JSON) to store `Evento` and `Tarefa`.
  - Create functions to add, list, and complete tasks/events.
- [ ] **Task 4: LLM Client & Tool Calling Loop**
  - Implement `src/llm.py` wrapping the `openai` client.
  - Create the main tool-calling loop (handling `tool_calls` from the LLM and passing results back).
  - Define initial tools schemas (e.g., `consultar_agenda`, `adicionar_tarefa`).
- [ ] **Task 5: Wire LLM to Streamlit**
  - Update `src/app.py` to send chat history to the LLM and stream/display responses.
  - Implement visual tool execution logs in the UI (as required by the spec).

### Checkpoint: Core Features
- [ ] User can chat with the LLM.
- [ ] LLM can successfully call `adicionar_tarefa` and it saves to local storage.
- [ ] Tool calls are logged visibly in the interface.

### Phase 3: RAG Implementation
- [ ] **Task 6: Material Ingestion (Chunking & Embedding)**
  - Implement `src/rag.py` to handle document loading (PDF/TXT), chunking (e.g., recursive character text splitter), and generating embeddings using `sentence-transformers`.
  - Save to ChromaDB.
- [ ] **Task 7: RAG Retrieval Tool**
  - Implement `buscar_material_rag` tool that queries ChromaDB.
  - Integrate this tool into the LLM's available tools.
- [ ] **Task 8: UI for Material Upload**
  - Add file uploader in Streamlit sidebar to allow users to upload materials and assign them to a `Disciplina`.

### Checkpoint: RAG Complete
- [ ] User can upload a PDF.
- [ ] User can ask "Quais são os principais pontos do material X?" and get a grounded answer.

### Phase 4: Learning Features & Integration
- [ ] **Task 9: Plano de Estudos (Study Plan)**
  - Implement a specific prompt/tool for generating a study plan combining Agenda and Materiais.
  - Add a button in the UI to optionally "Accept" the plan and insert its tasks into the Agenda.
- [ ] **Task 10: Sessão de Revisão (Interactive Review)**
  - Implement a dedicated UI mode or chat flow for Review Sessions.
  - The LLM generates questions based on selected materials and evaluates user answers.
- [ ] **Task 11: Recomendação de Revisão**
  - Implement logic to track difficult topics from Review Sessions.
  - Integrate these recommendations into the standard chat or Study Plan generation.

### Checkpoint: Features Complete
- [ ] All 5 required tools are implemented and working.
- [ ] Both learning features (Review Session, Recommendation) are functional.

### Phase 5: Evaluation & Delivery
- [ ] **Task 12: System Evaluation & Error Analysis**
  - Run the 10 required queries against the system.
  - Document the retrieval, generation, and classification (correct/partial/incorrect) in a Markdown report.
  - Identify 3 failures and document causes/solutions.
- [ ] **Task 13: Dataset Formatting**
  - Gather 10 academic documents into `data/`.
  - Write dataset documentation (origin, limitations, chunking strategy).
- [ ] **Task 14: Final Polish & README**
  - Ensure code has basic tests, error handling, and separation of concerns.
  - Write detailed `README.md` with instructions and list of AI tools used.

### Checkpoint: Ready for Submission
- [ ] All mandatory items from the spec are accounted for.
- [ ] Code is clean and explained.

## Risks and Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| Streamlit state loss on rerun | High | Rigorously use `st.session_state` for chat history and tool logs. |
| Local embedding slow on older PCs | Medium | Use `all-MiniLM-L6-v2` which is optimized and small. |
| Tool calling failure with Gemma API | High | Ensure tool schemas strictly follow OpenAI spec. Provide clear system prompts. |

## Open Questions
- Do we need PyPDF2 or pdfplumber for PDF extraction, or something simpler? (Will start with PyMuPDF or PyPDF2).