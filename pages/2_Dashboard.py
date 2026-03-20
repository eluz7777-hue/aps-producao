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

df_original = st.session_state["dados_dashboard"].copy()

# ===============================
# DATA
# ===============================
df_original["Data"] = pd.to_datetime(df_original["Início"], errors="coerce")
df_original = df_original.dropna(subset=["Data"])

# ===============================
# ROTEIRO
# ===============================
df_base = pd.read_excel("Processos_de_Fabricacao.xlsx")
df_base.columns = [c.strip().upper() for c in df_base.columns]
df_base["CODIGO"] = df_base["CODIGO"].astype(str)

# 🔥 remove colunas indevidas
colunas_invalidas = ["TOTAL", "TEMPO TOTAL", "OBS", "DESCRICAO"]

processos_validos = [
    c for c in df_base.columns
    if c != "CODIGO" and c not in colunas_invalidas
]

lista_codigos = sorted(df_base["CODIGO"].unique())

# ===============================
# SIMULAÇÃO
# ===============================
st.subheader("Simulação de PV (Entrada / Exclusão)")

if "df_simulado" not in st.session_state:
    st.session_state["df_simulado"] = df_original.copy()

df = st.session_state["df_simulado"]

col1, col2 = st.columns(2)

# ➕ INSERIR
with col1:
    st.markdown("### ➕ Inserir PV")

    with st.form("form_pv"):
        pv = str(st.text_input("PV")).strip()
        codigo = st.selectbox("Código da Peça", lista_codigos)
        qtd = st.number_input("Quantidade", min_value=1)
        entrega = st.date_input("Data de Entrega")

        if st.form_submit_button("Simular PV"):

            produto = df_base[df_base["CODIGO"] == codigo]

            if produto.empty:
                st.error("Código não encontrado")
            else:
                novas = []

                for col in processos_validos:

                    tempo = pd.to_numeric(produto.iloc[0][col], errors="coerce")

                    if pd.notna(tempo) and tempo > 0:
                        horas = (tempo * qtd) / 60

                        novas.append({
                            "PV": pv,
                            "Cliente": "SIMULADO",
                            "Processo": col,
                            "Maquina": col + "_SIM",
                            "Início": pd.to_datetime(entrega),
                            "Fim": pd.to_datetime(entrega),
                            "Duração (h)": horas
                        })

                st.session_state["df_simulado"] = pd.concat(
                    [df, pd.DataFrame(novas)],
                    ignore_index=True
                )

                st.success(f"PV {pv} simulada aplicada na carga")

# ➖ REMOVER (CORRIGIDO)
with col2:
    st.markdown("### ➖ Remover PV")

    df_remocao = st.session_state["df_simulado"].copy()
    df_remocao["PV"] = df_remocao["PV"].astype(str)

    lista_pv = sorted(df_remocao["PV"].dropna().unique())

    pv_sel = st.selectbox("PV", lista_pv)

    if st.button("Remover"):
        st.session_state["df_simulado"] = df_remocao[df_remocao["PV"] != pv_sel]
        st.success(f"PV {pv_sel} removida com sucesso")

df = st.session_state["df_simulado"]

# ===============================
# DATAS
# ===============================
df["Data"] = pd.to_datetime(df["Início"], errors="coerce")
df["Semana"] = df["Data"].dt.isocalendar().week
df["Ano"] = df["Data"].dt.year
df["Mes"] = df["Data"].dt.month

df = df.dropna(subset=["Semana","Ano","Mes"])

# ===============================
# PROCESSO CORRETO
# ===============================
if "Processo" not in df.columns:
    df["Processo"] = df["Maquina"].str.split("_").str[0]

df = df[df["Processo"].isin(processos_validos)]

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
# VISÃO
# ===============================
tipo = st.radio("Visualização", ["Semanal","Mensal"], horizontal=True)

if tipo == "Semanal":
    df["Periodo"] = "Sem " + df["Semana"].astype(int).astype(str)
    df["Periodo_ord"] = df["Ano"]*100 + df["Semana"]
