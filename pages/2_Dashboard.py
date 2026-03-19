import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")

st.title("📊 DASHBOARD DE CAPACIDADE")

# ===============================
# DADOS
# ===============================
if "dados_dashboard" not in st.session_state:
    st.warning("Execute o APS primeiro")
    st.stop()

df = st.session_state["dados_dashboard"].copy()
df["Data"] = pd.to_datetime(df["Início"])

# ===============================
# CONFIG
# ===============================
EFICIENCIA = 0.8

HORAS_DIA = {0:9,1:9,2:9,3:9,4:8}

MAQUINAS_QTD = {
    "PLASMA":1,
    "SERRA":1,
    "SOLDA":3,
    "PINTURA":1,
    "ACAB":2
}

def horas_dia(data):
    return HORAS_DIA.get(data.weekday(),0) * EFICIENCIA

# ===============================
# FILTROS
# ===============================
st.sidebar.header("Filtros")

pv_sel = st.sidebar.multiselect("PV", df["PV"].unique())
cliente_sel = st.sidebar.multiselect("Cliente", df["Cliente"].unique())

if pv_sel:
    df = df[df["PV"].isin(pv_sel)]

if cliente_sel:
    df = df[df["Cliente"].isin(cliente_sel)]

# ===============================
# VISUALIZAÇÃO
# ===============================
tipo = st.selectbox("Visualização", ["Semanal","Mensal"])

if tipo == "Semanal":
    df["Periodo_ord"] = df["Data"].dt.year*100 + df["Data"].dt.isocalendar().week
    df["Periodo"] = "Sem " + df["Data"].dt.isocalendar().week.astype(str)
else:
    df["Periodo_ord"] = df["Data"].dt.year*100 + df["Data"].dt.month
    df["Periodo"] = df["Data"].dt.strftime("%b/%Y")

# ===============================
# PROCESSO
# ===============================
df["Processo"] = df["Maquina"].str.split("_").str[0]

# ===============================
# DEMANDA
# ===============================
demanda = (
    df.groupby(["Periodo","Periodo_ord","Processo"])["Duração (h)"]
    .sum()
    .reset_index()
)

# ===============================
# CAPACIDADE
# ===============================
capacidade = []

for (periodo, proc), grupo in df.groupby(["Periodo","Processo"]):

    dias = grupo["Data"].dt.date.unique()

    total = 0
    for d in dias:
        dias = grupo["Data"].dt.date.unique()

dias_validos = [d for d in dias if pd.Timestamp(d).weekday() <= 4]

total_horas = sum(horas_dia(pd.Timestamp(d)) for d in dias_validos)

qtd = MAQUINAS_QTD.get(proc,1)

capacidade.append({
    "Periodo": periodo,
    "Processo": proc,
    "Capacidade (h)": total_horas * qtd
})
    

cap_df = pd.DataFrame(capacidade)

# ===============================
# JOIN
# ===============================
df_final = pd.merge(demanda, cap_df, on=["Periodo","Processo"], how="left")

# ===============================
# MÉTRICAS
# ===============================
df_final["Ocupação (%)"] = (df_final["Duração (h)"] / df_final["Capacidade (h)"]) * 100
df_final["Disponível (%)"] = 100 - df_final["Ocupação (%)"]

# ===============================
# STATUS (BOLINHAS)
# ===============================
def status(x):
    if x > 100:
        return "🔴"
    elif x > 80:
        return "🟡"
    else:
        return "🟢"

df_final["Status"] = df_final["Ocupação (%)"].apply(status)

# ===============================
# ORDENAÇÃO
# ===============================
df_final = df_final.sort_values("Periodo_ord")

# ===============================
# GRÁFICO (VERTICAL)
# ===============================
st.subheader("📊 Carga por Processo")

df_final["Label"] = df_final["Duração (h)"].astype(int).astype(str) + "h"

fig = px.bar(
    df_final,
    x="Periodo",
    y="Ocupação (%)",
    color="Processo",
    text="Label",
    barmode="group",
    category_orders={"Periodo": df_final["Periodo"].unique()}
)

# linha de gargalo
fig.add_hline(y=100, line_dash="dash")

fig.update_traces(textposition="outside")

st.plotly_chart(fig, use_container_width=True)

# ===============================
# PIZZA
# ===============================
st.subheader("🥧 Ocupação por Processo")

pizza = df.groupby("Processo")["Duração (h)"].sum().reset_index()

fig2 = px.pie(pizza, names="Processo", values="Duração (h)")
fig2.update_traces(textinfo="label+percent")

st.plotly_chart(fig2, use_container_width=True)

# ===============================
# TABELA
# ===============================
st.subheader("📋 Situação da Capacidade")

st.dataframe(df_final, use_container_width=True)

# ===============================
# RESUMO
# ===============================
st.subheader("📊 Resumo")

col1, col2 = st.columns(2)

col1.metric("Carga Total (h)", int(df_final["Duração (h)"].sum()))
col2.metric("Capacidade Total (h)", int(df_final["Capacidade (h)"].sum()))