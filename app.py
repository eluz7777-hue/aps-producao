import streamlit as st
import os

st.set_page_config(
    page_title="ELOHIM APS",
    layout="wide"
)

# ===============================
# 🔐 USUÁRIOS
# ===============================
USUARIOS = {
    "admin": "1608",
    "eduardo": "aps1608",
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
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        if os.path.exists("logo.png"):
            st.image("logo.png", width=140)

        st.title("🔐 ELOHIM APS")
        st.subheader("Acesso Restrito ao Sistema")

        user = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")

        if st.button("Entrar", use_container_width=True):
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
# SIDEBAR
# ===============================
st.sidebar.markdown("## 👤 Sessão")
st.sidebar.write(f"Usuário: **{st.session_state.usuario}**")

st.sidebar.markdown("---")
st.sidebar.markdown("## 📊 Módulos")

pagina = st.sidebar.radio(
    "Navegação",
    [
        "🏠 Visão Geral",
        "🏭 Carga & Capacidade",
        "📊 OEE & Qualidade"
    ]
)

st.sidebar.markdown("---")

if st.sidebar.button("🚪 Sair", use_container_width=True):
    st.session_state.logado = False
    st.session_state.usuario = ""
    st.rerun()

# ===============================
# HOME / VISÃO GERAL
# ===============================
if pagina == "🏠 Visão Geral":

    col1, col2 = st.columns([1, 6])

    with col1:
        if os.path.exists("logo.png"):
            st.image("logo.png", width=100)

    with col2:
        st.title("🚀 ELOHIM APS – Advanced Planning System")
        st.success(f"Bem-vindo, {st.session_state.usuario}")

    st.markdown("## 📌 Painel Central do Sistema")
    st.markdown("Selecione um módulo no menu lateral para navegar.")

    k1, k2, k3 = st.columns(3)

    k1.metric("🏭 Módulo APS", "Ativo")
    k2.metric("📊 Módulo OEE", "Ativo")
    k3.metric("🔐 Segurança", "OK")

    st.markdown("---")

    st.subheader("📂 Módulos Disponíveis")

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("### 🏭 APS | Carga & Capacidade")
        st.write("Planejamento industrial com análise de:")
        st.write("- carga por processo")
        st.write("- capacidade produtiva")
        st.write("- gargalos")
        st.write("- fila")
        st.write("- atraso por PV")
        st.write("- simulação operacional")

        if st.button("Abrir APS Carga & Capacidade", use_container_width=True):
            st.switch_page("pages/2_APS_Carga_Capacidade.py")

    with c2:
        st.markdown("### 📊 APS | OEE & Qualidade")
        st.write("Gestão de performance industrial com:")
        st.write("- OEE geral")
        st.write("- disponibilidade")
        st.write("- performance")
        st.write("- qualidade")
        st.write("- refugo")
        st.write("- semáforo executivo")

        if st.button("Abrir APS OEE & Qualidade", use_container_width=True):
            st.switch_page("pages/3_APS_OEE_Qualidade.py")

# ===============================
# REDIRECIONAMENTO
# ===============================
elif pagina == "🏭 Carga & Capacidade":
    st.switch_page("pages/2_APS_Carga_Capacidade.py")

elif pagina == "📊 OEE & Qualidade":
    st.switch_page("pages/3_APS_OEE_Qualidade.py")