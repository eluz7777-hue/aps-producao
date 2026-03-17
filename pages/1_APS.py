import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

st.set_page_config(layout="wide")

st.title("APS ELOHIM - ANÁLISE DE CAPACIDADE")

# ===============================
# CONFIGURAÇÃO REAL
# ===============================
EFICIENCIA = 0.8

HORAS_DIA = {
    0: 9,
    1: 9,
    2: 9,
    3: 9,
    4: 8
}

# ===============================
# MÁQUINAS REAIS
# ===============================
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
# TURNOS
# ===============================
def ajustar_para_turno(data):

    while True:

        if data.weekday() > 4:
            data += timedelta(days=1)
            data = data.replace(hour=7, minute=0)
            continue

        inicio = 7
        fim = 17 if data.weekday() < 4 else 16

        if data.hour < inicio:
            return data.replace(hour=inicio, minute=0)

        if data.hour >= fim:
            data += timedelta(days=1)
            data = data.replace(hour=7, minute=0)
            continue

        return data

def capacidade_dia(data):
    return HORAS_DIA.get(data.weekday(), 0) * EFICIENCIA

# ===============================
# BASE
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
            "ENTREGA": pd.to_datetime(entrega),
            "URGENTE": urgente
        })

# ===============================
# CONFLITO
# ===============================
def conflito(maquina, inicio, fim, agenda):
    for (i, f) in agenda[maquina]:
        if not (fim <= i or inicio >= f):
            return True
    return False

# ===============================
# APS
# ===============================
if st.button("Gerar APS"):

    df_ordens = pd.DataFrame(ordens)

    df_ordens = df_ordens.sort_values(
        by=["URGENTE", "ENTREGA"],
        ascending=[False, True]
    )

    agenda = {m: [] for maquinas in MAQUINAS.values() for m in maquinas}

    gantt = []

    inicio_global = ajustar_para_turno(datetime.now())

    for _, ordem in df_ordens.iterrows():

        produto = df_base[df_base["CODIGO"] == ordem["CODIGO"]]

        if produto.empty:
            continue

        tempo_inicio = inicio_global

        for processo in PROCESSOS_VALIDOS:

            if processo not in df_base.columns:
                continue

            tempo_min = produto.iloc[0][processo]

            if tempo_min <= 0:
                continue

            duracao_total = (tempo_min * ordem["QTD"]) / 60

            maquinas = MAQUINAS[processo]

            # 🔥 ESCOLHE MÁQUINA MENOS CARREGADA
            cargas = {
                m: sum([(f - i).total_seconds() for i, f in agenda[m]])
                for m in maquinas
            }

            maquina_escolhida = min(cargas, key=cargas.get)

            restante = duracao_total
            atual = tempo_inicio

            while restante > 0:

                atual = ajustar_para_turno(atual)

                cap = capacidade_dia(atual)

                if cap <= 0:
                    atual += timedelta(days=1)
                    continue

                horas_exec = min(restante, cap)

                tentativa = atual
                fim = tentativa + timedelta(hours=horas_exec)

                while conflito(maquina_escolhida, tentativa, fim, agenda):
                    tentativa += timedelta(minutes=10)
                    tentativa = ajustar_para_turno(tentativa)
                    fim = tentativa + timedelta(hours=horas_exec)

                agenda[maquina_escolhida].append((tentativa, fim))

                gantt.append({
                    "PV": ordem["PV"],
                    "Processo": processo,
                    "Maquina": maquina_escolhida,
                    "Início": tentativa,
                    "Fim": fim,
                    "Duração (h)": round(horas_exec, 2)
                })

                restante -= horas_exec
                atual = fim

            tempo_inicio = atual

    gantt_df = pd.DataFrame(gantt)

    st.subheader("Gantt de Produção")

    fig = px.timeline(
        gantt_df,
        x_start="Início",
        x_end="Fim",
        y="Maquina",
        color="PV",
        text="Duração (h)"
    )

    fig.update_yaxes(autorange="reversed")

    st.plotly_chart(fig, use_container_width=True)

    # ===============================
    # OCUPAÇÃO REAL
    # ===============================
    st.subheader("Ocupação Real (%)")

    ocup = (
        gantt_df.groupby("Maquina")["Duração (h)"]
        .sum()
        .reset_index()
    )

    dias = gantt_df["Início"].dt.date.nunique()
    capacidade_total = dias * 9 * EFICIENCIA

    ocup["Ocupação (%)"] = (ocup["Duração (h)"] / capacidade_total) * 100

    fig2 = px.bar(
        ocup,
        x="Maquina",
        y="Ocupação (%)",
        text_auto=True
    )

    st.plotly_chart(fig2, use_container_width=True)

    st.session_state["dados_dashboard"] = gantt_df