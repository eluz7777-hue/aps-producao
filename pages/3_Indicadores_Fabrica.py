import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Indicadores da Fábrica", layout="wide")

st.title("📊 Indicadores da Fábrica")
st.caption("Visão estratégica consolidada da operação industrial.")

# ============================================================
# 🔒 CARREGAMENTO BASE (REAPROVEITA APS)
# ============================================================
try:
    df = st.session_state.get("df", pd.DataFrame())
    df_operacional = st.session_state.get("df_operacional", pd.DataFrame())
except:
    df = pd.DataFrame()
    df_operacional = pd.DataFrame()

if df.empty:
    st.warning("Base do APS não carregada.")
    st.stop()

# ============================================================
# 📌 KPI PRINCIPAIS (CORRIGIDO)
# ============================================================

st.subheader("📌 Indicadores Principais")

df["Horas"] = pd.to_numeric(df.get("Horas", 0), errors="coerce").fillna(0)

carga_total = df["Horas"].sum()
total_pvs = df["PV"].nunique() if "PV" in df.columns else 0

# 🔒 GARGALO
if "Processo" in df.columns:
    processos = df.groupby("Processo")["Horas"].sum()
    gargalo = processos.idxmax() if not processos.empty else "N/D"
else:
    processos = pd.Series()
    gargalo = "N/D"

# 🔒 ATRASO (CORREÇÃO AQUI)
if "Dias para Entrega" in df.columns:
    atrasos = df[df["Dias para Entrega"] < 0]
    pct_atraso = (len(atrasos) / total_pvs * 100) if total_pvs > 0 else 0
else:
    atrasos = pd.DataFrame()
    pct_atraso = 0

k1, k2, k3, k4 = st.columns(4)

k1.metric("🏭 Carga Total (h)", f"{carga_total:,.1f}")
k2.metric("📦 PVs", total_pvs)
k3.metric("🚨 % em Atraso", f"{pct_atraso:.1f}%")
k4.metric("🔥 Gargalo Atual", gargalo)


# ============================================================
# 🧠 STATUS EXECUTIVO
# ============================================================
st.subheader("🚦 Status Executivo")

if "Dias para Entrega" in df.columns:
    atraso = (df["Dias para Entrega"] < 0).sum()
    risco = df["Dias para Entrega"].between(0, 3).sum()
    ok = (df["Dias para Entrega"] > 3).sum()
else:
    atraso = risco = ok = 0

s1, s2, s3 = st.columns(3)

s1.metric("🔴 Atrasados", int(atraso))
s2.metric("🟡 Risco", int(risco))
s3.metric("🟢 OK", int(ok))

# ============================================================
# 📊 BACKLOG POR PROCESSO
# ============================================================
st.subheader("📊 Backlog por Processo")

backlog = df.groupby("Processo", as_index=False)["Horas"].sum()
backlog = backlog.sort_values("Horas", ascending=False)

st.bar_chart(backlog.set_index("Processo"))

# ============================================================
# 📈 TENDÊNCIA (SIMPLES)
# ============================================================
st.subheader("📈 Tendência de Carga")

if "Data" in df.columns:
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
    tendencia = df.groupby("Data")["Horas"].sum()

    st.line_chart(tendencia)

# ============================================================
# ⚠️ ALERTAS INTELIGENTES
# ============================================================
st.subheader("⚠️ Alertas Inteligentes")

if pct_atraso > 20:
    st.error("🚨 Alto volume de atrasos detectado.")

if not processos.empty and processos.max() > processos.mean() * 2:
    st.warning(f"⚠️ Gargalo forte detectado em {gargalo}")

if carga_total == 0:
    st.info("Nenhuma carga registrada.")