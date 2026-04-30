import streamlit as st
import os
import pandas as pd

st.set_page_config(page_title="ELOHIM APS", layout="wide")

# ============================================================
# 🔒 DEFINIÇÃO DE CAMINHO
# ============================================================
BASE_PATH = os.path.dirname(os.path.abspath(__file__))

# ============================================================
# 🔥 CRIAÇÃO GARANTIDA DO EXCEL DE BAIXAS
# ============================================================
ARQUIVO_BAIXAS = "APS_BAIXAS_OPERACIONAIS.xlsx"

def garantir_arquivo_baixas_local(base_path):
    os.makedirs(base_path, exist_ok=True)
    caminho = os.path.join(base_path, ARQUIVO_BAIXAS)

    if not os.path.exists(caminho):
        df_vazio = pd.DataFrame(columns=[
            "PV","Cliente","CODIGO_PV","Processo","Horas",
            "Data_Baixa","Usuario","Observacao",
            "Status_Baixa","Data_Estorno","Motivo_Estorno"
        ])
        df_vazio.to_excel(caminho, index=False)

    return caminho

# ============================================================
# 🔍 EXECUÇÃO
# ============================================================
caminho_debug = garantir_arquivo_baixas_local(BASE_PATH)

st.write("📄 Caminho do arquivo de baixas:")
st.write(caminho_debug)

st.write("📌 Arquivo existe?")
st.write(os.path.exists(caminho_debug))


# ============================================================
# 🎨 ESTILO SIDEBAR (FUNCIONA NA NAV NATIVA)
# ============================================================
st.markdown("""
<style>
[data-testid="stSidebarNav"] ul li a {
    font-size: 18px !important;
    font-weight: 600 !important;
    text-transform: capitalize !important;
    padding: 10px 8px !important;
}

[data-testid="stSidebarNav"] ul li a[aria-current="page"] {
    background-color: rgba(0, 150, 255, 0.15);
    border-radius: 8px;
}

[data-testid="stSidebarNav"] > ul > li:first-child {
    display: none;
}

section[data-testid="stSidebar"] {
    background-color: #111827;
}

section[data-testid="stSidebar"] button {
    border-radius: 8px;
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
# 📌 SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("## ELOHIM APS")
    st.info(f"👤 {st.session_state.usuario}")

    if st.button("Sair"):
        st.session_state.logado = False
        st.rerun()

# ============================================================
# 🧱 LOGO (COM PROTEÇÃO DE ERRO)
# ============================================================
st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

caminho_logo = "logo.png"

if os.path.exists(caminho_logo):
    st.image(caminho_logo, width=180)
else:
    st.warning("⚠️ Logo não encontrada (adicione logo.png na raiz do projeto)")

# ============================================================
# 🏠 HOME
# ============================================================
st.title("Painel de Módulos")
st.markdown("---")

c1, c2, c3 = st.columns(3)

# CARGA
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

# OEE
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

# INDICADORES
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