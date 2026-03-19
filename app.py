import streamlit as st
import pandas as pd
from datetime import timedelta

st.set_page_config(layout="wide")

st.title("APS ELOHIM - ANÁLISE DE CAPACIDADE")

# ===============================
# CONFIG
# ===============================
EFICIENCIA = 0.8
LEAD_TIME = 21

HORAS_DIA = {0:9,1:9,2:9,3:9,4:8}

MAQUINAS = {
    "CORTE-PLASMA": ["PLASMA_1"],
    "CORTE - SERRA": ["SERRA_1"],
    "SOLDAGEM": ["SOLDA_1","SOLDA_2","SOLDA_3"],
    "PINTURA": ["PINTURA_1"],
    "ACABAMENTO": ["ACAB_1","ACAB_2"]
}

def capacidade_dia(data):
    if data.weekday() > 4:
        return 0
    return HORAS_DIA.get(data.weekday(),0) * EFICIENCIA

# ===============================
# PROCESSOS
# ===============================
df_base = pd.read_excel("Processos_de_Fabricacao.xlsx")
df_base.fillna(0, inplace=True)
df_base.columns = [c.strip().upper() for c in df_base.columns]
df_base["CODIGO"] = df_base["CODIGO"].astype(str).str.upper()

PROCESSOS = [c for c in df_base.columns if c != "CODIGO" and c in MAQUINAS]

# ===============================
# PV (AGORA COM CLIENTE CORRETO)
# ===============================
df_pv = pd.read_excel("Relacao_Pv.xlsx")

# normaliza
df_pv.columns = [c.strip().upper() for c in df_pv.columns]

# mapeamento completo
df_pv = df_pv.rename(columns={
    "CÓDIGO": "CODIGO",
    "DATA DE ENTREGA": "ENTREGA",
    "QUANTIDADE": "QTD",
    "CLIENTE": "CLIENTE"
})

# validação
for col in ["PV","CODIGO","QTD","ENTREGA","CLIENTE"]:
    if col not in df_pv.columns:
        st.error(f"Coluna faltando: {col}")
        st.write(df_pv.columns.tolist())
        st.stop()

# tratamento
df_pv["CODIGO"] = df_pv["CODIGO"].astype(str).str.upper()
df_pv["ENTREGA"] = pd.to_datetime(df_pv["ENTREGA"])
df_pv["QTD"] = pd.to_numeric(df_pv["QTD"], errors="coerce").fillna(0)
df_pv["CLIENTE"] = df_pv["CLIENTE"].astype(str)

st.success(f"{len(df_pv)} ordens carregadas")

# ===============================
# APS
# ===============================
if st.button("Gerar APS"):

    gantt = []

    for _, ordem in df_pv.iterrows():

        produto = df_base[df_base["CODIGO"] == ordem["CODIGO"]]

        if produto.empty:
            continue

        tempo = ordem["ENTREGA"] - timedelta(days=LEAD_TIME)

        for processo in PROCESSOS:

            tempo_min = produto.iloc[0][processo]

            if tempo_min <= 0:
                continue

            restante = (tempo_min * ordem["QTD"]) / 60

            while restante > 0:

                if tempo.weekday() > 4:
                    tempo += timedelta(days=1)
                    continue

                cap = capacidade_dia(tempo)
                horas = min(restante, cap)

                gantt.append({
                    "PV": ordem["PV"],
                    "Cliente": ordem["CLIENTE"],  # 🔥 CORREÇÃO AQUI
                    "Processo": processo,
                    "Maquina": MAQUINAS[processo][0],
                    "Início": tempo,
                    "Fim": tempo + timedelta(hours=horas),
                    "Duração (h)": round(horas)
                })

                restante -= horas
                tempo += timedelta(hours=horas)

    df_gantt = pd.DataFrame(gantt)

    if df_gantt.empty:
        st.error("APS não gerou dados")
        st.stop()

    st.session_state["dados_dashboard"] = df_gantt

    st.success("APS gerado com sucesso")