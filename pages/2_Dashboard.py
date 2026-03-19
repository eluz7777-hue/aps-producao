import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("📊 DASHBOARD DE CAPACIDADE")

if "dados_dashboard" not in st.session_state:
    st.stop()

df = st.session_state["dados_dashboard"].copy()
df["Data"] = pd.to_datetime(df["Início"])
df["Processo"] = df["Maquina"].str.split("_").str[0]

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
# PERÍODO
# ===============================
df["Periodo_ord"] = df["Data"].dt.year*100 + df["Data"].dt.isocalendar().week
df["Periodo"] = "Sem " + df["Data"].dt.isocalendar().week.astype(str)

# ===============================
# DEMANDA
# ===============================
dem = df.groupby(["Periodo","Periodo_ord","Processo"])["Duração (h)"].sum().reset_index()

# ===============================
# CAPACIDADE REAL
# ===============================
cap = []

for (p, proc), g in df.groupby(["Periodo","Processo"]):

    dias = g["Data"].dt.date.unique()
    horas = sum(horas_dia(pd.Timestamp(d)) for d in dias)

    qtd = MAQUINAS_QTD.get(proc,1)

    cap.append({
        "Periodo":p,
        "Processo":proc,
        "Capacidade (h)": horas * qtd
    })

cap_df = pd.DataFrame(cap)

df_final = pd.merge(dem, cap_df, on=["Periodo","Processo"])

# ===============================
# MÉTRICAS
# ===============================
df_final["Ocupação (%)"] = (df_final["Duração (h)"]/df_final["Capacidade (h)"])*100

def status(x):
    if x > 100: return "🔴"
    elif x > 80: return "🟡"
    else: return "🟢"

df_final["Status"] = df_final["Ocupação (%)"].apply(status)

df_final = df_final.sort_values("Periodo_ord")

# ===============================
# GRÁFICO VERTICAL (CORRIGIDO)
# ===============================
fig = px.bar(
    df_final,
    x="Periodo",
    y="Ocupação (%)",
    color="Processo",
    barmode="group",  # 🔥 NÃO empilhado
    text=df_final["Duração (h)"].astype(int)
)

fig.add_hline(y=100, line_dash="dash")
fig.update_traces(textposition="outside")

st.plotly_chart(fig, use_container_width=True)

# ===============================
# PIZZA
# ===============================
pizza = df.groupby("Processo")["Duração (h)"].sum().reset_index()

st.plotly_chart(
    px.pie(pizza, names="Processo", values="Duração (h)"),
    use_container_width=True
)

# ===============================
# TABELA
# ===============================
st.dataframe(df_final)