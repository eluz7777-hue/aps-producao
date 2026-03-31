import streamlit as st
import pandas as pd
import plotly.express as px

# ===============================
# CONFIG DA PÁGINA
# ===============================
st.set_page_config(page_title="APS | OEE & Qualidade", layout="wide")
st.title("APS | OEE & Qualidade")

# ===============================
# FORMATAÇÃO BR
# ===============================
def fmt_br_num(valor, casas=1):
    try:
        valor = float(valor)
        texto = f"{valor:,.{casas}f}"
        texto = texto.replace(",", "X").replace(".", ",").replace("X", ".")
        return texto
    except:
        return "0"

def fmt_br_int(valor):
    try:
        valor = int(round(float(valor), 0))
        return f"{valor:,}".replace(",", ".")
    except:
        return "0"

def fmt_br_pct(valor, casas=1):
    try:
        valor = float(valor)
        texto = f"{valor:,.{casas}f}%"
        texto = texto.replace(",", "X").replace(".", ",").replace("X", ".")
        return texto
    except:
        return "0,0%"

# ===============================
# SEMÁFORO INDUSTRIAL
# ===============================
def semaforo_oee(valor):
    if valor < 60:
        return "🔴 Crítico"
    elif valor < 75:
        return "🟡 Atenção"
    else:
        return "🟢 Bom"

def semaforo_indicador(valor, meta_amarela=75, meta_verde=85):
    if valor < meta_amarela:
        return "🔴"
    elif valor < meta_verde:
        return "🟡"
    else:
        return "🟢"

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
    "PEÇAS REFUGADAS",
    "DISPONIBILIDADE (H)",
    "PARADAS DE MAQUINA (H)",
    "TEMPO OPERANDO (H)"
]

faltantes = [c for c in colunas_esperadas if c not in df_oee.columns]

if faltantes:
    st.error(f"Colunas obrigatórias ausentes na planilha OEE: {faltantes}")
    st.stop()

# ===============================
# LIMPEZA E RENOMEAÇÃO
# ===============================
df_oee = df_oee[colunas_esperadas].copy()

df_oee = df_oee.rename(columns={
    "MÊS": "Mes",
    "PEÇAS PLANEJADAS PARA FABRICAÇÃO": "Planejadas",
    "PEÇAS FABRICADAS (FATURADAS)": "Fabricadas",
    "PEÇAS REFUGADAS": "Refugadas",
    "DISPONIBILIDADE (H)": "Disponibilidade_h",
    "PARADAS DE MAQUINA (H)": "Paradas_h",
    "TEMPO OPERANDO (H)": "Tempo_Operando_h"
})

# Remove linhas totalmente vazias
df_oee = df_oee.dropna(how="all")

# Padroniza mês
df_oee["Mes"] = df_oee["Mes"].astype(str).str.strip().str.upper()
df_oee = df_oee[df_oee["Mes"] != ""].copy()

# ===============================
# TRATAMENTO DE CAMPOS NUMÉRICOS
# ===============================
for col in ["Planejadas", "Fabricadas", "Refugadas", "Disponibilidade_h", "Paradas_h", "Tempo_Operando_h"]:
    df_oee[col] = (
        df_oee[col]
        .astype(str)
        .str.strip()
        .replace("-", "0")
    )

    # Trata apenas vírgula decimal
    df_oee[col] = df_oee[col].str.replace(",", ".", regex=False)

    df_oee[col] = pd.to_numeric(df_oee[col], errors="coerce").fillna(0)

# Considera apenas meses realizados
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
# CÁLCULOS INDUSTRIAIS
# ===============================
df_oee["Total Produzido"] = df_oee["Fabricadas"] + df_oee["Refugadas"]

# Disponibilidade (%)
df_oee["Disponibilidade (%)"] = df_oee.apply(
    lambda r: (r["Tempo_Operando_h"] / r["Disponibilidade_h"] * 100)
    if r["Disponibilidade_h"] > 0 else 0,
    axis=1
)

# Performance (%)
df_oee["Performance (%)"] = df_oee.apply(
    lambda r: (r["Fabricadas"] / r["Planejadas"] * 100)
    if r["Planejadas"] > 0 else 0,
    axis=1
)

# Qualidade (%)
df_oee["Qualidade (%)"] = df_oee.apply(
    lambda r: (r["Fabricadas"] / r["Total Produzido"] * 100)
    if r["Total Produzido"] > 0 else 0,
    axis=1
)

# Refugo (%)
df_oee["Refugo (%)"] = df_oee.apply(
    lambda r: (r["Refugadas"] / r["Total Produzido"] * 100)
    if r["Total Produzido"] > 0 else 0,
    axis=1
)

# OEE (%)
df_oee["OEE (%)"] = (
    (df_oee["Disponibilidade (%)"] / 100) *
    (df_oee["Performance (%)"] / 100) *
    (df_oee["Qualidade (%)"] / 100)
) * 100

# Arredondamento seguro
colunas_percentuais = [
    "Disponibilidade (%)",
    "Performance (%)",
    "Qualidade (%)",
    "Refugo (%)",
    "OEE (%)"
]

for col in colunas_percentuais:
    if col in df_oee.columns:
        df_oee[col] = df_oee[col].round(1)

# ===============================
# KPI GERAL
# ===============================
planejado_total = df_oee["Planejadas"].sum()
fabricado_total = df_oee["Fabricadas"].sum()
refugado_total = df_oee["Refugadas"].sum()
disponibilidade_total = df_oee["Disponibilidade_h"].sum()
paradas_total = df_oee["Paradas_h"].sum()
tempo_operando_total = df_oee["Tempo_Operando_h"].sum()

