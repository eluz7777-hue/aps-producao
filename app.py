import streamlit as st
import pandas as pd
from datetime import timedelta

st.set_page_config(layout="wide")
st.title("APS ELOHIM - CAPACIDADE INDUSTRIAL (PADRÃO SAP)")

EFICIENCIA = 0.8
LEAD_TIME = 25

HORAS_DIA = {0:9,1:9,2:9,3:9,4:8}

MAQUINAS = {
    "FRESADORAS": ["FRESA_1", "FRESA_2"],
    "SOLDAGEM": ["SOLDA_1","SOLDA_2","SOLDA_3","SOLDA_4"],
    "TORNO": ["TORNO_1","TORNO_2","TORNO_3"],
    "CORTE-PLASMA": ["PLASMA_1"],
    "CORTE-LASER": ["LASER_1"],
    "SERRA FITA": ["SERRA_FITA_1"],
    "SERRA CIRCULAR": ["SERRA_CIRC_1"],
    "CENTRO USINAGEM": ["CNC_1"],
    "DOBRADEIRA": ["DOBRA_1","DOBRA_2"],
    "PRENSA (AMASSAMENTO)": ["PRENSA_1"],
    "ROSQUEADEIRA": ["ROSQ_1"],
    "ACABAMENTO": ["ACAB_1","ACAB_2","ACAB_3"],
    "CALANDRA": ["CALANDRA_1","CALANDRA_2"],
    "PINTURA": ["PINTURA_1"],
    "METALEIRA": ["METALEIRA_1"]
}

def horas_dia(d):
    return HORAS_DIA.get(d.weekday(),0) * EFICIENCIA

def inicio_semana(d):
    return d - timedelta(days=d.weekday())

# ===============================
# BASE
# ===============================
df_base = pd.read_excel("Processos_de_Fabricacao.xlsx")
df_base.fillna(0, inplace=True)
df_base.columns = [c.strip().upper() for c in df_base.columns]
df_base["CODIGO"] = df_base["CODIGO"].astype(str).str.upper()

PROCESSOS = [c for c in df_base.columns if c != "CODIGO" and c in MAQUINAS]

# ===============================
# PV
# ===============================
df_pv = pd.read_excel("Relacao_Pv.xlsx")
df_pv.columns = [c.strip().upper() for c in df_pv.columns]

df_pv = df_pv.rename(columns={
    "CÓDIGO":"CODIGO",
    "DATA DE ENTREGA":"ENTREGA",
    "QUANTIDADE":"QTD"
})

df_pv["CODIGO"] = df_pv["CODIGO"].astype(str).str.upper()
df_pv["ENTREGA"] = pd.to_datetime(df_pv["ENTREGA"])
df_pv["QTD"] = pd.to_numeric(df_pv["QTD"], errors="coerce").fillna(0)

# 🔥 PRIORIDADE EDD
df_pv = df_pv.sort_values("ENTREGA")

# ===============================
# APS NIVELADO POR SEMANA
# ===============================
if st.button("Gerar APS"):

    gantt = []
    carga = {}

    def chave(m, d):
        return (m, d)

    for _, ordem in df_pv.iterrows():

        produto = df_base[df_base["CODIGO"] == ordem["CODIGO"]]
        if produto.empty:
            continue

        data_base = ordem["ENTREGA"] - timedelta(days=LEAD_TIME)
        semana = inicio_semana(data_base)

        fim_anterior = semana

        for processo in PROCESSOS:

            tempo_min = produto.iloc[0][processo]
            if tempo_min <= 0:
                continue

            restante = (tempo_min * ordem["QTD"]) / 60
            maquinas = MAQUINAS[processo]

            data = fim_anterior

            while restante > 0:

                semana_atual = inicio_semana(data)

                # 🔥 NÃO AVANÇA SEMANA SEM ENCHER A ATUAL
                dias_semana = [semana_atual + timedelta(days=i) for i in range(5)]

                for dia in dias_semana:

                    cap = horas_dia(dia)

                    for maquina in maquinas:

                        usado = carga.get(chave(maquina, dia.date()), 0)
                        disponivel = cap - usado

                        if disponivel <= 0:
                            continue

                        horas = min(restante, disponivel)

                        inicio = dia + timedelta(hours=usado)
                        fim = inicio + timedelta(hours=horas)

                        gantt.append({
                            "PV": ordem["PV"],
                            "Cliente": ordem["CLIENTE"],
                            "Processo": processo,
                            "Maquina": maquina,
                            "Início": inicio,
                            "Fim": fim,
                            "Duração (h)": round(horas,2)
                        })

                        carga[chave(maquina, dia.date())] = usado + horas
                        restante -= horas
                        fim_anterior = fim

                        if restante <= 0:
                            break

                    if restante <= 0:
                        break

                if restante > 0:
                    data = semana_atual + timedelta(days=7)

    st.session_state["dados_dashboard"] = pd.DataFrame(gantt)
    st.success("APS NIVELADO SEMANALMENTE 🚀")