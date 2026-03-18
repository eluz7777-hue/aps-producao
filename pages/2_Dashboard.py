import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

st.set_page_config(layout="wide")

st.title("📊 DASHBOARD DE CAPACIDADE")

if "dados_dashboard" not in st.session_state:
    st.stop()

df = st.session_state["dados_dashboard"].copy()
df["Data"] = pd.to_datetime(df["Início"])

HORAS_DIA = {0: 9, 1: 9, 2: 9, 3: 9, 4: 8}
EFICIENCIA = 0.8

def capacidade_dia(data):
    return HORAS_DIA.get(data.weekday(), 0) * EFICIENCIA

tipo = st.selectbox("Visualização", ["Semanal", "Mensal"])

if tipo == "Semanal":
    df["Periodo_ord"] = df["Data"].dt.strftime("%Y%U")
    df["Periodo"] = "Sem " + df["Data"].dt.isocalendar().week.astype(str)
else:
    df["Periodo_ord"] = df["Data"].dt.strftime("%Y%m")
    df["Periodo"] = df["Data"].dt.strftime("%b/%Y")

# DEMANDA
demanda = df.groupby(["Periodo","Periodo_ord","Maquina"])["Duração (h)"].sum().reset_index()

# CAPACIDADE CORRIGIDA
capacidade = []

for (p,po,m),g in df.groupby(["Periodo","Periodo_ord","Maquina"]):

    dias = pd.date_range(g["Data"].min(), g["Data"].max())

    total = sum(capacidade_dia(d) for d in dias if d.weekday()<=4)

    if total == 0:
        total = capacidade_dia(pd.Timestamp.today())  # 🔥 nunca zero

    capacidade.append({
        "Periodo":p,
        "Periodo_ord":po,
        "Maquina":m,
        "Capacidade (h)": round(total)
    })

cap_df = pd.DataFrame(capacidade)

df_final = pd.merge(demanda,cap_df,on=["Periodo","Periodo_ord","Maquina"])

df_final["Ocupação (%)"] = (df_final["Duração (h)"]/df_final["Capacidade (h)"])*100
df_final["Ocupação (%)"] = df_final["Ocupação (%)"].replace([np.inf,-np.inf],0).fillna(0)

df_final["Disponível (%)"] = 100 - df_final["Ocupação (%)"]

def status(x):
    if x<=85: return "🟢"
    elif x<=100: return "🟡"
    else: return "🔴"

df_final["Status"] = df_final["Ocupação (%)"].apply(status)

df_final = df_final.sort_values("Periodo_ord")

# GRÁFICO
df_plot = df_final.groupby(["Periodo","Periodo_ord","Maquina"]).agg({
    "Duração (h)":"sum",
    "Ocupação (%)":"mean"
}).reset_index()

df_plot["Label"] = df_plot["Maquina"]+"<br>"+df_plot["Duração (h)"].astype(int).astype(str)+"h"

fig = px.bar(df_plot,x="Periodo",y="Ocupação (%)",color="Maquina",text="Label")

fig.add_hline(y=100,line_dash="dash")
fig.update_traces(textposition="outside")

st.plotly_chart(fig,use_container_width=True)

# TABELA
st.dataframe(df_final,use_container_width=True)

# KPI (CORRIGIDO)
col1,col2,col3,col4 = st.columns(4)

col1.metric("Carga Total",int(df_final["Duração (h)"].sum()))
col2.metric("Capacidade Total",int(df_final["Capacidade (h)"].sum()))
col3.metric("Ocupação Média",round(df_final["Ocupação (%)"].mean(),1))
col4.metric("Disponível Médio",round(df_final["Disponível (%)"].mean(),1))