import streamlit as st
import pandas as pd
import plotly.express as px
import os
import time
import numpy as np

st.set_page_config(layout="wide")
st.title("📊 Dashboard de Capacidade")

# ===============================
# ATUALIZAÇÃO
# ===============================
if st.button("🔄 Atualizar Dados"):
    st.rerun()

st.write("Última atualização:", time.strftime("%d/%m/%Y %H:%M:%S"))

# ===============================
# FUNÇÃO DIAS ÚTEIS
# ===============================
def dias_uteis_no_mes(ano, mes):
    inicio = pd.Timestamp(year=ano, month=mes, day=1)
    fim = inicio + pd.offsets.MonthEnd(1)
    return np.busday_count(inicio.date(), (fim + pd.Timedelta(days=1)).date())

# ===============================
# LEITURA
# ===============================
BASE_PATH = os.getcwd()

df_pv = pd.read_excel(os.path.join(BASE_PATH, "Relacao_Pv.xlsx"))
df_base = pd.read_excel(os.path.join(BASE_PATH, "Processos_de_Fabricacao.xlsx"))

# ===============================
# PADRONIZAÇÃO
# ===============================
df_pv.columns = [c.strip().upper() for c in df_pv.columns]
df_base.columns = [c.strip().upper() for c in df_base.columns]

df_pv = df_pv.rename(columns={
    "CÓDIGO": "CODIGO",
    "DATA DE ENTREGA": "ENTREGA",
    "QUANTIDADE": "QTD"
})

df_pv["CODIGO"] = df_pv["CODIGO"].astype(str).str.strip()
df_base["CODIGO"] = df_base["CODIGO"].astype(str).str.strip()

df_pv["PV"] = df_pv["PV"].astype(str)
df_pv["ENTREGA"] = pd.to_datetime(df_pv["ENTREGA"], errors="coerce")

# ===============================
# PROCESSOS
# ===============================
PROCESSOS_VALIDOS = [
    "FRESADORAS","SOLDAGEM","TORNO","CORTE-PLASMA","CORTE-LASER",
    "SERRA FITA","SERRA CIRCULAR","CENTRO USINAGEM","DOBRADEIRA",
    "PRENSA (AMASSAMENTO)","ROSQUEADEIRA","ACABAMENTO",
    "CALANDRA","PINTURA","METALEIRA"
]

processos = [p for p in PROCESSOS_VALIDOS if p in df_base.columns]

# ===============================
# ROTEIRO
# ===============================
df_base_unico = df_base.drop_duplicates(subset=["CODIGO"])

# ===============================
# EXPANSÃO
# ===============================
linhas = []

for _, row in df_pv.iterrows():

    roteiro = df_base_unico[df_base_unico["CODIGO"] == row["CODIGO"]]

    if roteiro.empty:
        continue

    roteiro = roteiro.iloc[0]

    for proc in processos:

        tempo = pd.to_numeric(roteiro.get(proc), errors="coerce")

        if pd.notna(tempo) and tempo > 0:

            horas = (tempo * row["QTD"]) / 60

            linhas.append({
                "PV": row["PV"],
                "Cliente": row.get("CLIENTE","SEM CLIENTE"),
                "Processo": proc,
                "Data": row["ENTREGA"],
                "Horas": round(horas, 1)
            })

df = pd.DataFrame(linhas)

# ===============================
# DATAS
# ===============================
df["Semana"] = df["Data"].dt.isocalendar().week.astype(int)
df["Ano"] = df["Data"].dt.year
df["Mes"] = df["Data"].dt.month

tipo = st.radio("Visualização", ["Semanal","Mensal"], horizontal=True)

df["Periodo"] = (
    "Sem " + df["Semana"].astype(str)
    if tipo == "Semanal"
    else "Mês " + df["Mes"].astype(str)
)

# ===============================
# CAPACIDADE REAL
# ===============================
EFICIENCIA = 0.8
HORAS_DIA = 8

MAQUINAS = {
    "FRESADORAS":2,"SOLDAGEM":4,"TORNO":3,"CORTE-PLASMA":1,"CORTE-LASER":1,
    "SERRA FITA":1,"SERRA CIRCULAR":1,"CENTRO USINAGEM":1,"DOBRADEIRA":2,
    "PRENSA (AMASSAMENTO)":1,"ROSQUEADEIRA":1,"ACABAMENTO":3,
    "CALANDRA":2,"PINTURA":1,"METALEIRA":1
}

def capacidade(row):
    dias = dias_uteis_no_mes(row["Ano"], row["Mes"])
    maquinas = MAQUINAS.get(row["Processo"],1)
    return int(dias * HORAS_DIA * maquinas * EFICIENCIA)

dem = df.groupby(["Periodo","Processo","Mes","Ano"])["Horas"].sum().reset_index()
dem["Capacidade"] = dem.apply(capacidade, axis=1)

dem["Ocupação (%)"] = ((dem["Horas"]/dem["Capacidade"])*100).round(0).astype(int)

dem["Status"] = dem["Ocupação (%)"].apply(
    lambda x: "🔴" if x > 100 else ("🟡" if x > 80 else "🟢")
)

dem["Saldo (h)"] = (dem["Capacidade"] - dem["Horas"]).round(1)

# ===============================
# GRÁFICOS
# ===============================
st.subheader("📌 Ocupação por Processo (%)")

dem["Label"] = dem["Horas"].map(lambda x: f"{x:.1f}h")

fig = px.bar(
    dem,
    x="Periodo",
    y="Ocupação (%)",
    color="Processo",
    barmode="group",
    text="Label"
)

fig.add_hline(y=100, line_dash="dash")
fig.update_traces(textposition="outside")

st.plotly_chart(fig, use_container_width=True)

# ===============================
# DISTRIBUIÇÃO
# ===============================
st.subheader("📌 Distribuição de Carga por Processo")

df_total = df.groupby("Processo")["Horas"].sum().reset_index()
st.plotly_chart(px.pie(df_total, names="Processo", values="Horas"))

# ===============================
# CLIENTE COM TOTAL
# ===============================
st.subheader("📌 PV por Cliente")

pv_cliente = df.groupby("Cliente")["PV"].nunique().reset_index()

total = pv_cliente["PV"].sum()
pv_cliente = pd.concat([pv_cliente, pd.DataFrame([{"Cliente":"TOTAL","PV":total}])])

fig_cliente = px.bar(pv_cliente, x="Cliente", y="PV", text="PV")
fig_cliente.update_traces(textposition="outside")

st.plotly_chart(fig_cliente, use_container_width=True)

# ===============================
# AUDITORIA
# ===============================
st.subheader("📌 Auditoria de Capacidade")
st.dataframe(dem)

# ===============================
# 🔥 TABELA DE SEMANAS (NOVA)
# ===============================
st.subheader("📅 Calendário Semanal")

df_semanas = df[["Data","Semana","Ano"]].drop_duplicates()

df_semanas["Inicio Semana"] = df_semanas["Data"] - pd.to_timedelta(df_semanas["Data"].dt.weekday, unit="d")
df_semanas["Fim Semana"] = df_semanas["Inicio Semana"] + pd.Timedelta(days=6)

df_semanas = df_semanas.groupby(["Semana","Ano"]).agg({
    "Inicio Semana":"min",
    "Fim Semana":"max"
}).reset_index()

df_semanas = df_semanas.sort_values(["Ano","Semana"])

st.dataframe(df_semanas)