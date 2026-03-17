import streamlit as st
import pandas as pd

st.title("Dashboard Industrial")

st.info("Aqui entrarão indicadores globais da fábrica")

st.metric("OEE (simulado)", "82%")
st.metric("Atrasos", "12%")
st.metric("Utilização", "76%")