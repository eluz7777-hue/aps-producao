import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

st.set_page_config(layout="wide")

st.title("APS - Planejamento Avançado com Calendário Real")

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
        if data.weekday() >= 5:  # fim de semana
            data += timedelta(days=1)
            data = data.replace(hour=inicio_turno, minute=0)
            continue

        hora_atual = data.hour + data.minute/60
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
# INPUT
# =========================
st.subheader("Ordens de Produção")

st.write("Formato: CODIGO,QUANTIDADE,DATA_ENTREGA (AAAA-MM-DD)")

ordens = st.text_area(
    "",
    "15494625,5,2026-03-20\nHVHV311697-01,5,2026-03-18\n16323723,9,2026-03-25"
)

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

    pedidos = []

    for linha in ordens.strip().split("\n"):
        try:
            cod, qtd, data = linha.split(",")
            pedidos.append({
                "codigo": normalizar_codigo(cod),
                "qtd": int(qtd),
                "data": pd.to_datetime(data)
            })
        except:
            continue

    # 🔥 ORDENAR POR DATA
    pedidos = sorted(pedidos, key=lambda x: x["data"])

    timeline = []
    fila_maquinas = {p: [datetime.now().replace(hour=7, minute=0)]*maquinas[p] for p in maquinas}

    for pedido in pedidos:

        produto = df_base[df_base["CODIGO"] == pedido["codigo"]]

        if produto.empty:
            st.warning(f"Código não encontrado: {pedido['codigo']}")
            continue

        produto = produto.iloc[0]
        tempo_anterior = datetime.now().replace(hour=7, minute=0)

        for processo in maquinas.keys():

            if processo in df_base.columns:

                tempo_min = pd.to_numeric(produto[processo], errors='coerce')

                if pd.notna(tempo_min) and tempo_min > 0:

                    tempo_h = (tempo_min * pedido["qtd"]) / 60
                    tempo_real = tempo_h / eficiencia

                    maquinas_proc = fila_maquinas[processo]
                    idx = maquinas_proc.index(min(maquinas_proc))

                    inicio = max(maquinas_proc[idx], tempo_anterior)

                    fim = somar_horas(inicio, tempo_real)

                    fila_maquinas[processo][idx] = fim
                    tempo_anterior = fim

                    timeline.append({
                        "Ordem": pedido["codigo"],
                        "Processo": processo,
                        "Inicio": inicio,
                        "Fim": fim,
                        "Duracao": tempo_real
                    })

    df_gantt = pd.DataFrame(timeline)

    if df_gantt.empty:
        st.error("Nenhuma ordem válida.")
    else:

        st.subheader("Gantt com Datas Reais")

        fig = px.timeline(
            df_gantt,
            x_start="Inicio",
            x_end="Fim",
            y="Processo",
            color="Ordem"
        )

        fig.update_yaxes(autorange="reversed")

        st.plotly_chart(fig, use_container_width=True)

        # =========================
        # GARGALOS
        # =========================
        st.subheader("Análise de Gargalos")

        df_gantt["Dia"] = df_gantt["Inicio"].dt.date
        df_gantt["Semana"] = df_gantt["Inicio"].dt.isocalendar().week
        df_gantt["Mes"] = df_gantt["Inicio"].dt.month

        st.write("🔴 Gargalo Diário")
        st.dataframe(
            df_gantt.groupby(["Dia","Processo"])["Duracao"].sum().reset_index()
        )

        st.write("🟠 Gargalo Semanal")
        st.dataframe(
            df_gantt.groupby(["Semana","Processo"])["Duracao"].sum().reset_index()
        )

        st.write("🟢 Gargalo Mensal")
        st.dataframe(
            df_gantt.groupby(["Mes","Processo"])["Duracao"].sum().reset_index()
        )