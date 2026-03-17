import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")

st.title("📊 APS ELOHIM - CAPACIDADE REAL")

# ===============================
# CONFIG
# ===============================
EFICIENCIA = 0.8

HORAS_DIA = {
    0: 9,
    1: 9,
    2: 9,
    3: 9,
    4: 8
}

# ===============================
# DADOS
# ===============================
if "dados_dashboard" not in st.session_state:
    st.warning("Execute o APS primeiro")
    st.stop()

df = st.session_state["dados_dashboard"].copy()
df["Início"] = pd.to_datetime(df["Início"])

# ===============================
# FILTRO DE MÊS (NOVO)
# ===============================
st.subheader("📅 Seleção de Período")

meses = {
    "Janeiro": 1, "Fevereiro": 2, "Março": 3, "Abril": 4,
    "Maio": 5, "Junho": 6, "Julho": 7, "Agosto": 8,
    "Setembro": 9, "Outubro": 10, "Novembro": 11, "Dezembro": 12
}

mes_nome = st.selectbox("Selecione o mês", list(meses.keys()))
mes = meses[mes_nome]

# filtrar dados corretamente
df = df[df["Início"].dt.month == mes]

if df.empty:
    st.warning("Sem dados para este mês")
    st.stop()

# ===============================
# TIPO DE ANÁLISE
# ===============================
tipo = st.radio(
    "Tipo de análise",
    ["Diária", "Semanal", "Mensal"]
)

# ===============================
# PERÍODOS CORRETOS
# ===============================
if tipo == "Diária":
    df["Periodo"] = df["Início"].dt.strftime("%d/%m")

elif tipo == "Semanal":
    df["Semana"] = df["Início"].dt.isocalendar().week
    df["Periodo"] = "Semana " + df["Semana"].astype(str)

elif tipo == "Mensal":
    df["Periodo"] = df["Início"].dt.strftime("%Y-%m")

# ===============================
# DEMANDA
# ===============================
demanda = (
    df.groupby(["Periodo", "Maquina"])["Duração (h)"]
    .sum()
    .reset_index()
)

# ===============================
# CAPACIDADE REAL
# ===============================
def capacidade_periodo(df_periodo):

    dias = df_periodo["Início"].dt.date.unique()

    total_horas = 0

    for d in dias:
        d = pd.to_datetime(d)
        total_horas += HORAS_DIA.get(d.weekday(), 0)

    return total_horas * EFICIENCIA

capacidade_lista = []

for periodo in demanda["Periodo"].unique():

    df_p = df[df["Periodo"] == periodo]

    cap = capacidade_periodo(df_p)

    maquinas = df["Maquina"].unique()

    for m in maquinas:
        capacidade_lista.append({
            "Periodo": periodo,
            "Maquina": m,
            "Capacidade (h)": cap
        })

cap_df = pd.DataFrame(capacidade_lista)

# ===============================
# MERGE
# ===============================
df_final = pd.merge(demanda, cap_df, on=["Periodo", "Maquina"])

df_final["Ocupação (%)"] = (
    df_final["Duração (h)"] / df_final["Capacidade (h)"]
) * 100

df_final["Excesso (h)"] = (
    df_final["Duração (h)"] - df_final["Capacidade (h)"]
)

# ===============================
# ORDENAR PERÍODO
# ===============================
df_final = df_final.sort_values("Periodo")

# ===============================
# GRÁFICO
# ===============================
st.subheader("🏭 Demanda vs Capacidade")

fig1 = px.bar(
    df_final,
    x="Periodo",
    y=["Duração (h)", "Capacidade (h)"],
    color="Maquina",
    barmode="group",
    text_auto=True
)

st.plotly_chart(fig1, use_container_width=True)

# ===============================
# OCUPAÇÃO
# ===============================
st.subheader("📊 Ocupação (%)")

fig2 = px.bar(
    df_final,
    x="Periodo",
    y="Ocupação (%)",
    color="Maquina",
    text_auto=True
)

st.plotly_chart(fig2, use_container_width=True)

# ===============================
# GARGALOS
# ===============================
st.subheader("🔥 Gargalos")

gargalos = df_final[df_final["Excesso (h)"] > 0]

if gargalos.empty:
    st.success("Sem gargalos no período")
else:
    st.dataframe(gargalos)