import streamlit as st

st.set_page_config(
    page_title="ELOHIM APS",
    layout="wide"
)

# ===============================
# 🔐 USUÁRIOS
# ===============================
USUARIOS = {
    "admin": "1234",
    "eduardo": "aps2026",
    "gerente": "producao"
}

# ===============================
# SESSION
# ===============================
if "logado" not in st.session_state:
    st.session_state.logado = False

if "usuario" not in st.session_state:
    st.session_state.usuario = ""

# ===============================
# LOGIN
# ===============================
def tela_login():

    st.title("🔐 ELOHIM APS – Acesso Restrito")

    user = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):

        if user in USUARIOS and USUARIOS[user] == senha:
            st.session_state.logado = True
            st.session_state.usuario = user
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos")

# ===============================
# BLOQUEIO
# ===============================
if not st.session_state.logado:
    tela_login()
    st.stop()

# ===============================
# APP LIBERADO
# ===============================
st.title("🚀 ELOHIM APS – Advanced Planning System")

st.success(f"Bem-vindo, {st.session_state.usuario}")

if st.button("Sair"):
    st.session_state.logado = False
    st.rerun()