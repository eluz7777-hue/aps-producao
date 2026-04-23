import streamlit as st
import os
import pandas as pd
from datetime import datetime

# ============================================================
# CONFIG
# ============================================================
st.set_page_config(page_title="ELOHIM APS", layout="wide")

# ============================================================
# CSS
# ============================================================
st.markdown("""
<style>
.block-container {padding-top: 2rem;}

.status-box {
    padding: 18px;
    border-radius: 14px;
    text-align: center;
    font-size: 24px;
    font-weight: 600;
    margin-bottom: 15px;
}

.status-green {background: rgba(0,200,120,0.12);}
.status-yellow {background: rgba(255,200,0,0.12);}
.status-red {background: rgba(255,80,80,0.12);}
.status-gray {background: rgba(200,200,200,0.08);}
</style>
""", unsafe_allow_html=True)

# ============================================================
# USERS
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
# AUTOLOAD APS
# ============================================================
if "df" not in st.session_state:
    caminho = "data/APS_base.xlsx"
    if os.path.exists(caminho):
        try:
            st.session_state["df"] = pd.read_excel(caminho)
        except:
            st.session_state["df"] = pd.DataFrame()

df = st.session_state.get("df", pd.DataFrame())

# ============================================================
# APS
# ============================================================
def calcular_aps():

    if df.empty:
        return None

    if "Data" not in df.columns or "DATA_ENTREGA_APS" not in df.columns:
        return None

    base = df.copy()

    base["Data"] = pd.to_datetime(base["Data"], errors="coerce")
    base["DATA_ENTREGA_APS"] = pd.to_datetime(base["DATA_ENTREGA_APS"], errors="coerce")

    base = base.dropna(subset=["Data", "DATA_ENTREGA_APS"])

    if base.empty:
        return None

    pv = base.groupby("PV", as_index=False).agg(
        real=("Data","max"),
        plan=("DATA_ENTREGA_APS","min")
    )

    pv["atraso"] = (pv["real"] - pv["plan"]).dt.days.fillna(0)

    pct = (pv["atraso"] > 0).mean()*100
    total = len(pv)

    return pct, total

def status_aps(pct):

    if pct is None:
        return "⚪", "Sem dados", "status-gray"

    if pct > 20:
        return "🔴", "Crítico", "status-red"
    elif pct > 5:
        return "🟡", "Atenção", "status-yellow"
    else:
        return "🟢", "Controlado", "status-green"

# ============================================================
# OEE
# ============================================================
def carregar_oee():

    path = "data/Indicadores_oee/oee.xlsx"

    if not os.path.exists(path):
        return None

    df_oee = pd.read_excel(path)

    col = [c for c in df_oee.columns if "oee" in c.lower()]

    if not col:
        return None

    return float(df_oee[col[0]].dropna().iloc[-1])

# ============================================================
# NC EXTERNAS (CORRIGIDO)
# ============================================================
def carregar_nc():

    path = "data/Indicadores de Qualidade/Indicadores da Qualidade 2026.xlsx"

    if not os.path.exists(path):
        return 0

    df_nc = pd.read_excel(path)

    # tenta encontrar coluna de NC automaticamente
    col_nc = [c for c in df_nc.columns if "nc" in c.lower()]

    if not col_nc:
        return 0

    col = col_nc[0]

    # se tiver coluna de ano
    if "ano" in [c.lower() for c in df_nc.columns]:
        col_ano = [c for c in df_nc.columns if "ano" in c.lower()][0]
        ano_atual = datetime.now().year
        df_nc = df_nc[df_nc[col_ano] == ano_atual]

    return int(df_nc[col].sum())

# ============================================================
# STATUS GERAL
# ============================================================
def status_fabrica(pct_aps, oee):

    score = 0

    if pct_aps is not None:
        if pct_aps > 20:
            score += 2
        elif pct_aps > 5:
            score += 1

    if oee is not None:
        if oee < 60:
            score += 2
        elif oee < 75:
            score += 1

    if score >= 3:
        return "🔴", "Fábrica em Risco", "status-red"
    elif score >= 1:
        return "🟡", "Atenção Operacional", "status-yellow"
    else:
        return "🟢", "Operação Controlada", "status-green"

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:

    st.markdown("## ELOHIM APS")
    st.caption("Performance Industrial")

    st.info(f"👤 {st.session_state.usuario}")

    pagina = st.radio(
        "",
        ["Visão Geral","Carga & Capacidade","OEE & Qualidade","Indicadores"],
        label_visibility="collapsed"
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
    pct, total_pv = aps if aps else (None, 0)

    oee = carregar_oee()
    nc = carregar_nc()

    icon, texto, classe = status_fabrica(pct, oee)

    st.markdown(f"""
    <div class="status-box {classe}">
        {icon} {texto}
    </div>
    """, unsafe_allow_html=True)

    aps_icon, aps_txt, _ = status_aps(pct)

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric("APS", f"{aps_icon} {aps_txt}")
    c2.metric("OEE", f"{oee:.1f}%" if oee else "—")
    c3.metric("Atrasos (%)", f"{pct:.1f}%" if pct else "—")
    c4.metric("Total PVs", total_pv)
    c5.metric("NC Ext. (Ano)", nc)

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