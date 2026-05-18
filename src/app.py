import streamlit as st

st.set_page_config(page_title="Jarvis Acadêmico", page_icon="🎓", layout="wide")

st.title("🎓 Jarvis Acadêmico")
st.subheader("Seu Assistente Pessoal de Estudos")

# Inicializa o histórico de chat se não existir
if "messages" not in st.session_state:
    st.session_state.messages = []

# Exibe as mensagens do histórico
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Input do usuário
if prompt := st.chat_input("Como posso te ajudar hoje?"):
    # Adiciona mensagem do usuário ao histórico
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Exibe mensagem do usuário
    with st.chat_message("user"):
        st.markdown(prompt)

    # Resposta do Jarvis (Placeholder por enquanto)
    with st.chat_message("assistant"):
        response = f"Olá! Eu recebi sua mensagem: '{prompt}'. Em breve poderei consultar sua agenda e materiais!"
        st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})

# Sidebar para informações extras
with st.sidebar:
    st.title("Configurações")
    st.info("Aqui você poderá gerenciar suas Disciplinas e Materiais em breve.")
