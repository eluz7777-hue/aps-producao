import streamlit as st
import pandas as pd
from datetime import timedelta

st.set_page_config(layout="wide")

st.title("APS ELOHIM - ANÁLISE DE CAPACIDADE")

EFICIENCIA = 0.8

HORAS_DIA = {0: 9, 1: 9, 2: 9, 3: 9, 4: 8}

MAQUINAS = {
    "CORTE-LASER": ["LASER_1"],
    "CORTE-PLASMA": ["PLASMA_1"],
    "CORTE - SERRA": ["SERRA_1"],
    "FRESADORAS": ["FRESA_1", "FRESA_2", "FRESA_3"],
    "TORNO CNC": ["TORNO_1", "TORNO_2"],
    "SOLDAGEM": ["SOLDA_1", "SOLDA_2", "SOLDA_3"],
    "PINTURA": ["PINTURA_1"],
    "JATEAMENTO": ["JATO_1"],
    "MONTAGEM": ["MONT_1"],
    "ACABAMENTO": ["ACAB_1", "ACAB_2"],
    "PRENSA (AMASSAMENTO)": ["PRENSA_1"]
}

def capacidade_dia(data):
    if data.weekday() > 4:
        return 0
    return HORAS_DIA.get(data.weekday(), 0) * EFICIENCIA

# ===============================
# BASE
# ===============================
df_base = pd.read_excel("Processos_de_Fabricacao.xlsx")
df_base.fillna(0, inplace=True)
df_base["CODIGO"] = df_base["CODIGO"].astype(str).str.strip().str.upper()

colunas = list(df_base.columns)
PROCESSOS_VALIDOS = [c for c in colunas if c != "CODIGO" and c in MAQUINAS]

# ===============================
# INPUT
# ===============================
st.subheader("Ordens")

codigos = sorted(df_base["CODIGO"].unique())

qtd_ordens = st.number_input("Quantidade de ordens", 1, 20, 3)

ordens = []

for i in range(qtd_ordens):
    c1, c2, c3, c4 = st.columns(4)

    pv = c1.text_input(f"PV {i}", key=f"pv_{i}")
    codigo = c2.selectbox(f"Código {i}", ["-"] + codigos, key=f"cod_{i}")
    qtd = c3.number_input(f"Qtd {i}", 1, 10000, 1, key=f"qtd_{i}")
    entrega = c4.date_input(f"Entrega {i}", key=f"entrega_{i}")

    if codigo != "-":
        ordens.append({
            "PV": pv if pv else f"PV_{i}",
            "CODIGO": codigo,
            "QTD": qtd,
            "ENTREGA": pd.to_datetime(entrega)
        })

# ===============================
# APS COM NIVELAMENTO
# ===============================
if st.button("Gerar APS"):

    carga_semana = {}  # 🔥 controle semanal
    gantt = []

    def semana_key(data):
        return f"{data.year}_{data.isocalendar().week}"

    for ordem in ordens:

        produto = df_base[df_base["CODIGO"] == ordem["CODIGO"]]

        if produto.empty:
            continue

        tempo = ordem["ENTREGA"]

        for processo in reversed(PROCESSOS_VALIDOS):

            tempo_min = produto.iloc[0].get(processo, 0)

            if tempo_min <= 0:
                continue

            restante = (tempo_min * ordem["QTD"]) / 60
            maquinas = MAQUINAS[processo]

            while restante > 0:

                semana = semana_key(tempo)

                # 🔥 capacidade semanal (35h base)
                cap_semana = sum(capacidade_dia(tempo - timedelta(days=i)) for i in range(5))

                usado = carga_semana.get((processo, semana), 0)

                disponivel = cap_semana - usado

                if disponivel <= 0:
                    tempo -= timedelta(days=7)
                    continue

                horas = min(restante, disponivel)

                maquina = maquinas[0]  # mantém lógica simples

                inicio = tempo - timedelta(hours=horas)

                gantt.append({
                    "PV": ordem["PV"],
                    "Processo": processo,
                    "Maquina": maquina,
                    "Início": inicio,
                    "Fim": tempo,
                    "Duração (h)": round(horas)
                })

                carga_semana[(processo, semana)] = usado + horas
                restante -= horas
                tempo = inicio

    gantt_df = pd.DataFrame(gantt)

    if gantt_df.empty:
        st.error("Nenhum dado gerado.")
        st.stop()

    st.session_state["dados_dashboard"] = gantt_df

    st.success("APS com nivelamento gerado")