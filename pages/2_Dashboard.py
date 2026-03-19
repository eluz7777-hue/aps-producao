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

# ===============================
# TRATAMENTO
# ===============================
df["Data"] = pd.to_datetime(df["Início"])
df["Processo"] = df["Maquina"].str.split("_").str[0]

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
tipo = st.selectbox("Visualização", ["Semanal", "Mensal"])

if tipo == "Semanal":
    df["Periodo_ord"] = df["Data"].dt.year * 100 + df["Data"].dt.isocalendar().week
    df["Periodo"] = "Sem " + df["Data"].dt.isocalendar().week.astype(str)
else:
    df["Periodo_ord"] = df["Data"].dt.year * 100 + df["Data"].dt.month
    df["Periodo"] = df["Data"].dt.strftime("%b/%Y")

# ===============================
# CARGA POR MÁQUINA
# ===============================
st.subheader("📊 Carga por Máquina")

maq = (
    df.groupby(["Periodo","Periodo_ord","Maquina"])["Duração (h)"]
    .sum()
    .reset_index()
    .sort_values("Periodo_ord")
)

maq["Label"] = maq["Duração (h)"].astype(int).astype(str) + "h"

fig = px.bar(
    maq,
    x="Periodo",
    y="Duração (h)",
    color="Maquina",
    text="Label",
    barmode="group",
    category_orders={"Periodo": maq["Periodo"].unique()}
)

fig.update_traces(textposition="outside")

st.plotly_chart(fig, use_container_width=True)

# ===============================
# PIZZA MÁQUINA
# ===============================
st.subheader("🥧 Distribuição por Máquina")

pizza = df.groupby("Maquina")["Duração (h)"].sum().reset_index()

fig2 = px.pie(pizza, names="Maquina", values="Duração (h)")
fig2.update_traces(textinfo="label+percent")

st.plotly_chart(fig2, use_container_width=True)

# ===============================
# CARGA POR PROCESSO
# ===============================
st.subheader("📊 Carga por Processo")

proc = (
    df.groupby(["Periodo","Periodo_ord","Processo"])["Duração (h)"]
    .sum()
    .reset_index()
    .sort_values("Periodo_ord")
)

proc["Label"] = proc["Duração (h)"].astype(int).astype(str) + "h"

fig3 = px.bar(
    proc,
    x="Periodo",
    y="Duração (h)",
    color="Processo",
    text="Label",
    barmode="group",
    category_orders={"Periodo": proc["Periodo"].unique()}
)

fig3.update_traces(textposition="outside")

st.plotly_chart(fig3, use_container_width=True)

# ===============================
# PEDIDOS POR CLIENTE
# ===============================
st.subheader("📊 Pedidos por Cliente")

df["Mes"] = df["Data"].dt.strftime("%Y-%m")

cliente = (
    df.groupby(["Mes","Cliente"])["PV"]
    .nunique()
    .reset_index(name="Qtd PV")
)

fig4 = px.bar(
    cliente,
    x="Mes",
    y="Qtd PV",
    color="Cliente",
    text="Qtd PV"
)

fig4.update_traces(textposition="outside")

st.plotly_chart(fig4, use_container_width=True)

# ===============================
# TABELA FINAL
# ===============================
st.subheader("📋 Dados")

st.dataframe(df, use_container_width=True)