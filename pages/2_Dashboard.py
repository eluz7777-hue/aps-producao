# ===============================
# 🔥 SIMULAÇÃO DE PV (NOVO)
# ===============================
st.subheader("Simulação de PV (Entrada / Exclusão)")

# Inicializa base simulada
if "df_simulado" not in st.session_state:
    st.session_state["df_simulado"] = df.copy()

df = st.session_state["df_simulado"]

col1, col2 = st.columns(2)

# ===============================
# ➕ INSERIR PV
# ===============================
with col1:
    st.markdown("### ➕ Inserir PV")

    with st.form("form_pv"):
        pv = st.text_input("PV")
        cliente = st.text_input("Cliente")
        processo = st.selectbox("Processo", sorted(df["Processo"].unique()))
        maquina = st.text_input("Máquina (ex: FRESA_1)")
        horas = st.number_input("Duração (h)", min_value=0.1, step=0.1)
        data = st.date_input("Data")

        submitted = st.form_submit_button("Adicionar PV")

        if submitted:
            novo = pd.DataFrame([{
                "PV": pv,
                "Cliente": cliente,
                "Processo": processo,
                "Maquina": maquina,
                "Início": pd.to_datetime(data),
                "Fim": pd.to_datetime(data),
                "Duração (h)": horas
            }])

            st.session_state["df_simulado"] = pd.concat([df, novo], ignore_index=True)
            st.success("PV adicionada para simulação")

# ===============================
# ➖ REMOVER PV
# ===============================
with col2:
    st.markdown("### ➖ Remover PV")

    lista_pv = df["PV"].unique()

    pv_remove = st.selectbox("Selecione a PV para remover", lista_pv)

    if st.button("Remover PV"):
        st.session_state["df_simulado"] = df[df["PV"] != pv_remove]
        st.success("PV removida da simulação")

# Atualiza df após alterações
df = st.session_state["df_simulado"]