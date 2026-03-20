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
# CARREGA ROTEIRO
# ===============================
try:
    df_base = pd.read_excel("Processos_de_Fabricacao.xlsx")
    df_base.columns = [c.strip().upper() for c in df_base.columns]
    df_base["CODIGO"] = df_base["CODIGO"].astype(str)
    lista_codigos = sorted(df_base["CODIGO"].unique())
except:
    st.error("Erro ao carregar Processos_de_Fabricacao.xlsx")
    st.stop()

# ===============================
# SIMULAÇÃO
# ===============================
st.subheader("Simulação de PV (Entrada / Exclusão)")

if "df_simulado" not in st.session_state:
    st.session_state["df_simulado"] = df_original.copy()

df = st.session_state["df_simulado"]

col1, col2 = st.columns(2)

# ➕ INSERIR PV (AGORA CORRETO)
with col1:
    st.markdown("### ➕ Inserir PV")

    with st.form("form_pv"):
        pv = st.text_input("PV")
        codigo = st.selectbox("Código da Peça", lista_codigos)
        qtd = st.number_input("Quantidade", min_value=1, step=1)
        entrega = st.date_input("Data de Entrega")

        submitted = st.form_submit_button("Simular PV")

        if submitted:

            produto = df_base[df_base["CODIGO"] == codigo]

            if produto.empty:
                st.error("Código não encontrado no roteiro")
            else:
                novas_linhas = []

                for col in df_base.columns:
                    if col == "CODIGO":
                        continue

                    tempo_min = produto.iloc[0][col]

                    if tempo_min > 0:
                        horas = (tempo_min * qtd) / 60

                        novas_linhas.append({
                            "PV": pv,
                            "Cliente": "SIMULADO",
                            "Processo": col,
                            "Maquina": col.split()[0] + "_SIM",
                            "Início": pd.to_datetime(entrega),
                            "Fim": pd.to_datetime(entrega),
                            "Duração (h)": horas
                        })

                st.session_state["df_simulado"] = pd.concat(
                    [df, pd.DataFrame(novas_linhas)],
                    ignore_index=True
                )

                st.success("PV simulada com base no roteiro real")

# ➖ REMOVER PV
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
# DATAS
# ===============================
df["Semana"] = pd.to_numeric(df["Data"].dt.isocalendar().week, errors="coerce")
df["Ano"] = pd.to_numeric(df["Data"].dt.year, errors="coerce")
df["Mes"] = pd.to_numeric(df["Data"].dt.month, errors="coerce")

df = df.dropna(subset=["Semana","Ano","Mes"])

df["Processo"] = df["Maquina"].str.split("_").str[0]

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
# SELETOR
# ===============================
tipo_visao = st.radio("Visualização do Gráfico Principal", ["Semanal","Mensal"], horizontal=True)

# ===============================
# PERIODO
# ===============================
if tipo_visao == "Semanal":
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

    if tipo_visao == "Semanal":
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
        "Capacidade (h)": horas * qtd,
        "Horas Disponíveis": horas * qtd
    })

cap_df = pd.DataFrame(cap)

# ===============================
# MERGE
# ===============================
df_final = pd.merge(dem, cap_df, on=["Periodo","Processo"], how="left")
df_final = df_final.sort_values("Periodo_ord")

# ===============================
# OCUPAÇÃO
# ===============================
df_final["Ocupação (%)"] = (df_final["Duração (h)"] / df_final["Capacidade (h)"]) * 100

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
    text=df_final["Duração (h)"].fillna(0).astype(int)
)

fig.add_hline(y=100, line_dash="dash")
fig.update_traces(textposition="outside")

st.plotly_chart(fig, use_container_width=True)

# ===============================
# AUDITORIA
# ===============================
st.subheader("Auditoria Completa")

df_final["Saldo (h)"] = df_final["Capacidade (h)"] - df_final["Duração (h)"]

st.dataframe(df_final)

# ===============================
# MAPA DE SEMANAS
# ===============================
st.subheader("Mapa de Semanas")

semanas = df[["Ano","Semana"]].drop_duplicates().sort_values(["Ano","Semana"])

mapa = []

for _, row in semanas.iterrows():
    ano = int(row["Ano"])
    semana = int(row["Semana"])
    inicio = pd.to_datetime(f"{ano}-W{semana}-1", format="%G-W%V-%u")
    fim = inicio + pd.Timedelta(days=4)

    mapa.append({
        "Semana": semana,
        "Início": inicio.date(),
        "Fim": fim.date()
    })

st.dataframe(pd.DataFrame(mapa))