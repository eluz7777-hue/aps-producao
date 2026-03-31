import streamlit as st

# ===============================
# 🔐 BLOQUEIO DE ACESSO GLOBAL
# ===============================
if "logado" not in st.session_state or not st.session_state.logado:
    st.warning("🔒 Acesso não autorizado. Redirecionando para login...")
    st.switch_page("app.py")

import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import os
import time
import holidays
import math

st.set_page_config(layout="wide")

# ===============================
# LOGO + TÍTULO
# ===============================
col1, col2 = st.columns([1, 6])

with col1:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=80)

with col2:
    st.title("APS | Carga & Capacidade")

# ===============================
# CONFIG
# ===============================
import holidays

EFICIENCIA = 0.80

# Jornada real da fábrica
HORAS_SEG_A_QUI = 9  # 07h às 17h com 1h almoço
HORAS_SEXTA = 8      # 07h às 16h com 1h almoço
HORAS_DIA_UTIL_MEDIA = ((HORAS_SEG_A_QUI * 4) + HORAS_SEXTA) / 5

# Calendário de feriados Brasil
FERIADOS_BR = holidays.Brazil()

# Recursos / máquinas por processo
MAQUINAS = {
    "CORTE - SERRA": 2,          # Serra Fita + Serra Circular
    "CORTE-PLASMA": 1,
    "CORTE-LASER": 1,
    "CORTE-GUILHOTINA": 0,
    "TORNO CONVENCIONAL": 2,
    "TORNO CNC": 0,
    "CENTRO DE USINAGEM": 1,
    "FRESADORAS": 2,
    "PRENSA (AMASSAMENTO)": 1,
    "CALANDRA": 2,
    "DOBRADEIRA": 2,
    "ROSQUEADEIRA": 1,
    "METALEIRA": 1,
    "FURADEIRA DE BANCADA": 1,
    "SOLDAGEM": 4,
    "ACABAMENTO": 4,
    "JATEAMENTO": 1,
    "PINTURA": 1,
    "MONTAGEM": 1,
    "DIVERSOS": 0
}

def capacidade_mes_por_processo(ano, mes, processo):
    recursos = MAQUINAS.get(processo, 0)
    if recursos <= 0:
        return 0
    return horas_uteis_mes(ano, mes) * recursos * EFICIENCIA

# ===============================
# FERIADOS
# ===============================
br_holidays = holidays.Brazil()

def dias_uteis_periodo(inicio, fim):
    """
    Conta apenas os dias úteis reais entre duas datas
    (segunda a sexta, excluindo feriados nacionais).
    """
    if pd.isna(inicio) or pd.isna(fim):
        return 0

    inicio = pd.Timestamp(inicio).normalize()
    fim = pd.Timestamp(fim).normalize()

    if fim < inicio:
        return 0

    dias = pd.date_range(inicio, fim, freq="D")
    return sum(1 for d in dias if d.weekday() < 5 and d.date() not in br_holidays)

def horas_uteis_periodo(inicio, fim):
    """
    Calcula as horas úteis reais entre duas datas considerando:
    - Seg a Qui = 9h
    - Sexta = 8h
    - exclui sábados, domingos e feriados
    """
    if pd.isna(inicio) or pd.isna(fim):
        return 0

    inicio = pd.Timestamp(inicio).normalize()
    fim = pd.Timestamp(fim).normalize()

    if fim < inicio:
        return 0

    dias = pd.date_range(inicio, fim, freq="D")
    total_horas = 0

    for d in dias:
        if d.weekday() < 5 and d.date() not in br_holidays:
            if d.weekday() == 4:  # sexta
                total_horas += HORAS_SEXTA
            else:  # segunda a quinta
                total_horas += HORAS_SEG_A_QUI

    return total_horas

def dias_uteis_mes(ano, mes):
    inicio = pd.Timestamp(year=int(ano), month=int(mes), day=1)
    fim = inicio + pd.offsets.MonthEnd(1)
    return dias_uteis_periodo(inicio, fim)

def horas_uteis_mes(ano, mes):
    inicio = pd.Timestamp(year=int(ano), month=int(mes), day=1)
    fim = inicio + pd.offsets.MonthEnd(1)
    return horas_uteis_periodo(inicio, fim)

def horas_uteis_semana(inicio, fim):
    """
    Calcula as horas úteis reais da semana/período considerando:
    - Seg a Qui = 9h
    - Sexta = 8h
    - exclui sábados, domingos e feriados
    """
    if pd.isna(inicio) or pd.isna(fim):
        return 0

    inicio = pd.Timestamp(inicio).normalize()
    fim = pd.Timestamp(fim).normalize()

    if fim < inicio:
        return 0

    dias = pd.date_range(inicio, fim, freq="D")
    total_horas = 0

    for d in dias:
        if d.weekday() < 5 and d.date() not in br_holidays:
            if d.weekday() == 4:  # sexta
                total_horas += HORAS_SEXTA
            else:  # segunda a quinta
                total_horas += HORAS_SEG_A_QUI

    return total_horas

def capacidade_semana_por_processo(inicio, fim, processo):
    recursos = MAQUINAS.get(processo, 0)
    if recursos <= 0:
        return 0
    return horas_uteis_semana(inicio, fim) * recursos * EFICIENCIA

# ===============================
# CACHE DE LEITURA
# ===============================
@st.cache_data
def carregar_dados(base_path):
    df = pd.read_excel(os.path.join(base_path, "PV.xlsx"))
    return df

# ===============================
# ATUALIZAÇÃO
# ===============================
if st.button("🔄 Atualizar Dados"):
    st.cache_data.clear()
    st.rerun()

st.write("Última atualização:", time.strftime("%d/%m/%Y %H:%M:%S"))

