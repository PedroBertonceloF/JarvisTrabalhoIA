# 1. Use Streamlit for the User Interface

Date: 2026-05-17

## Status

Accepted

## Context

The system ("Jarvis Acadêmico") requires a way for the user to interact with the AI assistant. The specification mentions that a "interface gráfica" (GUI) is a differential (bonus) criteria. The core requirements include chat interactions, displaying study plans, managing calendar events and tasks, and handling document uploads (RAG materials).

We need to choose a UI framework that allows us to meet these requirements efficiently while demonstrating the bonus criteria. The options considered were:
1. **CLI (Command Line Interface):** Simplest to implement, but doesn't fulfill the "diferencial" GUI criteria.
2. **Custom Web App (FastAPI + React/Vue):** High flexibility, but significant overhead in managing a separate frontend and backend, state management, and API design, which might detract from the core AI requirements within the timeframe.
3. **Streamlit:** A Python-based framework specifically designed for building data/AI applications quickly.

## Decision

We will use **Streamlit** as the application interface.

## Consequences

**Positive:**
- Rapid development of a functional and presentable graphical interface, fulfilling the "diferencial" criteria.
- Everything is written in Python, allowing seamless integration with the LLM API, LangChain/LlamaIndex (if used), and local databases without needing REST APIs.
- Built-in components for chat (`st.chat_message`, `st.chat_input`), file uploads (`st.file_uploader`), and data display.

**Negative:**
- Streamlit's execution model (rerunning the script top-to-bottom on interaction) requires careful state management (`st.session_state`) for maintaining chat history, loaded materials, and tool call logs.
- Less customizability compared to a full React application regarding complex visual layouts.