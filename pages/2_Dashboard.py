import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("📊 DASHBOARD INDUSTRIAL - APS ELOHIM")

# ===============================
# VALIDAÇÃO
# ===============================
if "dados_dashboard" not in st.session_state:
    st.warning("Execute o APS primeiro")
    st.stop()

df = st.session_state["dados_dashboard"].copy()
df["Data"] = pd.to_datetime(df["Início"])

# ===============================
# PARÂMETROS
# ===============================
EFICIENCIA = 0.8
HORAS_DIA = {0:9,1:9,2:9,3:9,4:8}

MAQUINAS_QTD = {
    "FRESA":2,"SOLDA":4,"TORNO":3,"PLASMA":1,"LASER":1,
    "SERRA":2,"CNC":1,"DOBRA":2,"PRENSA":1,"ROSQ":1,
    "ACAB":3,"CALANDRA":2,"PINTURA":1,"METALEIRA":1
}

def horas_dia(d):
    return HORAS_DIA.get(d.weekday(),0) * EFICIENCIA

# ===============================
# TRATAMENTO DE DADOS
# ===============================
df["Semana"] = df["Data"].dt.isocalendar().week
df["Ano"] = df["Data"].dt.year
df["Mes"] = df["Data"].dt.month

df["Periodo"] = "Sem " + df["Semana"].astype(str)
df["Periodo_ord"] = df["Ano"]*100 + df["Semana"]

df["Processo"] = df["Maquina"].str.split("_").str[0]

# ===============================
# DEMANDA
# ===============================
dem = df.groupby(
    ["Periodo","Periodo_ord","Processo"]
)["Duração (h)"].sum().reset_index()

# ===============================
# CAPACIDADE REAL
# ===============================
cap = []

for (p, proc), g in df.groupby(["Periodo","Processo"]):

    dias = g["Data"].dt.date.unique()
    horas = sum(horas_dia(pd.Timestamp(d)) for d in dias)

    qtd = MAQUINAS_QTD.get(proc,1)

    capacidade = horas * qtd

    cap.append({
        "Periodo":p,
        "Processo":proc,
        "Capacidade (h)": capacidade,
        "Horas Disponíveis": capacidade
    })

cap_df = pd.DataFrame(cap)

df_final = pd.merge(dem, cap_df, on=["Periodo","Processo"])

# ===============================
# OCUPAÇÃO E STATUS
# ===============================
df_final["Ocupação (%)"] = (
    df_final["Duração (h)"] / df_final["Capacidade (h)"]
) * 100

def status(x):
    if x > 100:
        return "🔴"
    elif x > 80:
        return "🟡"
    else:
        return "🟢"

df_final["Status"] = df_final["Ocupação (%)"].apply(status)

df_final = df_final.sort_values("Periodo_ord")

# ===============================
# GRÁFICO PRINCIPAL (VERTICAL)
# ===============================
st.subheader("Ocupação por Processo (Semanal)")

fig = px.bar(
    df_final,
    x="Periodo",
    y="Ocupação (%)",
    color="Processo",
    barmode="group",  # 🔥 vertical, NÃO empilhado
    text=df_final["Duração (h)"].astype(int)
)

fig.add_hline(y=100, line_dash="dash")
fig.update_traces(textposition="outside")

st.plotly_chart(fig, use_container_width=True)

# ===============================
# PIZZA GERAL
# ===============================
st.subheader("Distribuição de Carga por Processo (Geral)")

pizza = df.groupby("Processo")["Duração (h)"].sum().reset_index()

st.plotly_chart(
    px.pie(
        pizza,
        names="Processo",
        values="Duração (h)",
        title="Carga Total por Processo"
    ),
    use_container_width=True
)

# ===============================
# PIZZA POR SEMANA
# ===============================
st.subheader("Distribuição por Processo - POR SEMANA")

semana_sel = st.selectbox(
    "Selecione a semana",
    sorted(df["Semana"].unique())
)

df_sem = df[df["Semana"] == semana_sel]

pizza_sem = df_sem.groupby("Processo")["Duração (h)"].sum().reset_index()

st.plotly_chart(
    px.pie(
        pizza_sem,
        names="Processo",
        values="Duração (h)",
        title=f"Semana {semana_sel}"
    ),
    use_container_width=True
)

# ===============================
# PIZZA POR MÊS
# ===============================
st.subheader("Distribuição por Processo - POR MÊS")

mes_sel = st.selectbox(
    "Selecione o mês",
    sorted(df["Mes"].unique())
)

df_mes = df[df["Mes"] == mes_sel]

pizza_mes = df_mes.groupby("Processo")["Duração (h)"].sum().reset_index()

st.plotly_chart(
    px.pie(
        pizza_mes,
        names="Processo",
        values="Duração (h)",
        title=f"Mês {mes_sel}"
    ),
    use_container_width=True
)

# ===============================
# PV POR CLIENTE
# ===============================
st.subheader("Número de PV por Cliente")

pv_cliente = df.groupby("Cliente")["PV"].nunique().reset_index()

st.plotly_chart(
    px.bar(
        pv_cliente,
        x="Cliente",
        y="PV",
        text="PV"
    ),
    use_container_width=True
)

# ===============================
# CAPACIDADE MENSAL
# ===============================
st.subheader("Carga Mensal (Horas)")

mensal = df.groupby("Mes")["Duração (h)"].sum().reset_index()

st.plotly_chart(
    px.bar(
        mensal,
        x="Mes",
        y="Duração (h)",
        text="Duração (h)"
    ),
    use_container_width=True
)

# ===============================
# MAPA DE SEMANAS
# ===============================
st.subheader("Mapa de Semanas (Datas Reais)")

semana_map = df.groupby("Semana")["Data"].agg(["min","max"]).reset_index()

semana_map.rename(columns={
    "min":"Início",
    "max":"Fim"
}, inplace=True)

st.dataframe(semana_map)

# ===============================
# TABELA FINAL
# ===============================
st.subheader("Tabela de Capacidade")

st.dataframe(df_final[[
    "Periodo",
    "Processo",
    "Duração (h)",
    "Horas Disponíveis",
    "Capacidade (h)",
    "Ocupação (%)",
    "Status"
]])