# ===============================
# LEITURA
# ===============================
BASE_PATH = os.getcwd()

df_pv = carregar_dados(BASE_PATH)

# Normaliza cabeçalhos
df_pv.columns = [c.strip().upper() for c in df_pv.columns]

# Padroniza nomes da planilha única
df_pv = df_pv.rename(columns={
    "CÓDIGO": "CODIGO_PV",
    "CODIGO": "CODIGO_PV",
    "DATA DE ENTREGA": "ENTREGA",
    "QUANTIDADE": "QTD",
    "QTD": "QTD",
    "QTDE": "QTD",
    "QTD.": "QTD"
})

# ===============================
# VALIDAÇÃO DE COLUNAS OBRIGATÓRIAS
# ===============================
colunas_obrigatorias = ["PV", "CLIENTE", "CODIGO_PV", "ENTREGA", "QTD"]
faltantes = [c for c in colunas_obrigatorias if c not in df_pv.columns]

if faltantes:
    st.error(f"A planilha PV.xlsx está faltando as colunas obrigatórias: {', '.join(faltantes)}")
    st.stop()

def normalizar_codigo(x):
    if pd.isna(x):
        return ""
    x = str(x)
    x = x.replace("\xa0", "")
    x = x.replace(" ", "")
    x = x.replace(".0", "")
    x = x.strip()
    return x

# ===============================
# NORMALIZAÇÃO SEGURA
# ===============================
df_pv["CODIGO_PV"] = df_pv["CODIGO_PV"].apply(normalizar_codigo)

# Chave única
df_pv["CODIGO_KEY"] = df_pv["CODIGO_PV"].astype(str).str.strip()

# Campos principais
df_pv["CLIENTE"] = df_pv["CLIENTE"].fillna("SEM CLIENTE")
df_pv["PV"] = df_pv["PV"].astype(str).str.strip()

# 🔥 CORREÇÃO CRÍTICA: leitura correta de data brasileira
df_pv["ENTREGA"] = pd.to_datetime(df_pv["ENTREGA"], errors="coerce", dayfirst=True)

# Quantidade e tempos aceitam decimal
df_pv["QTD"] = pd.to_numeric(df_pv["QTD"], errors="coerce").fillna(0)

# Remove duplicidades exatas
df_pv = df_pv.drop_duplicates().copy()

# Remove apenas linhas sem código
df_pv = df_pv[df_pv["CODIGO_KEY"] != ""].copy()

# ===============================
# PROCESSOS
# ===============================
PROCESSOS_VALIDOS = [
    "CORTE - SERRA",
    "CORTE-PLASMA",
    "CORTE-LASER",
    "CORTE-GUILHOTINA",
    "TORNO CONVENCIONAL",
    "TORNO CNC",
    "CENTRO DE USINAGEM",
    "FRESADORAS",
    "PRENSA (AMASSAMENTO)",
    "CALANDRA",
    "DOBRADEIRA",
    "ROSQUEADEIRA",
    "METALEIRA",
    "FURADEIRA DE BANCADA",
    "SOLDAGEM",
    "ACABAMENTO",
    "JATEAMENTO",
    "PINTURA",
    "MONTAGEM",
    "DIVERSOS"
]

processos = [p for p in PROCESSOS_VALIDOS if p in df_pv.columns]

# Converte todos os tempos para número (aceita decimal)
for proc in processos:
    df_pv[proc] = (
        df_pv[proc]
        .astype(str)
        .str.replace(",", ".", regex=False)
        .str.strip()
    )
    df_pv[proc] = pd.to_numeric(df_pv[proc], errors="coerce").fillna(0)


# ===============================
# EXPANSÃO CORRIGIDA (SEM ERRO)
# ===============================
pvs_totais_excel = df_pv["PV"].astype(str).str.strip().nunique()
pvs_excel_set = set(df_pv["PV"].astype(str).str.strip().unique())

linhas = []
pvs_excluidas = []
pvs_sem_carga = []
auditoria_pv = []

for _, row in df_pv.iterrows():

    pv_atual = str(row["PV"]).strip()
    cliente_atual = row.get("CLIENTE", "SEM CLIENTE")
    codigo_atual = row["CODIGO_PV"]

    status_pv = "OK"
    qtde_processos_validos = 0
    horas_totais_pv = 0
    motivos_pv = []

    # -------------------------------
    # Validações básicas
    # -------------------------------
    data_valida = not pd.isna(row["ENTREGA"])
    qtd_valida = pd.notna(row["QTD"]) and float(row["QTD"]) > 0

    if not data_valida:
        motivos_pv.append("Data de entrega inválida")

    if not qtd_valida:
        motivos_pv.append("Quantidade zero ou inválida")

    # Se data ou quantidade estiverem inválidas, não tenta expandir processo
    if not data_valida or not qtd_valida:
        status_pv = "Inconsistente"

        registro = {
            "PV": pv_atual,
            "Cliente": cliente_atual,
            "CODIGO": codigo_atual,
            "Motivo": " | ".join(motivos_pv)
        }

        pvs_excluidas.append(registro)
        pvs_sem_carga.append(registro)

        auditoria_pv.append({
            "PV": pv_atual,
            "Cliente": cliente_atual,
            "CODIGO": codigo_atual,
            "Status": status_pv,
            "Qtd": row["QTD"],
            "Total Processos Válidos": 0,
            "Horas Totais": 0,
            "Motivo": " | ".join(motivos_pv)
        })
        continue

    # -------------------------------
    # Expansão dos processos válidos
    # -------------------------------
    for proc in processos:
        tempo = pd.to_numeric(row.get(proc), errors="coerce")

        if pd.notna(tempo) and tempo > 0 and tempo <= 2500:
            qtde_processos_validos += 1

            horas = (tempo * float(row["QTD"])) / 60
            horas_totais_pv += horas

            linhas.append({
                "PV": pv_atual,
                "Cliente": cliente_atual,
                "Processo": proc,
                "Data": row["ENTREGA"],
                "Horas": horas
            })

    # -------------------------------
    # Se não teve nenhum processo válido
    # -------------------------------
    if qtde_processos_validos == 0:
        status_pv = "Sem processo válido"

        registro = {
            "PV": pv_atual,
            "Cliente": cliente_atual,
            "CODIGO": codigo_atual,
            "Motivo": "Nenhum processo com tempo > 0 e <= 2500"
        }

        pvs_excluidas.append(registro)
        pvs_sem_carga.append(registro)

        auditoria_pv.append({
            "PV": pv_atual,
            "Cliente": cliente_atual,
            "CODIGO": codigo_atual,
            "Status": status_pv,
            "Qtd": row["QTD"],
            "Total Processos Válidos": 0,
            "Horas Totais": 0,
            "Motivo": "Nenhum processo com tempo > 0 e <= 2500"
        })
    else:
        auditoria_pv.append({
            "PV": pv_atual,
            "Cliente": cliente_atual,
            "CODIGO": codigo_atual,
            "Status": status_pv,
            "Qtd": row["QTD"],
            "Total Processos Válidos": qtde_processos_validos,
            "Horas Totais": horas_totais_pv,
            "Motivo": ""
        })

