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
# LOAD APS
# ============================================================
def carregar_aps_df():
    path = "data/APS_base.xlsx"
    if not os.path.exists(path):
        return pd.DataFrame()
    return pd.read_excel(path)

# ============================================================
# APS CALCULO (CORRETO)
# ============================================================
def calcular_aps(df):

    if df.empty or "PV" not in df.columns:
        return None

    # identifica colunas automaticamente
    col_data = next((c for c in df.columns if "data" in c.lower() and "entrega" not in c.lower()), None)
    col_entrega = next((c for c in df.columns if "entrega" in c.lower()), None)

    if not col_data or not col_entrega:
        return None

    base = df.copy()

    base[col_data] = pd.to_datetime(base[col_data], errors="coerce")
    base[col_entrega] = pd.to_datetime(base[col_entrega], errors="coerce")

    base = base.dropna(subset=[col_data, col_entrega])

    if base.empty:
        return None

    pv = base.groupby("PV", as_index=False).agg(
        real=(col_data, "max"),
        plan=(col_entrega, "min")
    )

    pv["atraso_dias"] = (pv["real"] - pv["plan"]).dt.days.fillna(0)

    total_pv = len(pv)
    atrasadas = (pv["atraso_dias"] > 0).sum()
    pct = (atrasadas / total_pv) * 100 if total_pv > 0 else 0

    return pct, total_pv, atrasadas

# ============================================================
# OEE
# ============================================================
def carregar_oee():

    path = "data/Indicadores de Qualidade/OEE - 2026.xlsx"

    if not os.path.exists(path):
        return None

    df = pd.read_excel(path)

    col = next((c for c in df.columns if "oee" in c.lower()), None)

    if not col:
        return None

    serie = pd.to_numeric(df[col], errors="coerce").dropna()

    if serie.empty:
        return None

    return float(serie.iloc[-1])

# ============================================================
# NC EXTERNAS
# ============================================================
def carregar_nc():

    path = "data/Indicadores de Qualidade/Indicadores da Qualidade 2026.xlsx"

    if not os.path.exists(path):
        return 0

    df = pd.read_excel(path)

    col_nc = next((c for c in df.columns if "nc" in c.lower()), None)

    if not col_nc:
        return 0

    # filtra ano se existir
    col_ano = next((c for c in df.columns if "ano" in c.lower()), None)

    if col_ano:
        ano_atual = datetime.now().year
        df = df[df[col_ano] == ano_atual]

    return int(pd.to_numeric(df[col_nc], errors="coerce").fillna(0).sum())

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
        return "🔴 Fábrica em Risco", "status-red"
    elif score >= 1:
        return "🟡 Atenção", "status-yellow"
    else:
        return "🟢 Operação Controlada", "status-green"

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
        st.session_state.usuario = ""
        st.rerun()

# ============================================================
# HOME
# ============================================================
if pagina == "Visão Geral":

    st.title("🚀 ELOHIM APS")

    df_aps = carregar_aps_df()
    aps = calcular_aps(df_aps)

    pct, total_pv, atrasadas = aps if aps else (None, 0, 0)

    oee = carregar_oee()
    nc = carregar_nc()

    texto, classe = status_fabrica(pct, oee)

    st.markdown(f"""
    <div class="status-box {classe}">
        {texto}
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4, c5, c6 = st.columns(6)

    c1.metric("APS (%)", f"{pct:.1f}%" if pct else "—")
    c2.metric("PVs Totais", total_pv)
    c3.metric("PVs Atrasadas", atrasadas)
    c4.metric("OEE", f"{oee:.1f}%" if oee else "—")
    c5.metric("NC Ext.", nc)
    c6.metric("Status", texto.split(" ")[1])

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