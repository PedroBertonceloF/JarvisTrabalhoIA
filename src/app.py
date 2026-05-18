import sys
import os
from pathlib import Path

# Adiciona o diretório raiz do projeto ao PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

import streamlit as st
from src.storage import Storage
from src.llm import JarvisLLM
from src.rag import RAGService
import PyPDF2

st.set_page_config(page_title="Jarvis Acadêmico", page_icon="🎓", layout="wide")

# Inicializa as instâncias principais
@st.cache_resource
def get_services():
    db_path = os.getenv("SQLITE_DB_PATH", "./data/jarvis.db")
    chroma_path = os.getenv("DB_PATH", "./data/chroma_db")
    
    storage = Storage(db_path)
    rag_service = RAGService(chroma_path)
    llm = JarvisLLM(storage, rag_service)
    
    return llm, storage, rag_service

llm_service, storage_service, rag_service = get_services()

st.title("🎓 Jarvis Acadêmico")
st.subheader("Seu Assistente Pessoal de Estudos")

# Inicializa o histórico de chat se não existir
if "messages" not in st.session_state:
    st.session_state.messages = []

# Função para exibir uma mensagem (tratando tool calls)
def display_message(message):
    if hasattr(message, 'tool_calls') and message.tool_calls:
        with st.chat_message("assistant", avatar="🛠️"):
            for tool in message.tool_calls:
                st.info(f"Chamando ferramenta: `{tool.function.name}` com argumentos: `{tool.function.arguments}`")
    elif getattr(message, 'role', message.get('role', '')) == 'tool':
        with st.chat_message("tool", avatar="✅"):
            st.success(f"Resultado da ferramenta: {message.get('content', '')}")
    else:
        role = getattr(message, 'role', message.get('role', ''))
        content = getattr(message, 'content', message.get('content', ''))
        if content:
            with st.chat_message(role):
                st.markdown(content)

# Exibe as mensagens do histórico
for message in st.session_state.messages:
    display_message(message)

# Input do usuário
if prompt := st.chat_input("Como posso te ajudar hoje?"):
    # Adiciona mensagem do usuário ao histórico (formato dict para OpenAI)
    user_msg = {"role": "user", "content": prompt}
    st.session_state.messages.append(user_msg)
    
    # Exibe mensagem do usuário
    display_message(user_msg)

    # Processa com o LLM (passando o histórico)
    # O LLM pode alterar a lista messages in-place se chamar tools
    with st.spinner("Pensando..."):
        try:
            final_response_content = llm_service.chat(st.session_state.messages)
            
            # Adiciona a resposta final ao histórico
            final_msg = {"role": "assistant", "content": final_response_content}
            st.session_state.messages.append(final_msg)
            
            # Força o recarregamento para exibir os tool calls e a resposta
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao comunicar com o LLM: {e}")

# Sidebar para informações extras e Upload
with st.sidebar:
    st.title("📚 Materiais de Estudo")
    
    disciplina_input = st.text_input("Nome da Disciplina (ex: Inteligência Artificial)")
    uploaded_file = st.file_uploader("Envie seu material (PDF ou TXT)", type=['pdf', 'txt'])
    
    if st.button("Processar e Salvar Material"):
        if uploaded_file is not None and disciplina_input:
            with st.spinner("Lendo e vetorizando o documento..."):
                text_content = ""
                # Processa TXT
                if uploaded_file.name.endswith('.txt'):
                    text_content = uploaded_file.getvalue().decode("utf-8")
                # Processa PDF
                elif uploaded_file.name.endswith('.pdf'):
                    pdf_reader = PyPDF2.PdfReader(uploaded_file)
                    for page in pdf_reader.pages:
                        text_content += page.extract_text() + "\n"
                
                # Envia para o RAG
                if text_content:
                    success = rag_service.ingest_text(
                        text=text_content, 
                        disciplina=disciplina_input, 
                        source_name=uploaded_file.name
                    )
                    if success:
                        st.success(f"Material '{uploaded_file.name}' salvo em '{disciplina_input}'!")
                    else:
                        st.error("Erro ao salvar no banco vetorial.")
                else:
                    st.warning("Não foi possível extrair texto do arquivo.")
        else:
            st.warning("Por favor, preencha a disciplina e anexe um arquivo.")
    
    st.divider()
    st.title("📅 Agenda")
    if st.button("Ver Tarefas Salvas"):
        tasks = storage_service.get_all_tasks()
        st.write(tasks)