else:
    df["Periodo"] = "Mês " + df["Mes"].astype(int).astype(str)
    df["Periodo_ord"] = df["Ano"]*100 + df["Mes"]

# ===============================
# DEMANDA
# ===============================
dem = df.groupby(["Periodo","Periodo_ord","Processo"], as_index=False)["Duração (h)"].sum()

# ===============================
# CAPACIDADE
# ===============================
cap = []

for (periodo, proc), g in df.groupby(["Periodo","Processo"]):

    if tipo == "Semanal":
        semana = int(g["Semana"].iloc[0])
        ano = int(g["Ano"].iloc[0])
        inicio = pd.to_datetime(f"{ano}-W{semana}-1", format="%G-W%V-%u")
        dias = [inicio + pd.Timedelta(days=i) for i in range(5)]
    else:
        mes = int(g["Mes"].iloc[0])
        ano = int(g["Ano"].iloc[0])
        inicio = pd.Timestamp(year=ano, month=mes, day=1)
        fim = inicio + pd.offsets.MonthEnd(0)
        dias = pd.date_range(inicio, fim, freq="B")

    horas = sum(horas_dia(d) for d in dias)
    qtd = MAQUINAS_QTD.get(proc,1)

    cap.append({
        "Periodo": periodo,
        "Processo": proc,
        "Capacidade (h)": horas * qtd
    })

cap_df = pd.DataFrame(cap)

# ===============================
# MERGE
# ===============================
df_final = pd.merge(dem, cap_df, on=["Periodo","Processo"])

# ===============================
# STATUS
# ===============================
df_final["Ocupação (%)"] = (df_final["Duração (h)"]/df_final["Capacidade (h)"])*100

def status(x):
    if x > 100: return "🔴"
    elif x > 80: return "🟡"
    else: return "🟢"

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
    text=df_final["Duração (h)"].astype(int)
)

fig.add_hline(y=100, line_dash="dash")
fig.update_traces(textposition="outside")

st.plotly_chart(fig, use_container_width=True)

# ===============================
# PIZZAS
# ===============================
st.subheader("Carga por Processo")
st.plotly_chart(px.pie(df, names="Processo", values="Duração (h)"), use_container_width=True)

st.subheader("Carga por Semana")
sem_sel = st.selectbox("Semana", sorted(df["Semana"].unique()))
st.plotly_chart(px.pie(df[df["Semana"]==sem_sel], names="Processo", values="Duração (h)"), use_container_width=True)

st.subheader("Carga por Mês")
mes_sel = st.selectbox("Mês", sorted(df["Mes"].unique()))
st.plotly_chart(px.pie(df[df["Mes"]==mes_sel], names="Processo", values="Duração (h)"), use_container_width=True)

# ===============================
# PV CLIENTE
# ===============================
st.subheader("Número de PV por Cliente")
pv_cliente = df.groupby("Cliente")["PV"].nunique().reset_index()
st.plotly_chart(px.bar(pv_cliente, x="Cliente", y="PV", text="PV"), use_container_width=True)

# ===============================
# CARGA MENSAL
# ===============================
st.subheader("Carga Mensal")
mensal = df.groupby("Mes")["Duração (h)"].sum().reset_index()
st.plotly_chart(px.bar(mensal, x="Mes", y="Duração (h)"), use_container_width=True)

# ===============================
# MAPA SEMANAS
# ===============================
st.subheader("Mapa de Semanas")

mapa = []
for s in df["Semana"].unique():
    ano = int(df[df["Semana"]==s]["Ano"].iloc[0])
    inicio = pd.to_datetime(f"{ano}-W{int(s)}-1", format="%G-W%V-%u")
    fim = inicio + pd.Timedelta(days=4)
    mapa.append({"Semana":s,"Início":inicio.date(),"Fim":fim.date()})

st.dataframe(pd.DataFrame(mapa))

# ===============================
# AUDITORIA
# ===============================
st.subheader("Auditoria")

df_final["Saldo"] = df_final["Capacidade (h)"] - df_final["Duração (h)"]

st.dataframe(df_final)