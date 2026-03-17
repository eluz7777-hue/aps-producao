import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")

st.title("APS - Planejamento Avançado de Produção")

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

# =========================
# CARREGAR BASE
# =========================
df_base = pd.read_excel("Processos_de_Fabricacao.xlsx")

# limpar lixo
df_base = df_base.loc[:, ~df_base.columns.astype(str).str.contains("Unnamed")]
df_base = df_base.fillna(0)

# 🔥 NORMALIZAÇÃO FORTE (resolve 100%)
df_base["CODIGO"] = (
    df_base["CODIGO"]
    .astype(str)
    .str.replace(".0", "", regex=False)
    .str.replace(" ", "")
    .str.strip()
    .str.upper()
)

# =========================
# DEBUG VISUAL
# =========================
st.subheader("Códigos disponíveis (base real)")
st.dataframe(df_base[["CODIGO"]].drop_duplicates().head(30))

# =========================
# INPUT
# =========================
st.subheader("Ordens de Produção")

ordens = st.text_area(
    "Formato: CODIGO,QUANTIDADE",
    "15473448,10\n15473448,20\n10002343864,10"
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

    timeline = []
    fila_maquinas = {p: [0]*maquinas[p] for p in maquinas}

    linhas = ordens.strip().split("\n")

    for linha in linhas:

        try:
            cod, qtd = linha.split(",")
            cod = cod.strip().replace(" ", "").upper()
            qtd = int(qtd)
        except:
            continue

        produto = df_base[df_base["CODIGO"] == cod]

        if produto.empty:
            st.warning(f"Código não encontrado: {cod}")
            continue

        produto = produto.iloc[0]

        tempo_anterior = 0

        for processo in maquinas.keys():

            if processo in df_base.columns:

                tempo_min = pd.to_numeric(produto[processo], errors='coerce')

                if pd.notna(tempo_min) and tempo_min > 0:

                    tempo_h = (tempo_min * qtd) / 60
                    tempo_real = tempo_h / eficiencia

                    maquinas_proc = fila_maquinas[processo]
                    idx = maquinas_proc.index(min(maquinas_proc))

                    inicio = max(maquinas_proc[idx], tempo_anterior)

                    ativos = [p["Processo"] for p in timeline if p["Fim"] > inicio]

                    while not pode_rodar(processo, ativos):
                        inicio += 0.5
                        ativos = [p["Processo"] for p in timeline if p["Fim"] > inicio]

                    fim = inicio + tempo_real

                    fila_maquinas[processo][idx] = fim
                    tempo_anterior = fim

                    timeline.append({
                        "Ordem": cod,
                        "Processo": processo,
                        "Inicio": inicio,
                        "Fim": fim,
                        "Duracao": tempo_real
                    })

    df_gantt = pd.DataFrame(timeline)

    if df_gantt.empty:
        st.error("Nenhuma ordem válida.")
    else:

        st.subheader("Gantt de Produção")

        fig = px.bar(
            df_gantt,
            x="Duracao",
            y="Processo",
            base="Inicio",
            color="Ordem",
            orientation="h"
        )

        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Resumo")

        total = df_gantt["Fim"].max()
        st.success(f"Tempo total da fábrica: {round(total,2)} horas")

        gargalo = df_gantt.groupby("Processo")["Duracao"].sum().sort_values(ascending=False).index[0]
        st.error(f"GARGALO GLOBAL: {gargalo}")