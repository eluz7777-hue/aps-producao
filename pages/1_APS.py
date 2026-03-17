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
    0: 9,  # segunda
    1: 9,
    2: 9,
    3: 9,
    4: 8   # sexta
}

PROCESSOS_VALIDOS = [
    "CORTE - SERRA",
    "CORTE-LASER",
    "FRESADORAS",
    "PRENSA (AMASSAMENTO)",
    "SOLDAGEM",
    "ACABAMENTO",
    "TORNO CNC"
]

RESTRICOES = {
    "CORTE-LASER": ["PLASMA"],
    "PLASMA": ["CORTE-LASER"]
}

# ===============================
# FUNÇÃO TURNO
# ===============================
def ajustar_para_turno(data):
    while data.weekday() > 4:
        data += timedelta(days=1)

    hora_inicio = 7
    hora_fim = 17 if data.weekday() < 4 else 16

    if data.hour < hora_inicio:
        return data.replace(hour=hora_inicio, minute=0)

    if data.hour >= hora_fim:
        data += timedelta(days=1)
        return ajustar_para_turno(data)

    return data

# ===============================
# CAPACIDADE DIÁRIA
# ===============================
def capacidade_dia(data):
    horas = HORAS_DIA.get(data.weekday(), 0)
    return horas * EFICIENCIA

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
            "ENTREGA": pd.to_datetime(entrega),
            "URGENTE": urgente
        })

# ===============================
# CONFLITO
# ===============================
def conflito(processo, inicio, fim, agenda):
    for p, blocos in agenda.items():
        if p == processo or p in RESTRICOES.get(processo, []):
            for i, f in blocos:
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

    agenda = {p: [] for p in PROCESSOS_VALIDOS}

    inicio_global = ajustar_para_turno(datetime.now())

    gantt = []

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

            duracao_h = (tempo_min * ordem["QTD"]) / 60

            restante = duracao_h
            atual = tempo_inicio

            while restante > 0:

                atual = ajustar_para_turno(atual)

                cap_dia = capacidade_dia(atual)

                if cap_dia == 0:
                    atual += timedelta(days=1)
                    continue

                horas_exec = min(restante, cap_dia)

                fim = atual + timedelta(hours=horas_exec)

                tentativa = atual

                while conflito(processo, tentativa, fim, agenda):
                    tentativa += timedelta(minutes=10)
                    tentativa = ajustar_para_turno(tentativa)
                    fim = tentativa + timedelta(hours=horas_exec)

                agenda[processo].append((tentativa, fim))

                gantt.append({
                    "PV": ordem["PV"],
                    "Processo": processo,
                    "Maquina": processo,
                    "Início": tentativa,
                    "Fim": fim,
                    "Duração (h)": round(horas_exec, 2)
                })

                restante -= horas_exec
                atual = fim

            tempo_inicio = atual

    gantt_df = pd.DataFrame(gantt)

    # ===============================
    # GANTT
    # ===============================
    st.subheader("Gantt de Produção")

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
    # OCUPAÇÃO
    # ===============================
    st.subheader("Ocupação por Máquina (%)")

    ocupacao = (
        gantt_df.groupby("Maquina")["Duração (h)"]
        .sum()
        .reset_index()
    )

    dias = gantt_df["Início"].dt.date.nunique()
    capacidade_total = dias * 9 * EFICIENCIA

    ocupacao["Ocupação (%)"] = (ocupacao["Duração (h)"] / capacidade_total) * 100

    fig2 = px.bar(
        ocupacao,
        x="Maquina",
        y="Ocupação (%)",
        text_auto=True
    )

    st.plotly_chart(fig2, use_container_width=True)

    # ===============================
    # SALVAR
    # ===============================
    st.session_state["dados_dashboard"] = gantt_df