# Base principal de carga
df = pd.DataFrame(linhas)

# DataFrames auxiliares
df_excluidas = pd.DataFrame(pvs_excluidas)
df_sem_carga = pd.DataFrame(pvs_sem_carga)
df_auditoria_pv = pd.DataFrame(auditoria_pv)

# -------------------------------
# Garantia de rastreabilidade
# -------------------------------
pvs_auditadas_set = set(df_auditoria_pv["PV"].astype(str).str.strip().unique()) if not df_auditoria_pv.empty else set()
pvs_nao_auditadas = pvs_excel_set - pvs_auditadas_set

for pv_faltante in pvs_nao_auditadas:
    linha_pv = df_pv[df_pv["PV"].astype(str).str.strip() == pv_faltante]

    if not linha_pv.empty:
        row = linha_pv.iloc[0]

        registro = {
            "PV": str(row["PV"]).strip(),
            "Cliente": row.get("CLIENTE", "SEM CLIENTE"),
            "CODIGO": row["CODIGO_PV"],
            "Motivo": "PV não auditada por falha de processamento"
        }

        pvs_excluidas.append(registro)
        pvs_sem_carga.append(registro)

        auditoria_pv.append({
            "PV": str(row["PV"]).strip(),
            "Cliente": row.get("CLIENTE", "SEM CLIENTE"),
            "CODIGO": row["CODIGO_PV"],
            "Status": "Falha de processamento",
            "Qtd": row["QTD"],
            "Total Processos Válidos": 0,
            "Horas Totais": 0,
            "Motivo": "PV não auditada por falha de processamento"
        })

# Recria os dataframes finais após blindagem
df_excluidas = pd.DataFrame(pvs_excluidas)
df_sem_carga = pd.DataFrame(pvs_sem_carga)
df_auditoria_pv = pd.DataFrame(auditoria_pv)

if df.empty:
    st.warning("Nenhum dado válido foi encontrado para exibir no dashboard.")
    st.stop()    
# ===============================
# FILTRO POR CLIENTE
# ===============================
df_excluidas = pd.DataFrame(pvs_excluidas)
df["Cliente"] = df["Cliente"].fillna("SEM CLIENTE").astype(str).str.strip()

clientes_disponiveis = sorted(df["Cliente"].dropna().unique().tolist())
cliente_sel = st.selectbox("Filtrar Cliente", ["Todos"] + clientes_disponiveis)

if cliente_sel != "Todos":
    df = df[df["Cliente"] == cliente_sel].copy()
    df_excluidas = df_excluidas[df_excluidas["Cliente"] == cliente_sel].copy() if not df_excluidas.empty else df_excluidas
    df_sem_carga = df_sem_carga[df_sem_carga["Cliente"] == cliente_sel].copy() if not df_sem_carga.empty else df_sem_carga
    df_auditoria_pv = df_auditoria_pv[df_auditoria_pv["Cliente"] == cliente_sel].copy() if not df_auditoria_pv.empty else df_auditoria_pv

if df.empty:
    st.warning("Nenhum dado encontrado para o filtro selecionado.")
    st.stop()

# ===============================
# DATAS
# ===============================
df["Semana"] = df["Data"].dt.isocalendar().week.astype(int)
df["Ano"] = df["Data"].dt.year
df["Mes"] = df["Data"].dt.month
mes_ref = int(df["Mes"].mode()[0])
ano_ref = int(df["Ano"].mode()[0])

horas_mes = horas_uteis_mes(ano_ref, mes_ref)
total_recursos = sum(MAQUINAS.values())

# ===============================
# FILA REAL POR PROCESSO
# ===============================
df = df.sort_values(by=["Processo", "Data", "PV"]).reset_index(drop=True)
df["Fila Acumulada (h)"] = df.groupby("Processo")["Horas"].cumsum()

def capacidade_diaria_real(processo):
    """
    Capacidade média diária operacional por processo.
    Usada para estimativa contínua de fila.
    """
    recursos = MAQUINAS.get(processo, 0)
    if recursos <= 0:
        return 0
    return HORAS_DIA_UTIL_MEDIA * recursos * EFICIENCIA

df["Capacidade Diária Real (h)"] = df["Processo"].apply(capacidade_diaria_real)

