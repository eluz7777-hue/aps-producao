import streamlit as st
import pandas as pd

st.set_page_config(page_title="Indicadores da Fábrica", layout="wide")

st.title("📊 Indicadores da Fábrica")
st.caption("Painel estratégico da operação industrial")

# ============================================================
# 🔒 CARREGAR DADOS DO APS (BASE)
# ============================================================

df = st.session_state.get("df", pd.DataFrame())

if df.empty:
    st.warning("Base do APS não carregada.")
    st.stop()

# ============================================================
# 🚦 VISÃO GERAL (TOP LEVEL)
# ============================================================

st.subheader("🚦 Saúde da Fábrica")

# --- Segurança de colunas ---
df["Horas"] = pd.to_numeric(df.get("Horas", 0), errors="coerce").fillna(0)

total_pvs = df["PV"].nunique() if "PV" in df.columns else 0

# --- Atraso ---
if "Dias para Entrega" in df.columns:
    atrasos = df[df["Dias para Entrega"] < 0]
    pct_atraso = (len(atrasos) / total_pvs * 100) if total_pvs > 0 else 0
else:
    pct_atraso = 0

# --- Gargalo ---
if "Processo" in df.columns:
    proc = df.groupby("Processo")["Horas"].sum()
    gargalo = proc.idxmax() if not proc.empty else "N/D"
else:
    gargalo = "N/D"

# --- KPI CARDS ---
c1, c2, c3 = st.columns(3)

c1.metric("🚨 Atraso (%)", f"{pct_atraso:.1f}%")
c2.metric("🔥 Gargalo", gargalo)
c3.metric("📦 PVs", total_pvs)

# ============================================================
# 📊 ABAS ESTRATÉGICAS
# ============================================================

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "💰 Comercial",
    "🏭 Produção",
    "🧪 Qualidade",
    "🔧 Manutenção",
    "👷 RH"
])

# ============================================================
# 🏭 PRODUÇÃO (BASEADO NO APS)
# ============================================================

with tab2:

    st.subheader("🏭 Visão de Produção")

    carga_total = df["Horas"].sum()

    st.metric("Carga Total (h)", f"{carga_total:,.1f}")

    if "Processo" in df.columns:
        backlog = df.groupby("Processo")["Horas"].sum().sort_values(ascending=False)
        st.bar_chart(backlog)

# ============================================================
# 💰 COMERCIAL (VAMOS PLUGAR DEPOIS)
# ============================================================

with tab1:
    st.info("Indicadores comerciais serão conectados aqui")

# ============================================================
# 🧪 QUALIDADE
# ============================================================

with tab3:
    st.info("Indicadores de qualidade serão conectados aqui")

# ============================================================
# 🔧 MANUTENÇÃO
# ============================================================

with tab4:
    st.info("Indicadores de manutenção serão conectados aqui")

# ============================================================
# 👷 RH
# ============================================================

with tab5:
    st.info("Indicadores de RH serão conectados aqui")