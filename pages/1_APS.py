import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

st.title("Planejamento APS")

eficiencia = 0.8

maquinas = {
    "CORTE - SERRA": 1,
    "CORTE-LASER": 1,
    "FRESADORAS": 3,
    "SOLDAGEM": 3,
    "ACABAMENTO": 6
}

def normalizar_codigo(x):
    return str(x).replace(".0","").strip().upper()

df_base = pd.read_excel("Processos_de_Fabricacao.xlsx", dtype={"CODIGO": str})
df_base = df_base.fillna(0)
df_base["CODIGO"] = df_base["CODIGO"].apply(normalizar_codigo)

lista_codigos = sorted(df_base["CODIGO"].unique())

st.subheader("Ordens")

num = st.number_input("Qtd Ordens",1,10,3)

ordens = []

for i in range(num):

    col1,col2,col3,col4,col5 = st.columns(5)

    with col1:
        pv = st.text_input(f"PV {i}", key=f"pv{i}")

    with col2:
        cod = st.selectbox(f"Código {i}", lista_codigos, key=f"cod{i}")

    with col3:
        qtd = st.number_input(f"Qtd {i}",1,key=f"qtd{i}")

    with col4:
        data = st.date_input(f"Entrega {i}", key=f"data{i}")

    with col5:
        urg = st.checkbox("🔥", key=f"urg{i}")

    ordens.append({
        "pv": pv,
        "codigo": cod,
        "qtd": qtd,
        "data": pd.to_datetime(data),
        "urgente": urg
    })

if st.button("Gerar APS"):

    timeline = []
    inicio_base = datetime.now()

    for o in ordens:

        prod = df_base[df_base["CODIGO"] == o["codigo"]]

        if prod.empty:
            st.warning(f"Não encontrado: {o['codigo']}")
            continue

        prod = prod.iloc[0]
        tempo = inicio_base

        for p in maquinas:

            if p in df_base.columns and prod[p] > 0:

                dur = (prod[p]*o["qtd"])/60/eficiencia

                inicio = tempo
                fim = inicio + timedelta(hours=dur)

                tempo = fim

                timeline.append({
                    "PV": o["pv"],
                    "Processo": p,
                    "Inicio": inicio,
                    "Fim": fim,
                    "Duracao": round(dur,2)
                })

    df = pd.DataFrame(timeline)

    fig = px.timeline(df, x_start="Inicio", x_end="Fim", y="Processo", color="PV",
                      text=df["Duracao"].astype(str)+"h")

    fig.update_yaxes(autorange="reversed")

    st.plotly_chart(fig, use_container_width=True)