df["Fila (dias)"] = np.where(
    df["Capacidade Diária Real (h)"] > 0,
    df["Fila Acumulada (h)"] / df["Capacidade Diária Real (h)"],
    0
)

# ===============================
# CALENDÁRIO
# ===============================
cal = df[["Data", "Semana", "Ano"]].drop_duplicates().copy()

cal["Inicio"] = cal["Data"] - pd.to_timedelta(cal["Data"].dt.weekday, unit="d")
cal["Fim"] = cal["Inicio"] + pd.Timedelta(days=6)

cal = cal.groupby(["Semana", "Ano"]).agg({
    "Inicio": "min",
    "Fim": "max"
}).reset_index()

cal["Dias Úteis"] = cal.apply(
    lambda x: dias_uteis_periodo(x["Inicio"], x["Fim"]), axis=1
)

# ===============================
# VISÃO
# ===============================
tipo = st.radio("Visualização", ["Semanal", "Mensal"], horizontal=True)

# Garantia de colunas de data corretas
df["Ano"] = df["Data"].dt.year
df["Mes"] = df["Data"].dt.month
df["Semana"] = df["Data"].dt.isocalendar().week.astype(int)

if tipo == "Semanal":
    df["Periodo"] = "Sem " + df["Semana"].astype(str)

    dem = df.groupby(["Periodo", "Processo", "Semana", "Ano"], as_index=False)["Horas"].sum()
    dem = dem.merge(cal, on=["Semana", "Ano"], how="left")

    # Capacidade semanal real = dias úteis da semana × jornada real × recursos × eficiência
    dem["Capacidade"] = dem.apply(
    lambda r: capacidade_semana_por_processo(r["Inicio"], r["Fim"], r["Processo"]),
    axis=1
)

else:
    df["Periodo"] = "Mês " + df["Mes"].astype(str)

    dem = df.groupby(["Periodo", "Processo", "Mes", "Ano"], as_index=False)["Horas"].sum()

    dem["Capacidade"] = dem.apply(
        lambda r: capacidade_mes_por_processo(r["Ano"], r["Mes"], r["Processo"]),
        axis=1
    )

# Evita divisão por zero
dem["Capacidade"] = dem["Capacidade"].fillna(0)
dem["Ocupacao"] = np.where(
    dem["Capacidade"] > 0,
    (dem["Horas"] / dem["Capacidade"]) * 100,
    0
)

dem["Ocupacao"] = dem["Ocupacao"].replace([np.inf, -np.inf], 0).fillna(0)

# Remove processos sem capacidade produtiva da visão de ocupação
dem = dem[dem["Capacidade"] > 0].copy()

# Remove linhas zeradas para não poluir gráfico
dem = dem[(dem["Horas"] > 0) | (dem["Ocupacao"] > 0)].copy()

# Ordenação correta do eixo
if tipo == "Mensal":
    dem["Ordem_Periodo"] = dem["Mes"]
else:
    dem["Ordem_Periodo"] = dem["Semana"]

dem = dem.sort_values(["Ordem_Periodo", "Processo"]).copy()

# Rótulos com 1 casa decimal
dem["Horas_Label"] = dem["Horas"].round(1).astype(str) + "h"
dem["Ocupacao_Label"] = dem["Ocupacao"].round(1).astype(str) + "%"

# ===============================
# AGRUPAMENTO POR PROCESSO
# ===============================
dem_proc = df.groupby(["Processo"])["Horas"].sum().reset_index()

# ===============================
# MÉTRICAS
# ===============================
# Padronização técnica da ocupação
dem["Ocupacao"] = dem["Ocupacao"].replace([float("inf"), -float("inf")], 0)
dem["Ocupacao"] = dem["Ocupacao"].fillna(0)
dem["Ocupacao"] = dem["Ocupacao"].round(1)

def status(x):
    if x > 100:
        return "🔴"
    elif x > 80:
        return "🟡"
    else:
        return "🟢"

dem["Status"] = dem["Ocupacao"].apply(status)
dem["Saldo (h)"] = (dem["Capacidade"] - dem["Horas"]).round(1)

# Coluna apenas para exibição visual
dem["Ocupação (%)"] = dem["Ocupacao"].round(1)

# ===============================
# CAPACIDADE POR PROCESSO
# ===============================
if tipo == "Mensal":
    capacidade_proc = {
        proc: horas_uteis_mes(ano_ref, mes_ref) * MAQUINAS.get(proc, 0) * EFICIENCIA
        for proc in processos
    }
    dem_proc["Capacidade Processo"] = dem_proc["Processo"].map(capacidade_proc)

else:
    capacidade_proc = (
        dem.groupby("Processo", as_index=False)["Capacidade"]
        .sum()
        .rename(columns={"Capacidade": "Capacidade Processo"})
    )
    dem_proc = dem_proc.merge(capacidade_proc, on="Processo", how="left")

dem_proc["Capacidade Processo"] = dem_proc["Capacidade Processo"].fillna(0)

dem_proc["Utilização (%)"] = np.where(
    dem_proc["Capacidade Processo"] > 0,
    (dem_proc["Horas"] / dem_proc["Capacidade Processo"]) * 100,
    0
)

dem_proc["Utilização (%)"] = dem_proc["Utilização (%)"].replace([float("inf"), -float("inf")], 0)
dem_proc["Utilização (%)"] = dem_proc["Utilização (%)"].fillna(0)
dem_proc["Utilização (%)"] = dem_proc["Utilização (%)"].round(0).astype(int)

def faixa_utilizacao(x):
    if x > 100:
        return "Crítico"
    elif x > 80:
        return "Atenção"
    else:
        return "OK"

dem_proc["Faixa"] = dem_proc["Utilização (%)"].apply(faixa_utilizacao)

