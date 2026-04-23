import streamlit as st
import os
import pandas as pd

# ============================================================
# ⚙️ CONFIG
# ============================================================
st.set_page_config(page_title="ELOHIM APS", layout="wide")

# ============================================================
# 🎨 CSS (clean e profissional)
# ============================================================
st.markdown("""
<style>
.block-container {padding-top: 2rem;}

.status-box {
    padding: 20px;
    border-radius: 16px;
    text-align: center;
    font-size: 28px;
    font-weight: bold;
    margin-bottom: 10px;
}

.status-green {background: rgba(0,200,120,0.15);}
.status-yellow {background: rgba(255,200,0,0.15);}
.status-red {background: rgba(255,80,80,0.15);}
.status-gray {background: rgba(200,200,200,0.1);}
</style>
""", unsafe_allow_html=True)

# ============================================================
# 🔐 USERS
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
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        if os.path.exists("logo.png"):
            st.image("logo.png", width=200)

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
# 🔄 AUTOLOAD APS (REMOVE "SEM DADOS")
# ============================================================
if "df" not in st.session_state:
    caminho_aps = "data/APS_base.xlsx"

    if os.path.exists(caminho_aps):
        try:
            df_auto = pd.read_excel(caminho_aps)
            st.session_state["df"] = df_auto
        except:
            st.session_state["df"] = pd.DataFrame()

# ============================================================
# 📊 STATUS APS
# ============================================================
def status_aps():

    df = st.session_state.get("df", pd.DataFrame())

    if df.empty or "DATA_ENTREGA_APS" not in df.columns or "Data" not in df.columns:
        return "⚪", "Sem base"

    base = df.copy()
    base["Data"] = pd.to_datetime(base["Data"], errors="coerce")
    base["DATA_ENTREGA_APS"] = pd.to_datetime(base["DATA_ENTREGA_APS"], errors="coerce")
    base = base.dropna(subset=["Data", "DATA_ENTREGA_APS"])

    if base.empty:
        return "⚪", "Sem dados"

    pv = base.groupby("PV", as_index=False).agg(
        real=("Data","max"),
        plan=("DATA_ENTREGA_APS","min")
    )

    pv["atraso"] = (pv["real"] - pv["plan"]).dt.days.fillna(0)
    pct = (pv["atraso"] > 0).mean()*100

    if pct > 20:
        return "🔴", "Crítico"
    elif pct > 5:
        return "🟡", "Atenção"
    else:
        return "🟢", "Controlado"

# ============================================================
# 🧠 STATUS CONSOLIDADO
# ============================================================
def status_fabrica():

    aps_icon, aps_status = status_aps()

    if aps_icon == "🔴":
        return "🔴", "Fábrica em Risco", "status-red"
    elif aps_icon == "🟡":
        return "🟡", "Atenção Operacional", "status-yellow"
    elif aps_icon == "🟢":
        return "🟢", "Operação Controlada", "status-green"
    else:
        return "⚪", "Aguardando Dados", "status-gray"

# ============================================================
# 🎯 SIDEBAR
# ============================================================
with st.sidebar:

    if os.path.exists("logo.png"):
        st.image("logo.png", width=110)

    st.markdown("## ELOHIM APS")
    st.caption("Performance Industrial")

    st.divider()

    st.info(f"👤 {st.session_state.usuario}")

    pagina = st.radio(
        "",
        [
            "Visão Geral",
            "Carga & Capacidade",
            "OEE & Qualidade",
            "Indicadores"
        ],
        label_visibility="collapsed"
    )

    st.divider()

    if st.button("Sair"):
        st.session_state.logado = False
        st.rerun()

# ============================================================
# 🏠 HOME
# ============================================================
if pagina == "Visão Geral":

    st.title("🚀 ELOHIM APS")

    # 🔥 STATUS GERAL (DESTAQUE)
    icon, texto, classe = status_fabrica()

    st.markdown(f"""
    <div class="status-box {classe}">
        {icon} {texto}
    </div>
    """, unsafe_allow_html=True)

    # 🔎 KPIs ENXUTOS
    aps_icon, aps_txt = status_aps()

    c1, c2 = st.columns(2)

    c1.metric("APS", f"{aps_icon} {aps_txt}")
    c2.metric("Sistema", "🟢 OK")

    # ========================================================
    # 📂 MÓDULOS
    # ========================================================
    st.markdown("---")
    st.subheader("Módulos")

    c1, c2, c3 = st.columns(3)

    with c1:
        if st.button("🏭 Carga & Capacidade", key="carga"):
            st.switch_page("pages/2_APS_Carga_Capacidade.py")

    with c2:
        if st.button("📈 OEE & Qualidade", key="oee"):
            st.switch_page("pages/3_APS_OEE_Qualidade.py")

    with c3:
        if st.button("📊 Indicadores", key="ind"):
            st.switch_page("pages/3_Indicadores_Fabrica.py")

# ============================================================
# 🔁 REDIRECIONAMENTO
# ============================================================
elif pagina == "Carga & Capacidade":
    st.switch_page("pages/2_APS_Carga_Capacidade.py")

elif pagina == "OEE & Qualidade":
    st.switch_page("pages/3_APS_OEE_Qualidade.py")

elif pagina == "Indicadores":
    st.switch_page("pages/3_Indicadores_Fabrica.py")