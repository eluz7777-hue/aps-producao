import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

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

# ===============================
# PROCESSO
# ===============================
df["Processo"] = df["Maquina"].str.split("_").str[0]

# ===============================
# FERIADOS (ROBUSTO)
# ===============================
try:
    import holidays
    br_holidays = holidays.Brazil()
except:
    br_holidays = []

# ===============================
# CONFIG
# ===============================
HORAS_DIA = {0: 9, 1: 9, 2: 9, 3: 9, 4: 8}
EFICIENCIA = 0.8

MAQUINAS_QTD = {
    "PLASMA_1": 1,
    "SERRA_1": 1,
    "ACAB_1": 1,
    "ACAB_2": 1,
    "PINTURA_1": 1
}

def capacidade_dia(data):
    if data.weekday() > 4:
        return 0
    if data.date() in br_holidays:
        return 0
    return HORAS_DIA.get(data.weekday(), 0) * EFICIENCIA

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
# CAPACIDADE
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
df_final["Ocupação (%)"] = (df_final["Duração (h)"]/df_final["Capacidade (h)"])*100
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
# 📊 CARGA POR MÁQUINA
# ===============================
st.subheader("📊 Carga por Máquina")

df_plot = (
    df_final.groupby(["Periodo","Periodo_ord","Maquina"])
    .agg({"Duração (h)":"sum","Ocupação (%)":"mean"})
    .reset_index()
)

df_plot = df_plot.sort_values("Periodo_ord")
df_plot["Label"] = df_plot["Duração (h)"].astype(int).astype(str) + "h"

fig = px.bar(
    df_plot,
    x="Periodo",
    y="Ocupação (%)",
    color="Maquina",
    text="Label",
    barmode="group",
    category_orders={"Periodo": df_plot["Periodo"].unique()}
)

fig.add_hline(y=100, line_dash="dash")
fig.update_traces(textposition="outside", cliponaxis=False)

st.plotly_chart(fig, use_container_width=True)

# ===============================
# 🥧 PIZZA MÁQUINA
# ===============================
st.subheader("🥧 Distribuição por Máquina")

pizza = df_plot.groupby("Maquina")["Duração (h)"].sum().reset_index()

fig2 = px.pie(pizza, names="Maquina", values="Duração (h)")
fig2.update_traces(textinfo="label+percent")

st.plotly_chart(fig2, use_container_width=True)

# ===============================
# 📊 CARGA POR PROCESSO
# ===============================
st.subheader("📊 Carga por Processo")

proc_plot = (
    df_final.groupby(["Periodo","Periodo_ord","Processo"])
    .agg({"Duração (h)":"sum","Capacidade (h)":"sum"})
    .reset_index()
)

proc_plot["Ocupação (%)"] = (proc_plot["Duração (h)"]/proc_plot["Capacidade (h)"])*100
proc_plot = proc_plot.sort_values("Periodo_ord")

proc_plot["Label"] = proc_plot["Duração (h)"].astype(int).astype(str)+"h"

fig3 = px.bar(
    proc_plot,
    x="Periodo",
    y="Ocupação (%)",
    color="Processo",
    text="Label",
    barmode="group",
    category_orders={"Periodo": proc_plot["Periodo"].unique()}
)

fig3.add_hline(y=100, line_dash="dash")
fig3.update_traces(textposition="outside", cliponaxis=False)

st.plotly_chart(fig3, use_container_width=True)

# ===============================
# 🥧 PIZZA PROCESSO
# ===============================
st.subheader("🥧 Distribuição por Processo")

pizza_proc = proc_plot.groupby("Processo")["Duração (h)"].sum().reset_index()

fig4 = px.pie(pizza_proc, names="Processo", values="Duração (h)")
fig4.update_traces(textinfo="label+percent")

st.plotly_chart(fig4, use_container_width=True)

# ===============================
# 🔥 GARGALO MÉDIO E PICO
# ===============================
st.subheader("📊 Gargalo Médio vs Pico")

ranking_proc = (
    df_final.groupby("Processo")["Ocupação (%)"]
    .agg(["mean","max"])
    .reset_index()
)

ranking_proc.columns = ["Processo","Gargalo Médio (%)","Gargalo Pico (%)"]

df_melt = ranking_proc.melt(
    id_vars="Processo",
    value_vars=["Gargalo Médio (%)","Gargalo Pico (%)"],
    var_name="Tipo",
    value_name="Ocupação (%)"
)

fig5 = px.bar(
    df_melt,
    x="Processo",
    y="Ocupação (%)",
    color="Tipo",
    barmode="group",
    text="Ocupação (%)"
)

fig5.add_hline(y=100, line_dash="dash")
fig5.update_traces(textposition="outside")

st.plotly_chart(fig5, use_container_width=True)

# ===============================
# TABELA FINAL
# ===============================
st.subheader("📋 Situação da Capacidade")

st.dataframe(df_final, use_container_width=True)