import streamlit as st
import pandas as pd
import plotly.express as px
import os
import time

st.set_page_config(layout="wide")
st.title("📊 Dashboard de Capacidade")

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

for col in ["PV","CODIGO","QTD","ENTREGA"]:
    if col not in df_pv.columns:
        st.error(f"Coluna obrigatória ausente: {col}")
        st.stop()

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
# ROTEIRO (SEM DUPLICIDADE)
# ===============================
df_base_unico = df_base.drop_duplicates(subset=["CODIGO"])

# ===============================
# EXPANSÃO (BASE PV)
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

if df.empty:
    st.error("Nenhuma carga gerada.")
    st.stop()

# ===============================
# DATAS
# ===============================
df["Semana"] = df["Data"].dt.isocalendar().week.astype(int)
df["Mes"] = df["Data"].dt.month

tipo = st.radio("Visualização", ["Semanal","Mensal"], horizontal=True)

df["Periodo"] = (
    "Sem " + df["Semana"].astype(str)
    if tipo == "Semanal"
    else "Mês " + df["Mes"].astype(str)
)

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

def capacidade(proc):
    return int(HORAS_SEMANA * MAQUINAS.get(proc,1) * EFICIENCIA)

dem = df.groupby(["Periodo","Processo"])["Horas"].sum().reset_index()
dem["Capacidade"] = dem["Processo"].apply(capacidade)

dem["Ocupação (%)"] = ((dem["Horas"]/dem["Capacidade"])*100).round(0).astype(int)

dem["Status"] = dem["Ocupação (%)"].apply(
    lambda x: "🔴" if x > 100 else ("🟡" if x > 80 else "🟢")
)

dem["Saldo (h)"] = (dem["Capacidade"] - dem["Horas"]).round(1)

# ===============================
# GRÁFICO PRINCIPAL
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
fig_pizza = px.pie(df_total, names="Processo", values="Horas")
st.plotly_chart(fig_pizza)

# ===============================
# SEMANA
# ===============================
st.subheader("📌 Distribuição por Semana")

sem = st.selectbox("Semana", sorted(df["Semana"].unique()))

df_sem = df[df["Semana"] == sem].groupby("Processo")["Horas"].sum().reset_index()

fig_sem = px.bar(
    df_sem,
    x="Processo",
    y="Horas",
    text=df_sem["Horas"].map(lambda x: f"{x:.1f}")
)

fig_sem.update_traces(textposition="outside")
st.plotly_chart(fig_sem, use_container_width=True)

# ===============================
# MÊS
# ===============================
st.subheader("📌 Distribuição por Mês")

mes = st.selectbox("Mês", sorted(df["Mes"].unique()))

df_mes = df[df["Mes"] == mes].groupby("Processo")["Horas"].sum().reset_index()

fig_mes = px.bar(
    df_mes,
    x="Processo",
    y="Horas",
    text=df_mes["Horas"].map(lambda x: f"{x:.1f}")
)

fig_mes.update_traces(textposition="outside")
st.plotly_chart(fig_mes, use_container_width=True)

# ===============================
# CLIENTE (COM TOTAL)
# ===============================
st.subheader("📌 PV por Cliente")

pv_cliente = df.groupby("Cliente")["PV"].nunique().reset_index()

total_pv = pv_cliente["PV"].sum()

linha_total = pd.DataFrame([{
    "Cliente": "TOTAL",
    "PV": total_pv
}])

pv_cliente = pd.concat([pv_cliente, linha_total], ignore_index=True)

pv_cliente = pd.concat([
    pv_cliente[pv_cliente["Cliente"] != "TOTAL"],
    pv_cliente[pv_cliente["Cliente"] == "TOTAL"]
])

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
st.subheader("📌 Carga Mensal")

mensal = df.groupby("Mes")["Horas"].sum().reset_index()

fig_mensal = px.bar(
    mensal,
    x="Mes",
    y="Horas",
    text=mensal["Horas"].map(lambda x: f"{x:.1f}")
)

fig_mensal.update_traces(textposition="outside")

st.plotly_chart(fig_mensal, use_container_width=True)

# ===============================
# TABELA FINAL
# ===============================
st.subheader("📌 Auditoria de Capacidade")

st.dataframe(dem)