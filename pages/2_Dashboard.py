import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")

st.title("📊 DASHBOARD - APS ELOHIM")

# ===============================
# DADOS SIMULADOS (TEMPORÁRIO)
# depois vamos ligar com o APS real
# ===============================

dados = pd.DataFrame({
    "Processo": ["Corte", "Laser", "Fresa", "Solda", "Acabamento"],
    "Carga (h)": [20, 35, 50, 80, 25]
})

total_horas = dados["Carga (h)"].sum()
gargalo = dados.sort_values("Carga (h)", ascending=False).iloc[0]

# ===============================
# KPIs
# ===============================

col1, col2, col3, col4 = st.columns(4)

col1.metric("⏱️ Total de Horas", f"{total_horas} h")
col2.metric("🚨 Gargalo", gargalo["Processo"])
col3.metric("📦 Ordens", "12")
col4.metric("⚙️ Ocupação Média", "78%")

# ===============================
# GRÁFICO DE CARGA
# ===============================

st.subheader("Carga por Processo")

fig = px.bar(
    dados,
    x="Processo",
    y="Carga (h)",
    text="Carga (h)",
    color="Processo"
)

st.plotly_chart(fig, use_container_width=True)

# ===============================
# PERÍODO
# ===============================

st.subheader("Análise por Período")

periodo = st.selectbox(
    "Selecione o período",
    ["Diário", "Semanal", "Mensal"]
)

if periodo == "Diário":
    st.info("Visão detalhada do dia")
elif periodo == "Semanal":
    st.info("Visão consolidada da semana")
else:
    st.info("Visão estratégica mensal")

# ===============================
# ALERTAS
# ===============================

st.subheader("Alertas")

if gargalo["Carga (h)"] > 60:
    st.error(f"Gargalo crítico em {gargalo['Processo']}")
else:
    st.success("Fábrica dentro da capacidade")