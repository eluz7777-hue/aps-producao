import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")

st.title("APS - Simulador de Produção")

st.subheader("Simulador de Capacidade da Fábrica")

# CONFIGURAÇÃO DA FÁBRICA
eficiencia = 0.8
horas_dia = 9   # 07h–17h com 1h almoço → 9h úteis
horas_sexta = 8 # sexta

# MÁQUINAS (base inicial)
maquinas = {
    "Corte Laser": 1,
    "Solda Alumínio": 3,
    "Solda Aço": 3,
    "Fresadora": 3,
    "Torno": 2,
    "Acabamento": 6
}

st.subheader("Entrada de Produção")

pecas = st.number_input("Quantidade de peças", value=100)

tempo_laser = st.number_input("Tempo no Laser (min/peça)", value=5)
tempo_solda = st.number_input("Tempo na Solda (min/peça)", value=10)
tempo_fresa = st.number_input("Tempo na Fresa (min/peça)", value=8)

if st.button("Simular Fábrica"):

    dados = []

    for processo, qtd_maquinas in maquinas.items():

        if processo == "Corte Laser":
            tempo_total = pecas * tempo_laser / 60
        elif processo == "Solda Alumínio":
            tempo_total = pecas * tempo_solda / 60
        elif processo == "Fresadora":
            tempo_total = pecas * tempo_fresa / 60
        else:
            tempo_total = 0

        capacidade = qtd_maquinas * horas_dia * eficiencia

        ocupacao = (tempo_total / capacidade) * 100 if capacidade > 0 else 0

        dados.append({
            "Processo": processo,
            "Carga (h)": round(tempo_total,1),
            "Capacidade (h)": round(capacidade,1),
            "Ocupação (%)": round(ocupacao,1)
        })

    df = pd.DataFrame(dados)

    st.subheader("Resultado")

    st.dataframe(df, use_container_width=True)

    gargalo = df.sort_values(by="Ocupação (%)", ascending=False).iloc[0]

    st.error(f"Gargalo da fábrica: {gargalo['Processo']} ({gargalo['Ocupação (%)']}%)")