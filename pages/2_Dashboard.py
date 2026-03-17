import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")

st.title("📊 Dashboard APS Elohim")

# ===============================
# VERIFICA DADOS
# ===============================
if "dados_dashboard" not in st.session_state:
    st.warning("Execute o APS primeiro")
    st.stop()

df = st.session_state["dados_dashboard"].copy()

# ===============================
# GARANTE DATETIME
# ===============================
df["Início"] = pd.to_datetime(df["Início"])
df["Fim"] = pd.to_datetime(df["Fim"])

# ===============================
# SELETOR DE PERÍODO
# ===============================
st.subheader("Análise por Período")

periodo = st.selectbox(
    "Selecione o período",
    ["Diário", "Semanal", "Mensal"]
)

# ===============================
# AGRUPAMENTO CORRETO
# ===============================
if periodo == "Diário":
    df["Periodo"] = df["Início"].dt.date.astype(str)

elif periodo == "Semanal":
    df["Periodo"] = df["Início"].dt.to_period("W").astype(str)

elif periodo == "Mensal":
    df["Periodo"] = df["Início"].dt.to_period("M").astype(str)

# ===============================
# AGRUPA
# ===============================
df_group = (
    df.groupby(["Periodo", "Processo"])["Duração (h)"]
    .sum()
    .reset_index()
)

# ===============================
# GRÁFICO DE CARGA
# ===============================
st.subheader("Carga por Processo")

fig = px.bar(
    df_group,
    x="Periodo",
    y="Duração (h)",
    color="Processo",
    barmode="stack",
    text_auto=True
)

st.plotly_chart(fig, use_container_width=True)

# ===============================
# GARGALO POR PERÍODO
# ===============================
st.subheader("Gargalo por Período")

gargalo = (
    df_group.sort_values(["Periodo", "Duração (h)"], ascending=[True, False])
    .groupby("Periodo")
    .first()
    .reset_index()
)

fig2 = px.bar(
    gargalo,
    x="Periodo",
    y="Duração (h)",
    color="Processo",
    text_auto=True
)

st.plotly_chart(fig2, use_container_width=True)

# ===============================
# KPIs
# ===============================
st.subheader("Indicadores")

total = df["Duração (h)"].sum()
ordens = df["PV"].nunique()
processos = df["Processo"].nunique()

c1, c2, c3 = st.columns(3)

c1.metric("Total de Horas", round(total, 2))
c2.metric("Ordens", ordens)
c3.metric("Processos Ativos", processos)