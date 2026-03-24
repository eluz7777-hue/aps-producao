import streamlit as st

# ===============================
# 🔐 BLOQUEIO DE ACESSO GLOBAL
# ===============================
if "logado" not in st.session_state or not st.session_state.logado:
    st.warning("🔒 Acesso não autorizado. Redirecionando para login...")
    st.switch_page("app.py")

import pandas as pd
import plotly.express as px
import os
import time
import holidays
import math

st.set_page_config(layout="wide")

# ===============================
# LOGO + TÍTULO
# ===============================
col1, col2 = st.columns([1, 6])

with col1:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=80)

with col2:
    st.title("📊 ELOHIM APS – Advanced Planning System")

# ===============================
# CONFIG
# ===============================
EFICIENCIA = 0.8
HORAS_DIA = 8

MAQUINAS = {
    "FRESADORAS": 2,
    "SOLDAGEM": 4,
    "TORNO": 3,
    "CORTE-PLASMA": 1,
    "CORTE-LASER": 1,
    "SERRA FITA": 1,
    "SERRA CIRCULAR": 1,
    "CENTRO USINAGEM": 1,
    "DOBRADEIRA": 2,
    "PRENSA (AMASSAMENTO)": 1,
    "ROSQUEADEIRA": 1,
    "ACABAMENTO": 3,
    "CALANDRA": 2,
    "PINTURA": 1,
    "METALEIRA": 1
}

# ===============================
# FERIADOS
# ===============================
br_holidays = holidays.Brazil()

def dias_uteis_periodo(inicio, fim):
    if pd.isna(inicio) or pd.isna(fim):
        return 0
    dias = pd.date_range(inicio, fim, freq="D")
    return sum(1 for d in dias if d.weekday() < 5 and d.date() not in br_holidays)

def dias_uteis_mes(ano, mes):
    inicio = pd.Timestamp(year=int(ano), month=int(mes), day=1)
    fim = inicio + pd.offsets.MonthEnd(1)
    return dias_uteis_periodo(inicio, fim)

# ===============================
# CACHE
# ===============================
@st.cache_data
def carregar_dados(base_path):
    df_pv = pd.read_excel(os.path.join(base_path, "Relacao_Pv.xlsx"))
    df_base = pd.read_excel(os.path.join(base_path, "Processos_de_Fabricacao.xlsx"))
    return df_pv, df_base

# ===============================
# ATUALIZAÇÃO
# ===============================
if st.button("🔄 Atualizar Dados"):
    st.cache_data.clear()
    st.rerun()

st.write("Última atualização:", time.strftime("%d/%m/%Y %H:%M:%S"))

BASE_PATH = os.getcwd()

df_pv, df_base = carregar_dados(BASE_PATH)

# ===============================
# TRATAMENTO
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

df_pv["PV"] = df_pv["PV"].astype(str).str.strip()
df_pv["ENTREGA"] = pd.to_datetime(df_pv["ENTREGA"], errors="coerce")
df_pv["QTD"] = pd.to_numeric(df_pv["QTD"], errors="coerce").fillna(0)

df_base = df_base.drop_duplicates(subset=["CODIGO"])

# ===============================
# EXPANSÃO
# ===============================
processos = [p for p in MAQUINAS.keys() if p in df_base.columns]

linhas = []

for _, row in df_pv.iterrows():
    roteiro = df_base[df_base["CODIGO"] == row["CODIGO"]]

    if roteiro.empty:
        continue

    roteiro = roteiro.iloc[0]

    for proc in processos:
        tempo = pd.to_numeric(roteiro.get(proc), errors="coerce")

        if pd.notna(tempo) and tempo > 0:
            horas = (tempo * float(row["QTD"])) / 60

            linhas.append({
                "PV": row["PV"],
                "Cliente": row.get("CLIENTE", "SEM CLIENTE"),
                "Processo": proc,
                "Data": row["ENTREGA"],
                "Horas": horas
            })

df = pd.DataFrame(linhas)

if df.empty:
    st.warning("Nenhum dado válido encontrado.")
    st.stop()

