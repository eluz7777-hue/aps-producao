import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

st.set_page_config(layout="wide")

st.title("APS - Planejamento da Produção")

# ===============================
# CARREGAR BASE
# ===============================
df_base = pd.read_excel("Processos_de_Fabricacao.xlsx")

# Limpeza
df_base = df_base.loc[:, ~df_base.columns.str.contains("Unnamed")]
df_base.fillna(0, inplace=True)

df_base["CODIGO"] = df_base["CODIGO"].astype(str).str.strip().str.upper()

codigos_disponiveis = sorted(df_base["CODIGO"].unique())

# ===============================
# ENTRADA DE ORDENS
# ===============================
st.subheader("Ordens")

qtd_ordens = st.number_input("Quantidade de ordens", min_value=1, max_value=20, value=3)

ordens = []

for i in range(qtd_ordens):
    col1, col2, col3, col4, col5 = st.columns(5)

    pv = col1.text_input(f"PV {i}", key=f"pv_{i}")

    codigo = col2.selectbox(
        f"Código {i}",
        options=["-"] + codigos_disponiveis,
        key=f"cod_{i}"
    )

    qtd = col3.number_input(f"Qtd {i}", min_value=1, value=1, key=f"qtd_{i}")

    entrega = col4.date_input(f"Entrega {i}", key=f"entrega_{i}")

    urgente = col5.checkbox("🔥 Urgente", key=f"urg_{i}")

    if codigo != "-":
        ordens.append({
            "PV": pv if pv else f"PV_{i}",
            "CODIGO": codigo,
            "QTD": qtd,
            "ENTREGA": entrega,
            "URGENTE": urgente
        })

# ===============================
# PROCESSAMENTO APS
# ===============================
if st.button("Gerar APS"):

    if len(ordens) == 0:
        st.error("Nenhuma ordem válida")
        st.stop()

    df_ordens = pd.DataFrame(ordens)

    # Ordenação (urgente primeiro, depois data)
    df_ordens = df_ordens.sort_values(
        by=["URGENTE", "ENTREGA"],
        ascending=[False, True]
    )

    inicio_global = datetime.now()

    gantt = []

    for _, ordem in df_ordens.iterrows():

        produto = df_base[df_base["CODIGO"] == ordem["CODIGO"]]

        if produto.empty:
            st.warning(f"Código não encontrado: {ordem['CODIGO']}")
            continue

        tempo_inicio = inicio_global

        for col in df_base.columns:
            if col == "CODIGO":
                continue

            tempo_min = produto.iloc[0][col]

            if tempo_min > 0:
                duracao_h = (tempo_min * ordem["QTD"]) / 60

                tempo_fim = tempo_inicio + timedelta(hours=duracao_h)

                gantt.append({
                    "PV": ordem["PV"],
                    "Processo": col,
                    "Início": tempo_inicio,
                    "Fim": tempo_fim,
                    "Duração (h)": round(duracao_h, 2)
                })

                tempo_inicio = tempo_fim

    if len(gantt) == 0:
        st.error("Nenhum processo gerado")
        st.stop()

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
    # RESUMO
    # ===============================
    total_horas = gantt_df["Duração (h)"].sum()

    gargalo = (
        gantt_df.groupby("Processo")["Duração (h)"]
        .sum()
        .sort_values(ascending=False)
        .index[0]
    )

    st.success(f"Tempo total: {round(total_horas,2)} h")
    st.error(f"Gargalo: {gargalo}")

    # ===============================
    # SALVAR PARA DASHBOARD (AGORA CORRETO)
    # ===============================
    st.session_state["dados_dashboard"] = gantt_df
    st.session_state["total_horas"] = total_horas
    st.session_state["gargalo"] = gargalo
    st.session_state["ordens"] = df_ordens["PV"].nunique()