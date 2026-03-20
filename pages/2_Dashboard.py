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
# 🔥 SIMULAÇÃO DE PV (NOVO MODELO CORRETO)
# ===============================
st.subheader("Simulação de PV (Entrada / Exclusão)")

if "df_simulado" not in st.session_state:
    st.session_state["df_simulado"] = df.copy()

df = st.session_state["df_simulado"]

col1, col2 = st.columns(2)

# ===============================
# ➕ INSERIR PV (SIMPLIFICADO)
# ===============================
with col1:
    st.markdown("### ➕ Inserir PV")

    with st.form("form_pv"):
        pv = st.text_input("PV")
        codigo = st.text_input("Código da Peça")
        qtd = st.number_input("Quantidade", min_value=1, step=1)
        entrega = st.date_input("Data de Entrega")

        submitted = st.form_submit_button("Simular PV")

        if submitted:

            # 🔥 GERA CARGA SIMPLES (DISTRIBUIÇÃO POR PROCESSO)
            # Aqui usamos distribuição genérica por processo para impacto
            processos = df["Processo"].unique()

            novas_linhas = []

            for proc in processos:
                novas_linhas.append({
                    "PV": pv,
                    "Cliente": "SIMULADO",
                    "Processo": proc,
                    "Maquina": proc + "_SIM",
                    "Início": pd.to_datetime(entrega),
                    "Fim": pd.to_datetime(entrega),
                    "Duração (h)": qtd * 1  # carga estimada simples
                })

            st.session_state["df_simulado"] = pd.concat(
                [df, pd.DataFrame(novas_linhas)],
                ignore_index=True
            )

            st.success("PV simulada adicionada")

# ===============================
# ➖ REMOVER PV
# ===============================
with col2:
    st.markdown("### ➖ Remover PV")

    lista_pv = df["PV"].dropna().unique()

    pv_remove = st.selectbox("Selecione a PV", lista_pv)

    if st.button("Remover PV"):
        st.session_state["df_simulado"] = df[df["PV"] != pv_remove]
        st.success("PV removida")

# Atualiza df
df = st.session_state["df_simulado"]

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
# DATAS
# ===============================
df["Semana"] = df["Data"].dt.isocalendar().week.astype(int)
df["Ano"] = df["Data"].dt.year
df["Mes"] = df["Data"].dt.month.astype(int)

df["Processo"] = df["Maquina"].str.split("_").str[0]

# ===============================
# SELETOR
# ===============================
tipo_visao = st.radio(
    "Visualização do Gráfico Principal",
    ["Semanal", "Mensal"],
    horizontal=True
)

# ===============================
# PERIODO
# ===============================
if tipo_visao == "Semanal":
    df["Periodo"] = "Sem " + df["Semana"].astype(str)
    df["Periodo_ord"] = df["Ano"]*100 + df["Semana"]
else:
    df["Periodo"] = "Mês " + df["Mes"].astype(str)
    df["Periodo_ord"] = df["Ano"]*100 + df["Mes"]

# ===============================
# DEMANDA
# ===============================
dem = df.groupby(
    ["Periodo","Periodo_ord","Processo"],
    as_index=False
)["Duração (h)"].sum()

# ===============================
# CAPACIDADE
# ===============================
cap = []

for (periodo, proc), g in df.groupby(["Periodo","Processo"]):
    dias = g["Data"].dt.date.unique()
    horas = sum(horas_dia(pd.Timestamp(d)) for d in dias)
    qtd = MAQUINAS_QTD.get(proc,1)

    capacidade = horas * qtd

    cap.append({
        "Periodo": periodo,
        "Processo": proc,
        "Capacidade (h)": capacidade,
        "Horas Disponíveis": capacidade
    })

cap_df = pd.DataFrame(cap)

# ===============================
# MERGE
# ===============================
df_final = pd.merge(
    dem,
    cap_df,
    on=["Periodo","Processo"],
    how="left"
)

df_final = df_final.sort_values("Periodo_ord")

# ===============================
# OCUPAÇÃO
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

# ===============================
# GRÁFICO PRINCIPAL
# ===============================
st.subheader("Ocupação por Processo")

fig = px.bar(
    df_final,
    x="Periodo",
    y="Ocupação (%)",
    color="Processo",
    barmode="group",
    text=df_final["Duração (h)"].fillna(0).astype(int)
)

fig.add_hline(y=100, line_dash="dash")
fig.update_traces(textposition="outside")

st.plotly_chart(fig, use_container_width=True)

# ===============================
# RESTANTE (INALTERADO)
# ===============================
st.subheader("Distribuição de Carga por Processo (Geral)")
pizza = df.groupby("Processo")["Duração (h)"].sum().reset_index()
st.plotly_chart(px.pie(pizza, names="Processo", values="Duração (h)"), use_container_width=True)

st.subheader("Distribuição por Processo - POR SEMANA")
semana_sel = st.selectbox("Semana", sorted(df["Semana"].unique()))
df_sem = df[df["Semana"] == semana_sel]
pizza_sem = df_sem.groupby("Processo")["Duração (h)"].sum().reset_index()
st.plotly_chart(px.pie(pizza_sem, names="Processo", values="Duração (h)"), use_container_width=True)

st.subheader("Distribuição por Processo - POR MÊS")
mes_sel = st.selectbox("Mês", sorted(df["Mes"].unique()))
df_mes = df[df["Mes"] == mes_sel]
pizza_mes = df_mes.groupby("Processo")["Duração (h)"].sum().reset_index()
st.plotly_chart(px.pie(pizza_mes, names="Processo", values="Duração (h)"), use_container_width=True)

st.subheader("Número de PV por Cliente")
pv_cliente = df.groupby("Cliente")["PV"].nunique().reset_index()
st.plotly_chart(px.bar(pv_cliente, x="Cliente", y="PV", text="PV"), use_container_width=True)

st.subheader("Carga Mensal")
mensal = df.groupby("Mes")["Duração (h)"].sum().reset_index()
st.plotly_chart(px.bar(mensal, x="Mes", y="Duração (h)"), use_container_width=True)

st.subheader("Mapa de Semanas")
semana_map = df.groupby("Semana")["Data"].agg(["min","max"]).reset_index()
semana_map.rename(columns={"min":"Início","max":"Fim"}, inplace=True)
st.dataframe(semana_map)

st.subheader("Tabela de Capacidade")
st.dataframe(df_final)