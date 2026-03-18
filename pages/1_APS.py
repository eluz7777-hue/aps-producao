import streamlit as st
import pandas as pd
from datetime import timedelta

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

LEAD_TIME = 21  # dias

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

# ===============================
# FUNÇÃO CAPACIDADE
# ===============================
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

# 🔥 ORDEM DO PROCESSO VEM DO EXCEL
colunas = list(df_base.columns)
PROCESSOS_VALIDOS = [
    c for c in colunas
    if c != "CODIGO" and c in MAQUINAS
]

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
# APS FORWARD NIVELADO (CORRETO)
# ===============================
if st.button("Gerar APS"):

    carga_dia = {}  # controle por máquina/dia
    gantt = []

    def chave(maquina, data):
        return (maquina, data.date())

    for ordem in ordens:

        produto = df_base[df_base["CODIGO"] == ordem["CODIGO"]]

        if produto.empty:
            continue

        # 🔥 COMEÇA NO INÍCIO DO LEAD TIME
        tempo = ordem["ENTREGA"] - timedelta(days=LEAD_TIME)

        for processo in PROCESSOS_VALIDOS:

            tempo_min = produto.iloc[0].get(processo, 0)

            if tempo_min <= 0:
                continue

            restante = (tempo_min * ordem["QTD"]) / 60
            maquinas = MAQUINAS[processo]

            while restante > 0:

                # pula fim de semana
                if tempo.weekday() > 4:
                    tempo += timedelta(days=1)
                    continue

                cap_dia = capacidade_dia(tempo)

                alocado = False

                for maquina in maquinas:

                    usado = carga_dia.get(chave(maquina, tempo), 0)
                    disponivel = cap_dia - usado

                    if disponivel <= 0:
                        continue

                    horas = min(restante, disponivel)

                    inicio = tempo
                    fim = tempo + timedelta(hours=horas)

                    gantt.append({
                        "PV": ordem["PV"],
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
        st.error("Nenhum dado gerado. Verifique a planilha.")
        st.stop()

    st.session_state["dados_dashboard"] = gantt_df

    st.success("APS com nivelamento real gerado com sucesso")