# ===============================
# FILTRO
# ===============================
df["Cliente"] = df["Cliente"].fillna("SEM CLIENTE")

cliente = st.selectbox("Filtrar Cliente", ["Todos"] + sorted(df["Cliente"].unique()))

if cliente != "Todos":
    df = df[df["Cliente"] == cliente]

# ===============================
# DATAS
# ===============================
df["Semana"] = df["Data"].dt.isocalendar().week.astype(int)
df["Ano"] = df["Data"].dt.year
df["Mes"] = df["Data"].dt.month

# ===============================
# CAPACIDADE MENSAL (CORRETA)
# ===============================
mes_ref = int(df["Mes"].mode()[0])
ano_ref = int(df["Ano"].mode()[0])

dias_mes = dias_uteis_mes(ano_ref, mes_ref)
total_recursos = sum(MAQUINAS.values())

CAPACIDADE_MENSAL = int(dias_mes * total_recursos * HORAS_DIA * EFICIENCIA)

# ===============================
# FILA
# ===============================
df = df.sort_values(by=["Processo","Data"])
df["Fila"] = df.groupby("Processo")["Horas"].cumsum()

# ===============================
# VISÃO
# ===============================
tipo = st.radio("Visualização", ["Semanal","Mensal"], horizontal=True)

if tipo == "Semanal":
    df["Periodo"] = "Sem " + df["Semana"].astype(str)
else:
    df["Periodo"] = "Mês " + df["Mes"].astype(str)

dem = df.groupby(["Periodo","Processo"])["Horas"].sum().reset_index()

# ===============================
# STATUS (BOLINHAS)
# ===============================
dem["Capacidade"] = CAPACIDADE_MENSAL / len(MAQUINAS)
dem["Ocupação (%)"] = (dem["Horas"]/dem["Capacidade"]*100).round(0)

def status(x):
    if x > 100: return "🔴"
    elif x > 80: return "🟡"
    else: return "🟢"

dem["Status"] = dem["Ocupação (%)"].apply(status)

# ===============================
# RESUMO (RESTAURADO)
# ===============================
pv_carga = df.groupby(["PV","Data"])["Horas"].sum().reset_index()

pv_carga["Dias Necessários"] = pv_carga["Horas"] / HORAS_DIA

hoje = pd.Timestamp.today()

pv_carga["Dias Disponíveis"] = pv_carga["Data"].apply(
    lambda x: dias_uteis_periodo(hoje, x)
)

pv_carga["Atraso"] = pv_carga["Dias Necessários"] - pv_carga["Dias Disponíveis"]

atrasos = pv_carga[pv_carga["Atraso"] > 0]
risco = pv_carga[(pv_carga["Atraso"] <= 0) & (pv_carga["Atraso"] > -2)]

st.subheader("📊 Resumo Geral")

c1, c2, c3 = st.columns(3)

c1.metric("🔴 Atraso", len(atrasos))
c2.metric("🟡 Risco", len(risco))
c3.metric("🟢 OK", len(pv_carga) - len(atrasos) - len(risco))

# ===============================
# CAPACIDADE VS CARGA
# ===============================
st.subheader("📊 Capacidade vs Carga vs Ociosidade")

carga_total = df["Horas"].sum()
ociosidade = CAPACIDADE_MENSAL - carga_total

c1, c2, c3 = st.columns(3)

c1.metric("Capacidade", CAPACIDADE_MENSAL)
c2.metric("Carga", int(carga_total))
c3.metric("Ociosidade", int(ociosidade))

# ===============================
# GRÁFICO
# ===============================
fig = px.bar(dem, x="Periodo", y="Ocupação (%)", color="Processo", text="Horas")
fig.add_hline(y=100, line_dash="dash")

st.plotly_chart(fig, use_container_width=True)

# ===============================
# AUDITORIA
# ===============================
st.subheader("📋 Auditoria")

st.dataframe(dem)

# ===============================
# RANKING GARGALOS
# ===============================
st.subheader("🔥 Ranking Geral")

ranking = df.groupby("Processo")["Horas"].sum().reset_index()
ranking = ranking.sort_values(by="Horas", ascending=False)

st.dataframe(ranking)