import streamlit as st
import os
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="ELOHIM APS", layout="wide")

# ============================================================
# LOGIN
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
# LEITOR ROBUSTO
# ============================================================
def ler_excel(path):

    if not os.path.exists(path):
        return None

    for skip in range(6):
        try:
            df = pd.read_excel(path, skiprows=skip)
            if len(df.columns) > 3:
                return df
        except:
            pass

    return None

# ============================================================
# LOCALIZADOR FLEXÍVEL DE COLUNAS
# ============================================================
def achar_coluna(df, palavras):
    for c in df.columns:
        nome = c.lower()
        if all(p in nome for p in palavras):
            return c
    return None

# ============================================================
# APS
# ============================================================
def calcular_aps():

    df = ler_excel("data/APS_base.xlsx")
    if df is None:
        return None

    col_pv = achar_coluna(df, ["pv"])
    col_data = achar_coluna(df, ["data"])
    col_entrega = achar_coluna(df, ["entrega"])

    if not col_pv or not col_data or not col_entrega:
        return None

    df[col_data] = pd.to_datetime(df[col_data], errors="coerce")
    df[col_entrega] = pd.to_datetime(df[col_entrega], errors="coerce")

    df = df.dropna(subset=[col_data, col_entrega])

    pv = df.groupby(col_pv).agg(
        real=(col_data,"max"),
        plan=(col_entrega,"min")
    )

    pv["atraso"] = (pv["real"] - pv["plan"]).dt.days.fillna(0)

    total = len(pv)
    atrasadas = (pv["atraso"] > 0).sum()
    pct = (atrasadas / total * 100) if total else 0

    return pct, total, atrasadas

# ============================================================
# OEE
# ============================================================
def carregar_oee():

    df = ler_excel("data/Indicadores de Qualidade/OEE - 2026.xlsx")
    if df is None:
        return None

    col = achar_coluna(df, ["oee"])

    if not col:
        return None

    serie = pd.to_numeric(df[col], errors="coerce").dropna()

    return float(serie.iloc[-1]) if not serie.empty else None

# ============================================================
# NC
# ============================================================
def carregar_nc():

    df = ler_excel("data/Indicadores de Qualidade/Indicadores da Qualidade 2026.xlsx")
    if df is None:
        return 0

    col = achar_coluna(df, ["nc"])

    if not col:
        return 0

    return int(pd.to_numeric(df[col], errors="coerce").fillna(0).sum())

# ============================================================
# STATUS LIMPO
# ============================================================
def status_fabrica(pct, oee):

    if pct is None:
        return "⚪ Sem dados", "status-gray"

    if pct > 20 or (oee and oee < 60):
        return "🔴 Crítico", "status-red"
    elif pct > 5:
        return "🟡 Atenção", "status-yellow"
    else:
        return "🟢 Operação Controlada", "status-green"

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
# HOME
# ============================================================
if pagina == "Visão Geral":

    st.title("🚀 ELOHIM APS")

    aps = calcular_aps()
    pct, total, atrasadas = aps if aps else (None,0,0)

    oee = carregar_oee()
    nc = carregar_nc()

    texto, classe = status_fabrica(pct, oee)

    st.markdown(f"""
    <div style="padding:15px;border-radius:12px;background:rgba(0,200,120,0.15);text-align:center;font-size:20px;">
        {texto}
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
