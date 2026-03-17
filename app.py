import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

st.set_page_config(layout="wide")

st.title("APS + DASHBOARD INDUSTRIAL")

# =========================
# CONFIG
# =========================
eficiencia = 0.8

maquinas = {
    "CORTE - SERRA": 1,
    "CORTE-LASER": 1,
    "CORTE-PLASMA": 1,
    "FRESADORAS": 3,
    "TORNO CNC": 2,
    "DOBRADEIRA": 1,
    "PRENSA (AMASSAMENTO)": 1,
    "SOLDAGEM": 3,
    "ACABAMENTO": 6
}

inicio_turno = 7
fim_turno = 17

# =========================
# FUNÇÕES
# =========================
def somar_horas(data_inicio, horas):
    data = data_inicio
    horas_restantes = horas

    while horas_restantes > 0:

        if data.weekday() >= 5:
            data += timedelta(days=1)
            data = data.replace(hour=inicio_turno, minute=0)
            continue

        hora_atual = data.hour + data.minute / 60
        horas_disp = fim_turno - hora_atual

        if horas_restantes <= horas_disp:
            return data + timedelta(hours=horas_restantes)
        else:
            horas_restantes -= horas_disp
            data += timedelta(days=1)
            data = data.replace(hour=inicio_turno, minute=0)

    return data

def normalizar_codigo(x):
    if pd.isna(x):
        return ""
    return str(x).replace(".0","").strip().upper()

# =========================
# BASE
# =========================
df_base = pd.read_excel("Processos_de_Fabricacao.xlsx", dtype={"CODIGO": str})
df_base = df_base.loc[:, ~df_base.columns.astype(str).str.contains("Unnamed")]
df_base = df_base.fillna(0)
df_base["CODIGO"] = df_base["CODIGO"].apply(normalizar_codigo)

lista_codigos = sorted(df_base["CODIGO"].unique())

# =========================
# FORMULÁRIO
# =========================
st.subheader("Cadastro de Ordens")

num_ordens = st.number_input("Quantidade de ordens", 1, 20, 3)

ordens = []

for i in range(num_ordens):

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        pv = st.text_input(f"PV {i}", key=f"pv_{i}")

    with col2:
        codigo = st.selectbox(f"Código {i}", lista_codigos, key=f"cod_{i}")

    with col3:
        qtd = st.number_input(f"Qtd {i}", 1, key=f"qtd_{i}")

    with col4:
        data = st.date_input(f"Entrega {i}", key=f"data_{i}")

    with col5:
        urgente = st.checkbox("🔥 Urgente", key=f"urg_{i}")

    ordens.append({
        "pv": pv,
        "codigo": normalizar_codigo(codigo),
        "qtd": qtd,
        "data": pd.to_datetime(data),
        "urgente": urgente
    })

# =========================
# RESTRIÇÕES
# =========================
def pode_rodar(processo, ativos):

    if processo == "CORTE-PLASMA":
        if "CORTE-LASER" in ativos or "SOLDAGEM" in ativos:
            return False

    if processo == "SOLDAGEM":
        if "CORTE-PLASMA" in ativos:
            return False
        if ativos.count("SOLDAGEM") >= 2:
            return False

    return True

# =========================
# APS
# =========================
if st.button("Gerar APS"):

    urgentes = [o for o in ordens if o["urgente"]]
    normais = [o for o in ordens if not o["urgente"]]

    normais = sorted(normais, key=lambda x: x["data"])

    pedidos = urgentes + normais

    timeline = []
    resumo = []

    inicio_base = datetime.now().replace(hour=inicio_turno, minute=0)

    fila_maquinas = {
        p: [inicio_base for _ in range(maquinas[p])]
        for p in maquinas
    }

    for pedido in pedidos:

        produto = df_base[df_base["CODIGO"] == pedido["codigo"]]

        if produto.empty:
            st.warning(f"Código não encontrado: {pedido['codigo']}")
            continue

        produto = produto.iloc[0]
        tempo_anterior = inicio_base

        for processo in maquinas.keys():

            if processo in df_base.columns:

                tempo_min = pd.to_numeric(produto[processo], errors='coerce')

                if pd.notna(tempo_min) and tempo_min > 0:

                    tempo_h = (tempo_min * pedido["qtd"]) / 60
                    tempo_real = tempo_h / eficiencia

                    maquinas_proc = fila_maquinas[processo]
                    idx = maquinas_proc.index(min(maquinas_proc))

                    inicio = max(maquinas_proc[idx], tempo_anterior)

                    ativos = [p["Processo"] for p in timeline if p["Fim"] > inicio]

                    while not pode_rodar(processo, ativos):
                        inicio += timedelta(minutes=30)
                        ativos = [p["Processo"] for p in timeline if p["Fim"] > inicio]

                    fim = somar_horas(inicio, tempo_real)

                    fila_maquinas[processo][idx] = fim
                    tempo_anterior = fim

                    timeline.append({
                        "PV": pedido["pv"],
                        "Processo": processo,
                        "Inicio": inicio,
                        "Fim": fim,
                        "Duracao": round(tempo_real, 2)
                    })

        atraso_h = (tempo_anterior - pedido["data"]).total_seconds() / 3600

        resumo.append({
            "PV": pedido["pv"],
            "Urgente": "🔥" if pedido["urgente"] else "Padrão",
            "Atraso (h)": round(atraso_h,1),
            "Status": "🔴 Atrasado" if atraso_h > 0 else "🟢 Em dia"
        })

    df_gantt = pd.DataFrame(timeline)
    df_resumo = pd.DataFrame(resumo)

    # =========================
    # DASHBOARD
    # =========================
    st.subheader("Dashboard")

    total_ordens = len(df_resumo)
    atrasadas = len(df_resumo[df_resumo["Status"] == "🔴 Atrasado"])
    taxa_atraso = (atrasadas / total_ordens * 100) if total_ordens > 0 else 0

    col1, col2, col3 = st.columns(3)

    col1.metric("Total Ordens", total_ordens)
    col2.metric("Atrasadas", atrasadas)
    col3.metric("% Atraso", f"{round(taxa_atraso,1)}%")

    # =========================
    # GARGALO
    # =========================
    carga_proc = df_gantt.groupby("Processo")["Duracao"].sum().reset_index()

    gargalo = carga_proc.sort_values(by="Duracao", ascending=False).iloc[0]

    st.error(f"GARGALO PRINCIPAL: {gargalo['Processo']} ({round(gargalo['Duracao'],1)} h)")

    # =========================
    # GRÁFICO
    # =========================
    fig_bar = px.bar(carga_proc, x="Processo", y="Duracao", title="Carga por Processo")
    st.plotly_chart(fig_bar, use_container_width=True)

    # =========================
    # GANTT
    # =========================
    st.subheader("Gantt")

    fig = px.timeline(
        df_gantt,
        x_start="Inicio",
        x_end="Fim",
        y="Processo",
        color="PV",
        text=df_gantt["Duracao"].astype(str) + "h"
    )

    fig.update_traces(textposition="inside")
    fig.update_yaxes(autorange="reversed")

    st.plotly_chart(fig, use_container_width=True)

    # =========================
    # STATUS
    # =========================
    st.subheader("Status das Ordens")
    st.dataframe(df_resumo, use_container_width=True)