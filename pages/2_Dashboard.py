import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import holidays

st.set_page_config(layout="wide")

st.title("📊 DASHBOARD DE CAPACIDADE")

# ===============================
# DADOS
# ===============================
if "dados_dashboard" not in st.session_state:
    st.stop()

df = st.session_state["dados_dashboard"].copy()

if "Início" not in df.columns:
    st.error("APS não gerou dados corretamente.")
    st.stop()

df["Data"] = pd.to_datetime(df["Início"])

# 🔥 PROCESSO
df["Processo"] = df["Maquina"].str.split("_").str[0]

# ===============================
# CONFIG
# ===============================
HORAS_DIA = {0: 9, 1: 9, 2: 9, 3: 9, 4: 8}
EFICIENCIA = 0.8

# 🔥 FERIADOS BRASIL
br_holidays = holidays.Brazil()

def capacidade_dia(data):
    if data.weekday() > 4:
        return 0
    if data.date() in br_holidays:
        return 0
    return HORAS_DIA.get(data.weekday(), 0) * EFICIENCIA

MAQUINAS_QTD = {
    "PLASMA_1": 1,
    "SERRA_1": 1,
    "ACAB_1": 1,
    "ACAB_2": 1,
    "PINTURA_1": 1
}

# ===============================
# VISUALIZAÇÃO
# ===============================
tipo = st.selectbox("Visualização", ["Semanal", "Mensal"])

if tipo == "Semanal":
    df["Periodo_ord"] = df["Data"].dt.year * 100 + df["Data"].dt.isocalendar().week
    df["Periodo"] = "Sem " + df["Data"].dt.isocalendar().week.astype(str)
else:
    df["Periodo_ord"] = df["Data"].dt.year * 100 + df["Data"].dt.month
    df["Periodo"] = df["Data"].dt.strftime("%b/%Y")

# ===============================
# DEMANDA
# ===============================
df["Duração (h)"] = df["Duração (h)"].round(0)

demanda = (
    df.groupby(["Periodo","Periodo_ord","Maquina","Processo"])["Duração (h)"]
    .sum()
    .reset_index()
)

# ===============================
# CAPACIDADE (COM FERIADOS)
# ===============================
capacidade = []

for (p,po,m),g in df.groupby(["Periodo","Periodo_ord","Maquina"]):

    if tipo == "Semanal":
        ano = int(str(po)[:4])
        semana = int(str(po)[4:])
        dias = pd.date_range(
            start=pd.Timestamp.fromisocalendar(ano, semana, 1),
            periods=7
        )
    else:
        ano = int(str(po)[:4])
        mes = int(str(po)[4:])
        dias = pd.date_range(
            start=pd.Timestamp(ano, mes, 1),
            end=pd.Timestamp(ano, mes, 28)
        )

    total = sum(capacidade_dia(d) for d in dias)

    qtd = MAQUINAS_QTD.get(m, 1)
    total = total * qtd

    capacidade.append({
        "Periodo":p,
        "Periodo_ord":po,
        "Maquina":m,
        "Capacidade (h)":round(total)
    })

cap_df = pd.DataFrame(capacidade)

# ===============================
# JOIN
# ===============================
df_final = pd.merge(demanda,cap_df,on=["Periodo","Periodo_ord","Maquina"])

# ===============================
# MÉTRICAS
# ===============================
df_final["Ocupação (%)"] = (
    df_final["Duração (h)"]/df_final["Capacidade (h)"]
)*100

df_final["Ocupação (%)"] = df_final["Ocupação (%)"].round(0)
df_final["Disponível (%)"] = 100 - df_final["Ocupação (%)"]

def status(x):
    if x <= 85:
        return "🟢"
    elif x <= 100:
        return "🟡"
    else:
        return "🔴"

df_final["Status"] = df_final["Ocupação (%)"].apply(status)

df_final = df_final.sort_values("Periodo_ord")

# ===============================
# 🔥 GARGALO MÉDIO E PICO
# ===============================
ranking_proc = (
    df_final.groupby("Processo")["Ocupação (%)"]
    .agg(["mean","max"])
    .reset_index()
)

ranking_proc.columns = ["Processo","Gargalo Médio (%)","Gargalo Pico (%)"]

ranking_proc = ranking_proc.sort_values("Gargalo Pico (%)", ascending=False)

st.subheader("📊 Ranking de Gargalos por Processo")

st.dataframe(ranking_proc, use_container_width=True)

# ===============================
# 🔥 GRÁFICO GARGALO
# ===============================
st.subheader("📊 Gargalo Médio vs Pico")

df_melt = ranking_proc.melt(
    id_vars="Processo",
    value_vars=["Gargalo Médio (%)","Gargalo Pico (%)"],
    var_name="Tipo",
    value_name="Ocupação (%)"
)

fig_gargalo = px.bar(
    df_melt,
    x="Processo",
    y="Ocupação (%)",
    color="Tipo",
    barmode="group",
    text="Ocupação (%)"
)

fig_gargalo.add_hline(y=100, line_dash="dash")

fig_gargalo.update_traces(textposition="outside")

st.plotly_chart(fig_gargalo, use_container_width=True)

# ===============================
# TABELA FINAL
# ===============================
st.subheader("📋 Situação da Capacidade")

st.dataframe(df_final, use_container_width=True)