disponibilidade_geral = round(
    (tempo_operando_total / disponibilidade_total * 100),
    1
) if disponibilidade_total > 0 else 0

performance_geral = round(
    (fabricado_total / planejado_total * 100),
    1
) if planejado_total > 0 else 0

qualidade_geral = round(
    (fabricado_total / (fabricado_total + refugado_total) * 100),
    1
) if (fabricado_total + refugado_total) > 0 else 0

oee_geral = round(
    (disponibilidade_geral / 100) *
    (performance_geral / 100) *
    (qualidade_geral / 100) * 100,
    1
)

# ===============================
# INDICADORES PRINCIPAIS
# ===============================
st.subheader("📌 Indicadores Principais")

k1, k2, k3, k4 = st.columns(4)
k1.metric("Peças Planejadas", fmt_br_int(planejado_total))
k2.metric("Peças Fabricadas", fmt_br_int(fabricado_total))
k3.metric("Peças Refugadas", fmt_br_int(refugado_total))
k4.metric("OEE Geral", fmt_br_pct(oee_geral))

k5, k6, k7, k8 = st.columns(4)
k5.metric("Disponibilidade", fmt_br_pct(disponibilidade_geral))
k6.metric("Performance", fmt_br_pct(performance_geral))
k7.metric("Qualidade", fmt_br_pct(qualidade_geral))
k8.metric("Paradas de Máquina (h)", fmt_br_num(paradas_total, 1))

# ===============================
# SEMÁFORO EXECUTIVO
# ===============================
st.subheader("🚦 Semáforo Industrial")

s1, s2, s3, s4 = st.columns(4)

s1.metric("OEE", semaforo_oee(oee_geral))
s2.metric("Disponibilidade", semaforo_indicador(disponibilidade_geral, 75, 85))
s3.metric("Performance", semaforo_indicador(performance_geral, 75, 90))
s4.metric("Qualidade", semaforo_indicador(qualidade_geral, 95, 98))

# ===============================
# ANÁLISE MENSAL
# ===============================
st.subheader("📋 Análise Mensal")

tabela_exibir = df_oee.copy()

# Coluna de semáforo por mês
tabela_exibir["Status OEE"] = tabela_exibir["OEE (%)"].apply(semaforo_oee)

# Formatação BR
for col in ["Planejadas", "Fabricadas", "Refugadas"]:
    tabela_exibir[col] = tabela_exibir[col].apply(fmt_br_int)

for col in ["Disponibilidade_h", "Paradas_h", "Tempo_Operando_h"]:
    tabela_exibir[col] = tabela_exibir[col].apply(lambda x: fmt_br_num(x, 1))

for col in ["Disponibilidade (%)", "Performance (%)", "Qualidade (%)", "Refugo (%)", "OEE (%)"]:
    tabela_exibir[col] = tabela_exibir[col].apply(fmt_br_pct)

st.dataframe(
    tabela_exibir[[
        "Mes",
        "Status OEE",
        "Planejadas",
        "Fabricadas",
        "Refugadas",
        "Disponibilidade_h",
        "Paradas_h",
        "Tempo_Operando_h",
        "Disponibilidade (%)",
        "Performance (%)",
        "Qualidade (%)",
        "Refugo (%)",
        "OEE (%)"
    ]].rename(columns={
        "Disponibilidade_h": "Disponibilidade (h)",
        "Paradas_h": "Paradas de Máquina (h)",
        "Tempo_Operando_h": "Tempo Operando (h)"
    }),
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
    text_auto=".1f",
    title="Planejado x Fabricado por Mês"
)

fig1.update_layout(
    xaxis_title="Mês",
    yaxis_title="Peças"
)

st.plotly_chart(fig1, use_container_width=True)

# ===============================
# GRÁFICO 2 - OEE POR MÊS
# ===============================
st.subheader("📈 OEE por Mês")

df_oee_plot = df_oee.copy()
df_oee_plot["OEE_label"] = df_oee_plot["OEE (%)"].apply(fmt_br_pct)

fig2 = px.line(
    df_oee_plot,
    x="Mes",
    y="OEE (%)",
    markers=True,
    text="OEE_label",
    title="OEE por Mês"
)

fig2.update_traces(textposition="top center")

fig2.update_layout(
    xaxis_title="Mês",
    yaxis_title="OEE (%)"
)

st.plotly_chart(fig2, use_container_width=True)

# ===============================
# GRÁFICO 3 - D / P / Q
# ===============================
st.subheader("🎯 Disponibilidade x Performance x Qualidade")

df_dpq = df_oee.copy()
df_dpq["Disp_label"] = df_dpq["Disponibilidade (%)"].apply(fmt_br_pct)
df_dpq["Perf_label"] = df_dpq["Performance (%)"].apply(fmt_br_pct)
df_dpq["Qual_label"] = df_dpq["Qualidade (%)"].apply(fmt_br_pct)

fig3 = px.line(
    df_dpq,
    x="Mes",
    y=["Disponibilidade (%)", "Performance (%)", "Qualidade (%)"],
    markers=True,
    title="Disponibilidade x Performance x Qualidade"
)

fig3.update_layout(
    xaxis_title="Mês",
    yaxis_title="%"
)

st.plotly_chart(fig3, use_container_width=True)

# ===============================
# GRÁFICO 4 - REFUGO
# ===============================
st.subheader("🧯 Refugo por Mês")

fig4 = px.bar(
    df_oee,
    x="Mes",
    y="Refugadas",
    text_auto=".1f",
    title="Peças Refugadas por Mês"
)

fig4.update_layout(
    xaxis_title="Mês",
    yaxis_title="Peças Refugadas"
)

st.plotly_chart(fig4, use_container_width=True)