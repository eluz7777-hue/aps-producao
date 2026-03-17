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

# ===============================
# FILTRO DE VISUALIZAÇÃO
# ===============================
tipo = st.selectbox(
    "Selecione o período",
    ["Diário", "Semanal", "Mensal"]
)

# ===============================
# CRIA PERÍODOS
# ===============================
if tipo == "Diário":
    df["Periodo"] = df["Data"].dt.strftime("%d/%m")

elif tipo == "Semanal":
    df["Periodo"] = (
        "Semana " + df["Data"].dt.isocalendar().week.astype(str)
    )

elif tipo == "Mensal":
    df["Periodo"] = df["Data"].dt.strftime("%Y-%m")

# ===============================
# AGRUPAMENTO DEMANDA
# ===============================
demanda = (
    df.groupby(["Periodo", "Maquina"])["Duração (h)"]
    .sum()
    .reset_index()
)

# ===============================
# CAPACIDADE
# ===============================
HORAS_DIA = {
    0: 9,
    1: 9,
    2: 9,
    3: 9,
    4: 8
}

EFICIENCIA = 0.8

def capacidade_dia(data):
    return HORAS_DIA.get(data.weekday(), 0) * EFICIENCIA

# calcula capacidade por período
capacidade = []

for (periodo, maquina), grupo in df.groupby(["Periodo", "Maquina"]):

    datas_unicas = grupo["Data"].dt.date.unique()

    total = 0

    for d in datas_unicas:
        total += capacidade_dia(pd.Timestamp(d))

    capacidade.append({
        "Periodo": periodo,
        "Maquina": maquina,
        "Capacidade (h)": total
    })

cap_df = pd.DataFrame(capacidade)

# ===============================
# JOIN
# ===============================
df_final = pd.merge(
    demanda,
    cap_df,
    on=["Periodo", "Maquina"],
    how="left"
)

# 🔥 NOVA COLUNA (IMPORTANTE)
df_final["Capacidade Disponível (h)"] = df_final["Capacidade (h)"]

# ===============================
# MÉTRICAS
# ===============================
df_final["Ocupação (%)"] = (
    df_final["Duração (h)"] / df_final["Capacidade (h)"]
) * 100

df_final["Excesso (h)"] = (
    df_final["Duração (h)"] - df_final["Capacidade (h)"]
)

# ===============================
# FILTRO DE MÊS (NOVO)
# ===============================
meses = sorted(df["Data"].dt.strftime("%Y-%m").unique())

mes_selecionado = st.selectbox("Filtrar mês", ["Todos"] + meses)

if mes_selecionado != "Todos":
    df_final = df_final[df_final["Periodo"].str.contains(mes_selecionado)]

# ===============================
# GRÁFICO PRINCIPAL
# ===============================
st.subheader("Carga vs Capacidade")

fig = px.bar(
    df_final,
    x="Periodo",
    y=["Duração (h)", "Capacidade Disponível (h)"],
    color="Maquina",
    barmode="group",
    text_auto=True
)

st.plotly_chart(fig, use_container_width=True)

# ===============================
# GARGALOS
# ===============================
st.subheader("🔥 Gargalos")

gargalos = df_final[df_final["Excesso (h)"] > 0]

if gargalos.empty:
    st.success("Sem gargalos")
else:
    st.dataframe(gargalos)

# ===============================
# RESUMO
# ===============================
st.subheader("Resumo Geral")

col1, col2 = st.columns(2)

col1.metric("Carga Total (h)", round(df_final["Duração (h)"].sum(), 2))
col2.metric("Capacidade Total (h)", round(df_final["Capacidade (h)"].sum(), 2))