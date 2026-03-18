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
# CONFIG REAL DE TURNO
# ===============================
HORAS_DIA = {
    0: 9,  # seg
    1: 9,  # ter
    2: 9,  # qua
    3: 9,  # qui
    4: 8   # sex
}
EFICIENCIA = 0.8

def capacidade_dia(data):
    return HORAS_DIA.get(data.weekday(), 0) * EFICIENCIA

# ===============================
# FILTRO DE MÊS
# ===============================
meses = sorted(df["Data"].dt.strftime("%Y-%m").unique())
mes_sel = st.selectbox("Filtrar mês", ["Todos"] + meses)

if mes_sel != "Todos":
    df = df[df["Data"].dt.strftime("%Y-%m") == mes_sel]

# ===============================
# VISUALIZAÇÃO
# ===============================
tipo = st.selectbox("Visualização", ["Semanal", "Mensal"])

# ===============================
# CRIA PERÍODO
# ===============================
if tipo == "Semanal":

    df["Semana"] = df["Data"].dt.isocalendar().week
    df["Mes"] = df["Data"].dt.strftime("%b")

    df["Periodo"] = (
        "Sem " + df["Semana"].astype(str) +
        "<br>" + df["Mes"]
    )

elif tipo == "Mensal":

    df["Periodo"] = df["Data"].dt.strftime("%b/%Y")

# ===============================
# DEMANDA (HORAS CHEIAS)
# ===============================
df["Duração (h)"] = df["Duração (h)"].round(0)

demanda = (
    df.groupby(["Periodo", "Maquina"])["Duração (h)"]
    .sum()
    .reset_index()
)

demanda["Duração (h)"] = demanda["Duração (h)"].astype(int)

# ===============================
# CAPACIDADE
# ===============================
capacidade = []

for (periodo, maquina), grupo in df.groupby(["Periodo", "Maquina"]):

    inicio = grupo["Data"].min().date()
    fim = grupo["Data"].max().date()

    dias = pd.date_range(start=inicio, end=fim)

    total = 0

    for d in dias:
        if d.weekday() <= 4:
            total += capacidade_dia(d)

    capacidade.append({
        "Periodo": periodo,
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
    on=["Periodo", "Maquina"],
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
# TEXTO NAS COLUNAS (MELHORADO)
# ===============================
df_final["Label"] = (
    df_final["Maquina"] + "<br>" +
    df_final["Duração (h)"].astype(str) + "h"
)

# ===============================
# GRÁFICO LIMPO
# ===============================
st.subheader("📊 Carga por Máquina")

fig = px.bar(
    df_final,
    x="Periodo",
    y="Ocupação (%)",
    color="Maquina",
    text="Label",
    barmode="group"
)

fig.update_traces(textposition="outside")

fig.update_layout(
    yaxis_title="Ocupação (%)",
    xaxis_title="Período",
    uniformtext_minsize=8,
    uniformtext_mode='hide'
)

st.plotly_chart(fig, use_container_width=True)

# ===============================
# TABELA
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