# ===============================
# ATRASO
# ===============================
pv_carga = df.groupby(["PV", "Cliente", "Data"], as_index=False)["Horas"].sum()

# Capacidade média diária real da fábrica (global)
recursos_ativos = sum(v for v in MAQUINAS.values() if v > 0)

capacidade_media_diaria_global = (
    HORAS_DIA_UTIL_MEDIA * recursos_ativos * EFICIENCIA
)

pv_carga["Dias Necessários"] = np.where(
    capacidade_media_diaria_global > 0,
    pv_carga["Horas"] / capacidade_media_diaria_global,
    0
)

hoje = pd.Timestamp.today().normalize()

pv_carga["Horas Disponíveis"] = pv_carga["Data"].apply(
    lambda x: horas_uteis_periodo(hoje, x) * EFICIENCIA
)

pv_carga["Dias Disponíveis"] = np.where(
    capacidade_media_diaria_global > 0,
    pv_carga["Horas Disponíveis"] / capacidade_media_diaria_global,
    0
)

pv_carga["Atraso (dias)"] = (
    pv_carga["Dias Necessários"] - pv_carga["Dias Disponíveis"]
).apply(lambda x: max(0, math.ceil(x)))

# ===============================
# PIZZA / ATRASOS
# ===============================
# PVs reais no APS = todas as PVs auditadas (não apenas as com carga expandida)
pvs_no_aps = df_auditoria_pv["PV"].astype(str).str.strip().nunique()

# PVs em atraso
atrasos = pv_carga[pv_carga["Atraso (dias)"] > 0].copy()

# Critério de risco: sem atraso, mas com pouca folga
if "Dias Disponíveis" in pv_carga.columns:
    risco = pv_carga[
        (pv_carga["Atraso (dias)"] == 0) &
        (pv_carga["Dias Disponíveis"] <= 3)
    ].copy()
else:
    risco = pd.DataFrame(columns=pv_carga.columns)

# ===============================
# RISCO
# ===============================
risco = pv_carga[
    (pv_carga["Atraso (dias)"] == 0) &
    (pv_carga["Dias Necessários"] > pv_carga["Dias Disponíveis"] * 0.8)
].copy()

# ===============================
# KPIs / VISÃO EXECUTIVA
# ===============================
st.subheader("📌 Indicadores Principais")

# -------------------------------
# CARGA TOTAL = demanda real
# -------------------------------
carga_total = round(df["Horas"].sum(), 1)

# -------------------------------
# CAPACIDADE GLOBAL DA FÁBRICA
# -------------------------------
recursos_ativos = sum(v for v in MAQUINAS.values() if v > 0)

# Usa o mês mais frequente da base como referência executiva
mes_ref = int(df["Mes"].mode()[0])
ano_ref = int(df["Ano"].mode()[0])

horas_mes_ref = horas_uteis_mes(ano_ref, mes_ref)

capacidade_total = round(
    recursos_ativos * horas_mes_ref * EFICIENCIA,
    1
)

# -------------------------------
# UTILIZAÇÃO GLOBAL
# -------------------------------
utilizacao_total = round((carga_total / capacidade_total) * 100, 1) if capacidade_total > 0 else 0

# -------------------------------
# EXIBIÇÃO DOS KPIs
# -------------------------------
k1, k2, k3 = st.columns(3)

k1.metric("Carga Total (h)", f"{carga_total:,.1f}")
k2.metric("Capacidade Mensal (h)", f"{capacidade_total:,.1f}")
k3.metric("Utilização (%)", f"{utilizacao_total:.1f}%")

# ===============================
# RESUMO
# ===============================
st.subheader("📊 Resumo Geral")

# Garantia de PVs no APS = universo auditado
pvs_no_aps = df_auditoria_pv["PV"].astype(str).str.strip().nunique()

# Atrasos
atrasos = pv_carga[pv_carga["Atraso (dias)"] > 0].copy()

# Risco = sem atraso, mas com pouca folga
if "Dias Disponíveis" in pv_carga.columns:
    risco = pv_carga[
        (pv_carga["Atraso (dias)"] == 0) &
        (pv_carga["Dias Disponíveis"] <= 3)
    ].copy()
else:
    risco = pd.DataFrame(columns=pv_carga.columns)

ok = max(0, pvs_no_aps - len(atrasos) - len(risco))

col1, col2, col3 = st.columns(3)

col1.metric("🔴 Atraso", len(atrasos))
col2.metric("🟡 Risco", len(risco))
col3.metric("🟢 OK", ok)

c4, c5 = st.columns(2)

c4.metric("PVs no Excel", pvs_totais_excel)
c5.metric("PVs no APS", pvs_no_aps)

# ===============================
# ALERTA DE CAPACIDADE CRÍTICA
# ===============================
st.subheader("⚠️ Capacidade Crítica")

critico = dem[dem["Ocupacao"] > 95].copy()

if not critico.empty:
    st.error("Capacidade próxima ou acima do limite detectada.")
    st.dataframe(
        critico.sort_values(["Ocupacao", "Horas"], ascending=[False, False]).reset_index(drop=True)
    )
else:
    st.success("Capacidade sob controle.")

# ===============================
# GRÁFICO OCUPAÇÃO
# ===============================
st.subheader("📌 Ocupação por Processo (%)")

dem["Label"] = dem["Ocupacao"].map(lambda x: f"{x:.1f}%")

fig = px.bar(
    dem.sort_values(["Ordem_Periodo", "Processo"]),
    x="Periodo",
    y="Ocupacao",
    color="Processo",
    barmode="group",
    text="Label"
)

fig.add_hline(y=100, line_dash="dash")

fig.update_traces(textposition="outside", cliponaxis=False)

