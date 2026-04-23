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
# FUNÇÃO: LER EXCEL (COM ABAS)
# ============================================================
def ler_excel_seguro(path):

    if not os.path.exists(path):
        return None

    try:
        xls = pd.ExcelFile(path)
        for aba in xls.sheet_names:
            df = xls.parse(aba)
            if not df.empty:
                return df
    except:
        return None

    return None

# ============================================================
# APS
# ============================================================
def calcular_aps():

    df = ler_excel_seguro("data/APS_base.xlsx")

    if df is None or df.empty:
        return None

    if "PV" not in df.columns:
        return None

    col_data = next((c for c in df.columns if "data" in c.lower() and "entrega" not in c.lower()), None)
    col_entrega = next((c for c in df.columns if "entrega" in c.lower()), None)

    if not col_data or not col_entrega:
        return None

    df[col_data] = pd.to_datetime(df[col_data], errors="coerce")
    df[col_entrega] = pd.to_datetime(df[col_entrega], errors="coerce")

    df = df.dropna(subset=[col_data, col_entrega])

    if df.empty:
        return None

    pv = df.groupby("PV", as_index=False).agg(
        real=(col_data, "max"),
        plan=(col_entrega, "min")
    )

    pv["atraso"] = (pv["real"] - pv["plan"]).dt.days.fillna(0)

    total = len(pv)
    atrasadas = (pv["atraso"] > 0).sum()
    pct = (atrasadas / total * 100) if total > 0 else 0

    return pct, total, atrasadas

# ============================================================
# OEE
# ============================================================
def carregar_oee():

    df = ler_excel_seguro("data/Indicadores de Qualidade/OEE - 2026.xlsx")

    if df is None:
        return None

    col = next((c for c in df.columns if "oee" in c.lower()), None)

    if not col:
        return None

    serie = pd.to_numeric(df[col], errors="coerce").dropna()

    if serie.empty:
        return None

    return float(serie.iloc[-1])

# ============================================================
# NC
# ============================================================
def carregar_nc():

    df = ler_excel_seguro("data/Indicadores de Qualidade/Indicadores da Qualidade 2026.xlsx")

    if df is None:
        return 0

    col = next((c for c in df.columns if "nc" in c.lower()), None)

    if not col:
        return 0

    col_ano = next((c for c in df.columns if "ano" in c.lower()), None)

    if col_ano:
        ano = datetime.now().year
        df = df[df[col_ano] == ano]

    return int(pd.to_numeric(df[col], errors="coerce").fillna(0).sum())

# ============================================================
# STATUS
# ============================================================
def status_fabrica(pct, oee):

    score = 0

    if pct is not None:
        if pct > 20: score += 2
        elif pct > 5: score += 1

    if oee is not None:
        if oee < 60: score += 2
        elif oee < 75: score += 1

    if score >= 3:
        return "🔴 Operação em Risco"
    elif score >= 1:
        return "🟡 Atenção"
    else:
        return "🟢 Operação Controlada"

# ============================================================
# HOME
# ============================================================
st.title("🚀 ELOHIM APS")

aps = calcular_aps()
pct, total, atrasadas = aps if aps else (None, 0, 0)

oee = carregar_oee()
nc = carregar_nc()

st.success(status_fabrica(pct, oee))

c1, c2, c3, c4, c5, c6 = st.columns(6)

c1.metric("APS (%)", f"{pct:.1f}%" if pct is not None else "—")
c2.metric("PVs Totais", total)
c3.metric("PVs Atrasadas", atrasadas)
c4.metric("OEE", f"{oee:.1f}%" if oee else "—")
c5.metric("NC Ext.", nc)
c6.metric("Status", "Operação")