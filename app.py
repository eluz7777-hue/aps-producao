import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")

st.title("APS - Gantt de Produção (Profissional)")

# =========================
# CARREGAR BASE
# =========================
df_base = pd.read_excel("Processos_de_Fabricacao.xlsx")

# limpar colunas lixo
df_base = df_base.loc[:, ~df_base.columns.str.contains("Unnamed")]

# preencher vazios
df_base = df_base.fillna(0)

# =========================
# CONFIGURAÇÃO
# =========================
eficiencia = 0.8
horas_dia = 9

# =========================
# INPUT
# =========================
st.subheader("Simulação por Código")

codigo = st.text_input("Código da peça")
quantidade = st.number_input("Quantidade", value=100)

if st.button("Gerar Programação"):

    df_base["CODIGO"] = df_base["CODIGO"].astype(str).str.strip().str.upper()
codigo_input = codigo.strip().upper()
produto = df_base[df_base["CODIGO"] == codigo_input]

    if produto.empty:
        st.error("Código não encontrado")
    else:
        produto = produto.iloc[0]

        timeline = []
        tempo_acumulado = 0

        for coluna in df_base.columns:

            if coluna not in ["CODIGO", "CLIENTE", "DESCRICAO"]:

                tempo_min = produto[coluna]

                if tempo_min > 0:

                    tempo_total_h = (tempo_min * quantidade) / 60
                    tempo_real = tempo_total_h / eficiencia

                    inicio = tempo_acumulado
                    fim = inicio + tempo_real

                    timeline.append({
                        "Processo": coluna,
                        "Início": inicio,
                        "Fim": fim,
                        "Duração (h)": round(tempo_real,2)
                    })

                    tempo_acumulado = fim

        df_gantt = pd.DataFrame(timeline)

        st.subheader("Linha do Tempo da Produção")

        fig = px.timeline(
            df_gantt,
            x_start="Início",
            x_end="Fim",
            y="Processo",
            color="Processo"
        )

        fig.update_yaxes(autorange="reversed")

        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Resumo")

        tempo_total = df_gantt["Fim"].max()

        st.success(f"Tempo total de produção: {round(tempo_total,1)} horas")

        gargalo = df_gantt.sort_values(by="Duração (h)", ascending=False).iloc[0]

        st.error(f"GARGALO: {gargalo['Processo']} ({gargalo['Duração (h)']} h)")