import streamlit as st
import pandas as pd
import plotly.express as px
import os
import time
import holidays

st.set_page_config(layout="wide")

st.title("📊 Dashboard de Capacidade - APS Nível 4")st.title("📊 ELOHIM APS – Advanced Planning System")

# ===============================
# CONFIG
# ===============================
EFICIENCIA = 0.8
HORAS_DIA = 8

# ===============================
# FERIADOS
# ===============================
br_holidays = holidays.Brazil()

def dias_uteis_periodo(inicio, fim):
    dias = pd.date_range(inicio, fim, freq='D')
    return sum(1 for d in dias if d.weekday() < 5 and d.date() not in br_holidays)

def dias_uteis_mes(ano, mes):
    inicio = pd.Timestamp(year=ano, month=mes, day=1)
    fim = inicio + pd.offsets.MonthEnd(1)
    return dias_uteis_periodo(inicio, fim)

# ===============================
# ATUALIZAÇÃO
# ===============================
if st.button("🔄 Atualizar Dados"):
    st.rerun()

st.write("Última atualização:", time.strftime("%d/%m/%Y %H:%M:%S"))

# ===============================
# LEITURA
# ===============================
BASE_PATH = os.getcwd()

df_pv = pd.read_excel(os.path.join(BASE_PATH, "Relacao_Pv.xlsx"))
df_base = pd.read_excel(os.path.join(BASE_PATH, "Processos_de_Fabricacao.xlsx"))

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

# ===============================
# CALENDÁRIO
# ===============================
calendario = df[["Data","Semana","Ano"]].drop_duplicates()

calendario["Inicio Semana"] = calendario["Data"] - pd.to_timedelta(calendario["Data"].dt.weekday, unit="d")
calendario["Fim Semana"] = calendario["Inicio Semana"] + pd.Timedelta(days=6)

calendario = calendario.groupby(["Semana","Ano"]).agg({
    "Inicio Semana":"min",
    "Fim Semana":"max"
}).reset_index()

calendario["Dias Úteis"] = calendario.apply(
    lambda x: dias_uteis_periodo(x["Inicio Semana"], x["Fim Semana"]), axis=1
)

# ===============================
# SELETOR
# ===============================
tipo = st.radio("Visualização", ["Semanal","Mensal"], horizontal=True)

MAQUINAS = {
    "FRESADORAS":2,"SOLDAGEM":4,"TORNO":3,"CORTE-PLASMA":1,"CORTE-LASER":1,
    "SERRA FITA":1,"SERRA CIRCULAR":1,"CENTRO USINAGEM":1,"DOBRADEIRA":2,
    "PRENSA (AMASSAMENTO)":1,"ROSQUEADEIRA":1,"ACABAMENTO":3,
    "CALANDRA":2,"PINTURA":1,"METALEIRA":1
}

if tipo == "Semanal":
    df["Periodo"] = "Sem " + df["Semana"].astype(str)
    dem = df.groupby(["Periodo","Processo","Semana","Ano"])["Horas"].sum().reset_index()
    dem = dem.merge(calendario, on=["Semana","Ano"], how="left")

    def capacidade(row):
        return int(row["Dias Úteis"] * HORAS_DIA * MAQUINAS.get(row["Processo"],1) * EFICIENCIA)

else:
    df["Periodo"] = "Mês " + df["Mes"].astype(str)
    dem = df.groupby(["Periodo","Processo","Mes","Ano"])["Horas"].sum().reset_index()

    def capacidade(row):
        return int(dias_uteis_mes(row["Ano"], row["Mes"]) * HORAS_DIA * MAQUINAS.get(row["Processo"],1) * EFICIENCIA)

dem["Capacidade"] = dem.apply(capacidade, axis=1)

# ===============================
# STATUS
# ===============================
dem["Ocupação (%)"] = ((dem["Horas"]/dem["Capacidade"])*100).round(0).astype(int)

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
# APS NÍVEL 3
# ===============================
st.subheader("🚨 Análise de Gargalos")

gargalo = dem.sort_values("Ocupação (%)", ascending=False).iloc[0]
st.error(f"GARGALO: {gargalo['Processo']} ({gargalo['Ocupação (%)']}%)")

st.subheader("📊 Ranking de Criticidade")
st.dataframe(dem.sort_values("Ocupação (%)", ascending=False))

# ===============================
# GRÁFICO
# ===============================
st.subheader("📌 Ocupação por Processo (%)")

dem["Label"] = dem["Horas"].map(lambda x: f"{x:.1f}h")

fig = px.bar(
    dem,
    x="Periodo",
    y="Ocupação (%)",
    color="Processo",
    text="Label",
    barmode="group"
)

fig.add_hline(y=100, line_dash="dash")
fig.update_traces(textposition="outside")

st.plotly_chart(fig, use_container_width=True)

# ===============================
# CLIENTE
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
# CALENDÁRIO
# ===============================
st.subheader("📅 Calendário Industrial")
st.dataframe(calendario)

# ===============================
# 🔥 PREVISÃO DE ATRASO POR PV
# ===============================
st.subheader("⏱️ Previsão de Atraso por PV")

pv_carga = df.groupby(["PV","Cliente","Data"])["Horas"].sum().reset_index()

pv_carga["Dias Necessários"] = (pv_carga["Horas"] / HORAS_DIA).round(1)

hoje = pd.Timestamp.today().normalize()

def dias_ate_entrega(data):
    if pd.isna(data):
        return 0
    return dias_uteis_periodo(hoje, data)

pv_carga["Dias Disponíveis"] = pv_carga["Data"].apply(dias_ate_entrega)

def status_pv(row):
    if row["Dias Necessários"] > row["Dias Disponíveis"]:
        return "🔴 ATRASO"
    elif row["Dias Necessários"] > row["Dias Disponíveis"] * 0.8:
        return "🟡 RISCO"
    else:
        return "🟢 OK"

pv_carga["Status"] = pv_carga.apply(status_pv, axis=1)

pv_carga["Atraso (dias)"] = (
    pv_carga["Dias Necessários"] - pv_carga["Dias Disponíveis"]
).apply(lambda x: round(x,1) if x > 0 else 0)

pv_carga = pv_carga.sort_values(by="Atraso (dias)", ascending=False)

st.dataframe(pv_carga)

st.subheader("🚨 PVs com Maior Risco de Atraso")

fig_atraso = px.bar(
    pv_carga.head(10),
    x="PV",
    y="Atraso (dias)",
    color="Status",
    text="Atraso (dias)"
)

fig_atraso.update_traces(textposition="outside")

st.plotly_chart(fig_atraso, use_container_width=True)