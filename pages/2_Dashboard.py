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
# CONFIG REAL
# ===============================
HORAS_DIA = {0: 9, 1: 9, 2: 9, 3: 9, 4: 8}
EFICIENCIA = 0.8

# 🔥 QUANTIDADE DE MÁQUINAS
MAQUINAS_QTD = {
    "PLASMA_1": 1,
    "SERRA_1": 1,
    "ACAB_1": 1,
    "ACAB_2": 1,
    "PINTURA_1": 1
    # 👉 ajuste conforme sua fábrica
}

def capacidade_dia(data):
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
    df.groupby(["Periodo", "Periodo_ord", "Maquina"])["Duração (h)"]
    .sum()
    .reset_index()
)

# ===============================
# CAPACIDADE CORRETA
# ===============================
capacidade = []

for (p, po, m), g in df.groupby(["Periodo", "Periodo_ord", "Maquina"]):

    # 🔥 pega TODOS os dias do período
    if tipo == "Semanal":
        ano = int(str(po)[:4])
        semana = int(str(po)[4:])
        dias = pd.date_range(
            start=pd.Timestamp.fromisocalendar(ano, semana, 1),
            periods=5
        )
    else:
        ano = int(str(po)[:4])
        mes = int(str(po)[4:])
        dias = pd.date_range(
            start=pd.Timestamp(ano, mes, 1),
            end=pd.Timestamp(ano, mes, 28)
        )

    total = sum(capacidade_dia(d) for d in dias if d.weekday() <= 4)

    qtd = MAQUINAS_QTD.get(m, 1)

    total = total * qtd

    capacidade.append({
        "Periodo": p,
        "Periodo_ord": po,
        "Maquina": m,
        "Capacidade (h)": round(total)
    })

cap_df = pd.DataFrame(capacidade)

# ===============================
# JOIN
# ===============================
df_final = pd.merge(
    demanda,
    cap_df,
    on=["Periodo", "Periodo_ord", "Maquina"]
)

# ===============================
# MÉTRICAS
# ===============================
df_final["Ocupação (%)"] = (
    df_final["Duração (h)"] / df_final["Capacidade (h)"]
) * 100

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
# GRÁFICO
# ===============================
df_plot = (
    df_final.groupby(["Periodo", "Periodo_ord", "Maquina"])
    .agg({
        "Duração (h)": "sum",
        "Ocupação (%)": "mean"
    })
    .reset_index()
)

df_plot = df_plot.sort_values("Periodo_ord")

df_plot["Label"] = df_plot["Duração (h)"].astype(int).astype(str) + "h"

st.subheader("📊 Carga por Máquina")

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
# TABELA
# ===============================
st.subheader("📋 Situação da Capacidade")

st.dataframe(df_final, use_container_width=True)