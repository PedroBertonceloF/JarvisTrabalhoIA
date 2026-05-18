import streamlit as st
import os
from src.storage import Storage
from src.llm import JarvisLLM

st.set_page_config(page_title="Jarvis Acadêmico", page_icon="🎓", layout="wide")

# Inicializa as instâncias principais
@st.cache_resource
def get_services():
    db_path = os.getenv("SQLITE_DB_PATH", "./data/jarvis.db")
    storage = Storage(db_path)
    llm = JarvisLLM(storage)
    return llm, storage

llm_service, storage_service = get_services()

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

# Sidebar para informações extras
with st.sidebar:
    st.title("Configurações")
    st.info("Aqui você poderá gerenciar suas Disciplinas e Materiais em breve.")
    
    st.divider()
    st.subheader("Estado do Banco")
    if st.button("Ver Tarefas Salvas"):
        tasks = storage_service.get_all_tasks()
        st.write(tasks)

