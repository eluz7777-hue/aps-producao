import streamlit as st

st.set_page_config(
    page_title="APS Elohim",
    layout="wide"
)

# =========================
# SIDEBAR COM LOGO
# =========================
st.sidebar.image("logo.png", use_container_width=True)

st.sidebar.markdown("## APS ELOHIM")
st.sidebar.markdown("### Análise de Capacidade")

st.sidebar.markdown("---")
st.sidebar.info("Sistema de Planejamento Industrial")

# =========================
# TÍTULO CENTRAL
# =========================
st.markdown(
    "<h1 style='text-align: center;'>APS ELOHIM - ANÁLISE DE CAPACIDADE</h1>",
    unsafe_allow_html=True
)

st.markdown("## 👈 Use o menu lateral para navegar entre as páginas")