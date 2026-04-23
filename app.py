import streamlit as st

st.set_page_config(page_title="ELOHIM APS", layout="wide")

# ============================================================
# 🎨 ESTILO GLOBAL (FUNCIONA NA SIDEBAR NATIVA)
# ============================================================
st.markdown("""
<style>

/* ===== MENU DE PÁGINAS ===== */
[data-testid="stSidebarNav"] ul li a {
    font-size: 18px !important;
    font-weight: 600 !important;
    text-transform: capitalize !important;
    padding: 10px 8px !important;
}

/* item ativo */
[data-testid="stSidebarNav"] ul li a[aria-current="page"] {
    background-color: rgba(0, 150, 255, 0.15);
    border-radius: 8px;
}

/* remove "app" do topo */
[data-testid="stSidebarNav"] > ul > li:first-child {
    display: none;
}

/* espaçamento */
[data-testid="stSidebarNav"] {
    padding-top: 10px;
}

/* sidebar geral */
section[data-testid="stSidebar"] {
    background-color: #111827;
}

/* usuário */
section[data-testid="stSidebar"] .stInfo {
    font-size: 15px;
    border-radius: 10px;
}

/* botão */
section[data-testid="stSidebar"] button {
    border-radius: 8px;
}

/* títulos principais */
h1 {
    font-size: 36px !important;
}

/* cards */
h3 {
    font-size: 22px !important;
}

</style>
""", unsafe_allow_html=True)

# ============================================================
# 🔐 LOGIN
# ============================================================
USUARIOS = {
    "admin": "1608",
    "eduardo": "aps1608",
    "gerente": "producao"
}

if "logado" not in st.session_state:
    st.session_state.logado = False

if "usuario" not in st.session_state:
    st.session_state.usuario = ""

def login():
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        st.title("🔐 ELOHIM APS")

        u = st.text_input("Usuário")
        s = st.text_input("Senha", type="password")

        if st.button("Entrar", use_container_width=True):
            if u in USUARIOS and USUARIOS[u] == s:
                st.session_state.logado = True
                st.session_state.usuario = u
                st.rerun()
            else:
                st.error("Usuário inválido")

if not st.session_state.logado:
    login()
    st.stop()

# ============================================================
# 📌 SIDEBAR (USUÁRIO)
# ============================================================
with st.sidebar:
    st.markdown("## ELOHIM APS")
    st.info(f"👤 {st.session_state.usuario}")

    if st.button("Sair"):
        st.session_state.logado = False
        st.rerun()

# ============================================================
# 🏠 HOME
# ============================================================
st.title("🚀 ELOHIM APS")

st.markdown("### Painel de Módulos")
st.markdown("---")

c1, c2, c3 = st.columns(3)

# ============================================================
# 🏭 CARGA & CAPACIDADE
# ============================================================
with c1:
    st.markdown("### 🏭 Carga & Capacidade")

    st.markdown("""
    - Planejamento de Produção  
    - Capacidade por Máquina  
    - Balanceamento de Carga  
    - Acompanhamento de Prazos  
    - Identificação de Gargalos  
    """)

    if st.button("Abrir", key="aps", use_container_width=True):
        st.switch_page("pages/2_APS_Carga_Capacidade.py")

# ============================================================
# 📈 OEE & QUALIDADE
# ============================================================
with c2:
    st.markdown("### 📈 OEE & Qualidade")

    st.markdown("""
    - Cálculo de OEE  
    - Disponibilidade  
    - Performance  
    - Qualidade  
    - Análise de Perdas  
    """)

    if st.button("Abrir", key="oee", use_container_width=True):
        st.switch_page("pages/3_APS_OEE_Qualidade.py")

# ============================================================
# 📊 INDICADORES
# ============================================================
with c3:
    st.markdown("### 📊 Indicadores")

    st.markdown("""
    - Custos de Manutenção  
    - Indicadores Industriais  
    - Comparativo com Metas  
    - Análise Mensal  
    - Visão Estratégica  
    """)

    if st.button("Abrir", key="indicadores", use_container_width=True):
        st.switch_page("pages/3_Indicadores_Fabrica.py")

st.markdown("---")

st.caption("ELOHIM APS • Sistema de Planejamento e Performance Industrial")