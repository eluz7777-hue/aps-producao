import streamlit as st

# ===============================
# 🔐 BLOQUEIO DE ACESSO GLOBAL
# ===============================
if "logado" not in st.session_state or not st.session_state.logado:
    st.warning("🔒 Acesso não autorizado. Redirecionando para login...")
    st.switch_page("app.py")

import streamlit as st
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
# CACHE DE LEITURA
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

# ===============================
# LEITURA
# ===============================
BASE_PATH = os.getcwd()

df_pv, df_base = carregar_dados(BASE_PATH)

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
# PROCESSOS
# ===============================
PROCESSOS_VALIDOS = [
    "FRESADORAS", "SOLDAGEM", "TORNO", "CORTE-PLASMA", "CORTE-LASER",
    "SERRA FITA", "SERRA CIRCULAR", "CENTRO USINAGEM", "DOBRADEIRA",
    "PRENSA (AMASSAMENTO)", "ROSQUEADEIRA", "ACABAMENTO",
    "CALANDRA", "PINTURA", "METALEIRA"
]

processos = [p for p in PROCESSOS_VALIDOS if p in df_base.columns]

# ===============================
# EXPANSÃO CORRIGIDA (SEM ERRO)
# ===============================
linhas = []

for _, row in df_pv.iterrows():
    roteiro = df_base[df_base["CODIGO"] == row["CODIGO"]]

    if roteiro.empty:
        continue

    roteiro = roteiro.iloc[0]

    for proc in processos:
        tempo = pd.to_numeric(roteiro.get(proc), errors="coerce")

        # Mantida a proteção já existente
        if pd.notna(tempo) and tempo > 0 and tempo < 1000:
            horas = (tempo * float(row["QTD"])) / 60

            linhas.append({
                "PV": row["PV"],
                "Cliente": row.get("CLIENTE", "SEM CLIENTE"),
                "Processo": proc,
                "Data": row["ENTREGA"],
                "Horas": horas  # sem arredondar na base
            })

df = pd.DataFrame(linhas)

if df.empty:
    st.warning("Nenhum dado válido foi encontrado para exibir no dashboard.")
    st.stop()

# ===============================
# FILTRO POR CLIENTE
# ===============================
df["Cliente"] = df["Cliente"].fillna("SEM CLIENTE").astype(str).str.strip()

clientes_disponiveis = sorted(df["Cliente"].dropna().unique().tolist())
cliente_sel = st.selectbox("Filtrar Cliente", ["Todos"] + clientes_disponiveis)

if cliente_sel != "Todos":
    df = df[df["Cliente"] == cliente_sel].copy()

if df.empty:
    st.warning("Nenhum dado encontrado para o filtro selecionado.")
    st.stop()

# ===============================
# DATAS
# ===============================
df["Semana"] = df["Data"].dt.isocalendar().week.astype(int)
df["Ano"] = df["Data"].dt.year
df["Mes"] = df["Data"].dt.month

# ===============================
# FILA REAL POR PROCESSO
# ===============================
df = df.sort_values(by=["Processo", "Data", "PV"]).reset_index(drop=True)
df["Fila Acumulada (h)"] = df.groupby("Processo")["Horas"].cumsum()
df["Fila (dias)"] = df["Fila Acumulada (h)"] / HORAS_DIA

# ===============================
# CALENDÁRIO
# ===============================
cal = df[["Data", "Semana", "Ano"]].drop_duplicates().copy()

cal["Inicio"] = cal["Data"] - pd.to_timedelta(cal["Data"].dt.weekday, unit="d")
cal["Fim"] = cal["Inicio"] + pd.Timedelta(days=6)

cal = cal.groupby(["Semana", "Ano"]).agg({
    "Inicio": "min",
    "Fim": "max"
}).reset_index()

cal["Dias Úteis"] = cal.apply(
    lambda x: dias_uteis_periodo(x["Inicio"], x["Fim"]), axis=1
)

# ===============================
# VISÃO
# ===============================
tipo = st.radio("Visualização", ["Semanal", "Mensal"], horizontal=True)

if tipo == "Semanal":
    df["Periodo"] = "Sem " + df["Semana"].astype(str)

    dem = df.groupby(["Periodo", "Processo", "Semana", "Ano"], as_index=False)["Horas"].sum()
    dem = dem.merge(cal, on=["Semana", "Ano"], how="left")

    dem["Capacidade"] = dem.apply(
        lambda r: int(
            r["Dias Úteis"] *
            HORAS_DIA *
            MAQUINAS.get(r["Processo"], 1) *
            EFICIENCIA
        ),
        axis=1
    )

