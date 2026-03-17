import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")

st.title("📊 APS ELOHIM - DASHBOARD DE CAPACIDADE")

# ===============================
# VALIDAR DADOS
# ===============================
if "dados_dashboard" not in st.session_state:
    st.warning("Execute o APS primeiro")
    st.stop()

df = st.session_state["dados_dashboard"].copy()

# ===============================
# GARANTIR TIPOS
# ===============================
df["Início"] = pd.to_datetime(df["Início"])
df["Fim"] = pd.to_datetime(df["Fim"])

# Se ainda não existir coluna Maquina, cria automaticamente
if "Maquina" not in df.columns:
    df["Maquina"] = df["Processo"]

# ===============================
# SELETOR DE PERÍODO
# ===============================
st.subheader("📅 Análise por Período")

periodo = st.selectbox(
    "Selecione o período",
    ["Diário", "Semanal", "Mensal"]
)

# ===============================
# CRIAR COLUNA DE PERÍODO (SEM ERRO JSON)
# ===============================
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
# GRÁFICO 1 - CARGA POR MÁQUINA
# ===============================
st.subheader("🏭 Carga por Máquina")

fig1 = px.bar(
    df_maquina,
    x="Periodo",
    y="Duração (h)",
    color="Maquina",
    barmode="group",
    text_auto=True
)

st.plotly_chart(fig1, use_container_width=True)

# ===============================
# GRÁFICO 2 - GARGALO POR PERÍODO
# ===============================
st.subheader("🔥 Gargalo por Período")

gargalo = (
    df_maquina
    .sort_values(["Periodo", "Duração (h)"], ascending=[True, False])
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
# GRÁFICO 3 - RANKING GERAL
# ===============================
st.subheader("📊 Ranking Geral de Gargalos")

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
# KPI FINAL
# ===============================
st.subheader("📌 Indicadores Gerais")

total_horas = df["Duração (h)"].sum()
total_ordens = df["PV"].nunique()
total_maquinas = df["Maquina"].nunique()

c1, c2, c3 = st.columns(3)

c1.metric("Horas Totais", round(total_horas, 2))
c2.metric("Ordens", total_ordens)
c3.metric("Máquinas Utilizadas", total_maquinas)