import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")

st.title("APS - Simulador de Produção (Múltiplas Ordens)")

# CONFIGURAÇÃO
eficiencia = 0.8
horas_dia = 9

# RECURSOS REAIS
recursos = {
    "Corte Laser": 1,
    "Solda Alumínio": 3,
    "Solda Aço": 3,
    "Torno": 2,
    "Fresa": 3,
    "Acabamento": 6
}

st.subheader("Cadastro de Ordens")

# CRIAR ORDENS
num_ordens = st.number_input("Quantidade de ordens", min_value=1, max_value=10, value=3)

ordens = []

for i in range(int(num_ordens)):
    st.markdown(f"### Ordem {i+1}")
    
    pecas = st.number_input(f"Peças O{i+1}", value=100, key=f"p{i}")
    
    tempo_laser = st.number_input(f"Laser (min/peça) O{i+1}", value=5, key=f"l{i}")
    tempo_solda = st.number_input(f"Solda (min/peça) O{i+1}", value=8, key=f"s{i}")
    tempo_torno = st.number_input(f"Torno (min/peça) O{i+1}", value=6, key=f"t{i}")
    tempo_fresa = st.number_input(f"Fresa (min/peça) O{i+1}", value=7, key=f"f{i}")
    tempo_acab = st.number_input(f"Acabamento (min/peça) O{i+1}", value=5, key=f"a{i}")

    ordens.append({
        "pecas": pecas,
        "laser": tempo_laser,
        "solda": tempo_solda,
        "torno": tempo_torno,
        "fresa": tempo_fresa,
        "acab": tempo_acab
    })

# SIMULAÇÃO
if st.button("Simular Carteira de Pedidos"):

    carga_total = {
        "Corte Laser": 0,
        "Solda Alumínio": 0,
        "Solda Aço": 0,
        "Torno": 0,
        "Fresa": 0,
        "Acabamento": 0
    }

    for ordem in ordens:

        carga_total["Corte Laser"] += (ordem["pecas"] * ordem["laser"]) / 60
        carga_total["Solda Alumínio"] += (ordem["pecas"] * ordem["solda"]) / 60
        carga_total["Solda Aço"] += (ordem["pecas"] * ordem["solda"]) / 60
        carga_total["Torno"] += (ordem["pecas"] * ordem["torno"]) / 60
        carga_total["Fresa"] += (ordem["pecas"] * ordem["fresa"]) / 60
        carga_total["Acabamento"] += (ordem["pecas"] * ordem["acab"]) / 60

    dados = []

    for recurso, carga in carga_total.items():

        capacidade = recursos[recurso] * horas_dia * eficiencia
        ocupacao = (carga / capacidade) * 100 if capacidade > 0 else 0

        dias_necessarios = carga / capacidade if capacidade > 0 else 0

        dados.append({
            "Recurso": recurso,
            "Carga Total (h)": round(carga,1),
            "Capacidade/dia (h)": round(capacidade,1),
            "Ocupação (%)": round(ocupacao,1),
            "Dias Necessários": round(dias_necessarios,1)
        })

    df = pd.DataFrame(dados)

    st.subheader("Resultado da Carteira")

    st.dataframe(df, use_container_width=True)

    gargalo = df.sort_values(by="Dias Necessários", ascending=False).iloc[0]

    st.error(f"GARGALO DA FÁBRICA: {gargalo['Recurso']} → {gargalo['Dias Necessários']} dias")

    st.subheader("Diagnóstico")

    for i in df.itertuples():
        if i._4 > 100:
            st.error(f"{i.Recurso} sobrecarregado ({i._4}%)")
        elif i._4 > 80:
            st.warning(f"{i.Recurso} no limite ({i._4}%)")
        else:
            st.success(f"{i.Recurso} OK ({i._4}%)")