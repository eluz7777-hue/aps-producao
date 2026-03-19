import streamlit as st

try:
    import pandas as pd
    from datetime import timedelta
    import os

    st.set_page_config(layout="wide")
    st.write("✅ Imports OK")

    # ===============================
    # TESTE DE ARQUIVO
    # ===============================
    def encontrar_arquivo(nome):
        caminhos = [
            nome,
            f"projeto/{nome}",
            f"./projeto/{nome}"
        ]
        for c in caminhos:
            if os.path.exists(c):
                st.write(f"📂 Encontrado: {c}")
                return c
        return None

    path_proc = encontrar_arquivo("Processos_de_Fabricacao.xlsx")
    path_pv = encontrar_arquivo("Relacao_Pv.xlsx")

    if not path_proc:
        st.error("❌ NÃO encontrou Processos_de_Fabricacao.xlsx")
        st.stop()

    if not path_pv:
        st.error("❌ NÃO encontrou Relacao_Pv.xlsx")
        st.stop()

    # ===============================
    # TESTE LEITURA
    # ===============================
    df_base = pd.read_excel(path_proc)
    st.write("✅ Leu Processos OK")

    df_pv = pd.read_excel(path_pv)
    st.write("✅ Leu PV OK")

    st.success("🎯 Tudo carregado corretamente!")

except Exception as e:
    st.error("💥 ERRO DETECTADO:")
    st.exception(e)