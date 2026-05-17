# Product Requirements Document: Jarvis Acadêmico

## Problem Statement

Students struggle to organize their academic lives across multiple tools. They have schedules and tasks scattered in one place, while their study materials (PDFs, notes) are disconnected in another. When preparing for exams, they lack an intelligent system that can synthezise their materials, test their knowledge, and help them plan their study sessions based on their upcoming schedule and past performance.

## Solution

"Jarvis Acadêmico" is an AI-powered academic assistant that unifies scheduling, task management, and document analysis. Powered by a Large Language Model (LLM) and Retrieval-Augmented Generation (RAG), Jarvis allows students to chat naturally to manage their calendar, query the contents of their study materials, generate personalized study plans, and engage in active-recall review sessions to improve learning.

## User Stories

1. As a student, I want to chat with an AI assistant in a visual interface, so that I can easily interact with my academic data.
2. As a student, I want to upload study materials (PDFs, TXTs) and assign them to a specific "Disciplina", so that the AI can access my coursework.
3. As a student, I want to ask questions about my uploaded materials (e.g., "Explique regressão logística"), so that I can get summaries and explanations based directly on my texts.
4. As a student, I want to add new events (like classes or exams) to my Agenda, so that the assistant knows my schedule.
5. As a student, I want to query my Agenda (e.g., "O que tenho hoje?"), so that I can plan my day.
6. As a student, I want to add specific actionable tasks (Tarefas) to my Agenda, so that I can keep track of assignments.
7. As a student, I want to mark a Tarefa as completed, so that I can track my progress.
8. As a student, I want to ask Jarvis to generate a "Plano de Estudos", so that I get a structured study proposal combining my upcoming events, open tasks, and relevant materials.
9. As a student, I want the option to convert the generated "Plano de Estudos" into actual Tasks in my Agenda, so that I can track the execution of the plan.
10. As a student, I want to request a "Sessão de Revisão" for a specific Disciplina and its Materials, so that the AI asks me questions to test my knowledge (active recall).
11. As a student, I want the system to identify topics I struggled with during the Sessão de Revisão, so that it can provide a "Recomendação de Revisão" for future study sessions.
12. As a system evaluator, I want to see visual logs of the tools the LLM decides to call, so that I can verify the tool-calling mechanism is working correctly.

## Implementation Decisions

- **UI Framework:** Streamlit will be used for the graphical interface, handling chat state and file uploads.
- **LLM Integration:** The OpenAI Python SDK will be used as the client. During development, it will connect to a local **Ollama** instance. For production, the base URL and API key will be swapped via `.env` to connect to the professor's Gemma 12B API.
- **Tool Calling:** The LLM will autonomously decide when to invoke tools. The system will implement at least 5 tools: `consultar_agenda`, `listar_tarefas`, `adicionar_tarefa`, `concluir_tarefa`, and `buscar_material_rag`.
- **RAG Stack:** `ChromaDB` will be used for local persistent vector storage. `sentence-transformers` (specifically `all-MiniLM-L6-v2`) will be used to generate embeddings locally.
- **Storage Module:** A local SQLite database (or structured JSON) will be used to persist the `Agenda` (containing both `Evento` and `Tarefa` records).
- **Deep Modules:**
  - `storage`: Encapsulates all DB/file I/O for events and tasks.
  - `rag`: Encapsulates document chunking, embedding generation, and vector search.
  - `learning`: Encapsulates the prompts and business logic for Study Plans, Review Sessions, and Recommendations.
  - `llm`: Encapsulates the OpenAI client and the tool-execution loop.
  - `ui`: Streamlit presentation layer.

## Testing Decisions

- Tests should verify external behavior and data integrity, not implementation details.
- **Automated Tests Scope:**
  - **`storage` module:** Unit tests will verify that tasks and events can be created, retrieved accurately by date/status, and updated. Tests will use an in-memory SQLite DB or temporary JSON files to avoid side effects.
  - **`rag` module:** Unit tests will verify that text chunking works as expected and that the ChromaDB client can successfully ingest text and retrieve the most relevant chunks given a mock query.
- **Prior Art:** We will use standard Python `unittest` or `pytest` frameworks. Tests will focus on verifying the contracts of the deep modules before integrating them into the LLM orchestration layer.

## Out of Scope

- User authentication or multi-user support (the system is single-user/local).
- Complex frontend frameworks (React, Vue) or separate backend REST APIs (everything runs within the Streamlit lifecycle).
- Web scraping or fetching materials from the internet automatically (materials must be uploaded by the user).
- Using external cloud vector databases (e.g., Pinecone) or paid embedding APIs (e.g., OpenAI text-embedding-ada-002).
- Implementing a Huffman compression/decompression algorithm for file uploads (may be considered later as a bonus/differential for `.txt` files, but is out of scope for the core requirements).

## Further Notes

- The project has a strict dataset requirement: 10 academic documents must be included in a `/data` folder with documentation detailing their origin, limitations, and the chunking strategy used.
- A final evaluation report detailing 10 specific questions, the retrieved context, the answer, and an error analysis of 3 failures is mandatory for delivery.