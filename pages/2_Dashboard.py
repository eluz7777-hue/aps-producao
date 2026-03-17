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
# DATETIME
# ===============================
df["Início"] = pd.to_datetime(df["Início"])

# ===============================
# FILTRO PERÍODO
# ===============================
st.subheader("Análise por Período")

periodo = st.selectbox(
    "Selecione o período",
    ["Diário", "Semanal", "Mensal"]
)

if periodo == "Diário":
    df["Periodo"] = df["Início"].dt.date.astype(str)

elif periodo == "Semanal":
    df["Periodo"] = df["Início"].dt.to_period("W").astype(str)

elif periodo == "Mensal":
    df["Periodo"] = df["Início"].dt.to_period("M").astype(str)

# ===============================
# AGRUPAMENTO POR MÁQUINA
# ===============================
df_maquina = (
    df.groupby(["Periodo", "Maquina"])["Duração (h)"]
    .sum()
    .reset_index()
)

# ===============================
# GRÁFICO DE CARGA (VERTICAL)
# ===============================
st.subheader("Carga por Máquina")

fig = px.bar(
    df_maquina,
    x="Periodo",
    y="Duração (h)",
    color="Maquina",
    barmode="group",
    text_auto=True
)

st.plotly_chart(fig, use_container_width=True)

# ===============================
# GARGALO POR PERÍODO
# ===============================
st.subheader("Gargalo por Máquina")

gargalo = (
    df_maquina.sort_values(["Periodo", "Duração (h)"], ascending=[True, False])
    .groupby("Periodo")
    .first()
    .reset_index()
)

fig2 = px.bar(
    gargalo,
    x="Periodo",
    y="Duração (h)",
    color="Maquina",
    text_auto=True
)

st.plotly_chart(fig2, use_container_width=True)

# ===============================
# RANKING GERAL
# ===============================
st.subheader("Ranking de Gargalos")

ranking = (
    df.groupby("Maquina")["Duração (h)"]
    .sum()
    .sort_values(ascending=False)
    .reset_index()
)

fig3 = px.bar(
    ranking,
    x="Maquina",
    y="Duração (h)",
    text_auto=True
)

st.plotly_chart(fig3, use_container_width=True)

# ===============================
# KPI
# ===============================
st.subheader("Indicadores")

total = df["Duração (h)"].sum()
ordens = df["PV"].nunique()
maquinas = df["Maquina"].nunique()

c1, c2, c3 = st.columns(3)

c1.metric("Horas Totais", round(total, 2))
c2.metric("Ordens", ordens)
c3.metric("Máquinas Ativas", maquinas)