else:
    df["Periodo"] = "Mês " + df["Mes"].astype(str)

    dem = df.groupby(["Periodo", "Processo", "Mes", "Ano"], as_index=False)["Horas"].sum()

    dem["Dias Úteis"] = dem.apply(
        lambda r: dias_uteis_mes(r["Ano"], r["Mes"]),
        axis=1
    )

    dem["Capacidade"] = dem.apply(
        lambda r: int(
            r["Dias Úteis"] *
            HORAS_DIA *
            MAQUINAS.get(r["Processo"], 1) *
            EFICIENCIA
        ),
        axis=1
    )

# ===============================
# MÉTRICAS
# ===============================
dem["Ocupação (%)"] = ((dem["Horas"] / dem["Capacidade"]) * 100).replace([float("inf")], 0).fillna(0)
dem["Ocupação (%)"] = dem["Ocupação (%)"].round(0).astype(int)

def status(x):
    if x > 100:
        return "🔴"
    elif x > 80:
        return "🟡"
    else:
        return "🟢"

dem["Status"] = dem["Ocupação (%)"].apply(status)
dem["Saldo (h)"] = (dem["Capacidade"] - dem["Horas"]).round(1)

# ===============================
# INDICADORES EXECUTIVOS
# ===============================
st.subheader("📊 Indicadores Gerais")

col_a, col_b, col_c = st.columns(3)

total_horas = df["Horas"].sum()
total_capacidade = dem["Capacidade"].sum()
utilizacao_global = 0

if total_capacidade > 0:
    utilizacao_global = int(round((total_horas / total_capacidade) * 100, 0))

col_a.metric("Carga Total (h)", int(round(total_horas, 0)))
col_b.metric("Capacidade Total (h)", int(round(total_capacidade, 0)))
col_c.metric("Utilização Global (%)", utilizacao_global)

# ===============================
# ALERTA DE CAPACIDADE CRÍTICA
# ===============================
st.subheader("⚠️ Capacidade Crítica")

critico = dem[dem["Ocupação (%)"] > 95].copy()

if not critico.empty:
    st.error("Capacidade próxima ou acima do limite detectada.")
    st.dataframe(
        critico.sort_values(["Ocupação (%)", "Horas"], ascending=[False, False]).reset_index(drop=True)
    )
else:
    st.success("Capacidade sob controle.")

# ===============================
# GRÁFICO OCUPAÇÃO
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
# GARGALO AUTOMÁTICO
# ===============================
st.subheader("🔥 Gargalos do Período")

gargalos = dem.sort_values(
    by=["Periodo", "Ocupação (%)", "Horas"],
    ascending=[True, False, False]
).copy()

top_gargalos = gargalos.groupby("Periodo").head(3).reset_index(drop=True)

st.dataframe(top_gargalos)

# ===============================
# CURVA DE CARGA
# ===============================
st.subheader("📈 Evolução da Carga")

carga = df.groupby("Data", as_index=False)["Horas"].sum().sort_values("Data")
carga["Carga Acumulada (h)"] = carga["Horas"].cumsum()

fig_carga = px.line(
    carga,
    x="Data",
    y="Carga Acumulada (h)",
    title="Carga Acumulada no Tempo",
    markers=True
)

st.plotly_chart(fig_carga, use_container_width=True)

# ===============================
# PV CLIENTE
# ===============================
st.subheader("📌 PV por Cliente")

pv_cliente = df.groupby("Cliente", as_index=False)["PV"].nunique()
total = pv_cliente["PV"].sum()

pv_cliente = pd.concat(
    [pv_cliente, pd.DataFrame([{"Cliente": "TOTAL", "PV": total}])],
    ignore_index=True
)

fig_cliente = px.bar(pv_cliente, x="Cliente", y="PV", text="PV")
fig_cliente.update_traces(textposition="outside")

st.plotly_chart(fig_cliente, use_container_width=True)

# ===============================
# FILA POR PROCESSO
# ===============================
st.subheader("📦 Fila por Processo")

fila_exibicao = df[["PV", "Cliente", "Processo", "Data", "Horas", "Fila Acumulada (h)", "Fila (dias)"]].copy()
fila_exibicao["Horas"] = fila_exibicao["Horas"].round(1)
fila_exibicao["Fila Acumulada (h)"] = fila_exibicao["Fila Acumulada (h)"].round(1)
fila_exibicao["Fila (dias)"] = fila_exibicao["Fila (dias)"].round(1)

