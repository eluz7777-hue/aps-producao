import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("📊 APS ELOHIM - DASHBOARD INDUSTRIAL")

# ===============================
# BASES (SEM SIMULAÇÃO)
# ===============================
df_pv = pd.read_excel("Relacao_Pv.xlsx")
df_base = pd.read_excel("Processos_de_Fabricacao.xlsx")

df_pv.columns = [c.strip().upper() for c in df_pv.columns]
df_base.columns = [c.strip().upper() for c in df_base.columns]

df_pv = df_pv.rename(columns={
    "CÓDIGO": "CODIGO",
    "DATA DE ENTREGA": "ENTREGA",
    "QUANTIDADE": "QTD"
})

df_pv["CODIGO"] = df_pv["CODIGO"].astype(str)
df_pv["PV"] = df_pv["PV"].astype(str)
df_pv["ENTREGA"] = pd.to_datetime(df_pv["ENTREGA"])

df_base["CODIGO"] = df_base["CODIGO"].astype(str)

# ===============================
# PROCESSOS VÁLIDOS (FIXO)
# ===============================
PROCESSOS_VALIDOS = [
    "FRESADORAS","SOLDAGEM","TORNO","CORTE-PLASMA","CORTE-LASER",
    "SERRA FITA","SERRA CIRCULAR","CENTRO USINAGEM","DOBRADEIRA",
    "PRENSA (AMASSAMENTO)","ROSQUEADEIRA","ACABAMENTO",
    "CALANDRA","PINTURA","METALEIRA"
]

processos = [p for p in PROCESSOS_VALIDOS if p in df_base.columns]

# ===============================
# EXPANSÃO PROCESSOS
# ===============================
linhas = []

for _, row in df_pv.iterrows():

    roteiro = df_base[df_base["CODIGO"] == row["CODIGO"]]

    if roteiro.empty:
        continue

    for proc in processos:

        tempo = pd.to_numeric(roteiro.iloc[0][proc], errors="coerce")

        if pd.notna(tempo) and tempo > 0:

            horas = int((tempo * row["QTD"]) / 60)  # 🔥 SEM DECIMAL

            linhas.append({
                "PV": row["PV"],
                "Cliente": row.get("CLIENTE","SEM CLIENTE"),
                "Processo": proc,
                "Data": row["ENTREGA"],
                "Horas": horas
            })

df = pd.DataFrame(linhas)

# ===============================
# DATAS
# ===============================
df["Semana"] = df["Data"].dt.isocalendar().week.astype(int)
df["Mes"] = df["Data"].dt.month

# ===============================
# CAPACIDADE
# ===============================
EFICIENCIA = 0.8
HORAS_SEMANA = 44

MAQUINAS = {
    "FRESADORAS":2,"SOLDAGEM":4,"TORNO":3,"CORTE-PLASMA":1,"CORTE-LASER":1,
    "SERRA FITA":1,"SERRA CIRCULAR":1,"CENTRO USINAGEM":1,"DOBRADEIRA":2,
    "PRENSA (AMASSAMENTO)":1,"ROSQUEADEIRA":1,"ACABAMENTO":3,
    "CALANDRA":2,"PINTURA":1,"METALEIRA":1
}

# ===============================
# VISÃO
# ===============================
tipo = st.radio("Visualização", ["Semanal","Mensal"], horizontal=True)

if tipo == "Semanal":
    df["Periodo"] = "Sem " + df["Semana"].astype(str)
else:
    df["Periodo"] = "Mês " + df["Mes"].astype(str)

# ===============================
# DEMANDA
# ===============================
dem = df.groupby(["Periodo","Processo"])["Horas"].sum().reset_index()

def capacidade(proc):
    return int(HORAS_SEMANA * MAQUINAS.get(proc,1) * EFICIENCIA)

dem["Capacidade"] = dem["Processo"].apply(capacidade)
dem["Ocupação (%)"] = (dem["Horas"]/dem["Capacidade"])*100

# ===============================
# STATUS (BOLINHAS)
# ===============================
def status(x):
    if x > 100: return "🔴"
    elif x > 80: return "🟡"
    else: return "🟢"

dem["Status"] = dem["Ocupação (%)"].apply(status)

dem["Saldo (h)"] = dem["Capacidade"] - dem["Horas"]

# ===============================
# GRÁFICO PRINCIPAL
# ===============================
st.subheader("Ocupação por Processo (%)")

fig = px.bar(
    dem,
    x="Periodo",
    y="Ocupação (%)",
    color="Processo",
    barmode="group",
    text=dem["Horas"]
)

fig.add_hline(y=100, line_dash="dash")
fig.update_traces(textposition="outside")

st.plotly_chart(fig, use_container_width=True)

# ===============================
# PIZZA GERAL
# ===============================
st.subheader("Distribuição de Carga por Processo (Horas)")
st.plotly_chart(px.pie(df, names="Processo", values="Horas"))

# ===============================
# PIZZA SEMANA
# ===============================
st.subheader("Distribuição por Processo - Semana")
sem = st.selectbox("Semana", sorted(df["Semana"].unique()))
st.plotly_chart(px.pie(df[df["Semana"]==sem], names="Processo", values="Horas"))

# ===============================
# PIZZA MÊS
# ===============================
st.subheader("Distribuição por Processo - Mês")
mes = st.selectbox("Mês", sorted(df["Mes"].unique()))
st.plotly_chart(px.pie(df[df["Mes"]==mes], names="Processo", values="Horas"))

# ===============================
# PV POR CLIENTE
# ===============================
st.subheader("Quantidade de PV por Cliente")

pv_cliente = df.groupby("Cliente")["PV"].nunique().reset_index()

fig_cliente = px.bar(
    pv_cliente,
    x="Cliente",
    y="PV",
    text="PV"
)

fig_cliente.update_traces(textposition="outside")

st.plotly_chart(fig_cliente, use_container_width=True)

# ===============================
# CARGA MENSAL
# ===============================
st.subheader("Carga Mensal (Horas)")

mensal = df.groupby("Mes")["Horas"].sum().reset_index()

fig_mensal = px.bar(
    mensal,
    x="Mes",
    y="Horas",
    text="Horas"
)

fig_mensal.update_traces(textposition="outside")

st.plotly_chart(fig_mensal, use_container_width=True)

# ===============================
# TABELA FINAL
# ===============================
st.subheader("Auditoria de Capacidade (Gargalos)")

st.dataframe(dem)