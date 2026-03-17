import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")

st.title("📊 APS ELOHIM - CAPACIDADE INDUSTRIAL")

# ===============================
# CONFIGURAÇÃO
# ===============================
EFICIENCIA = 0.8

HORAS_DIA = {
    0: 9,
    1: 9,
    2: 9,
    3: 9,
    4: 8
}

# quantidade de máquinas
MAQUINAS_QTD = {
    "LASER_1": 1,
    "FRESA_1": 1,
    "FRESA_2": 1,
    "FRESA_3": 1,
    "TORNO_1": 1,
    "TORNO_2": 1,
    "SOLDA_1": 1,
    "SOLDA_2": 1,
    "SOLDA_3": 1,
    "ACAB_1": 1,
    "ACAB_2": 1,
    "SERRA_1": 1,
    "PRENSA_1": 1
}

# ===============================
# VALIDAR DADOS
# ===============================
if "dados_dashboard" not in st.session_state:
    st.warning("Execute o APS primeiro")
    st.stop()

df = st.session_state["dados_dashboard"].copy()

df["Início"] = pd.to_datetime(df["Início"])

# ===============================
# PERÍODO
# ===============================
st.subheader("📅 Análise por Período")

periodo = st.selectbox(
    "Selecione o período",
    ["Diário", "Semanal", "Mensal"]
)

if periodo == "Diário":
    df["Periodo"] = df["Início"].dt.date.astype(str)

elif periodo == "Semanal":
    df["Periodo"] = df["Início"].dt.to_period("W").astype(str)

elif periodo == "Mensal":
    df["Periodo"] = df["Início"].dt.to_period("M").astype(str)

# ===============================
# DEMANDA
# ===============================
demanda = (
    df.groupby(["Periodo", "Maquina"])["Duração (h)"]
    .sum()
    .reset_index()
)

# ===============================
# CAPACIDADE
# ===============================
def calcular_capacidade(periodo_str):

    datas = pd.date_range(start=periodo_str + "-01", periods=31)

    dias_uteis = [d for d in datas if d.weekday() <= 4]

    horas = sum([HORAS_DIA[d.weekday()] for d in dias_uteis])

    return horas * EFICIENCIA

capacidade_lista = []

for periodo_val in demanda["Periodo"].unique():

    base_cap = calcular_capacidade(periodo_val)

    for maquina in demanda["Maquina"].unique():

        qtd = MAQUINAS_QTD.get(maquina, 1)

        capacidade_lista.append({
            "Periodo": periodo_val,
            "Maquina": maquina,
            "Capacidade (h)": base_cap * qtd
        })

capacidade_df = pd.DataFrame(capacidade_lista)

# ===============================
# MERGE
# ===============================
df_final = pd.merge(
    demanda,
    capacidade_df,
    on=["Periodo", "Maquina"],
    how="left"
)

df_final["Ocupação (%)"] = (
    df_final["Duração (h)"] / df_final["Capacidade (h)"]
) * 100

df_final["Excesso (h)"] = (
    df_final["Duração (h)"] - df_final["Capacidade (h)"]
)

# ===============================
# GRÁFICO DEMANDA vs CAPACIDADE
# ===============================
st.subheader("🏭 Demanda vs Capacidade")

fig = px.bar(
    df_final,
    x="Maquina",
    y=["Duração (h)", "Capacidade (h)"],
    barmode="group",
    text_auto=True
)

st.plotly_chart(fig, use_container_width=True)

# ===============================
# GARGALOS
# ===============================
st.subheader("🔥 Gargalos Reais")

gargalos = df_final[df_final["Excesso (h)"] > 0]

if gargalos.empty:
    st.success("Nenhum gargalo no período")
else:
    st.dataframe(gargalos)

# ===============================
# OCUPAÇÃO
# ===============================
st.subheader("📊 Ocupação (%)")

fig2 = px.bar(
    df_final,
    x="Maquina",
    y="Ocupação (%)",
    text_auto=True
)

st.plotly_chart(fig2, use_container_width=True)