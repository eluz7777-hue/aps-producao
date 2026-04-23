import streamlit as st
import os
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="ELOHIM APS", layout="wide")

# ============================================================
# USUÁRIOS
# ============================================================
USUARIOS = {
    "admin": "1608",
    "eduardo": "aps1608",
    "gerente": "producao"
}

# ============================================================
# SESSION
# ============================================================
if "logado" not in st.session_state:
    st.session_state.logado = False

if "usuario" not in st.session_state:
    st.session_state.usuario = ""

# ============================================================
# LOGIN
# ============================================================
def tela_login():
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        st.title("🔐 ELOHIM APS")

        user = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")

        if st.button("Entrar", use_container_width=True):
            if user in USUARIOS and USUARIOS[user] == senha:
                st.session_state.logado = True
                st.session_state.usuario = user
                st.rerun()
            else:
                st.error("Usuário ou senha inválidos")

if not st.session_state.logado:
    tela_login()
    st.stop()

# ============================================================
# LEITOR INTELIGENTE DE EXCEL (RESOLVE SEU PROBLEMA)
# ============================================================
def ler_excel(path):

    if not os.path.exists(path):
        return None

    for skip in range(5):  # tenta 0 até 4 linhas acima
        try:
            df = pd.read_excel(path, skiprows=skip)

            if df.columns.str.contains("PV", case=False).any() or \
               df.columns.str.contains("OEE", case=False).any() or \
               df.columns.str.contains("NC", case=False).any():
                return df
        except:
            continue

    return None

# ============================================================
# APS
# ============================================================
def calcular_aps():

    df = ler_excel("data/APS_base.xlsx")

    if df is None or "PV" not in df.columns:
        return None

    col_data = next((c for c in df.columns if "data" in c.lower() and "entrega" not in c.lower()), None)
    col_entrega = next((c for c in df.columns if "entrega" in c.lower()), None)

    if not col_data or not col_entrega:
        return None

    df[col_data] = pd.to_datetime(df[col_data], errors="coerce")
    df[col_entrega] = pd.to_datetime(df[col_entrega], errors="coerce")

    df = df.dropna(subset=[col_data, col_entrega])

    pv = df.groupby("PV").agg(real=(col_data,"max"), plan=(col_entrega,"min"))

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

    col = next((c for c in df.columns if "oee" in c.lower()), None)

    if not col:
        return None

    return float(pd.to_numeric(df[col], errors="coerce").dropna().iloc[-1])

# ============================================================
# NC
# ============================================================
def carregar_nc():

    df = ler_excel("data/Indicadores de Qualidade/Indicadores da Qualidade 2026.xlsx")

    if df is None:
        return 0

    col = next((c for c in df.columns if "nc" in c.lower()), None)

    if not col:
        return 0

    return int(pd.to_numeric(df[col], errors="coerce").fillna(0).sum())

# ============================================================
# STATUS
# ============================================================
def status(pct, oee):

    if pct is None:
        return "⚪ Sem dados"

    if pct > 20 or (oee and oee < 60):
        return "🔴 Crítico"
    elif pct > 5:
        return "🟡 Atenção"
    else:
        return "🟢 Controlado"

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("## ELOHIM APS")
    st.info(f"👤 {st.session_state.usuario}")

    pagina = st.radio(
        "",
        ["Visão Geral","Carga & Capacidade","OEE & Qualidade","Indicadores"]
    )

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

    st.success(status(pct, oee))

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric("APS (%)", f"{pct:.1f}%" if pct else "—")
    c2.metric("PVs", total)
    c3.metric("Atrasadas", atrasadas)
    c4.metric("OEE", f"{oee:.1f}%" if oee else "—")
    c5.metric("NC", nc)

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