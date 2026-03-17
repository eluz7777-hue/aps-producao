import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

st.set_page_config(layout="wide")

st.title("APS - Planejamento Avançado com Interface Profissional")

# =========================
# CONFIGURAÇÃO FÁBRICA
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
# FUNÇÃO DE CALENDÁRIO
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
        horas_disponiveis = fim_turno - hora_atual

        if horas_restantes <= horas_disponiveis:
            return data + timedelta(hours=horas_restantes)
        else:
            horas_restantes -= horas_disponiveis
            data += timedelta(days=1)
            data = data.replace(hour=inicio_turno, minute=0)

    return data

# =========================
# NORMALIZAR CÓDIGO
# =========================
def normalizar_codigo(x):
    if pd.isna(x):
        return ""
    x = str(x)
    x = x.replace(".0", "")
    x = x.replace(" ", "")
    return x.strip().upper()

# =========================
# CARREGAR BASE
# =========================
df_base = pd.read_excel(
    "Processos_de_Fabricacao.xlsx",
    dtype={"CODIGO": str}
)

df_base = df_base.loc[:, ~df_base.columns.astype(str).str.contains("Unnamed")]
df_base = df_base.fillna(0)
df_base["CODIGO"] = df_base["CODIGO"].apply(normalizar_codigo)

# =========================
# FORMULÁRIO DE ORDENS
# =========================
st.subheader("Cadastro de Ordens")

num_ordens = st.number_input("Quantidade de ordens", min_value=1, max_value=20, value=3)

ordens = []

for i in range(num_ordens):
    st.markdown(f"### Ordem {i+1}")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        pv = st.text_input(f"PV {i}", key=f"pv_{i}")

    with col2:
        codigo = st.text_input(f"Código {i}", key=f"cod_{i}")

    with col3:
        qtd = st.number_input(f"Qtd {i}", min_value=1, value=1, key=f"qtd_{i}")

    with col4:
        data = st.date_input(f"Entrega {i}", key=f"data_{i}")

    ordens.append({
        "pv": pv,
        "codigo": normalizar_codigo(codigo),
        "qtd": qtd,
        "data": pd.to_datetime(data)
    })

# =========================
# RESTRIÇÕES
# =========================
def pode_rodar(processo, ativos):

    if processo == "CORTE-PLASMA":
        if "CORTE-LASER" in ativos or "SOLDAGEM" in ativos:
            return False

    if processo == "CORTE-LASER":
        if "CORTE-PLASMA" in ativos:
            return False

    if processo == "SOLDAGEM":
        if "CORTE-PLASMA" in ativos:
            return False
        if ativos.count("SOLDAGEM") >= 2:
            return False

    return True

# =========================
# EXECUÇÃO APS
# =========================
if st.button("Gerar APS"):

    # ordenar por data de entrega
    pedidos = sorted(ordens, key=lambda x: x["data"])

    timeline = []
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

                    ativos = [
                        p["Processo"]
                        for p in timeline
                        if p["Fim"] > inicio
                    ]

                    while not pode_rodar(processo, ativos):
                        inicio += timedelta(minutes=30)
                        ativos = [
                            p["Processo"]
                            for p in timeline
                            if p["Fim"] > inicio
                        ]

                    fim = somar_horas(inicio, tempo_real)

                    fila_maquinas[processo][idx] = fim
                    tempo_anterior = fim

                    timeline.append({
                        "PV": pedido["pv"],
                        "Ordem": pedido["codigo"],
                        "Processo": processo,
                        "Inicio": inicio,
                        "Fim": fim,
                        "Duracao": round(tempo_real, 2)
                    })

    df_gantt = pd.DataFrame(timeline)

    if df_gantt.empty:
        st.error("Nenhuma ordem válida.")
    else:

        st.subheader("Gantt de Produção")

        fig = px.timeline(
            df_gantt,
            x_start="Inicio",
            x_end="Fim",
            y="Processo",
            color="PV",
            text=df_gantt["Duracao"].astype(str) + " h"
        )

        fig.update_traces(textposition="inside", textfont_size=12)
        fig.update_yaxes(autorange="reversed")

        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Resumo")

        total = df_gantt["Fim"].max()
        st.success(f"Tempo total da fábrica: {round((total - inicio_base).total_seconds()/3600,2)} horas")

        st.write("🔴 Gargalo por Processo")
        st.dataframe(
            df_gantt.groupby("Processo")["Duracao"].sum().sort_values(ascending=False)
        )