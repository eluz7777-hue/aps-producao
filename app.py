import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")

st.title("APS - Gantt de Produção (Profissional)")

# =========================
# CARREGAR BASE
# =========================
df_base = pd.read_excel("Processos_de_Fabricacao.xlsx")

df_base = df_base.loc[:, ~df_base.columns.astype(str).str.contains("Unnamed")]
df_base = df_base.fillna(0)

df_base["CODIGO"] = (
    df_base["CODIGO"]
    .astype(str)
    .str.replace(".0", "", regex=False)
    .str.strip()
    .str.upper()
)

# =========================
# PROCESSOS REAIS
# =========================
processos_validos = [
    "CORTE - SERRA",
    "CORTE-LASER",
    "CORTE-PLASMA",
    "FRESADORAS",
    "TORNO CNC",
    "DOBRADEIRA",
    "PRENSA (AMASSAMENTO)",
    "SOLDAGEM",
    "ACABAMENTO"
]

# =========================
# INPUT
# =========================
st.subheader("Simulação por Código")

codigo = st.text_input("Código da peça")
quantidade = st.number_input("Quantidade", value=100)

st.write("Códigos disponíveis:")
st.write(df_base["CODIGO"].head(20))

# =========================
# BOTÃO
# =========================
if st.button("Gerar Programação"):

    codigo_input = codigo.strip().upper().replace(".0", "")

    produto = df_base[df_base["CODIGO"] == codigo_input]

    if produto.empty:
        st.error("Código não encontrado")
    else:
        produto = produto.iloc[0]

        eficiencia = 0.8
        timeline = []
        tempo_acumulado = 0

        for processo in processos_validos:

            if processo in df_base.columns:

                tempo_min = pd.to_numeric(produto[processo], errors='coerce')

                if pd.notna(tempo_min) and tempo_min > 0:

                    tempo_total_h = (tempo_min * quantidade) / 60
                    tempo_real = tempo_total_h / eficiencia

                    inicio = tempo_acumulado
                    fim = inicio + tempo_real

                    timeline.append({
                        "Processo": processo,
                        "Inicio": inicio,
                        "Fim": fim,
                        "Duracao": tempo_real
                    })

                    tempo_acumulado = fim

        df_gantt = pd.DataFrame(timeline)

        if df_gantt.empty:
            st.warning("Esse produto não possui tempos cadastrados.")
        else:
            st.subheader("Linha do Tempo da Produção")

            # Gantt com eixo numérico (correto)
            fig = px.bar(
                df_gantt,
                x="Duracao",
                y="Processo",
                base="Inicio",
                orientation="h",
                text="Duracao"
            )

            fig.update_layout(
                xaxis_title="Horas",
                yaxis_title="Processo"
            )

            st.plotly_chart(fig, use_container_width=True)

            st.subheader("Resumo")

            tempo_total = df_gantt["Fim"].max()

            st.success(f"Tempo total de produção: {round(tempo_total,2)} horas")

            gargalo = df_gantt.sort_values(by="Duracao", ascending=False).iloc[0]

            st.error(f"GARGALO: {gargalo['Processo']} ({round(gargalo['Duracao'],2)} h)")