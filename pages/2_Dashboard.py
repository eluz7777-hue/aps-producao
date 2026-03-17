import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")

st.title("📊 DASHBOARD - APS ELOHIM")

# ===============================
# VERIFICA SE TEM DADOS DO APS
# ===============================

if "dados_dashboard" not in st.session_state:
    st.warning("⚠️ Execute o APS primeiro")
    st.stop()

df = st.session_state["dados_dashboard"]

total_horas = st.session_state.get("total_horas", 0)
gargalo = st.session_state.get("gargalo", "N/A")
ordens = st.session_state.get("ordens", 0)

# ===============================
# KPIs
# ===============================

col1, col2, col3, col4 = st.columns(4)

col1.metric("⏱️ Total de Horas", f"{round(total_horas,2)} h")
col2.metric("🚨 Gargalo", gargalo)
col3.metric("📦 Ordens", ordens)
col4.metric("⚙️ Ocupação Média", "Calculando...")

# ===============================
# CARGA POR PROCESSO
# ===============================

st.subheader("Carga por Processo")

carga_processo = df.groupby("Processo")["Duração (h)"].sum().reset_index()

fig = px.bar(
    carga_processo,
    x="Processo",
    y="Duração (h)",
    text="Duração (h)",
    color="Processo"
)

st.plotly_chart(fig, use_container_width=True)

# ===============================
# PERÍODO
# ===============================

st.subheader("Análise por Período")

periodo = st.selectbox(
    "Selecione o período",
    ["Diário", "Semanal", "Mensal"]
)

df["Inicio"] = pd.to_datetime(df["Início"])

if periodo == "Diário":
    agrupado = df.groupby(df["Inicio"].dt.date)["Duração (h)"].sum().reset_index()
elif periodo == "Semanal":
    agrupado = df.groupby(df["Inicio"].dt.to_period("W"))["Duração (h)"].sum().reset_index()
else:
    agrupado = df.groupby(df["Inicio"].dt.to_period("M"))["Duração (h)"].sum().reset_index()

fig2 = px.bar(
    agrupado,
    x=agrupado.columns[0],
    y="Duração (h)",
    text="Duração (h)"
)

st.plotly_chart(fig2, use_container_width=True)

# ===============================
# ALERTAS
# ===============================

st.subheader("Alertas")

if total_horas > 100:
    st.error("🔥 Alta carga na fábrica")
else:
    st.success("Fábrica dentro da capacidade")