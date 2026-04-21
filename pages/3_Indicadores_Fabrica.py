import streamlit as st

st.set_page_config(page_title="Indicadores da Fábrica", layout="wide")

st.title("📊 Indicadores da Fábrica")
st.caption("Visão estratégica consolidada da operação industrial.")

# ===============================
# KPIs GERAIS
# ===============================
st.subheader("📌 Indicadores Principais")

k1, k2, k3, k4 = st.columns(4)

k1.metric("🏭 Produção Total", "—")
k2.metric("⏱️ Horas Produzidas", "—")
k3.metric("📈 Eficiência Global", "—")
k4.metric("🚨 Atrasos", "—")


# ===============================
# VISÃO EXECUTIVA
# ===============================
st.subheader("🧠 Visão Executiva")

st.info("Aqui entrarão análises consolidadas da fábrica.")