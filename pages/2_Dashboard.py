import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")

st.title("📊 DASHBOARD DE CAPACIDADE")

if "dados_dashboard" not in st.session_state:
    st.warning("Execute o APS primeiro")
    st.stop()

df = st.session_state["dados_dashboard"].copy()

df["Data"] = pd.to_datetime(df["Início"])

# ===============================
# CLIENTE
# ===============================
st.subheader("📊 Pedidos por Cliente (Mensal)")

if "Cliente" in df.columns:

    df["Mes"] = df["Data"].dt.strftime("%Y-%m")

    pedidos_cliente = (
        df.groupby(["Mes","Cliente"])["PV"]
        .nunique()
        .reset_index(name="Qtd PV")
    )

    fig = px.bar(
        pedidos_cliente,
        x="Mes",
        y="Qtd PV",
        color="Cliente",
        text="Qtd PV"
    )

    fig.update_traces(textposition="outside")

    st.plotly_chart(fig, use_container_width=True)