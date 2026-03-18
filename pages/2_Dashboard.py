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
# FILTRO DE MÊS
# ===============================
meses = sorted(df["Data"].dt.strftime("%Y-%m").unique())
mes_sel = st.selectbox("Filtrar mês", ["Todos"] + meses)

if mes_sel != "Todos":
    df = df[df["Data"].dt.strftime("%Y-%m") == mes_sel]

# ===============================
# PERÍODO (SEM DIÁRIO)
# ===============================
tipo = st.selectbox("Período", ["Semanal", "Mensal"])

if tipo == "Semanal":
    df["Periodo"] = (
        df["Data"].dt.strftime("%Y") +
        "-S" +
        df["Data"].dt.isocalendar().week.astype(str).str.zfill(2)
    )
else:
    df["Periodo"] = df["Data"].dt.strftime("%Y-%m")

# ===============================
# DEMANDA
# ===============================
demanda = (
    df.groupby(["Periodo", "Maquina"])["Duração (h)"]
    .sum()
    .reset_index()
)

# ===============================
# CAPACIDADE
# ===============================
HORAS_DIA = {0: 9, 1: 9, 2: 9, 3: 9, 4: 8}
EFICIENCIA = 0.8

def capacidade_dia(data):
    return HORAS_DIA.get(data.weekday(), 0) * EFICIENCIA

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
        "Capacidade (h)": total
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

def classificar(c):
    if c <= 85:
        return "🟢 Normal"
    elif c <= 100:
        return "🟡 Atenção"
    else:
        return "🔴 Sobrecarga"

df_final["Status"] = df_final["Ocupação (%)"].apply(classificar)

# ===============================
# GRÁFICO
# ===============================
st.subheader("📊 Ocupação por Máquina")

fig = px.bar(
    df_final,
    x="Periodo",
    y="Ocupação (%)",
    color="Status",
    facet_col="Maquina",
    text="Ocupação (%)"
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

col1, col2, col3 = st.columns(3)

col1.metric("Carga Total (h)", round(df_final["Duração (h)"].sum(), 2))
col2.metric("Capacidade Total (h)", round(df_final["Capacidade (h)"].sum(), 2))
col3.metric("Ocupação Média (%)", round(df_final["Ocupação (%)"].mean(), 1))