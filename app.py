import streamlit as st
import os
import pandas as pd

# ============================================================
# ⚙️ CONFIG
# ============================================================
st.set_page_config(
    page_title="ELOHIM APS",
    layout="wide"
)

# ============================================================
# 🎨 CSS
# ============================================================
st.markdown("""
<style>
.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
}

div[data-testid="metric-container"] {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.08);
    padding: 16px 18px;
    border-radius: 14px;
}

section[data-testid="stSidebar"] {
    border-right: 1px solid rgba(255,255,255,0.06);
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# 🔐 USUÁRIOS
# ============================================================
USUARIOS = {
    "admin": "1608",
    "eduardo": "aps1608",
    "gerente": "producao"
}

# ============================================================
# 🧠 SESSION
# ============================================================
if "logado" not in st.session_state:
    st.session_state.logado = False

if "usuario" not in st.session_state:
    st.session_state.usuario = ""

# ============================================================
# 🔐 LOGIN
# ============================================================
def tela_login():
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        if os.path.exists("logo.png"):
            st.image("logo.png", width=220)

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

# ============================================================
# 🚫 BLOQUEIO
# ============================================================
if not st.session_state.logado:
    tela_login()
    st.stop()

# ============================================================
# 🎯 SIDEBAR
# ============================================================
with st.sidebar:

    if os.path.exists("logo.png"):
        st.image("logo.png", width=120)

    st.markdown("## ⚙️ ELOHIM APS")
    st.caption("Planejamento e Performance Industrial")

    st.divider()

    st.markdown("### 👤 Sessão")
    st.info(f"Usuário: **{st.session_state.usuario}**")

    st.divider()

    st.markdown("### 🧭 Navegação")

    pagina = st.radio(
        "",
        [
            "📊 Visão Geral",
            "🏭 Carga & Capacidade",
            "📈 OEE & Qualidade",
            "📊 Indicadores"
        ],
        label_visibility="collapsed"
    )

    st.divider()

    if st.button("🚪 Sair", use_container_width=True):
        st.session_state.logado = False
        st.session_state.usuario = ""
        st.rerun()

# ============================================================
# 📊 FUNÇÃO STATUS APS (REAL)
# ============================================================
def status_aps():

    df = st.session_state.get("df", pd.DataFrame())

    if df.empty or "DATA_ENTREGA_APS" not in df.columns or "Data" not in df.columns:
        return "⚪ Sem dados"

    base = df.copy()

    base["Data"] = pd.to_datetime(base["Data"], errors="coerce")
    base["DATA_ENTREGA_APS"] = pd.to_datetime(base["DATA_ENTREGA_APS"], errors="coerce")

    base = base.dropna(subset=["Data", "DATA_ENTREGA_APS"])

    if base.empty:
        return "⚪ Sem dados"

    pv = base.groupby("PV", as_index=False).agg(
        real=("Data", "max"),
        planejado=("DATA_ENTREGA_APS", "min")
    )

    pv["atraso"] = (pv["real"] - pv["planejado"]).dt.days.fillna(0)

    pct = (pv["atraso"] > 0).mean() * 100

    if pct > 20:
        return "🔴 Crítico"
    elif pct > 5:
        return "🟡 Atenção"
    else:
        return "🟢 Controlado"

# ============================================================
# 📊 VISÃO GERAL
# ============================================================
if pagina == "📊 Visão Geral":

    st.title("🚀 ELOHIM APS – Advanced Planning System")

    st.success(f"Bem-vindo, {st.session_state.usuario}")

    st.markdown("## 📌 Painel Central")

    # 🔥 STATUS DINÂMICO
    statusAPS = status_aps()

    k1, k2, k3, k4 = st.columns(4)

    k1.metric("🏭 APS", statusAPS)
    k2.metric("📊 OEE", "🟢 Operando")
    k3.metric("📈 Indicadores", "🟢 Atualizado")
    k4.metric("🔐 Sistema", "🟢 OK")

    # ========================================================
    # 📂 MÓDULOS
    # ========================================================
    st.markdown("---")
    st.subheader("📂 Módulos")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown("### 🏭 Carga & Capacidade")
        if st.button("Abrir", key="btn_carga", use_container_width=True):
            st.switch_page("pages/2_APS_Carga_Capacidade.py")

    with c2:
        st.markdown("### 📈 OEE & Qualidade")
        if st.button("Abrir", key="btn_oee", use_container_width=True):
            st.switch_page("pages/3_APS_OEE_Qualidade.py")

    with c3:
        st.markdown("### 📊 Indicadores")
        if st.button("Abrir", key="btn_ind", use_container_width=True):
            st.switch_page("pages/3_Indicadores_Fabrica.py")

# ============================================================
# 🔁 REDIRECIONAMENTO
# ============================================================
elif pagina == "🏭 Carga & Capacidade":
    st.switch_page("pages/2_APS_Carga_Capacidade.py")

elif pagina == "📈 OEE & Qualidade":
    st.switch_page("pages/3_APS_OEE_Qualidade.py")

elif pagina == "📊 Indicadores":
    st.switch_page("pages/3_Indicadores_Fabrica.py")