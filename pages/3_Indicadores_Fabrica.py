import streamlit as st
import pandas as pd

st.set_page_config(page_title="Indicadores da Fábrica", layout="wide")

st.title("📊 Indicadores da Fábrica")
st.caption("Painel estratégico alinhado à ISO 9001")

# ============================================================
# 🔒 BASE APS (APENAS PARA INDICADORES)
# ============================================================

df = st.session_state.get("df", pd.DataFrame())

# ============================================================
# 🚦 VISÃO GERAL (SAÚDE DA FÁBRICA)
# ============================================================

st.subheader("🚦 Saúde da Fábrica")

total_pvs = df["PV"].nunique() if "PV" in df.columns else 0

# 🔴 atraso (único dado vindo do APS)
if "Dias para Entrega" in df.columns:
    atrasos = df[df["Dias para Entrega"] < 0]
    pct_atraso = (len(atrasos) / total_pvs * 100) if total_pvs > 0 else 0
else:
    pct_atraso = 0

# 🟡 classificação simples (ISO mindset)
def classificar(valor):
    if valor > 20:
        return "🔴 Crítico"
    elif valor > 5:
        return "🟡 Atenção"
    else:
        return "🟢 Controlado"

c1, c2 = st.columns(2)

c1.metric("🚨 Atraso (%)", f"{pct_atraso:.1f}%")
c2.metric("Status Produção", classificar(pct_atraso))

st.divider()

# ============================================================
# 📊 ABAS ESTRATÉGICAS
# ============================================================

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "💰 Comercial",
    "🧪 Qualidade",
    "🏭 Produção",
    "🔧 Manutenção",
    "📦 Fornecedores",
    "👷 RH"
])

# ============================================================
# 💰 COMERCIAL
# ============================================================

with tab1:
    st.subheader("💰 Indicadores Comerciais")

    st.info("➡️ Aqui entra: conversão orçamento → pedido, volume, tendência")

# ============================================================
# 🧪 QUALIDADE
# ============================================================

with tab2:
    st.subheader("🧪 Indicadores de Qualidade")

    st.info("➡️ Aqui entra: NC interna, externa, refugo, retrabalho")

# ============================================================
# 🏭 PRODUÇÃO (SÓ ATRASO)
# ============================================================

with tab3:
    st.subheader("🏭 Produção (Indicadores Estratégicos)")

    st.metric("Atraso (%)", f"{pct_atraso:.1f}%")

# ============================================================
# 🔧 MANUTENÇÃO
# ============================================================

with tab4:
    st.subheader("🔧 Indicadores de Manutenção")

    st.info("➡️ Aqui entra: custo manutenção, preventiva vs corretiva")

# ============================================================
# 📦 FORNECEDORES
# ============================================================

with tab5:
    st.subheader("📦 Compras / Fornecedores")

    st.info("➡️ Aqui entra: atraso fornecedor, qualidade fornecedor")

# ============================================================
# 👷 RH
# ============================================================

with tab6:
    st.subheader("👷 Indicadores de RH")

    st.info("➡️ Aqui entra: absenteísmo, treinamento, horas extras")