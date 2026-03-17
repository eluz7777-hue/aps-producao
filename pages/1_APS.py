import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

st.set_page_config(layout="wide")

st.title("APS - Planejamento com Restrições Reais")

# ===============================
# PROCESSOS VÁLIDOS
# ===============================
PROCESSOS_VALIDOS = [
    "CORTE - SERRA",
    "CORTE-LASER",
    "FRESADORAS",
    "PRENSA (AMASSAMENTO)",
    "SOLDAGEM",
    "ACABAMENTO",
    "TORNO CNC"
]

# ===============================
# RESTRIÇÕES
# ===============================
RESTRICOES = {
    "CORTE-LASER": ["PLASMA"],
    "PLASMA": ["CORTE-LASER"],
    "TORNO CNC": ["FRESADORAS"]  # exemplo de isolamento
}

# ===============================
# CARREGAR BASE
# ===============================
df_base = pd.read_excel("Processos_de_Fabricacao.xlsx")
df_base = df_base.loc[:, ~df_base.columns.str.contains("Unnamed")]
df_base.fillna(0, inplace=True)

df_base["CODIGO"] = df_base["CODIGO"].astype(str).str.strip().str.upper()

for col in PROCESSOS_VALIDOS:
    if col in df_base.columns:
        df_base[col] = pd.to_numeric(df_base[col], errors="coerce").fillna(0)

codigos = sorted(df_base["CODIGO"].unique())

# ===============================
# ENTRADA
# ===============================
st.subheader("Ordens")

qtd_ordens = st.number_input("Quantidade de ordens", 1, 20, 3)

ordens = []

for i in range(qtd_ordens):
    c1, c2, c3, c4, c5 = st.columns(5)

    pv = c1.text_input(f"PV {i}", key=f"pv_{i}")
    codigo = c2.selectbox(f"Código {i}", ["-"] + codigos, key=f"cod_{i}")
    qtd = c3.number_input(f"Qtd {i}", 1, 10000, 1, key=f"qtd_{i}")
    entrega = c4.date_input(f"Entrega {i}", key=f"entrega_{i}")
    urgente = c5.checkbox("🔥 Urgente", key=f"urg_{i}")

    if codigo != "-":
        ordens.append({
            "PV": pv if pv else f"PV_{i}",
            "CODIGO": codigo,
            "QTD": qtd,
            "ENTREGA": entrega,
            "URGENTE": urgente
        })

# ===============================
# FUNÇÃO DE CONFLITO
# ===============================
def verifica_conflito(processo, inicio, fim, agenda):
    for p, blocos in agenda.items():

        # mesma máquina ou conflito
        conflito = p == processo or p in RESTRICOES.get(processo, [])

        if conflito:
            for (i, f) in blocos:
                if not (fim <= i or inicio >= f):
                    return True
    return False

# ===============================
# APS
# ===============================
if st.button("Gerar APS"):

    if not ordens:
        st.error("Nenhuma ordem válida")
        st.stop()

    df_ordens = pd.DataFrame(ordens)
    df_ordens = df_ordens.sort_values(by=["URGENTE", "ENTREGA"], ascending=[False, True])

    agenda = {p: [] for p in PROCESSOS_VALIDOS}

    inicio_global = datetime.now()
    gantt = []

    for _, ordem in df_ordens.iterrows():

        produto = df_base[df_base["CODIGO"] == ordem["CODIGO"]]

        if produto.empty:
            continue

        tempo_inicio = inicio_global

        for processo in PROCESSOS_VALIDOS:

            if processo not in df_base.columns:
                continue

            tempo_min = float(produto.iloc[0][processo])

            if tempo_min <= 0:
                continue

            duracao_h = (tempo_min * ordem["QTD"]) / 60

            if duracao_h > 200:
                continue

            # 🔥 RESPEITA RESTRIÇÕES
            tentativa = tempo_inicio
            while True:
                tempo_fim = tentativa + timedelta(hours=duracao_h)

                if not verifica_conflito(processo, tentativa, tempo_fim, agenda):
                    break

                tentativa += timedelta(minutes=10)

            # salva na agenda
            agenda[processo].append((tentativa, tempo_fim))

            gantt.append({
                "PV": ordem["PV"],
                "Processo": processo,
                "Início": tentativa,
                "Fim": tempo_fim,
                "Duração (h)": round(duracao_h, 2)
            })

            tempo_inicio = tempo_fim

    gantt_df = pd.DataFrame(gantt)

    # ===============================
    # GANTT
    # ===============================
    st.subheader("Gantt com Restrições")

    fig = px.timeline(
        gantt_df,
        x_start="Início",
        x_end="Fim",
        y="Processo",
        color="PV",
        text="Duração (h)"
    )

    fig.update_yaxes(autorange="reversed")

    st.plotly_chart(fig, use_container_width=True)

    # ===============================
    # RESUMO
    # ===============================
    total = gantt_df["Duração (h)"].sum()

    gargalo = (
        gantt_df.groupby("Processo")["Duração (h)"]
        .sum()
        .sort_values(ascending=False)
        .index[0]
    )

    st.success(f"Tempo total: {round(total,2)} h")
    st.error(f"Gargalo: {gargalo}")

    # dashboard
    st.session_state["dados_dashboard"] = gantt_df
    st.session_state["total_horas"] = total
    st.session_state["gargalo"] = gargalo
    st.session_state["ordens"] = df_ordens["PV"].nunique()