st.dataframe(fila_exibicao)

# ===============================
# AUDITORIA
# ===============================
st.subheader("📌 Auditoria de Capacidade")

auditoria = dem.copy()
auditoria["Horas"] = auditoria["Horas"].round(1)

st.dataframe(auditoria)

# ===============================
# CALENDÁRIO
# ===============================
st.subheader("📅 Calendário Industrial")
st.dataframe(cal)

# ===============================
# ATRASO
# ===============================
st.subheader("⏱️ Previsão de Atraso por PV")

pv_carga = df.groupby(["PV", "Cliente", "Data"], as_index=False)["Horas"].sum()

pv_carga["Dias Necessários"] = pv_carga["Horas"] / HORAS_DIA

hoje = pd.Timestamp.today().normalize()

pv_carga["Dias Disponíveis"] = pv_carga["Data"].apply(
    lambda x: dias_uteis_periodo(hoje, x)
)

pv_carga["Atraso (dias)"] = (
    pv_carga["Dias Necessários"] - pv_carga["Dias Disponíveis"]
).apply(lambda x: max(0, math.ceil(x)))

pv_carga_exibicao = pv_carga.copy()
pv_carga_exibicao["Horas"] = pv_carga_exibicao["Horas"].round(1)
pv_carga_exibicao["Dias Necessários"] = pv_carga_exibicao["Dias Necessários"].round(1)

st.dataframe(pv_carga_exibicao)

# ===============================
# PIZZA
# ===============================
st.subheader("🥧 Distribuição de Atraso")

atrasos = pv_carga[pv_carga["Atraso (dias)"] > 0].copy()

if not atrasos.empty:
    dist = atrasos.groupby("Atraso (dias)", as_index=False)["PV"].count()

    fig_pizza = px.pie(dist, names="Atraso (dias)", values="PV")
    st.plotly_chart(fig_pizza, use_container_width=True)

    atraso_select = st.selectbox(
        "Selecionar atraso",
        sorted(atrasos["Atraso (dias)"].unique())
    )

    detalhe = atrasos[atrasos["Atraso (dias)"] == atraso_select].copy()
    detalhe["Horas"] = detalhe["Horas"].round(1)
    detalhe["Dias Necessários"] = detalhe["Dias Necessários"].round(1)

    st.subheader("📋 Detalhamento")
    st.dataframe(detalhe)

else:
    st.success("Nenhum atraso 🎉")

# ===============================
# RISCO
# ===============================
st.subheader("⚠️ PVs em Risco")

risco = pv_carga[
    (pv_carga["Atraso (dias)"] == 0) &
    (pv_carga["Dias Necessários"] > pv_carga["Dias Disponíveis"] * 0.8)
].copy()

risco_exibicao = risco.copy()
if not risco_exibicao.empty:
    risco_exibicao["Horas"] = risco_exibicao["Horas"].round(1)
    risco_exibicao["Dias Necessários"] = risco_exibicao["Dias Necessários"].round(1)

st.dataframe(risco_exibicao)

# ===============================
# CAPACIDADE MENSAL FIXA (NOVO)
# ===============================
mes_ref = int(df["Mes"].mode()[0])
ano_ref = int(df["Ano"].mode()[0])

dias_mes = dias_uteis_mes(ano_ref, mes_ref)
total_recursos = sum(MAQUINAS.values())

capacidade_mensal_total = int(
    dias_mes * HORAS_DIA * total_recursos * EFICIENCIA
)

carga_total = df["Horas"].sum()

utilizacao_global = 0
if capacidade_mensal_total > 0:
    utilizacao_global = int((carga_total / capacidade_mensal_total) * 100)

st.subheader("📊 Indicadores Gerais")

c1, c2, c3 = st.columns(3)

c1.metric("Carga Total (h)", int(carga_total))
c2.metric("Capacidade Mensal (h)", capacidade_mensal_total)
c3.metric("Utilização (%)", utilizacao_global)

# ===============================
# RESUMO
# ===============================
st.subheader("📊 Resumo Geral")

col1, col2, col3 = st.columns(3)

col1.metric("🔴 Atraso", len(atrasos))
col2.metric("🟡 Risco", len(risco))
col3.metric("🟢 OK", len(pv_carga) - len(atrasos) - len(risco))