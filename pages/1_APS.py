import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

st.set_page_config(layout="wide")

st.title("APS ELOHIM - ANÁLISE DE CAPACIDADE")

# ===============================
# CONFIG
# ===============================
EFICIENCIA = 0.8

HORAS_DIA = {
    0: 9,
    1: 9,
    2: 9,
    3: 9,
    4: 8
}

MAQUINAS = {
    "CORTE-LASER": ["LASER_1"],
    "FRESADORAS": ["FRESA_1", "FRESA_2", "FRESA_3"],
    "TORNO CNC": ["TORNO_1", "TORNO_2"],
    "SOLDAGEM": ["SOLDA_1", "SOLDA_2", "SOLDA_3"],
    "ACABAMENTO": ["ACAB_1", "ACAB_2"],
    "CORTE - SERRA": ["SERRA_1"],
    "PRENSA (AMASSAMENTO)": ["PRENSA_1"]
}

PROCESSOS_VALIDOS = list(MAQUINAS.keys())

# ===============================
# TURNO
# ===============================
def capacidade_dia(data):
    return HORAS_DIA.get(data.weekday(), 0) * EFICIENCIA

def ajustar_turno(data):
    while True:
        if data.weekday() > 4:
            data -= timedelta(days=1)
            continue
        return data

# ===============================
# BASE
# ===============================
df_base = pd.read_excel("Processos_de_Fabricacao.xlsx")
df_base.fillna(0, inplace=True)
df_base["CODIGO"] = df_base["CODIGO"].astype(str).str.strip().str.upper()

codigos = sorted(df_base["CODIGO"].unique())

# ===============================
# INPUT
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
            "ENTREGA": pd.to_datetime(entrega)
        })

# ===============================
# APS COM CAPACIDADE REAL
# ===============================
if st.button("Gerar APS"):

    # controle de carga por máquina por dia
    carga = {}

    gantt = []

    def get_key(maquina, data):
        return f"{maquina}_{data.date()}"

    for ordem in ordens:

        produto = df_base[df_base["CODIGO"] == ordem["CODIGO"]]

        if produto.empty:
            continue

        tempo_fim = ordem["ENTREGA"]

        for processo in reversed(PROCESSOS_VALIDOS):

            if processo not in df_base.columns:
                continue

            tempo_min = produto.iloc[0][processo]

            if tempo_min <= 0:
                continue

            restante = (tempo_min * ordem["QTD"]) / 60

            maquinas = MAQUINAS[processo]

            while restante > 0:

                tempo_fim = ajustar_turno(tempo_fim)

                cap_dia = capacidade_dia(tempo_fim)

                # tenta alocar em qualquer máquina disponível
                alocado = False

                for maquina in maquinas:

                    key = get_key(maquina, tempo_fim)
                    usado = carga.get(key, 0)

                    disponivel = cap_dia - usado

                    if disponivel <= 0:
                        continue

                    horas = min(restante, disponivel)

                    inicio = tempo_fim - timedelta(hours=horas)

                    gantt.append({
                        "PV": ordem["PV"],
                        "Processo": processo,
                        "Maquina": maquina,
                        "Início": inicio,
                        "Fim": tempo_fim,
                        "Duração (h)": round(horas, 0)
                    })

                    carga[key] = usado + horas

                    restante -= horas
                    tempo_fim = inicio

                    alocado = True
                    break

                # se nenhuma máquina tinha espaço → volta um dia
                if not alocado:
                    tempo_fim -= timedelta(days=1)

    gantt_df = pd.DataFrame(gantt)

    st.subheader("Gantt Balanceado (REAL)")

    fig = px.timeline(
        gantt_df,
        x_start="Início",
        x_end="Fim",
        y="Maquina",
        color="PV"
    )

    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(fig, use_container_width=True)

    st.session_state["dados_dashboard"] = gantt_df