import streamlit as st
import pandas as pd
import plotly.express as px

# ===============================
# CONFIG DA PÁGINA
# ===============================
st.set_page_config(page_title="APS | OEE & Qualidade", layout="wide")
st.title("APS | OEE & Qualidade")

# ===============================
# LEITURA DA PLANILHA OEE
# ===============================
ARQUIVO_OEE = "OEE - 2026.xlsx"

try:
    df_oee = pd.read_excel(ARQUIVO_OEE)
except Exception as e:
    st.error(f"Erro ao ler a planilha OEE: {e}")
    st.stop()

# ===============================
# PADRONIZAÇÃO DE COLUNAS
# ===============================
df_oee.columns = df_oee.columns.astype(str).str.strip().str.upper()

colunas_esperadas = [
    "MÊS",
    "PEÇAS PLANEJADAS PARA FABRICAÇÃO",
    "PEÇAS FABRICADAS (FATURADAS)",
    "PEÇAS REFUGADAS"
]

faltantes = [c for c in colunas_esperadas if c not in df_oee.columns]

if faltantes:
    st.error(f"Colunas obrigatórias ausentes na planilha OEE: {faltantes}")
    st.stop()

# ===============================
# LIMPEZA E FILTRO DE DADOS
# ===============================
df_oee = df_oee[colunas_esperadas].copy()

df_oee = df_oee.rename(columns={
    "MÊS": "Mes",
    "PEÇAS PLANEJADAS PARA FABRICAÇÃO": "Planejadas",
    "PEÇAS FABRICADAS (FATURADAS)": "Fabricadas",
    "PEÇAS REFUGADAS": "Refugadas"
})

# Remove linhas totalmente vazias
df_oee = df_oee.dropna(how="all")

# Preenche vazios numéricos com zero
for col in ["Planejadas", "Fabricadas", "Refugadas"]:
    df_oee[col] = pd.to_numeric(df_oee[col], errors="coerce").fillna(0)

# Remove meses sem nome
df_oee["Mes"] = df_oee["Mes"].astype(str).str.strip().str.upper()
df_oee = df_oee[df_oee["Mes"] != ""].copy()

# Considera apenas meses com dados do período já realizado
df_oee = df_oee[df_oee["Planejadas"] > 0].copy()

if df_oee.empty:
    st.warning("Nenhum dado válido encontrado na planilha OEE.")
    st.stop()

# ===============================
# ORDEM DOS MESES
# ===============================
ordem_meses = {
    "JAN": 1, "FEV": 2, "MAR": 3, "ABR": 4, "MAI": 5, "JUN": 6,
    "JUL": 7, "AGO": 8, "SET": 9, "OUT": 10, "NOV": 11, "DEZ": 12
}

df_oee["Ordem"] = df_oee["Mes"].map(ordem_meses)
df_oee = df_oee.sort_values("Ordem").reset_index(drop=True)

# ===============================
# CÁLCULOS OEE & QUALIDADE
# ===============================
df_oee["Total Produzido"] = df_oee["Fabricadas"] + df_oee["Refugadas"]

df_oee["Atingimento (%)"] = df_oee.apply(
    lambda r: (r["Fabricadas"] / r["Planejadas"] * 100) if r["Planejadas"] > 0 else 0,
    axis=1
)

df_oee["Qualidade (%)"] = df_oee.apply(
    lambda r: (r["Fabricadas"] / r["Total Produzido"] * 100) if r["Total Produzido"] > 0 else 0,
    axis=1
)

df_oee["Refugo (%)"] = df_oee.apply(
    lambda r: (r["Refugadas"] / r["Total Produzido"] * 100) if r["Total Produzido"] > 0 else 0,
    axis=1
)

df_oee["Eficiência Industrial (%)"] = (
    (df_oee["Atingimento (%)"] / 100) *
    (df_oee["Qualidade (%)"] / 100) * 100
)

