import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="ELOHIM APS", layout="wide")

# ============================================================
# LOGIN (MANTIDO)
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

        if st.button("Entrar"):
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
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("## ELOHIM APS")
    st.info(f"👤 {st.session_state.usuario}")

    pagina = st.radio("", [
        "Visão Geral",
        "Carga & Capacidade",
        "OEE & Qualidade",
        "Indicadores"
    ])

    if st.button("Sair"):
        st.session_state.logado = False
        st.rerun()

# ============================================================
# 🔥 APS DIRETO DO ARQUIVO (SEM SESSION_STATE)
# ============================================================
def calcular_aps_direto():

    caminho = "PV.xlsx"

    if not os.path.exists(caminho):
        return None, 0, 0

    try:
        df = pd.read_excel(caminho)
    except:
        return None, 0, 0

    df.columns = df.columns.astype(str).str.upper().str.strip()

    if "PV" not in df.columns or "ENTREGA" not in df.columns:
        return None, 0, 0

    df["ENTREGA"] = pd.to_datetime(df["ENTREGA"], errors="coerce", dayfirst=True)

    df = df.dropna(subset=["ENTREGA"])

    hoje = pd.Timestamp.today().normalize()

    pv = df.groupby("PV").agg(
        entrega=("ENTREGA", "min")
    )

    pv["atraso"] = (hoje - pv["entrega"]).dt.days
    pv["atrasado"] = pv["atraso"] > 0

    total = len(pv)
    atrasadas = pv["atrasado"].sum()

    pct = (atrasadas / total * 100) if total else 0

    return pct, total, atrasadas

# ============================================================
# OEE
# ============================================================
def carregar_oee():

    caminho = "data/Indicadores de Qualidade/OEE - 2026.xlsx"

    if not os.path.exists(caminho):
        return None

    try:
        df = pd.read_excel(caminho)
    except:
        return None

    df.columns = df.columns.astype(str).str.upper()

    for col in df.columns:
        if "OEE" in col:
            serie = pd.to_numeric(df[col], errors="coerce").dropna()
            if not serie.empty:
                return float(serie.iloc[-1])

    return None

# ============================================================
# NC
# ============================================================
def carregar_nc():

    caminho = "data/Indicadores de Qualidade/Indicadores da Qualidade 2026.xlsx"

    if not os.path.exists(caminho):
        return 0

    try:
        df = pd.read_excel(caminho)
    except:
        return 0

    df.columns = df.columns.astype(str).str.upper()

    for col in df.columns:
        if "NC" in col:
            return int(pd.to_numeric(df[col], errors="coerce").fillna(0).sum())

    return 0

# ============================================================
# STATUS
# ============================================================
def status(pct):

    if pct is None:
        return "⚪ Sem dados"

    if pct > 15:
        return "🔴 Crítico"
    elif pct > 5:
        return "🟡 Atenção"
    else:
        return "🟢 Controlado"

# ============================================================
# HOME
# ============================================================
if pagina == "Visão Geral":

    st.title("🚀 ELOHIM APS")

    pct, total, atrasadas = calcular_aps_direto()
    oee = carregar_oee()
    nc = carregar_nc()

    st.markdown(f"""
    <div style="padding:15px;border-radius:12px;background:rgba(0,200,120,0.15);text-align:center;font-size:20px;">
        {status(pct)}
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric("APS (%)", f"{pct:.1f}%" if pct else "—")
    c2.metric("PVs Totais", total)
    c3.metric("PVs Atrasadas", atrasadas)
    c4.metric("OEE", f"{oee:.1f}%" if oee else "—")
    c5.metric("NC Ext.", nc)

    st.markdown("---")

    c1, c2, c3 = st.columns(3)

    if c1.button("🏭 Carga & Capacidade"):
        st.switch_page("pages/2_APS_Carga_Capacidade.py")

    if c2.button("📈 OEE & Qualidade"):
        st.switch_page("pages/3_APS_OEE_Qualidade.py")

    if c3.button("📊 Indicadores"):
        st.switch_page("pages/3_Indicadores_Fabrica.py")

# ============================================================
# REDIRECIONAMENTO
# ============================================================
elif pagina == "Carga & Capacidade":
    st.switch_page("pages/2_APS_Carga_Capacidade.py")

elif pagina == "OEE & Qualidade":
    st.switch_page("pages/3_APS_OEE_Qualidade.py")

elif pagina == "Indicadores":
    st.switch_page("pages/3_Indicadores_Fabrica.py")