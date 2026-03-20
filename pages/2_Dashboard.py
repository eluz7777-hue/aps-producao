import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("📊 APS ELOHIM - DASHBOARD INDUSTRIAL")

# ===============================
# BASES
# ===============================
df_pv = pd.read_excel("Relacao_Pv.xlsx")
df_base = pd.read_excel("Processos_de_Fabricacao.xlsx")

df_pv.columns = [c.strip().upper() for c in df_pv.columns]
df_base.columns = [c.strip().upper() for c in df_base.columns]

df_pv = df_pv.rename(columns={
    "CÓDIGO":"CODIGO",
    "DATA DE ENTREGA":"ENTREGA",
    "QUANTIDADE":"QTD"
})

df_pv["CODIGO"] = df_pv["CODIGO"].astype(str)
df_pv["PV"] = df_pv["PV"].astype(str)
df_pv["ENTREGA"] = pd.to_datetime(df_pv["ENTREGA"])

df_base["CODIGO"] = df_base["CODIGO"].astype(str)

processos = [c for c in df_base.columns if c != "CODIGO"]

# ===============================
# ESTADO
# ===============================
if "pv_simulada" not in st.session_state:
    st.session_state["pv_simulada"] = []

# ===============================
# SIMULAÇÃO
# ===============================
st.subheader("Simulação de PV")

col1, col2 = st.columns(2)

# ➕ INSERIR
with col1:
    with st.form("simular"):
        pv = st.text_input("PV")
        codigo = st.selectbox("Código", df_base["CODIGO"].unique())
        qtd = st.number_input("Quantidade", min_value=1)
        entrega = st.date_input("Entrega")

        if st.form_submit_button("Simular"):
            st.session_state["pv_simulada"].append({
                "PV": str(pv),
                "CODIGO": str(codigo),
                "QTD": qtd,
                "ENTREGA": entrega
            })
            st.success("PV simulada adicionada")
            st.rerun()

# ➖ REMOVER
with col2:
    pv_remove = st.text_input("Remover PV")

    if st.button("Remover"):
        st.session_state["pv_simulada"] = [
            x for x in st.session_state["pv_simulada"]
            if x["PV"] != pv_remove
        ]
        st.success("PV removida")
        st.rerun()

# ===============================
# BASE TOTAL
# ===============================
df_sim = pd.DataFrame(st.session_state["pv_simulada"])

if not df_sim.empty:
    df_sim["ENTREGA"] = pd.to_datetime(df_sim["ENTREGA"])
    df_total = pd.concat([df_pv, df_sim], ignore_index=True)
else:
    df_total = df_pv.copy()

# ===============================
# EXPANSÃO PROCESSOS
# ===============================
linhas = []

for _, row in df_total.iterrows():

    roteiro = df_base[df_base["CODIGO"] == row["CODIGO"]]

    if roteiro.empty:
        continue

    for proc in processos:

        tempo = pd.to_numeric(roteiro.iloc[0][proc], errors="coerce")

        if pd.notna(tempo) and tempo > 0:

            horas = (tempo * row["QTD"]) / 60

            linhas.append({
                "PV": row["PV"],
                "Cliente": row.get("CLIENTE","SIM"),
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
df["Ano"] = df["Data"].dt.year

# ===============================
# PARÂMETROS
# ===============================
EFICIENCIA = 0.8
HORAS_SEMANA = 44

MAQUINAS = {
    "FRESADORAS":2,"SOLDAGEM":4,"TORNO":3,"PLASMA":1,"LASER":1,
    "SERRA":2,"CNC":1,"DOBRA":2,"PRENSA":1,"ROSQ":1,
    "ACABAMENTO":3,"CALANDRA":2,"PINTURA":1,"METALEIRA":1
}

# ===============================
# VISÃO
# ===============================
tipo = st.radio("Visualização", ["Semanal","Mensal"])

if tipo == "Semanal":
    df["Periodo"] = "Sem " + df["Semana"].astype(str)
else:
    df["Periodo"] = "Mês " + df["Mes"].astype(str)

# ===============================
# DEMANDA
# ===============================
dem = df.groupby(["Periodo","Processo"])["Horas"].sum().reset_index()

def capacidade(proc):
    return HORAS_SEMANA * MAQUINAS.get(proc,1) * EFICIENCIA

dem["Capacidade"] = dem["Processo"].apply(capacidade)

dem["Ocupação (%)"] = (dem["Horas"]/dem["Capacidade"])*100

# ===============================
# STATUS (🔴🟡🟢 RESTAURADO)
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
st.subheader("Ocupação por Processo")

fig = px.bar(
    dem,
    x="Periodo",
    y="Ocupação (%)",
    color="Processo",
    barmode="group",
    text=dem["Horas"].astype(int)
)

fig.add_hline(y=100, line_dash="dash")
fig.update_traces(textposition="outside")

st.plotly_chart(fig, use_container_width=True)

# ===============================
# PIZZAS (TODAS)
# ===============================
st.subheader("Carga por Processo")
st.plotly_chart(px.pie(df, names="Processo", values="Horas"), use_container_width=True)

st.subheader("Carga por Semana")
sem = st.selectbox("Semana", sorted(df["Semana"].unique()))
st.plotly_chart(px.pie(df[df["Semana"]==sem], names="Processo", values="Horas"))

st.subheader("Carga por Mês")
mes = st.selectbox("Mês", sorted(df["Mes"].unique()))
st.plotly_chart(px.pie(df[df["Mes"]==mes], names="Processo", values="Horas"))

# ===============================
# PV CLIENTE
# ===============================
st.subheader("PV por Cliente")
pv_cliente = df.groupby("Cliente")["PV"].nunique().reset_index()
st.plotly_chart(px.bar(pv_cliente, x="Cliente", y="PV"), use_container_width=True)

# ===============================
# CARGA MENSAL
# ===============================
st.subheader("Carga Mensal")
mensal = df.groupby("Mes")["Horas"].sum().reset_index()
st.plotly_chart(px.bar(mensal, x="Mes", y="Horas"), use_container_width=True)

# ===============================
# TABELA FINAL (COM BOLINHAS)
# ===============================
st.subheader("Auditoria de Capacidade")

st.dataframe(dem)