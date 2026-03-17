import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")

st.title("APS - Simulador com Base Real")

# CARREGAR PLANILHA
df_base = pd.read_excel("Processos_de_Fabricacao.xlsx")
df_base = df_base.fillna(0)
st.write(df_base.columns)

# LIMPEZA BÁSICA
df_base = df_base.dropna(subset=["CODIGO"])

st.subheader("Consulta de Produto")

codigo = st.text_input("Digite o código da peça")

eficiencia = 0.8
horas_dia = 9

recursos = {
    "CORTE-LASER": 1,
    "SOLDAGEM": 3,
    "FRESADORAS": 3,
    "TORNO CNC": 2,
    "ACABAMENTO": 6
}

if st.button("Simular por Código"):

    produto = df_base[df_base["CODIGO"] == codigo]

    if produto.empty:
        st.error("Código não encontrado")
    else:
        produto = produto.iloc[0]

        dados = []

        for processo in recursos.keys():

            if processo in df_base.columns:

                tempo_min = produto[processo]

                if pd.notna(tempo_min):

                    tempo_h = tempo_min / 60
                    capacidade = recursos[processo] * horas_dia * eficiencia
                    ocupacao = (tempo_h / capacidade) * 100

                    dados.append({
                        "Processo": processo,
                        "Tempo (h)": round(tempo_h,2),
                        "Capacidade (h/dia)": round(capacidade,1),
                        "Ocupação (%)": round(ocupacao,1)
                    })

        df = pd.DataFrame(dados)

        st.dataframe(df, use_container_width=True)

        if not df.empty:
            gargalo = df.sort_values(by="Ocupação (%)", ascending=False).iloc[0]
            st.error(f"GARGALO: {gargalo['Processo']} ({gargalo['Ocupação (%)']}%)")