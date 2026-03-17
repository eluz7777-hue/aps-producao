import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")

st.title("APS - Simulador de Produção (Fábrica Real)")

st.subheader("Entrada da Ordem")

# ENTRADA
pecas = st.number_input("Quantidade de peças", value=100)

tempo_laser = st.number_input("Tempo Corte Laser (min/peça)", value=5)
tempo_solda_al = st.number_input("Tempo Solda Alumínio (min/peça)", value=8)
tempo_solda_ac = st.number_input("Tempo Solda Aço (min/peça)", value=10)
tempo_torno = st.number_input("Tempo Torno (min/peça)", value=6)
tempo_fresa = st.number_input("Tempo Fresa (min/peça)", value=7)
tempo_acabamento = st.number_input("Tempo Acabamento (min/peça)", value=5)

# CONFIGURAÇÃO DA FÁBRICA
eficiencia = 0.8
horas_dia = 9

# MÁQUINAS REAIS (baseado na sua fábrica)
recursos = {
    "Corte Laser (André)": 1,
    "Solda Alumínio (3 operadores)": 3,
    "Solda Aço Carbono (3 operadores)": 3,
    "Torno Convencional (2 operadores)": 2,
    "Fresa (3 operadores)": 3,
    "Acabamento (6 operadores)": 6
}

if st.button("Simular Produção Real"):

    dados = []

    processos = {
        "Corte Laser (André)": tempo_laser,
        "Solda Alumínio (3 operadores)": tempo_solda_al,
        "Solda Aço Carbono (3 operadores)": tempo_solda_ac,
        "Torno Convencional (2 operadores)": tempo_torno,
        "Fresa (3 operadores)": tempo_fresa,
        "Acabamento (6 operadores)": tempo_acabamento
    }

    for processo, tempo_unit in processos.items():

        qtd_maquinas = recursos[processo]

        tempo_total_horas = (pecas * tempo_unit) / 60

        capacidade = qtd_maquinas * horas_dia * eficiencia

        ocupacao = (tempo_total_horas / capacidade) * 100 if capacidade > 0 else 0

        dados.append({
            "Recurso": processo,
            "Carga (h)": round(tempo_total_horas,1),
            "Capacidade (h/dia)": round(capacidade,1),
            "Ocupação (%)": round(ocupacao,1)
        })

    df = pd.DataFrame(dados)

    st.subheader("Capacidade da Fábrica")

    st.dataframe(df, use_container_width=True)

    gargalo = df.sort_values(by="Ocupação (%)", ascending=False).iloc[0]

    st.error(f"GARGALO: {gargalo['Recurso']} → {gargalo['Ocupação (%)']}% de ocupação")

    # ALERTAS VISUAIS
    st.subheader("Diagnóstico")

    for i in df.itertuples():
        if i._4 > 100:
            st.error(f"{i.Recurso} está SOBRECARREGADO ({i._4}%)")
        elif i._4 > 80:
            st.warning(f"{i.Recurso} próximo do limite ({i._4}%)")
        else:
            st.success(f"{i.Recurso} com folga ({i._4}%)")