fig.update_layout(
    yaxis_title="Ocupação (%)",
    xaxis_title="Período",
    uniformtext_minsize=8,
    uniformtext_mode="hide"
)

st.plotly_chart(fig, use_container_width=True)
# ===============================
# VISÃO CAPACIDADE POR PROCESSO
# ===============================
st.subheader("📊 Utilização por Processo (%)")

fig_proc = px.bar(
    dem_proc.sort_values("Utilização (%)", ascending=False),
    x="Processo",
    y="Utilização (%)",
    text="Utilização (%)",
    color="Faixa",
    color_discrete_map={
        "OK": "green",
        "Atenção": "gold",
        "Crítico": "red"
    }
)

fig_proc.add_hline(y=100, line_dash="dash")
fig_proc.update_traces(texttemplate="%{text}")
fig_proc.update_yaxes(title="Utilização (%)")

st.plotly_chart(fig_proc, use_container_width=True)
st.subheader("🥧 Distribuição de Status dos Processos")

status_proc = dem_proc.groupby("Faixa", as_index=False)["Processo"].count()
status_proc = status_proc.rename(columns={"Processo": "Quantidade"})

fig_status = px.pie(
    status_proc,
    names="Faixa",
    values="Quantidade",
    color="Faixa",
    color_discrete_map={
        "OK": "green",
        "Atenção": "gold",
        "Crítico": "red"
    },
    title="Status dos Processos"
)

st.plotly_chart(fig_status, use_container_width=True)

# ===============================
# CURVA DE CARGA
# ===============================
st.subheader("📈 Evolução da Carga")

carga = df.groupby("Data", as_index=False)["Horas"].sum().sort_values("Data")
carga["Carga Acumulada (h)"] = carga["Horas"].cumsum()

fig_carga = px.line(
    carga,
    x="Data",
    y="Carga Acumulada (h)",
    title="Carga Acumulada no Tempo",
    markers=True
)

st.plotly_chart(fig_carga, use_container_width=True)

# ===============================
# PV CLIENTE
# ===============================
st.subheader("📌 PV por Cliente")

pv_cliente = df.groupby("Cliente", as_index=False)["PV"].nunique()
total = pv_cliente["PV"].sum()

pv_cliente = pd.concat(
    [pv_cliente, pd.DataFrame([{"Cliente": "TOTAL", "PV": total}])],
    ignore_index=True
)

fig_cliente = px.bar(pv_cliente, x="Cliente", y="PV", text="PV")
fig_cliente.update_traces(textposition="outside")

st.plotly_chart(fig_cliente, use_container_width=True)

# ===============================
# PIZZA
# ===============================
st.subheader("🥧 Distribuição de Atraso")

if not atrasos.empty:
    dist = atrasos.groupby("Atraso (dias)", as_index=False)["PV"].count()

    fig_pizza = px.pie(dist, names="Atraso (dias)", values="PV")
    st.plotly_chart(fig_pizza, use_container_width=True)

    atraso_select = st.selectbox(
        "Selecionar atraso",
        sorted(atrasos["Atraso (dias)"].unique())
    )

    detalhe = atrasos[atrasos["Atraso (dias)"] == atraso_select].copy()
    detalhe["Horas"] = detalhe["Horas"].round(1)
    detalhe["Dias Necessários"] = detalhe["Dias Necessários"].round(1)

    st.subheader("📋 Detalhamento")
    st.dataframe(detalhe)

else:
    st.success("Nenhum atraso 🎉")

# ============================================================
# ===================== ANÁLISE OPERACIONAL ==================
# ============================================================
st.markdown("## 🏭 Análise Operacional")

# ===============================
# GARGALO AUTOMÁTICO
# ===============================
st.subheader("🔥 Gargalos do Período")

gargalos = dem.sort_values(
    by=["Periodo", "Ocupacao", "Horas"],
    ascending=[True, False, False]
).copy()

top_gargalos = gargalos.groupby("Periodo").head(3).reset_index(drop=True)
top_gargalos["Semáforo"] = top_gargalos["Ocupacao"].apply(status)
top_gargalos["Ocupação (%)"] = top_gargalos["Ocupacao"].round(1)

st.dataframe(
    top_gargalos[["Periodo", "Semáforo", "Processo", "Horas", "Capacidade", "Ocupação (%)", "Saldo (h)"]]
)

st.subheader("🏭 Carga Real x Capacidade por Processo (h)")

fig_cap_proc = px.bar(
    dem_proc.sort_values("Capacidade Processo", ascending=False),
    x="Processo",
    y=["Horas", "Capacidade Processo"],
    barmode="group",
    text_auto=".1f",
    title="Carga Real x Capacidade por Processo (h)"
)

fig_cap_proc.update_layout(
    yaxis_title="Horas",
    xaxis_title="Processo"
)

st.plotly_chart(fig_cap_proc, use_container_width=True, key="grafico_capacidade_carga_processo")

# ===============================
# CAPACIDADE X CARGA POR PROCESSO
# ===============================
st.subheader("🏭 Capacidade x Carga por Processo")
st.dataframe(dem_proc)

# ============================================================
# ==================== TABELAS E AUDITORIA ===================
# ============================================================
st.markdown("## 📋 Tabelas e Auditoria")

# ===============================
# FILA POR PROCESSO
# ===============================
st.subheader("📦 Fila por Processo")

fila_exibicao = df[["PV", "Cliente", "Processo", "Data", "Horas", "Fila Acumulada (h)", "Fila (dias)"]].copy()
fila_exibicao["Horas"] = fila_exibicao["Horas"].round(1)
fila_exibicao["Fila Acumulada (h)"] = fila_exibicao["Fila Acumulada (h)"].round(1)
fila_exibicao["Fila (dias)"] = fila_exibicao["Fila (dias)"].round(1)

