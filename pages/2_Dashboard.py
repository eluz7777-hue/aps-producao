import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")

st.title("📊 DASHBOARD DE CAPACIDADE")

if "dados_dashboard" not in st.session_state:
    st.stop()

df = st.session_state["dados_dashboard"].copy()

if "Início" not in df.columns:
    st.error("APS não gerou dados corretamente.")
    st.stop()

df["Data"] = pd.to_datetime(df["Início"])

# ===============================
# PEDIDOS POR CLIENTE
# ===============================
st.subheader("📊 Pedidos por Cliente (Mensal)")

if "Cliente" in df.columns:

    df["Mes"] = df["Data"].dt.strftime("%Y-%m")

    pedidos_cliente = (
        df.groupby(["Mes","Cliente"])["PV"]
        .nunique()
        .reset_index(name="Qtd PV")
    )

    fig_cliente = px.bar(
        pedidos_cliente,
        x="Mes",
        y="Qtd PV",
        color="Cliente",
        barmode="group",
        text="Qtd PV"
    )

    fig_cliente.update_traces(textposition="outside")

    st.plotly_chart(fig_cliente, use_container_width=True)

# ===============================
# DADOS CAPACIDADE
# ===============================
df["Processo"] = df["Maquina"].str.split("_").str[0]

st.subheader("📋 Dados")

st.dataframe(df, use_container_width=True)