# Arredondamentos
for col in ["Atingimento (%)", "Qualidade (%)", "Refugo (%)", "Eficiência Industrial (%)"]:
    df_oee[col] = df_oee[col].round(1)

# ===============================
# KPIs PRINCIPAIS
# ===============================
st.subheader("📌 Indicadores Principais")

planejado_total = int(df_oee["Planejadas"].sum())
fabricado_total = int(df_oee["Fabricadas"].sum())
refugado_total = int(df_oee["Refugadas"].sum())

atingimento_geral = round(
    (fabricado_total / planejado_total * 100), 1
) if planejado_total > 0 else 0

qualidade_geral = round(
    (fabricado_total / (fabricado_total + refugado_total) * 100), 1
) if (fabricado_total + refugado_total) > 0 else 0

eficiencia_geral = round(
    (atingimento_geral / 100) * (qualidade_geral / 100) * 100, 1
)

k1, k2, k3, k4 = st.columns(4)

k1.metric("Peças Planejadas", f"{planejado_total:,}")
k2.metric("Peças Fabricadas", f"{fabricado_total:,}")
k3.metric("Peças Refugadas", f"{refugado_total:,}")
k4.metric("Eficiência Industrial (%)", f"{eficiencia_geral:.1f}%")

k5, k6 = st.columns(2)
k5.metric("Atingimento (%)", f"{atingimento_geral:.1f}%")
k6.metric("Qualidade (%)", f"{qualidade_geral:.1f}%")

# ===============================
# TABELA ANALÍTICA
# ===============================
st.subheader("📋 Análise Mensal")

tabela = df_oee.copy()

st.dataframe(
    tabela[[
        "Mes",
        "Planejadas",
        "Fabricadas",
        "Refugadas",
        "Atingimento (%)",
        "Qualidade (%)",
        "Refugo (%)",
        "Eficiência Industrial (%)"
    ]],
    use_container_width=True
)

# ===============================
# GRÁFICO 1 - PLANEJADO X FABRICADO
# ===============================
st.subheader("📊 Planejado x Fabricado")

fig1 = px.bar(
    df_oee,
    x="Mes",
    y=["Planejadas", "Fabricadas"],
    barmode="group",
    text_auto=".0f",
    title="Planejado x Fabricado por Mês"
)

fig1.update_layout(
    xaxis_title="Mês",
    yaxis_title="Peças"
)

st.plotly_chart(fig1, use_container_width=True)

# ===============================
# GRÁFICO 2 - REFUGO
# ===============================
st.subheader("🧯 Refugo por Mês")

fig2 = px.bar(
    df_oee,
    x="Mes",
    y="Refugadas",
    text_auto=".0f",
    title="Peças Refugadas por Mês"
)

fig2.update_layout(
    xaxis_title="Mês",
    yaxis_title="Peças Refugadas"
)

st.plotly_chart(fig2, use_container_width=True)

# ===============================
# GRÁFICO 3 - EFICIÊNCIA INDUSTRIAL
# ===============================
st.subheader("📈 Eficiência Industrial (%)")

fig3 = px.line(
    df_oee,
    x="Mes",
    y="Eficiência Industrial (%)",
    markers=True,
    text="Eficiência Industrial (%)",
    title="Eficiência Industrial por Mês"
)

fig3.update_traces(textposition="top center")

fig3.update_layout(
    xaxis_title="Mês",
    yaxis_title="Eficiência Industrial (%)"
)

st.plotly_chart(fig3, use_container_width=True)

# ===============================
# GRÁFICO 4 - QUALIDADE X ATINGIMENTO
# ===============================
st.subheader("🎯 Qualidade x Atingimento")

fig4 = px.line(
    df_oee,
    x="Mes",
    y=["Atingimento (%)", "Qualidade (%)"],
    markers=True,
    title="Qualidade x Atingimento"
)

fig4.update_layout(
    xaxis_title="Mês",
    yaxis_title="%"
)

st.plotly_chart(fig4, use_container_width=True)