st.dataframe(fila_exibicao)

# ===============================
# AUDITORIA
# ===============================
st.subheader("📌 Auditoria de Capacidade")

auditoria = dem.copy()
auditoria["Horas"] = auditoria["Horas"].round(1)
auditoria["Capacidade"] = auditoria["Capacidade"].round(1)
auditoria["Ocupação (%)"] = auditoria["Ocupacao"].round(1)
auditoria["Semáforo"] = auditoria["Ocupacao"].apply(status)

st.dataframe(
    auditoria[["Periodo", "Semáforo", "Processo", "Horas", "Capacidade", "Ocupação (%)", "Saldo (h)"]]
)

# ===============================
# ATRASO
# ===============================
st.subheader("⏱️ Previsão de Atraso por PV")

pv_carga_exibicao = pv_carga.copy()
pv_carga_exibicao["Horas"] = pv_carga_exibicao["Horas"].round(1)
pv_carga_exibicao["Dias Necessários"] = pv_carga_exibicao["Dias Necessários"].round(1)

st.dataframe(pv_carga_exibicao)

# ===============================
# RISCO
# ===============================
st.subheader("⚠️ PVs em Risco")

risco_exibicao = risco.copy()
if not risco_exibicao.empty:
    risco_exibicao["Horas"] = risco_exibicao["Horas"].round(1)
    risco_exibicao["Dias Necessários"] = risco_exibicao["Dias Necessários"].round(1)

st.dataframe(risco_exibicao)

# ===============================
# CALENDÁRIO
# ===============================
st.subheader("📅 Calendário Industrial")
st.dataframe(cal)

# ===============================
# AUDITORIA DE PV
# ===============================
st.subheader("🧪 Auditoria de PV")

if not df_auditoria_pv.empty:
    resumo_auditoria = df_auditoria_pv["Status"].value_counts().reset_index()
    resumo_auditoria.columns = ["Status", "Qtde"]

    col1, col2, col3 = st.columns(3)
    col1.metric("PVs no Excel", pvs_totais_excel)
    col2.metric("PVs no APS", df["PV"].astype(str).str.strip().nunique())
    col3.metric("PVs Auditadas", df_auditoria_pv["PV"].astype(str).str.strip().nunique())

    st.dataframe(df_auditoria_pv.sort_values(["Status", "PV"]))
else:
    st.info("Nenhuma auditoria de PV disponível.")

# ===============================
# ROTEIRO POR CÓDIGO
# ===============================
st.markdown("## 🧩 Roteiro de Fabricação por Código")

# Base original (não expandida)
base_roteiro = df_pv.copy()

# Mantém apenas códigos válidos
base_roteiro = base_roteiro[base_roteiro["CODIGO_KEY"] != ""].copy()

# Agrupa por código (caso tenha repetição)
processos_ordenados = [
    "CORTE - SERRA",
    "CORTE-PLASMA",
    "CORTE-LASER",
    "CORTE-GUILHOTINA",
    "TORNO CONVENCIONAL",
    "TORNO CNC",
    "CENTRO DE USINAGEM",
    "FRESADORAS",
    "FURADEIRA DE BANCADA",
    "PRENSA (AMASSAMENTO)",
    "CALANDRA",
    "DOBRADEIRA",
    "ROSQUEADEIRA",
    "METALEIRA",
    "SOLDAGEM",
    "ACABAMENTO",
    "JATEAMENTO",
    "PINTURA",
    "MONTAGEM",
    "DIVERSOS"
]

roteiro = base_roteiro.groupby("CODIGO_KEY")[processos_ordenados].max().reset_index()
# Garante formato numérico
for proc in processos:
    roteiro[proc] = pd.to_numeric(roteiro[proc], errors="coerce").fillna(0)

# Remove processos zerados (opcional visual)
# roteiro = roteiro.loc[:, (roteiro != 0).any(axis=0)]

st.subheader("📋 Base de Roteiros")
st.dataframe(roteiro)

# ===============================
# CONSULTA DE ROTEIRO
# ===============================
st.subheader("🔎 Consultar Roteiro por Código")

codigos_disponiveis = sorted(roteiro["CODIGO_KEY"].unique().tolist())

codigo_sel = st.selectbox("Selecione o código", codigos_disponiveis)

roteiro_sel = roteiro[roteiro["CODIGO_KEY"] == codigo_sel].copy()

# Transforma em formato vertical (mais legível)
roteiro_detalhado = roteiro_sel.melt(
    id_vars=["CODIGO_KEY"],
    value_vars=processos,
    var_name="Processo",
    value_name="Tempo (min)"
)

# Remove processos sem tempo
roteiro_detalhado = roteiro_detalhado[roteiro_detalhado["Tempo (min)"] > 0]

# ===============================
# ORDEM LÓGICA DO ROTEIRO (PADRÃO INDUSTRIAL)
# ===============================
ORDEM_PROCESSOS = {
    "CORTE - SERRA": 10,
    "CORTE-PLASMA": 20,
    "CORTE-LASER": 30,
    "CORTE-GUILHOTINA": 40,
    "TORNO CONVENCIONAL": 50,
    "TORNO CNC": 60,
    "CENTRO DE USINAGEM": 70,
    "FRESADORAS": 80,
    "FURADEIRA DE BANCADA": 90,
    "PRENSA (AMASSAMENTO)": 100,
    "CALANDRA": 110,
    "DOBRADEIRA": 120,
    "ROSQUEADEIRA": 130,
    "METALEIRA": 140,
    "SOLDAGEM": 150,
    "ACABAMENTO": 160,
    "JATEAMENTO": 170,
    "PINTURA": 180,
    "MONTAGEM": 190,
    "DIVERSOS": 200
}

