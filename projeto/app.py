import streamlit as st
import pandas as pd
from datetime import timedelta
import os

st.set_page_config(layout="wide")

st.title("APS ELOHIM - ANÁLISE DE CAPACIDADE")

# ===============================
# CONFIG
# ===============================
EFICIENCIA = 0.8

HORAS_DIA = {0:9,1:9,2:9,3:9,4:8}

LEAD_TIME = 21

BASE_DIR = "projeto"

MAQUINAS = {
    "CORTE-LASER": ["LASER_1"],
    "CORTE-PLASMA": ["PLASMA_1"],
    "CORTE - SERRA": ["SERRA_1"],
    "FRESADORAS": ["FRESA_1","FRESA_2","FRESA_3"],
    "TORNO CNC": ["TORNO_1","TORNO_2"],
    "SOLDAGEM": ["SOLDA_1","SOLDA_2","SOLDA_3"],
    "PINTURA": ["PINTURA_1"],
    "JATEAMENTO": ["JATO_1"],
    "MONTAGEM": ["MONT_1"],
    "ACABAMENTO": ["ACAB_1","ACAB_2"],
    "PRENSA (AMASSAMENTO)": ["PRENSA_1"]
}

def capacidade_dia(data):
    if data.weekday() > 4:
        return 0
    return HORAS_DIA.get(data.weekday(),0) * EFICIENCIA

# ===============================
# BASE PROCESSOS
# ===============================
df_base = pd.read_excel(os.path.join(BASE_DIR, "Processos_de_Fabricacao.xlsx"))
df_base.fillna(0, inplace=True)
df_base["CODIGO"] = df_base["CODIGO"].astype(str).str.strip().str.upper()

colunas = list(df_base.columns)
PROCESSOS_VALIDOS = [c for c in colunas if c != "CODIGO" and c in MAQUINAS]

# ===============================
# CARREGAR PLANILHA PV
# ===============================
st.subheader("📂 Carregar Ordens")

ordens = []

try:
    df_pv = pd.read_excel(os.path.join(BASE_DIR, "Relacao_Pv.xlsx"))

    df_pv["CODIGO"] = df_pv["CODIGO"].astype(str).str.upper()
    df_pv["ENTREGA"] = pd.to_datetime(df_pv["ENTREGA"])

    st.success(f"{len(df_pv)} ordens carregadas")

    for _, row in df_pv.iterrows():
        ordens.append({
            "PV": row["PV"],
            "CODIGO": row["CODIGO"],
            "QTD": row["QTD"],
            "ENTREGA": row["ENTREGA"],
            "CLIENTE": row.get("CLIENTE","")
        })

except Exception as e:
    st.error(f"Erro ao carregar planilha: {e}")

# ===============================
# APS FORWARD NIVELADO
# ===============================
if st.button("Gerar APS"):

    carga_dia = {}
    gantt = []

    def chave(maquina, data):
        return (maquina, data.date())

    for ordem in ordens:

        produto = df_base[df_base["CODIGO"] == ordem["CODIGO"]]

        if produto.empty:
            continue

        tempo = ordem["ENTREGA"] - timedelta(days=LEAD_TIME)

        for processo in PROCESSOS_VALIDOS:

            tempo_min = produto.iloc[0].get(processo, 0)

            if tempo_min <= 0:
                continue

            restante = (tempo_min * ordem["QTD"]) / 60
            maquinas = MAQUINAS[processo]

            while restante > 0:

                if tempo.weekday() > 4:
                    tempo += timedelta(days=1)
                    continue

                cap = capacidade_dia(tempo)
                alocado = False

                for maquina in maquinas:

                    usado = carga_dia.get(chave(maquina, tempo), 0)
                    disponivel = cap - usado

                    if disponivel <= 0:
                        continue

                    horas = min(restante, disponivel)

                    inicio = tempo
                    fim = tempo + timedelta(hours=horas)

                    gantt.append({
                        "PV": ordem["PV"],
                        "Cliente": ordem["CLIENTE"],
                        "Processo": processo,
                        "Maquina": maquina,
                        "Início": inicio,
                        "Fim": fim,
                        "Duração (h)": round(horas)
                    })

                    carga_dia[chave(maquina, tempo)] = usado + horas
                    restante -= horas
                    tempo = fim

                    alocado = True
                    break

                if not alocado:
                    tempo += timedelta(days=1)

    gantt_df = pd.DataFrame(gantt)

    if gantt_df.empty:
        st.error("Nenhum dado gerado.")
        st.stop()

    st.session_state["dados_dashboard"] = gantt_df

    st.success("APS gerado com sucesso")