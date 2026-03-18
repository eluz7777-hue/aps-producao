import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")

st.title("📊 DASHBOARD DE CAPACIDADE")

# ===============================
# VERIFICA DADOS
# ===============================
if "dados_dashboard" not in st.session_state:
    st.warning("Execute o APS primeiro")
    st.stop()

df = st.session_state["dados_dashboard"].copy()
df["Data"] = pd.to_datetime(df["Início"])

# ===============================
# CONFIG TURNOS + EFICIÊNCIA
# ===============================
HORAS_DIA = {0: 9, 1: 9, 2: 9, 3: 9, 4: 8}
EFICIENCIA = 0.8

# 🔥 QUANTIDADE DE MÁQUINAS (AJUSTADO)
MAQUINAS_QTD = {
    "LASER_1": 1,
    "FRESA_1": 1,
    "FRESA_2": 1,
    "FRESA_3": 1,
    "TORNO_1": 1,
    "TORNO_2": 1,
    "SOLDA_1": 1,
    "SOLDA_2": 1,
    "SOLDA_3": 1,
    "ACAB_1": 1,
    "ACAB_2": 1,
    "SERRA_1": 1,
    "PRENSA_1": 1
}

def capacidade_dia(data):
    return HORAS_DIA.get(data.weekday(), 0) * EFICIENCIA

# ===============================
# FILTRO DE MÊS
# ===============================
meses_ordem = sorted(df["Data"].dt.to_period("M").unique())

meses = [str(m) for m in meses_ordem]

mes_sel = st.selectbox("Filtrar mês", ["Todos"] + meses)

if mes_sel != "Todos":
    df = df[df["Data"].dt.to_period("M").astype(str) == mes_sel]

# ===============================
# VISUALIZAÇÃO
# ===============================
tipo = st.selectbox("Visualização", ["Semanal", "Mensal"])

if tipo == "Semanal":
    df["Ano"] = df["Data"].dt.year
    df["Semana"] = df["Data"].dt.isocalendar().week
    df["Mes"] = df["Data"].dt.strftime("%b")

    df["Periodo_ord"] = df["Ano"].astype(str) + df["Semana"].astype(str).str.zfill(2)

    df["Periodo"] = "Sem " + df["Semana"].astype(str) + "<br>" + df["Mes"]

elif tipo == "Mensal":
    df["Periodo_ord"] = df["Data"].dt.to_period("M").astype(str)
    df["Periodo"] = df["Data"].dt.strftime("%b/%Y")

# ===============================
# DEMANDA
# ===============================
df["Duração (h)"] = df["Duração (h)"].round(0)

demanda = (
    df.groupby(["Periodo", "Periodo_ord", "Maquina", "PV"])["Duração (h)"]
    .sum()
    .reset_index()
)

demanda["Duração (h)"] = demanda["Duração (h)"].astype(int)

# ===============================
# CAPACIDADE CORRETA (MULTI MÁQUINAS)
# ===============================
capacidade = []

for (periodo, periodo_ord, maquina), grupo in df.groupby(["Periodo", "Periodo_ord", "Maquina"]):

    inicio = grupo["Data"].min().date()
    fim = grupo["Data"].max().date()

    dias = pd.date_range(start=inicio, end=fim)

    total = 0

    for d in dias:
        if d.weekday() <= 4:
            total += capacidade_dia(d)

    qtd_maquinas = MAQUINAS_QTD.get(maquina, 1)

    total = total * qtd_maquinas

    capacidade.append({
        "Periodo": periodo,
        "Periodo_ord": periodo_ord,
        "Maquina": maquina,
        "Capacidade (h)": int(round(total, 0))
    })

cap_df = pd.DataFrame(capacidade)

# ===============================
# JOIN
# ===============================
df_final = pd.merge(
    demanda,
    cap_df,
    on=["Periodo", "Periodo_ord", "Maquina"],
    how="left"
)

# ===============================
# MÉTRICAS
# ===============================
df_final["Ocupação (%)"] = (
    df_final["Duração (h)"] / df_final["Capacidade (h)"]
) * 100

df_final["Ocupação (%)"] = df_final["Ocupação (%)"].round(0)
df_final["Disponível (%)"] = 100 - df_final["Ocupação (%)"]

# ===============================
# STATUS BOLINHAS
# ===============================
def status(c):
    if c <= 85:
        return "🟢"
    elif c <= 100:
        return "🟡"
    else:
        return "🔴"

df_final["Status"] = df_final["Ocupação (%)"].apply(status)

# ===============================
# ORDENAÇÃO CORRETA
# ===============================
df_final = df_final.sort_values("Periodo_ord")

# ===============================
# LABELS
# ===============================
df_plot = (
    df_final.groupby(["Periodo", "Periodo_ord", "Maquina"])
    .agg({
        "Duração (h)": "sum",
        "Ocupação (%)": "mean"
    })
    .reset_index()
)

df_plot["Label"] = (
    df_plot["Maquina"] + "<br>" +
    df_plot["Duração (h)"].astype(str) + "h"
)

# ===============================
# GRÁFICO PRINCIPAL
# ===============================
fig = px.bar(
    df_plot.sort_values("Periodo_ord"),
    x="Periodo",
    y="Ocupação (%)",
    color="Maquina",
    text="Label",
    barmode="group"
)

fig.add_hline(y=100, line_dash="dash")

fig.update_traces(textposition="outside")

st.plotly_chart(fig, use_container_width=True)

# ===============================
# GRÁFICO PIZZA
# ===============================
st.subheader("🥧 Distribuição de Carga por Recurso")

pizza = (
    df_plot.groupby("Maquina")["Duração (h)"]
    .sum()
    .reset_index()
)

fig2 = px.pie(
    pizza,
    names="Maquina",
    values="Duração (h)"
)

st.plotly_chart(fig2, use_container_width=True)

# ===============================
# TABELA FINAL
# ===============================
st.subheader("📋 Situação da Capacidade")

st.dataframe(
    df_final.sort_values("Ocupação (%)", ascending=False),
    use_container_width=True
)

# ===============================
# KPI
# ===============================
st.subheader("Resumo Geral")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Carga Total (h)", int(df_final["Duração (h)"].sum()))
col2.metric("Capacidade Total (h)", int(df_final["Capacidade (h)"].sum()))
col3.metric("Ocupação Média (%)", int(df_final["Ocupação (%)"].mean()))
col4.metric("Disponível Médio (%)", int(df_final["Disponível (%)"].mean()))