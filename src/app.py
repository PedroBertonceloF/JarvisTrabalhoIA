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
from src.learning import LearningService
from src.tools import ToolRegistry
from src.controller import AppController
import json

st.set_page_config(page_title="Jarvis Acadêmico", page_icon="🎓", layout="wide")

# Inicializa as instâncias principais
def get_services():
    db_path = os.getenv("SQLITE_DB_PATH", "./data/jarvis.db")
    chroma_path = os.getenv("DB_PATH", "./data/chroma_db")
    
    storage = Storage(db_path)
    rag_service = RAGService(chroma_path)
    learning = LearningService(rag_service)
    registry = ToolRegistry()
    
    # O LLM precisa do registry
    llm = JarvisLLM(registry)
    
    # O Controller agora orquestra o registro das ferramentas
    controller = AppController(rag_service, learning, llm, storage)
    controller.register_tools(registry)
    
    return llm, storage, rag_service, learning, controller

llm_service, storage_service, rag_service, learning_service, controller = get_services()

st.title("🎓 Jarvis Acadêmico")
st.subheader("Seu Assistente Pessoal de Estudos")

# Inicializa o histórico de chat se não existir
if "messages" not in st.session_state:
    st.session_state.messages = []

if "review_mode" not in st.session_state:
    st.session_state.review_mode = False
    st.session_state.review_question = ""
    st.session_state.review_context = ""
    st.session_state.review_disciplina = ""

if "pending_plan" not in st.session_state:
    st.session_state.pending_plan = None

# Função para exibir uma mensagem (tratando tool calls)
def display_message(message):
    role = message.get('role', '')
    content = message.get('content', '')
    
    if role == "tool_call_request":
        with st.chat_message("assistant", avatar="🛠️"):
            st.info(f"Chamando ferramenta: `{message.get('tool_name')}` com argumentos: `{message.get('tool_args')}`")
    elif role == "tool_call_result":
        with st.chat_message("tool", avatar="✅"):
            st.success(f"Resultado da ferramenta: {content}")
    else:
        if content:
            with st.chat_message(role):
                st.markdown(content)

# Exibe as mensagens do histórico
for message in st.session_state.messages:
    display_message(message)

if st.session_state.review_mode:
    st.info(f"**Modo Revisão Ativo:** {st.session_state.review_disciplina}")
    st.markdown(f"### Pergunta:\n{st.session_state.review_question}")
    
    if answer := st.chat_input("Sua resposta:"):
        st.write(f"**Você:** {answer}")
        with st.spinner("Avaliando resposta..."):
            evaluation = controller.evaluate_review_answer(
                st.session_state,
                answer
            )
            
            # Formatação do feedback com base no status
            status = evaluation.get("status", "UNKNOWN")
            feedback = evaluation.get("feedback", "Sem feedback.")
            topic = evaluation.get("topic", "Desconhecido")
            
            if status == "CORRECT":
                st.success(f"✅ **Correto!** {feedback}")
            elif status == "PARTIAL":
                st.warning(f"⚠️ **Parcialmente Correto.** {feedback}")
            else:
                st.error(f"❌ **Incorreto.** {feedback}")
                
            st.session_state.review_mode = False # Encerra após uma pergunta por simplicidade
            if st.button("Continuar no chat normal"):
                st.rerun()

else:
    # Input do usuário normal
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
                
                # Tenta extrair plano de estudos via controller
                st.session_state.pending_plan = controller.extract_study_plan(final_response_content)

                # Adiciona a resposta final ao histórico
                final_msg = {"role": "assistant", "content": final_response_content}
                st.session_state.messages.append(final_msg)
                
                # Força o recarregamento para exibir os tool calls e a resposta
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao comunicar com o LLM: {e}")

# Exibe botão de salvar plano se houver um pendente
if st.session_state.pending_plan:
    st.info("💡 **Plano de Estudos Detectado!** Você pode salvar essas tarefas na sua agenda.")
    if st.button("✅ Aceitar Plano e Salvar na Agenda"):
        count = controller.accept_study_plan(st.session_state.pending_plan)
        st.success(f"{count} tarefas adicionadas com sucesso!")
        st.session_state.pending_plan = None
        st.rerun()
    if st.button("❌ Descartar Sugestões"):
        st.session_state.pending_plan = None
        st.rerun()

# Sidebar para informações extras e Upload
with st.sidebar:
    st.title("📚 Materiais de Estudo")
    
    disciplina_input = st.text_input("Nome da Disciplina (ex: Inteligência Artificial)")
    uploaded_file = st.file_uploader("Envie seu material (PDF ou TXT)", type=['pdf', 'txt'])
    
    if st.button("Processar e Salvar Material"):
        if uploaded_file is not None and disciplina_input:
            with st.spinner("Lendo e vetorizando o documento..."):
                success, message = controller.process_material(
                    filename=uploaded_file.name,
                    content=uploaded_file.getvalue(),
                    disciplina=disciplina_input
                )
                if success:
                    st.success(message)
                else:
                    st.error(message)
        else:
            st.warning("Por favor, preencha a disciplina e anexe um arquivo.")
    
    st.divider()
    st.title("🧠 Sessão de Revisão")
    review_disciplina_input = st.text_input("Disciplina para revisar")
    
    if st.button("Iniciar Revisão"):
        with st.spinner("Preparando sessão..."):
            success, message = controller.start_review_session(
                review_disciplina_input, 
                st.session_state
            )
            if success:
                st.rerun()
            else:
                st.warning(message)
            
    if st.session_state.review_mode:
        if st.button("Encerrar Revisão"):
            st.session_state.review_mode = False
            st.rerun()
            
    st.divider()
    st.title("💡 Recomendações de Estudo")
    dificuldades = storage_service.get_difficulties()
    if dificuldades:
        st.write("Tópicos que você teve dificuldade recentemente:")
        for d in dificuldades[:5]: # Mostra as 5 mais recentes
            st.warning(f"**{d['disciplina']}**: {d['topic']}")
    else:
        st.info("Nenhuma dificuldade registrada ainda. Faça uma Sessão de Revisão!")
    
    st.divider()
    st.title("📅 Agenda")
    if st.button("Ver Tarefas Salvas"):
        tasks = storage_service.get_all_tasks()
        st.write(tasks)