roteiro_detalhado["Operação"] = roteiro_detalhado["Processo"].map(ORDEM_PROCESSOS).fillna(999)
roteiro_detalhado = roteiro_detalhado.sort_values("Operação")

st.subheader(f"🛠️ Roteiro do Código: {codigo_sel}")

roteiro_exibicao = roteiro_detalhado[["Operação", "Processo", "Tempo (min)"]].copy()
roteiro_exibicao["Tempo (h)"] = (roteiro_exibicao["Tempo (min)"] / 60).round(2)
roteiro_exibicao = roteiro_exibicao.reset_index(drop=True)

st.dataframe(roteiro_exibicao)
tempo_total_min = roteiro_exibicao["Tempo (min)"].sum()
tempo_total_h = round(tempo_total_min / 60, 2)

col_rt1, col_rt2 = st.columns(2)
col_rt1.metric("⏱️ Tempo Total (min)", f"{tempo_total_min:,.0f}")
col_rt2.metric("🕒 Tempo Total (h)", f"{tempo_total_h:,.2f}")

# ===============================
# EXPORTAÇÃO
# ===============================
st.subheader("📥 Exportar Roteiro")

arquivo_excel = roteiro.copy()

@st.cache_data
def converter_excel(df):
    from io import BytesIO
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Roteiro")
    return buffer.getvalue()

excel_bytes = converter_excel(arquivo_excel)

st.download_button(
    label="📥 Baixar Roteiros em Excel",
    data=excel_bytes,
    file_name="roteiro_fabricacao.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# ============================================================
# ================= SIMULAÇÃO DE GARGALO =====================
# ============================================================
st.markdown("## 🚨 Simulação de Gargalo por Processo")

st.subheader("🔎 Verificar quais PVs estouram a capacidade do processo")

processo_gargalo_sel = st.selectbox(
    "Selecione o processo gargalo",
    sorted(df["Processo"].dropna().unique().tolist()),
    key="gargalo_processo_select"
)

# Base do processo selecionado
df_gargalo = df[df["Processo"] == processo_gargalo_sel].copy()

if not df_gargalo.empty:
    # Agrupa carga da PV apenas nesse processo
    gargalo_pv = (
        df_gargalo.groupby(["PV", "Cliente", "Data"], as_index=False)["Horas"]
        .sum()
        .sort_values(["Data", "PV"])
        .reset_index(drop=True)
    )

    # Carga acumulada na sequência de entrega
    gargalo_pv["Carga Acumulada (h)"] = gargalo_pv["Horas"].cumsum()

    # Recursos do processo
    recursos_gargalo = MAQUINAS.get(processo_gargalo_sel, 0)

    # Capacidade média diária do processo
    capacidade_dia_gargalo = capacidade_diaria_real(processo_gargalo_sel)

    hoje = pd.Timestamp.today().normalize()

    # Horas úteis disponíveis até a data da entrega (considerando o recurso escolhido)
    gargalo_pv["Horas Disponíveis até Entrega"] = gargalo_pv["Data"].apply(
        lambda x: horas_uteis_periodo(hoje, x) * recursos_gargalo * EFICIENCIA
    )

    # Saldo do gargalo
    gargalo_pv["Saldo Gargalo (h)"] = (
        gargalo_pv["Horas Disponíveis até Entrega"] - gargalo_pv["Carga Acumulada (h)"]
    ).round(1)

    # Estouro
    gargalo_pv["Estoura Gargalo?"] = np.where(
        gargalo_pv["Saldo Gargalo (h)"] < 0,
        "SIM",
        "NÃO"
    )

    # Dias estimados de estouro
    gargalo_pv["Dias de Estouro"] = np.where(
        capacidade_dia_gargalo > 0,
        np.ceil(np.abs(np.minimum(gargalo_pv["Saldo Gargalo (h)"], 0)) / capacidade_dia_gargalo),
        0
    )

    gargalo_pv["Dias de Estouro"] = gargalo_pv["Dias de Estouro"].astype(int)

    # Semáforo
    def semaforo_gargalo(x):
        if x == "SIM":
            return "🔴"
        return "🟢"

    gargalo_pv["Semáforo"] = gargalo_pv["Estoura Gargalo?"].apply(semaforo_gargalo)

    st.subheader(f"📋 Sequência de PVs no processo: {processo_gargalo_sel}")

    exib_gargalo = gargalo_pv.copy()
    exib_gargalo["Horas"] = exib_gargalo["Horas"].round(1)
    exib_gargalo["Carga Acumulada (h)"] = exib_gargalo["Carga Acumulada (h)"].round(1)
    exib_gargalo["Horas Disponíveis até Entrega"] = exib_gargalo["Horas Disponíveis até Entrega"].round(1)

    st.dataframe(
        exib_gargalo[
            [
                "Semáforo",
                "PV",
                "Cliente",
                "Data",
                "Horas",
                "Carga Acumulada (h)",
                "Horas Disponíveis até Entrega",
                "Saldo Gargalo (h)",
                "Estoura Gargalo?",
                "Dias de Estouro"
            ]
        ]
    )

    # Resumo executivo
    total_estouro = (gargalo_pv["Estoura Gargalo?"] == "SIM").sum()
    total_ok = (gargalo_pv["Estoura Gargalo?"] == "NÃO").sum()

    g1, g2, g3 = st.columns(3)
    g1.metric("🔴 PVs que Estouram", int(total_estouro))
    g2.metric("🟢 PVs Viáveis", int(total_ok))
    g3.metric("⚙️ Recursos do Processo", int(recursos_gargalo))

else:
    st.info("Não há carga para o processo selecionado.")