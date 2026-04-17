import streamlit as st

# ===============================
# 🔐 BLOQUEIO DE ACESSO GLOBAL
# ===============================
if "logado" not in st.session_state or not st.session_state.logado:
    st.warning("🔒 Acesso não autorizado. Redirecionando para login...")
    st.switch_page("app.py")

# ===============================
# IMPORTS (ORGANIZADOS)
# ===============================
import numpy as np
import pandas as pd
import plotly.express as px
import os
import time
import holidays
import math
import shutil
from datetime import datetime

st.set_page_config(layout="wide")

# ============================================================
# 🔐 CONTROLE OFICIAL DE HISTÓRICO + BACKUP AUTOMÁTICO (ROBUSTO)
# ============================================================

PASTA_BACKUP_BAIXAS = "backup_baixas"
ARQUIVO_HISTORICO_BAIXAS = "APS_BAIXAS_OPERACIONAIS.xlsx"


def _garantir_pasta_backup():
    os.makedirs(PASTA_BACKUP_BAIXAS, exist_ok=True)


def _gerar_nome_backup():
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return f"APS_BAIXAS_OPERACIONAIS_{timestamp}.xlsx"


def _criar_backup():
    try:
        if not os.path.exists(ARQUIVO_HISTORICO_BAIXAS):
            return False, "Arquivo ainda não existe (primeira gravação)"

        _garantir_pasta_backup()

        destino = os.path.join(
            PASTA_BACKUP_BAIXAS,
            _gerar_nome_backup()
        )

        shutil.copy2(ARQUIVO_HISTORICO_BAIXAS, destino)

        return True, destino

    except Exception as e:
        return False, str(e)


def salvar_historico_baixas(df):
    """
    🔴 ÚNICO PONTO OFICIAL DE GRAVAÇÃO DO HISTÓRICO
    🔒 COM PROTEÇÃO CONTRA PERDA DE DADOS
    """

    try:
        if df is None or df.empty:
            return {
                "ok": False,
                "erro": "DataFrame vazio - gravação cancelada para evitar perda de histórico",
                "backup_ok": False,
                "backup_msg": None
            }

        backup_ok, backup_msg = _criar_backup()

        df.to_excel(ARQUIVO_HISTORICO_BAIXAS, index=False)

        return {
            "ok": True,
            "linhas": len(df),
            "backup_ok": backup_ok,
            "backup_msg": backup_msg
        }

    except Exception as e:
        return {
            "ok": False,
            "erro": str(e),
            "backup_ok": False,
            "backup_msg": None
        }

# ===============================
# FORMATAÇÃO BR (INALTERADO)
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
# LOGO + TÍTULO (INALTERADO)
# ===============================
col1, col2 = st.columns([1, 6])

with col1:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=80)

with col2:
    st.title("APS | Carga & Capacidade")

# ===============================
# CONFIG ORIGINAL (INALTERADO)
# ===============================
EFICIENCIA = 0.80

HORAS_SEG_A_QUI = 9
HORAS_SEXTA = 8
HORAS_DIA_UTIL_MEDIA = ((HORAS_SEG_A_QUI * 4) + HORAS_SEXTA) / 5

FERIADOS_BR = holidays.Brazil()

MAQUINAS = {
    "CORTE - SERRA": 2,
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

# ===============================
# FUNÇÕES DE TEMPO (INALTERADAS)
# ===============================
br_holidays = holidays.Brazil()

def dias_uteis_periodo(inicio, fim):
    if pd.isna(inicio) or pd.isna(fim):
        return 0

    inicio = pd.Timestamp(inicio).normalize()
    fim = pd.Timestamp(fim).normalize()

    if fim < inicio:
        return 0

    dias = pd.date_range(inicio, fim, freq="D")
    return sum(1 for d in dias if d.weekday() < 5 and d.date() not in br_holidays)

def horas_uteis_periodo(inicio, fim):
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
            total_horas += HORAS_SEXTA if d.weekday() == 4 else HORAS_SEG_A_QUI

    return total_horas

def dias_uteis_mes(ano, mes):
    inicio = pd.Timestamp(year=int(ano), month=int(mes), day=1)
    fim = inicio + pd.offsets.MonthEnd(1)
    return dias_uteis_periodo(inicio, fim)

def horas_uteis_mes(ano, mes):
    inicio = pd.Timestamp(year=int(ano), month=int(mes), day=1)
    fim = inicio + pd.offsets.MonthEnd(1)
    return horas_uteis_periodo(inicio, fim)

def capacidade_mes_por_processo(ano, mes, processo):
    recursos = MAQUINAS.get(processo, 0)
    if recursos <= 0:
        return 0
    return horas_uteis_mes(ano, mes) * recursos * EFICIENCIA


# ============================================================
# CAPACIDADE SEMANAL POR PROCESSO (CORREÇÃO CRÍTICA)
# ============================================================
def capacidade_semana_por_processo(inicio, fim, processo):

    recursos = MAQUINAS.get(processo, 0)

    if recursos <= 0:
        return 0

    horas = horas_uteis_periodo(inicio, fim)

    return horas * recursos * EFICIENCIA





# ===============================
# CACHE (INALTERADO)
# ===============================
@st.cache_data(ttl=0)
def carregar_dados(arquivo_pv, file_mtime):
    df = pd.read_excel(arquivo_pv)
    return df




# ===============================
# CSS VISUAL PREMIUM APS
# ===============================
st.markdown("""
<style>
/* ===== FUNDO E ESPAÇAMENTO ===== */
.block-container {
    padding-top: 2.2rem;
    padding-bottom: 2rem;
}

/* ===== TÍTULOS ===== */
h1, h2, h3 {
    letter-spacing: 0.2px;
}

/* ===== SUBTÍTULOS ===== */
div[data-testid="stMarkdownContainer"] h2 {
    border-left: 5px solid #FF7A00;
    padding-left: 12px;
    margin-top: 1.2rem;
    margin-bottom: 0.8rem;
}

/* ===== MÉTRICAS ===== */
div[data-testid="metric-container"] {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255,255,255,0.08);
    padding: 16px 18px;
    border-radius: 14px;
    box-shadow: 0 0 0 rgba(0,0,0,0);
    transition: all 0.2s ease-in-out;
}

div[data-testid="metric-container"]:hover {
    transform: translateY(-2px);
    border: 1px solid rgba(255,122,0,0.35);
}

/* ===== TABELAS ===== */
div[data-testid="stDataFrame"] {
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px;
    overflow: hidden;
}

/* ===== SELECTBOX / INPUT ===== */
div[data-baseweb="select"],
div[data-testid="stTextInput"] > div {
    border-radius: 10px !important;
}

/* ===== BOTÕES ===== */
button[kind="primary"] {
    border-radius: 10px !important;
    font-weight: 600 !important;
}

/* ===== DOWNLOAD BUTTON ===== */
div.stDownloadButton > button {
    border-radius: 10px !important;
    font-weight: 600 !important;
    background-color: #FF7A00 !important;
    color: white !important;
    border: none !important;
}

/* ===== ALERTAS ===== */
div[data-testid="stAlert"] {
    border-radius: 12px;
}

/* ===== DIVISORES ===== */
hr {
    border: none;
    border-top: 1px solid rgba(255,255,255,0.08);
    margin: 1.4rem 0;
}
</style>
""", unsafe_allow_html=True)

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
PAGE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(PAGE_DIR)

arquivo_pv = os.path.join(ROOT_DIR, "PV.xlsx")
BASE_PATH = ROOT_DIR

st.caption(f"📂 Lendo arquivo: {arquivo_pv}")

if not os.path.exists(arquivo_pv):
    st.error(f"Arquivo PV.xlsx não encontrado em: {arquivo_pv}")
    st.stop()

file_mtime = os.path.getmtime(arquivo_pv)

df_pv = carregar_dados(arquivo_pv, file_mtime)

# ===============================
# NORMALIZAÇÃO FORTE DE CABEÇALHOS
# ===============================
df_pv.columns = [
    str(c)
    .replace("\xa0", "")   # remove espaço invisível
    .replace("\n", "")
    .replace("\r", "")
    .replace("  ", " ")
    .strip()
    .upper()
    for c in df_pv.columns
]

# ===============================
# PADRONIZAÇÃO DE NOMES DE COLUNAS
# ===============================
mapa_colunas = {
    "CÓDIGO": "CODIGO_PV",
    "CODIGO": "CODIGO_PV",
    "DATA DE ENTREGA": "ENTREGA",
    "QUANTIDADE": "QTD",
    "QTD": "QTD",
    "QTDE": "QTD",
    "QTD.": "QTD",
    "QTE": "QTD"
}

df_pv = df_pv.rename(columns=lambda x: mapa_colunas.get(x, x))

# ===============================
# VALIDAÇÃO DE COLUNAS OBRIGATÓRIAS
# ===============================
colunas_obrigatorias = ["PV", "CLIENTE", "CODIGO_PV", "ENTREGA", "QTD"]
faltantes = [c for c in colunas_obrigatorias if c not in df_pv.columns]

if faltantes:
    st.error(f"A planilha PV.xlsx está faltando as colunas obrigatórias: {', '.join(faltantes)}")
    st.write("Colunas encontradas no arquivo:", df_pv.columns.tolist())
    st.stop()

# ===============================
# FUNÇÃO DE NORMALIZAÇÃO DE CÓDIGO
# ===============================
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

# Data brasileira
df_pv["ENTREGA"] = pd.to_datetime(df_pv["ENTREGA"], errors="coerce", dayfirst=True)

# ===============================
# COLUNA PADRÃO DE ENTREGA DO APS
# ===============================
df_pv["DATA_ENTREGA_APS"] = df_pv["ENTREGA"]

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
    tempos_debug = []

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
            "CODIGO_PV": codigo_atual,
            "DATA_ENTREGA_APS": row.get("DATA_ENTREGA_APS", pd.NaT),
            "Motivo": " | ".join(motivos_pv)
        }

        pvs_excluidas.append(registro)
        pvs_sem_carga.append(registro)

        auditoria_pv.append({
            "PV": pv_atual,
            "Cliente": cliente_atual,
            "CODIGO": codigo_atual,
            "CODIGO_PV": codigo_atual,
            "DATA_ENTREGA_APS": row.get("DATA_ENTREGA_APS", pd.NaT),
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
        valor_original = row.get(proc)
        tempo = pd.to_numeric(valor_original, errors="coerce")

        if pd.notna(tempo) and tempo > 0:
            qtde_processos_validos += 1

            horas = (tempo * float(row["QTD"])) / 60
            horas_totais_pv += horas

            linhas.append({
                "PV": pv_atual,
                "Cliente": cliente_atual,
                "CODIGO_PV": codigo_atual,
                "Processo": proc,
                "Data": row["ENTREGA"],
                "ENTREGA": row["ENTREGA"],
                "DATA_ENTREGA_APS": row.get("DATA_ENTREGA_APS", row["ENTREGA"]),
                "Horas": horas
            })
        else:
            tempos_debug.append(f"{proc}={valor_original}")

    # -------------------------------
    # Se não teve nenhum processo válido
    # -------------------------------
    if qtde_processos_validos == 0:
        status_pv = "Sem processo válido"

        motivo_sem_processo = "Nenhum processo com tempo > 0"
        if tempos_debug:
            motivo_sem_processo += " | " + " ; ".join(tempos_debug[:10])

        registro = {
            "PV": pv_atual,
            "Cliente": cliente_atual,
            "CODIGO": codigo_atual,
            "CODIGO_PV": codigo_atual,
            "DATA_ENTREGA_APS": row.get("DATA_ENTREGA_APS", pd.NaT),
            "Motivo": motivo_sem_processo
        }

        pvs_excluidas.append(registro)
        pvs_sem_carga.append(registro)

        auditoria_pv.append({
            "PV": pv_atual,
            "Cliente": cliente_atual,
            "CODIGO": codigo_atual,
            "CODIGO_PV": codigo_atual,
            "DATA_ENTREGA_APS": row.get("DATA_ENTREGA_APS", pd.NaT),
            "Status": status_pv,
            "Qtd": row["QTD"],
            "Total Processos Válidos": 0,
            "Horas Totais": 0,
            "Motivo": motivo_sem_processo
        })
    else:
        auditoria_pv.append({
            "PV": pv_atual,
            "Cliente": cliente_atual,
            "CODIGO": codigo_atual,
            "CODIGO_PV": codigo_atual,
            "DATA_ENTREGA_APS": row.get("DATA_ENTREGA_APS", pd.NaT),
            "Status": status_pv,
            "Qtd": row["QTD"],
            "Total Processos Válidos": qtde_processos_validos,
            "Horas Totais": horas_totais_pv,
            "Motivo": ""
        })

# Base principal de carga
df_original = pd.DataFrame(linhas)

# Blindagem de colunas críticas
if not df_original.empty:
    if "DATA_ENTREGA_APS" in df_original.columns:
        df_original["DATA_ENTREGA_APS"] = pd.to_datetime(
            df_original["DATA_ENTREGA_APS"],
            errors="coerce",
            dayfirst=True
        )

    if "ENTREGA" in df_original.columns:
        df_original["ENTREGA"] = pd.to_datetime(
            df_original["ENTREGA"],
            errors="coerce",
            dayfirst=True
        )

    if "Data" in df_original.columns:
        df_original["Data"] = pd.to_datetime(
            df_original["Data"],
            errors="coerce",
            dayfirst=True
        )



# =============================== 
# BAIXAS OPERACIONAIS APS
# ===============================
ARQUIVO_BAIXAS = "APS_BAIXAS_OPERACIONAIS.xlsx"

COLUNAS_BAIXAS = [
    "PV",
    "Cliente",
    "CODIGO_PV",
    "Processo",
    "Horas",
    "Data_Baixa",
    "Usuario",
    "Observacao",
    "Status_Baixa",
    "Data_Estorno",
    "Motivo_Estorno"
]

def caminho_arquivo_baixas(base_path):
    return os.path.join(base_path, ARQUIVO_BAIXAS)

def garantir_arquivo_baixas(base_path):
    os.makedirs(base_path, exist_ok=True)
    caminho = caminho_arquivo_baixas(base_path)

    if not os.path.exists(caminho):
        df_vazio = pd.DataFrame(columns=COLUNAS_BAIXAS)
        df_vazio.to_excel(caminho, index=False)

    return caminho


# =============================== 
# PADRONIZAR BAIXAS OPERACIONAIS APS
# ===============================

def _padronizar_df_baixas(df_baixas):

    if df_baixas is None or df_baixas.empty:
        return pd.DataFrame(columns=COLUNAS_BAIXAS + ["CHAVE_OPERACAO"])

    df_baixas = df_baixas.copy()

    for col in COLUNAS_BAIXAS:
        if col not in df_baixas.columns:
            df_baixas[col] = None

    df_baixas = df_baixas[COLUNAS_BAIXAS].copy()

    colunas_texto = [
        "PV", "Cliente", "CODIGO_PV", "Processo",
        "Usuario", "Observacao", "Status_Baixa",
        "Data_Estorno", "Motivo_Estorno"
    ]

    for col in colunas_texto:
        df_baixas[col] = df_baixas[col].fillna("").astype(str).str.strip()

    df_baixas["PV"] = df_baixas["PV"].str.upper()
    df_baixas["CODIGO_PV"] = df_baixas["CODIGO_PV"].str.upper()
    df_baixas["Processo"] = df_baixas["Processo"].str.upper()
    df_baixas["Cliente"] = df_baixas["Cliente"].replace("", "SEM CLIENTE")

    df_baixas["Status_Baixa"] = (
        df_baixas["Status_Baixa"]
        .replace("", "ATIVA")
        .str.upper()
    )

    df_baixas["Horas"] = pd.to_numeric(df_baixas["Horas"], errors="coerce").fillna(0)
    df_baixas["Data_Baixa"] = pd.to_datetime(df_baixas["Data_Baixa"], errors="coerce")
    df_baixas["Data_Estorno"] = df_baixas["Data_Estorno"].fillna("").astype(str)

    df_baixas["CHAVE_OPERACAO"] = (
        df_baixas["PV"] + "||" +
        df_baixas["Processo"] + "||" +
        df_baixas["CODIGO_PV"]
    )

    df_baixas = df_baixas.sort_values(
        by=["Data_Baixa", "PV", "Processo"],
        ascending=[False, True, True]
    ).reset_index(drop=True)

    return df_baixas


# ============================================================
# FUNÇÃO DE CARREGAMENTO
# ============================================================
@st.cache_data(ttl=0)
def carregar_baixas_operacionais(base_path, file_mtime_baixas):

    caminho = garantir_arquivo_baixas(base_path)

    try:
        df_baixas = pd.read_excel(caminho, dtype=str)
        return _padronizar_df_baixas(df_baixas)
    except Exception as e:
        st.warning(f"Erro ao ler baixas: {e}")
        return pd.DataFrame(columns=COLUNAS_BAIXAS + ["CHAVE_OPERACAO"])


# ============================================================
# 🔥 CARREGAMENTO DAS BAIXAS (TEM QUE VIR AQUI)
# ============================================================

caminho_baixas = garantir_arquivo_baixas(BASE_PATH)

try:
    file_mtime_baixas = os.path.getmtime(caminho_baixas)
except:
    file_mtime_baixas = 0

df_baixas = carregar_baixas_operacionais(BASE_PATH, file_mtime_baixas)

df_baixas_ativas = df_baixas[
    df_baixas["Status_Baixa"].isin(["ATIVA", "TERCEIRIZADA"])
].copy()

st.session_state["df_baixas_ativas"] = df_baixas_ativas


# ============================================================
# BASE OPERACIONAL VISUAL
# ============================================================

df_operacional = df_original.copy()



# --------------------------------------------
# FUNÇÃO DE NORMALIZAÇÃO (CORRIGIDA)
# --------------------------------------------
def normalizar_chave_operacao(pv, processo, codigo):

    def limpar(valor):
        if pd.isna(valor):
            return ""

        return (
            str(valor)
            .strip()
            .upper()
            .replace("  ", " ")
            .replace(" - ", "-")
            .replace("- ", "-")
            .replace(" -", "-")
        )

    pv = limpar(pv)
    processo = limpar(processo)
    codigo = limpar(codigo)

    return f"{pv}||{processo}||{codigo}"


# --------------------------------------------
# GARANTE CHAVE PADRÃO NA BASE OPERACIONAL
# --------------------------------------------
if not df_operacional.empty:
    for col in ["PV", "Processo", "CODIGO_PV"]:
        if col not in df_operacional.columns:
            df_operacional[col] = ""

        df_operacional[col] = (
            df_operacional[col]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.upper()
        )

    df_operacional["CHAVE_OPERACAO"] = df_operacional.apply(
        lambda r: normalizar_chave_operacao(
            r["PV"], r["Processo"], r["CODIGO_PV"]
        ),
        axis=1
    )
else:
    df_operacional["CHAVE_OPERACAO"] = ""


# --------------------------------------------
# BASE OFICIAL PARA TIRAR DA FILA (CORRIGIDO)
# --------------------------------------------
df_baixas_ativas = st.session_state.get("df_baixas_ativas", pd.DataFrame())

if not df_baixas_ativas.empty:

    df_baixas_tmp = df_baixas_ativas.copy()

    # NORMALIZA IGUAL À BASE OPERACIONAL
    for col in ["PV", "Processo", "CODIGO_PV"]:
        if col not in df_baixas_tmp.columns:
            df_baixas_tmp[col] = ""

        df_baixas_tmp[col] = (
            df_baixas_tmp[col]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.upper()
        )

    # 🔥 CHAVE USANDO A MESMA FUNÇÃO
    df_baixas_tmp["CHAVE_OPERACAO"] = df_baixas_tmp.apply(
        lambda r: normalizar_chave_operacao(
            r["PV"], r["Processo"], r["CODIGO_PV"]
        ),
        axis=1
    )

    # 🔥 SET DE CHAVES (SIMPLES E CONFIÁVEL)
    chaves_baixadas_ativas = set(df_baixas_tmp["CHAVE_OPERACAO"])

else:
    chaves_baixadas_ativas = set()


# --------------------------------------------
# APLICA STATUS OPERACIONAL (SIMPLIFICADO E CORRETO)
# --------------------------------------------
df_operacional["Status Operacional"] = df_operacional["CHAVE_OPERACAO"].apply(
    lambda chave: "✅ Baixado" if chave in chaves_baixadas_ativas else "⏳ Pendente"
)

# ============================================================
# BASE PENDENTE REAL (USADA NOS CÁLCULOS DO APS)
# ============================================================
df = df_operacional[df_operacional["Status Operacional"] == "⏳ Pendente"].copy()
df = df.reset_index(drop=True)
# DataFrames auxiliares
df_excluidas = pd.DataFrame(pvs_excluidas)
df_sem_carga = pd.DataFrame(pvs_sem_carga)
df_auditoria_pv = pd.DataFrame(auditoria_pv)

# Blindagem dos auxiliares
for _df_aux in [df_excluidas, df_sem_carga, df_auditoria_pv]:
    if not _df_aux.empty and "DATA_ENTREGA_APS" in _df_aux.columns:
        _df_aux["DATA_ENTREGA_APS"] = pd.to_datetime(
            _df_aux["DATA_ENTREGA_APS"],
            errors="coerce",
            dayfirst=True
        )

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
            "CODIGO_PV": row["CODIGO_PV"],
            "DATA_ENTREGA_APS": row.get("DATA_ENTREGA_APS", pd.NaT),
            "Motivo": "PV não auditada por falha de processamento"
        }

        pvs_excluidas.append(registro)
        pvs_sem_carga.append(registro)

        auditoria_pv.append({
            "PV": str(row["PV"]).strip(),
            "Cliente": row.get("CLIENTE", "SEM CLIENTE"),
            "CODIGO": row["CODIGO_PV"],
            "CODIGO_PV": row["CODIGO_PV"],
            "DATA_ENTREGA_APS": row.get("DATA_ENTREGA_APS", pd.NaT),
            "Status": "Falha de processamento",
            "Qtd": row["QTD"],
            "Total Processos Válidos": 0,
            "Horas Totais": 0,
            "Motivo": "PV não auditada por falha de processamento"
        })

df_excluidas = pd.DataFrame(pvs_excluidas)
df_sem_carga = pd.DataFrame(pvs_sem_carga)
df_auditoria_pv = pd.DataFrame(auditoria_pv)

for _df_aux in [df_excluidas, df_sem_carga, df_auditoria_pv]:
    if not _df_aux.empty and "DATA_ENTREGA_APS" in _df_aux.columns:
        _df_aux["DATA_ENTREGA_APS"] = pd.to_datetime(
            _df_aux["DATA_ENTREGA_APS"],
            errors="coerce",
            dayfirst=True
        )

if df.empty:
    st.error("Nenhum dado válido foi encontrado para exibir no dashboard.")

    st.markdown("### 🔎 Diagnóstico da expansão da base")

    st.write("**Total de linhas em df_pv:**", len(df_pv))
    st.write("**Total de PVs únicas no Excel:**", df_pv["PV"].astype(str).str.strip().nunique())

    if "ENTREGA" in df_pv.columns:
        st.write("**Linhas com ENTREGA válida:**", df_pv["ENTREGA"].notna().sum())

    if "QTD" in df_pv.columns:
        st.write("**Linhas com QTD > 0:**", (pd.to_numeric(df_pv["QTD"], errors="coerce").fillna(0) > 0).sum())

    st.markdown("### 📋 Prévia da base lida")
    st.dataframe(df_pv.head(20), use_container_width=True)

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

    dem = df.groupby(
        ["Periodo", "Processo", "Semana", "Ano"],
        as_index=False
    )["Horas"].sum()

    dem = dem.merge(cal, on=["Semana", "Ano"], how="left")

    # DEBUG (mantenha por enquanto)
    st.write("DEBUG dem colunas:", dem.columns.tolist())
    st.write("DEBUG dem preview:", dem.head())

    # 🔒 FUNÇÃO SEGURA
    def calcular_capacidade_segura(r):
        try:
            inicio = r.get("Inicio", None)
            fim = r.get("Fim", None)
            processo = r.get("Processo", None)

            if pd.isna(inicio) or pd.isna(fim) or processo is None:
                return 0

            return capacidade_semana_por_processo(inicio, fim, processo)
        except Exception as e:
            return 0

    dem["Capacidade"] = dem.apply(calcular_capacidade_segura, axis=1)

else:
    df["Periodo"] = "Mês " + df["Mes"].astype(str)

    dem = df.groupby(
        ["Periodo", "Processo", "Mes", "Ano"],
        as_index=False
    )["Horas"].sum()

    dem["Capacidade"] = dem.apply(
        lambda r: capacidade_mes_por_processo(
            r.get("Ano"),
            r.get("Mes"),
            r.get("Processo")
        ),
        axis=1
    )

# ===============================
# TRATAMENTOS FINAIS
# ===============================

# Evita divisão por zero
dem["Capacidade"] = dem["Capacidade"].fillna(0)

dem["Ocupacao"] = np.where(
    dem["Capacidade"] > 0,
    (dem["Horas"] / dem["Capacidade"]) * 100,
    0
)

dem["Ocupacao"] = dem["Ocupacao"].replace([np.inf, -np.inf], 0).fillna(0)

# Remove processos sem capacidade produtiva
dem = dem[dem["Capacidade"] > 0].copy()

# Remove linhas irrelevantes
dem = dem[(dem["Horas"] > 0) | (dem["Ocupacao"] > 0)].copy()

# Ordenação
if tipo == "Mensal":
    dem["Ordem_Periodo"] = dem["Mes"]
else:
    dem["Ordem_Periodo"] = dem["Semana"]

dem = dem.sort_values(["Ordem_Periodo", "Processo"]).copy()

# Labels
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

dem["Saldo (h)"] = (dem["Capacidade"] - dem["Horas"]).round(1)

# Coluna apenas para exibição visual
dem["Ocupação (%)"] = dem["Ocupacao"].round(1)


# ============================================================
# 🔷 BASE EXECUTIVA APS (PV + PRAZO + STATUS)
# ============================================================

# 🔒 Validação mínima da base
if df is None or df.empty:
    st.error("Erro: base APS (df) está vazia.")
    st.stop()

if "DATA_ENTREGA_APS" not in df.columns:
    st.error("Erro: coluna DATA_ENTREGA_APS não encontrada.")
    st.stop()

if "Horas" not in df.columns:
    st.error("Erro: coluna Horas não encontrada.")
    st.stop()

# ============================================================
# 📦 CONSOLIDAÇÃO POR PV
# ============================================================

pv_carga = (
    df.groupby("PV", as_index=False)
    .agg({
        "Horas": "sum",
        "DATA_ENTREGA_APS": "min"
    })
)

# 🔒 Garantia de tipo de data
pv_carga["DATA_ENTREGA_APS"] = pd.to_datetime(
    pv_carga["DATA_ENTREGA_APS"],
    errors="coerce"
)



# ============================================================
# 📅 CÁLCULO DE PRAZO
# ============================================================

hoje = pd.Timestamp.now().normalize()

pv_carga["Dias Disponíveis"] = (
    pv_carga["DATA_ENTREGA_APS"] - hoje
).dt.days

pv_carga["Dias Disponíveis"] = pd.to_numeric(
    pv_carga["Dias Disponíveis"], errors="coerce"
).fillna(0)

# 🔥 PRIMEIRO CALCULA ATRASO
pv_carga["Atraso (dias)"] = np.where(
    pv_carga["Dias Disponíveis"] < 0,
    pv_carga["Dias Disponíveis"] * -1,
    0
)

# 🔥 DEPOIS USA
pv_carga["Status Prazo"] = np.where(
    pv_carga["Atraso (dias)"] > 0,
    "Atrasado",
    np.where(
        pv_carga["Dias Disponíveis"] <= 3,
        "Risco",
        "OK"
    )
)


# ============================================================
# 🔮 PREVISÃO REAL DE ENTREGA (APS INTELIGENTE)
# ============================================================

df_previsao = df.copy()

if not df_previsao.empty:

    df_previsao["Data Prevista Processo"] = df_previsao["Data"] + pd.to_timedelta(
        df_previsao["Fila (dias)"], unit="D"
    )

    pv_previsao = (
        df_previsao.groupby("PV", as_index=False)
        .agg({
            "Data Prevista Processo": "max"
        })
    )

    # 🔒 PROTEÇÃO CONTRA DUPLICAÇÃO
    if "Data Prevista Processo" in pv_carga.columns:
        pv_carga = pv_carga.drop(columns=["Data Prevista Processo"])

    pv_carga = pv_carga.merge(
        pv_previsao,
        on="PV",
        how="left"
    )

    pv_carga["Atraso Real (dias)"] = (
        pv_carga["Data Prevista Processo"] - pv_carga["DATA_ENTREGA_APS"]
    ).dt.days

    pv_carga["Atraso Real (dias)"] = pd.to_numeric(
        pv_carga["Atraso Real (dias)"],
        errors="coerce"
    ).fillna(0)

    pv_carga["Status Real"] = np.where(
        pv_carga["Atraso Real (dias)"] > 0,
        "🔴 Vai atrasar",
        np.where(
            pv_carga["Atraso Real (dias)"] >= -2,
            "🟡 Risco real",
            "🟢 OK"
        )
    )

else:
    pv_carga["Data Prevista Processo"] = pd.NaT
    pv_carga["Atraso Real (dias)"] = 0
    pv_carga["Status Real"] = "⚪ Sem dados"





# ============================================================
# 🚦 STATUS EXECUTIVO
# ============================================================

pv_carga["Status Prazo"] = np.where(
    pv_carga["Atraso (dias)"] > 0,
    "Atrasado",
    np.where(
        pv_carga["Dias Disponíveis"] <= 3,
        "Risco",
        "OK"
    )
)

# ============================================================
# 📊 AGRUPAMENTOS EXECUTIVOS
# ============================================================

atrasos = pv_carga[pv_carga["Atraso (dias)"] > 0].copy()

risco = pv_carga[
    (pv_carga["Atraso (dias)"] == 0) &
    (pv_carga["Dias Disponíveis"] <= 3)
].copy()

ok = pv_carga[
    (pv_carga["Atraso (dias)"] == 0) &
    (pv_carga["Dias Disponíveis"] > 3)
].copy()

# 🔒 Blindagem final
if pv_carga.empty:
    st.error("Erro crítico: pv_carga não foi gerado corretamente.")
    st.stop()



# ============================================================
# 🔥 GARGALO POR IMPACTO REAL (APS INTELIGENTE)
# ============================================================

df_impacto = df.copy()

if not df_impacto.empty and "Fila (dias)" in df_impacto.columns:

    df_impacto["Fila (dias)"] = pd.to_numeric(
        df_impacto["Fila (dias)"], errors="coerce"
    ).fillna(0)

    impacto_gargalo = (
        df_impacto.groupby("Processo", as_index=False)
        .agg(
            Impacto_Total_Dias=("Fila (dias)", "sum"),
            PVs_Impactadas=("PV", "nunique")
        )
    )

    impacto_gargalo = impacto_gargalo.sort_values(
        ["Impacto_Total_Dias", "PVs_Impactadas"],
        ascending=[False, False]
    ).reset_index(drop=True)

else:
    impacto_gargalo = pd.DataFrame(
        columns=["Processo", "Impacto_Total_Dias", "PVs_Impactadas"]
    )


# ============================================================
# ==================== PAINEL EXECUTIVO APS ==================
# ============================================================
st.markdown("## 📊 Painel Executivo APS")
st.caption("Indicadores estratégicos, status geral e leitura executiva da produção.")


# ===============================
# BASE EXECUTIVA
# ===============================
carga_total = round(df["Horas"].sum(), 1)

recursos_ativos = sum(v for v in MAQUINAS.values() if v > 0)

mes_ref = int(df["Mes"].mode()[0])
ano_ref = int(df["Ano"].mode()[0])

horas_mes_ref = horas_uteis_mes(ano_ref, mes_ref)

capacidade_total = round(
    recursos_ativos * horas_mes_ref * EFICIENCIA,
    1
)

utilizacao_total = round((carga_total / capacidade_total) * 100, 1) if capacidade_total > 0 else 0

pvs_no_aps = df_auditoria_pv["PV"].astype(str).str.strip().nunique()

atrasos = pv_carga[pv_carga["Atraso (dias)"] > 0].copy()

if "Dias Disponíveis" in pv_carga.columns:
    risco = pv_carga[
        (pv_carga["Atraso (dias)"] == 0) &
        (pv_carga["Dias Disponíveis"] <= 3)
    ].copy()
else:
    risco = pd.DataFrame(columns=pv_carga.columns)

ok = max(0, pvs_no_aps - len(atrasos) - len(risco))

gargalo_exec = None
processo_mais_carga = None
ocupacao_max = 0.0

if not dem.empty:
    gargalo_exec = (
        dem.sort_values(["Ocupacao", "Horas"], ascending=[False, False])
        .iloc[0]["Processo"]
    )
    ocupacao_max = float(
        dem.sort_values(["Ocupacao", "Horas"], ascending=[False, False])
        .iloc[0]["Ocupacao"]
    )

if not dem_proc.empty:
    processo_mais_carga = (
        dem_proc.sort_values("Horas", ascending=False)
        .iloc[0]["Processo"]
    )

# ===============================
# KPIs PRINCIPAIS
# ===============================
st.subheader("📌 Indicadores Principais")

k1, k2, k3, k4 = st.columns(4)
k1.metric("🏭 Carga Total (h)", fmt_br_num(carga_total, 1))
k2.metric("⚙️ Capacidade Mensal (h)", fmt_br_num(capacidade_total, 1))
k3.metric("📈 Utilização Global", fmt_br_pct(utilizacao_total, 1))
k4.metric("📦 PVs no APS", fmt_br_int(pvs_no_aps))

# ===============================
# FUNÇÃO AUXILIAR - SEMÁFORO ENTREGA
# ===============================
def semaforo_entrega(dias):
    if pd.isna(dias):
        return "⚪ Sem data"
    elif dias < 0:
        return "🔴 Atrasado"
    elif dias <= 3:
        return "🟠 Urgente"
    elif dias <= 7:
        return "🟡 Atenção"
    else:
        return "🟢 Normal"

def status(x):
    try:
        x = float(x)
    except:
        return "⚪"

    if x >= 100:
        return "🔴"
    elif x >= 90:
        return "🟠"
    elif x >= 75:
        return "🟡"
    else:
        return "🟢"

# ===============================
# STATUS EXECUTIVO
# ===============================
st.subheader("🚦 Status Executivo")

s1, s2, s3, s4 = st.columns(4)
s1.metric("🔴 Atraso", fmt_br_int(len(atrasos)))
s2.metric("🟡 Risco", fmt_br_int(len(risco)))
s3.metric("🟢 OK", fmt_br_int(ok))
s4.metric("📄 PVs no Excel", fmt_br_int(pvs_totais_excel))

# ===============================
# DESTAQUES DA OPERAÇÃO
# ===============================
st.subheader("🔥 Destaques da Operação")

d1, d2, d3 = st.columns(3)
d1.metric("🔥 Gargalo Principal", gargalo_exec if gargalo_exec else "N/D")
d2.metric("🏗️ Processo Mais Carregado", processo_mais_carga if processo_mais_carga else "N/D")
d3.metric("📍 Pico de Ocupação", fmt_br_pct(ocupacao_max, 1))

# ============================================================
# Mini Dashboard por Gargalo (INTELIGENTE)
# ============================================================

def _normalizar_coluna_processo(df, coluna="Processo"):
    if df is None or df.empty or coluna not in df.columns:
        return df

    df = df.copy()
    df[coluna] = df[coluna].fillna("").astype(str).str.strip().str.upper()
    return df


def montar_mini_dashboard_gargalos(fila, df_baixas_ativas=None):

    # 🔒 Proteção total
    if df_baixas_ativas is None or not isinstance(df_baixas_ativas, pd.DataFrame):
        df_baixas_ativas = pd.DataFrame()

    if fila is None or fila.empty:
        return pd.DataFrame(columns=[
            "Processo",
            "Qtd_Fila",
            "Horas_Fila",
            "Qtd_Baixas_Ativas",
            "Carga_Total",
            "Score",
            "Status_Gargalo",
            "Ranking"
        ])

    # ------------------------------------------------------------
    # BASE DA FILA
    # ------------------------------------------------------------
    fila_tmp = fila.copy()
    fila_tmp = _normalizar_coluna_processo(fila_tmp, "Processo")

    if "Horas" not in fila_tmp.columns:
        fila_tmp["Horas"] = 0

    fila_tmp["Horas"] = pd.to_numeric(fila_tmp["Horas"], errors="coerce").fillna(0)

    resumo_fila = (
        fila_tmp.groupby("Processo", dropna=False)
        .agg(
            Qtd_Fila=("Processo", "size"),
            Horas_Fila=("Horas", "sum")
        )
        .reset_index()
    )

    # ------------------------------------------------------------
    # BASE DE BAIXAS ATIVAS (BLINDADO)
    # ------------------------------------------------------------
    if (
        df_baixas_ativas is None
        or not isinstance(df_baixas_ativas, pd.DataFrame)
        or df_baixas_ativas.empty
        or "Processo" not in df_baixas_ativas.columns
    ):
        resumo_baixas = pd.DataFrame(columns=["Processo", "Qtd_Baixas_Ativas"])
    else:
        baixas_tmp = df_baixas_ativas.copy()
        baixas_tmp = _normalizar_coluna_processo(baixas_tmp, "Processo")

        resumo_baixas = (
            baixas_tmp.groupby("Processo", dropna=False)
            .agg(Qtd_Baixas_Ativas=("Processo", "size"))
            .reset_index()
        )

    # ------------------------------------------------------------
    # CONSOLIDAÇÃO
    # ------------------------------------------------------------
    df_dash = resumo_fila.merge(
        resumo_baixas,
        on="Processo",
        how="left"
    )

    df_dash["Qtd_Baixas_Ativas"] = df_dash["Qtd_Baixas_Ativas"].fillna(0).astype(int)
    df_dash["Qtd_Fila"] = df_dash["Qtd_Fila"].fillna(0).astype(int)
    df_dash["Horas_Fila"] = pd.to_numeric(df_dash["Horas_Fila"], errors="coerce").fillna(0)

    # ------------------------------------------------------------
    # CARGA TOTAL
    # ------------------------------------------------------------
    df_dash["Carga_Total"] = df_dash["Qtd_Fila"] + df_dash["Qtd_Baixas_Ativas"]

    # ------------------------------------------------------------
    # SCORE
    # ------------------------------------------------------------
    df_dash["Score"] = (
        (df_dash["Horas_Fila"] * 1.5) +
        (df_dash["Qtd_Fila"] * 1.0) +
        (df_dash["Qtd_Baixas_Ativas"] * 0.5)
    )

    # ------------------------------------------------------------
    # CLASSIFICAÇÃO
    # ------------------------------------------------------------
    def classificar_gargalo(score):
        if score >= 80:
            return "CRITICO"
        elif score >= 30:
            return "ATENCAO"
        else:
            return "CONTROLADO"

    df_dash["Status_Gargalo"] = df_dash["Score"].apply(classificar_gargalo)

    # ------------------------------------------------------------
    # ORDENAÇÃO
    # ------------------------------------------------------------
    df_dash = df_dash.sort_values(
        by=["Score", "Horas_Fila", "Qtd_Fila"],
        ascending=[False, False, False]
    ).reset_index(drop=True)

    df_dash["Ranking"] = df_dash.index + 1

    return df_dash



# ============================================================
# RESUMO DOS CARDS
# ============================================================

def resumo_cards_gargalos(df_dash):

    if df_dash is None or df_dash.empty:
        return {
            "total_processos": 0,
            "total_itens_fila": 0,
            "total_horas_fila": 0.0,
            "total_baixas_ativas": 0,
            "gargalo_critico": "-",
            "qtd_criticos": 0,
            "qtd_atencao": 0,
            "qtd_controlados": 0
        }

    gargalo_critico = df_dash.iloc[0]["Processo"]

    return {
        "total_processos": int(df_dash["Processo"].nunique()),
        "total_itens_fila": int(df_dash["Qtd_Fila"].sum()),
        "total_horas_fila": float(df_dash["Horas_Fila"].sum()),
        "total_baixas_ativas": int(df_dash["Qtd_Baixas_Ativas"].sum()),
        "gargalo_critico": gargalo_critico,
        "qtd_criticos": int((df_dash["Status_Gargalo"] == "CRITICO").sum()),
        "qtd_atencao": int((df_dash["Status_Gargalo"] == "ATENCAO").sum()),
        "qtd_controlados": int((df_dash["Status_Gargalo"] == "CONTROLADO").sum())
    }

# ============================================================
# ======================= GRÁFICOS ============================
# ============================================================
st.markdown("## 📈 Indicadores Visuais")
st.caption("Leitura gráfica da ocupação, carga, atraso e distribuição da produção.")

# ===============================
# 1) OCUPAÇÃO POR PROCESSO
# ===============================
st.subheader("📌 Ocupação por Processo (%)")

dem_plot = dem.copy()
dem_plot["Label"] = dem_plot["Ocupacao"].apply(lambda x: fmt_br_pct(x, 1))
dem_plot["Hover_Ocupacao"] = dem_plot["Ocupacao"].apply(lambda x: fmt_br_pct(x, 1))
dem_plot["Hover_Horas"] = dem_plot["Horas"].apply(lambda x: fmt_br_num(x, 1))
dem_plot["Hover_Capacidade"] = dem_plot["Capacidade"].apply(lambda x: fmt_br_num(x, 1))

fig = px.bar(
    dem_plot.sort_values(["Ordem_Periodo", "Processo"]),
    x="Periodo",
    y="Ocupacao",
    color="Processo",
    barmode="group",
    text="Label",
    custom_data=["Processo", "Hover_Ocupacao", "Hover_Horas", "Hover_Capacidade"]
)

fig.add_hline(y=100, line_dash="dash")

fig.update_traces(
    textposition="outside",
    hovertemplate=(
        "<b>%{x}</b><br>"
        "Processo: %{customdata[0]}<br>"
        "Ocupação: %{customdata[1]}<br>"
        "Carga: %{customdata[2]} h<br>"
        "Capacidade: %{customdata[3]} h"
        "<extra></extra>"
    )
)

fig.update_layout(
    yaxis_title="Ocupação (%)",
    xaxis_title="Período"
)

st.plotly_chart(fig, use_container_width=True)

# ============================================================
# 📊 UTILIZAÇÃO POR PROCESSO (BASE)
# ============================================================

# capacidade por processo no mês
def capacidade_processo(processo):
    recursos = MAQUINAS.get(processo, 0)
    if recursos <= 0:
        return 0
    return horas_mes * recursos * EFICIENCIA

dem_proc["Capacidade Processo"] = dem_proc["Processo"].apply(capacidade_processo)

# evita divisão por zero
dem_proc["Utilização (%)"] = np.where(
    dem_proc["Capacidade Processo"] > 0,
    (dem_proc["Horas"] / dem_proc["Capacidade Processo"]) * 100,
    0
)

dem_proc["Utilização (%)"] = dem_proc["Utilização (%)"].replace([np.inf, -np.inf], 0).fillna(0).round(1)

# classificação (opcional mas recomendado)
dem_proc["Faixa"] = np.where(
    dem_proc["Utilização (%)"] >= 100, "Crítico",
    np.where(dem_proc["Utilização (%)"] >= 80, "Atenção", "OK")
)

# ===============================
# 2) UTILIZAÇÃO POR PROCESSO
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

# ===============================
# 3) EVOLUÇÃO DA CARGA
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
# 4) DISTRIBUIÇÃO DE ATRASO
# ===============================
st.subheader("📊 Distribuição de Atraso por Faixa")

df_atraso = atrasos.copy()

if "Atraso (dias)" not in df_atraso.columns:
    df_atraso["Atraso (dias)"] = 0

df_atraso["Atraso (dias)"] = (
    pd.to_numeric(df_atraso["Atraso (dias)"], errors="coerce")
    .fillna(0)
    .clip(lower=0)
)

df_atraso = df_atraso[df_atraso["Atraso (dias)"] > 0].copy()

if not df_atraso.empty:

    max_atraso = int(df_atraso["Atraso (dias)"].max())
    bins = list(range(0, max_atraso + 3, 2))

    labels = []
    for i in range(len(bins)-1):
        inicio = bins[i] + 1
        fim = bins[i+1]
        labels.append(f"{inicio}-{fim}")

    df_atraso["Faixa"] = pd.cut(
        df_atraso["Atraso (dias)"],
        bins=bins,
        labels=labels,
        include_lowest=True
    )

    dist = (
        df_atraso.groupby("Faixa", observed=False)["PV"]
        .nunique()
        .reset_index(name="Quantidade")
    )

    dist = dist[dist["Quantidade"] > 0]

    dist["Ordem"] = dist["Faixa"].astype(str).str.extract(r"(\d+)").astype(int)
    dist = dist.sort_values("Ordem")

    fig_bar = px.bar(
        dist,
        x="Faixa",
        y="Quantidade",
        text="Quantidade",
        title="Escalonamento de Atraso (em dias)",
    )

    fig_bar.update_traces(textposition="outside")

    fig_bar.update_layout(
        xaxis_title="Faixa de Atraso (dias)",
        yaxis_title="Quantidade de PVs",
        height=450,
        showlegend=False,
        uniformtext_minsize=8,
        uniformtext_mode='hide'
    )

    st.plotly_chart(fig_bar, use_container_width=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Maior atraso", f"{df_atraso['Atraso (dias)'].max():.0f} dias")

    with col2:
        st.metric("Média", f"{df_atraso['Atraso (dias)'].mean():.1f} dias")

    with col3:
        st.metric("Total em atraso", f"{len(df_atraso)} PVs")

    faixa_select = st.selectbox(
        "Selecionar faixa para detalhamento",
        dist["Faixa"].astype(str).tolist(),
        key="faixa_bar_select"
    )

    detalhe = df_atraso[
        df_atraso["Faixa"].astype(str) == faixa_select
    ].copy()

    st.subheader("📋 Detalhamento da Faixa")

    st.dataframe(
        detalhe.sort_values("Atraso (dias)", ascending=False),
        use_container_width=True
    )

else:
    st.success("Nenhum atraso 🎉")

# ===============================
# 5) PV POR CLIENTE
# ===============================
st.subheader("📌 PV por Cliente")

pv_cliente_base = df_auditoria_pv.copy()

if cliente_sel != "Todos":
    pv_cliente_base = pv_cliente_base[pv_cliente_base["Cliente"] == cliente_sel].copy()

pv_cliente = pv_cliente_base.groupby("Cliente", as_index=False)["PV"].nunique()
total = pv_cliente["PV"].sum()

pv_cliente = pd.concat(
    [pv_cliente, pd.DataFrame([{"Cliente": "TOTAL", "PV": total}])],
    ignore_index=True
)

fig_cliente = px.bar(
    pv_cliente.sort_values("PV", ascending=False),
    x="Cliente",
    y="PV",
    text="PV"
)

fig_cliente.update_traces(textposition="outside")
fig_cliente.update_layout(
    xaxis_title="Cliente",
    yaxis_title="Quantidade de PVs"
)

st.plotly_chart(fig_cliente, use_container_width=True)

# ===============================
# 6) DISTRIBUIÇÃO DE STATUS (OPCIONAL)
# ===============================
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
# 7) COMPARAÇÃO CARGA x CAPACIDADE
# ===============================
st.subheader("📊 Carga x Capacidade por Processo")

base = dem_proc.copy()

# segurança numérica
for col in ["Horas", "Capacidade Processo"]:
    if col not in base.columns:
        base[col] = 0

    base[col] = pd.to_numeric(base[col], errors="coerce").fillna(0)

fig_comp = px.bar(
    base.sort_values("Horas", ascending=False),
    x="Processo",
    y=["Horas", "Capacidade Processo"],
    barmode="group",
    text_auto=True
)

# cores corretas
fig_comp.update_traces(
    selector=dict(name="Horas"),
    marker_color="#FF7A00"  # laranja
)

fig_comp.update_traces(
    selector=dict(name="Capacidade Processo"),
    marker_color="#1f77b4"  # azul
)

# rótulos em cima
fig_comp.update_traces(
    textposition="outside"
)

fig_comp.update_layout(
    yaxis_title="Horas",
    height=550,
    xaxis_title="Processo",
    uniformtext_minsize=8,
    uniformtext_mode="hide"
)

st.plotly_chart(fig_comp, use_container_width=True)


# ============================================================
# AUDITORIA DE PV 
# ============================================================

st.subheader("🧪 Auditoria de PV")

if not df_auditoria_pv.empty:

    df_auditoria_pv["PV"] = df_auditoria_pv["PV"].astype(str).str.strip()

    total_excel = pvs_totais_excel
    total_aps = df_auditoria_pv["PV"].nunique()
    total_auditadas = len(df_auditoria_pv)

    resumo_auditoria = (
        df_auditoria_pv["Status"]
        .value_counts()
        .reset_index()
    )
    resumo_auditoria.columns = ["Status", "Qtde"]

    def semaforo_auditoria(x):
        x = str(x).strip().upper()
        if x == "OK":
            return "🟢"
        elif x == "DIVERGENTE":
            return "🟡"
        elif x == "FALTANDO":
            return "🔴"
        elif x == "SEM PROCESSO VÁLIDO":
            return "🟠"
        return "⚪"

    df_auditoria_exibicao = df_auditoria_pv.copy()
    df_auditoria_exibicao["Semáforo"] = df_auditoria_exibicao["Status"].apply(semaforo_auditoria)

    qtd_ok = (df_auditoria_exibicao["Status"].astype(str).str.upper().str.strip() == "OK").sum()
    qtd_divergente = (df_auditoria_exibicao["Status"].astype(str).str.upper().str.strip() == "DIVERGENTE").sum()
    qtd_faltando = (df_auditoria_exibicao["Status"].astype(str).str.upper().str.strip() == "FALTANDO").sum()
    qtd_sem_processo = (df_auditoria_exibicao["Status"].astype(str).str.upper().str.strip() == "SEM PROCESSO VÁLIDO").sum()

    col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
    col1.metric("📄 PVs Excel", f"{total_excel:,.0f}")
    col2.metric("⚙️ PVs APS", f"{total_aps:,.0f}")
    col3.metric("🔍 Registros", f"{total_auditadas:,.0f}")
    col4.metric("🟢 OK", f"{qtd_ok:,.0f}")
    col5.metric("🟡 Divergente", f"{qtd_divergente:,.0f}")
    col6.metric("🔴 Faltando", f"{qtd_faltando:,.0f}")
    col7.metric("🟠 Sem Processo", f"{qtd_sem_processo:,.0f}")

    st.markdown("### 📊 Resumo da Auditoria")
    st.dataframe(
        resumo_auditoria,
        use_container_width=True,
        hide_index=True
    )

    st.markdown("### 🚨 PVs com inconsistência de processo")

    problemas_processo = df_auditoria_pv[
        df_auditoria_pv["Status"].astype(str).str.strip().str.upper() == "SEM PROCESSO VÁLIDO"
    ].copy()

    if not problemas_processo.empty:
        if "DATA_ENTREGA_APS" in problemas_processo.columns:
            problemas_processo["DATA_ENTREGA_APS"] = pd.to_datetime(
                problemas_processo["DATA_ENTREGA_APS"],
                errors="coerce"
            ).dt.strftime("%d/%m/%Y")

        colunas_problema = [
            "PV",
            "Cliente",
            "CODIGO_PV",
            "DATA_ENTREGA_APS",
            "Qtd",
            "Status",
            "Motivo"
        ]
        colunas_problema = [c for c in colunas_problema if c in problemas_processo.columns]

        st.dataframe(
            problemas_processo[colunas_problema]
            .sort_values(["PV"])
            .reset_index(drop=True),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.success("Nenhuma PV com inconsistência de processo encontrada ✅")

    st.markdown("### 📋 Detalhamento da Auditoria")
    colunas_auditoria = ["Semáforo"] + [c for c in df_auditoria_exibicao.columns if c != "Semáforo"]

    st.dataframe(
        df_auditoria_exibicao[colunas_auditoria]
        .sort_values(["Status", "PV"])
        .reset_index(drop=True),
        use_container_width=True,
        height=420
    )

else:
    st.info("Nenhuma auditoria de PV disponível.")

with st.expander("🧩 Roteiro de Fabricação por Código", expanded=False):

    base_roteiro = df_pv.copy()
    base_roteiro = base_roteiro[base_roteiro["CODIGO_KEY"] != ""].copy()

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

    processos_validos = [p for p in processos_ordenados if p in base_roteiro.columns]

    if len(processos_validos) == 0:
        st.warning("Nenhum processo válido encontrado na planilha.")
    else:
        roteiro = base_roteiro.groupby("CODIGO_KEY")[processos_validos].max().reset_index()

        for proc in processos_validos:
            roteiro[proc] = pd.to_numeric(roteiro[proc], errors="coerce").fillna(0)

        st.markdown("### 🔎 Consultar Roteiro por Código")

        col_r1, col_r2, col_r3 = st.columns([2, 1, 1])

        codigos = sorted(roteiro["CODIGO_KEY"].unique().tolist())
        codigo_sel = col_r1.selectbox("Selecione o código", codigos)

        roteiro_sel = roteiro[roteiro["CODIGO_KEY"] == codigo_sel].copy()

        roteiro_detalhado = roteiro_sel.melt(
            id_vars=["CODIGO_KEY"],
            value_vars=processos_validos,
            var_name="Processo",
            value_name="Tempo (min)"
        )

        roteiro_detalhado["Tempo (min)"] = pd.to_numeric(
            roteiro_detalhado["Tempo (min)"], errors="coerce"
        ).fillna(0)

        roteiro_detalhado = roteiro_detalhado[roteiro_detalhado["Tempo (min)"] > 0].copy()

        ordem = {p: i for i, p in enumerate(processos_ordenados)}
        roteiro_detalhado["Ordem"] = roteiro_detalhado["Processo"].map(ordem).fillna(999)
        roteiro_detalhado = roteiro_detalhado.sort_values("Ordem")

        roteiro_exibicao = roteiro_detalhado[["Processo", "Tempo (min)"]].copy()
        roteiro_exibicao["Tempo (h)"] = (roteiro_exibicao["Tempo (min)"] / 60).round(2)

        tempo_total_min = roteiro_exibicao["Tempo (min)"].sum()
        tempo_total_h = round(tempo_total_min / 60, 2)
        qtd_processos = len(roteiro_exibicao)

        col_r2.metric("🧩 Etapas", f"{qtd_processos:,.0f}")
        col_r3.metric("⏱️ Tempo Total (h)", f"{tempo_total_h:,.2f}")

        st.markdown(f"### 🛠️ Roteiro do Código: `{codigo_sel}`")

        if not roteiro_exibicao.empty:
            st.dataframe(
                roteiro_exibicao.reset_index(drop=True),
                use_container_width=True,
                height=420,
                hide_index=True
            )
        else:
            st.warning("Este código não possui tempos válidos nos processos mapeados.")

        with st.expander("📋 Base Completa de Roteiros", expanded=False):
            st.dataframe(
                roteiro,
                use_container_width=True,
                height=320,
                hide_index=True
            )

        from io import BytesIO

        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            roteiro.to_excel(writer, index=False)

        st.download_button(
            label="📥 Baixar Roteiros em Excel",
            data=buffer.getvalue(),
            file_name="roteiro_fabricacao.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )




# ============================================================
# SALVAR BAIXA OPERACIONAL (VERSÃO FINAL INTEGRADA APS)
# ============================================================
def salvar_baixa_operacional(base_path, registro_baixa):

    caminho = garantir_arquivo_baixas(base_path)

    # ------------------------------------------------------------
    # CARREGA BASE
    # ------------------------------------------------------------
    try:
        df_existente = pd.read_excel(caminho, dtype=str)
    except Exception:
        df_existente = pd.DataFrame(columns=COLUNAS_BAIXAS)

    df_existente = df_existente.copy()

    # ------------------------------------------------------------
    # NOVO REGISTRO
    # ------------------------------------------------------------
    novo = pd.DataFrame([registro_baixa])

    for col in COLUNAS_BAIXAS:
        if col not in novo.columns:
            novo[col] = ""

    # ------------------------------------------------------------
    # PADRONIZAÇÃO
    # ------------------------------------------------------------
    for col in ["PV", "CODIGO_PV", "Processo"]:
        novo[col] = (
            novo[col]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.upper()
        )

    novo["Cliente"] = novo["Cliente"].fillna("").astype(str).str.strip()

    novo["Status_Baixa"] = (
        novo["Status_Baixa"]
        .fillna("ATIVA")
        .astype(str)
        .str.strip()
        .str.upper()
    )

    novo["Horas"] = pd.to_numeric(novo["Horas"], errors="coerce").fillna(0)
    novo["Data_Baixa"] = pd.to_datetime(novo["Data_Baixa"], errors="coerce")

    # ------------------------------------------------------------
    # 🔥 CHAVE USANDO FUNÇÃO OFICIAL (CRÍTICO)
    # ------------------------------------------------------------
    novo["CHAVE_OPERACAO"] = novo.apply(
        lambda r: normalizar_chave_operacao(
            r["PV"], r["Processo"], r["CODIGO_PV"]
        ),
        axis=1
    )

    chave_nova = novo["CHAVE_OPERACAO"].iloc[0]

    # ------------------------------------------------------------
    # VALIDAÇÃO
    # ------------------------------------------------------------
    if not df_existente.empty:

        df_tmp = df_existente.copy()

        df_tmp["CHAVE_OPERACAO"] = df_tmp.apply(
            lambda r: normalizar_chave_operacao(
                r["PV"], r["Processo"], r["CODIGO_PV"]
            ),
            axis=1
        )

        df_tmp["Status_Baixa"] = (
            df_tmp["Status_Baixa"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.upper()
        )

        registros = df_tmp[df_tmp["CHAVE_OPERACAO"] == chave_nova]

        if not registros.empty:

            registros_ativos = registros[
                registros["Status_Baixa"].isin(["ATIVA", "TERCEIRIZADA"])
            ]

            if not registros_ativos.empty:

                log = novo.copy()
                log["Status_Baixa"] = "TENTATIVA_DUPLICADA"
                log["Motivo_Estorno"] = "Tentativa bloqueada - já existe baixa ativa"
                log["Data_Baixa"] = pd.Timestamp.now()

                df_existente = pd.concat([df_existente, log], ignore_index=True)
                df_existente.to_excel(caminho, index=False)

                return {
                    "ok": False,
                    "erro": "Operação já possui baixa ativa",
                    "tipo": "duplicidade"
                }

    # ------------------------------------------------------------
    # SALVAMENTO
    # ------------------------------------------------------------
    df_final = pd.concat([df_existente, novo], ignore_index=True)

    try:
        df_final.to_excel(caminho, index=False)
        return {"ok": True}

    except Exception as e:
        return {
            "ok": False,
            "erro": str(e),
            "tipo": "erro_gravacao"
        }




# ============================================================
# HISTÓRICOS
# ============================================================

def historico_baixas_completo(df_baixas):

    if df_baixas is None or df_baixas.empty:
        return pd.DataFrame(columns=COLUNAS_BAIXAS + ["CHAVE_OPERACAO"])

    return _padronizar_df_baixas(df_baixas)


def historico_baixas_ativas(df_baixas):

    if df_baixas is None or df_baixas.empty:
        return pd.DataFrame(columns=COLUNAS_BAIXAS + ["CHAVE_OPERACAO"])

    df_tmp = _padronizar_df_baixas(df_baixas)

    return df_tmp[
        df_tmp["Status_Baixa"].isin(["ATIVA", "TERCEIRIZADA"])
    ].copy()


# ============================================================
# ESTORNO
# ============================================================

def estornar_baixa_operacional(base_path, pv, processo, codigo_pv="", motivo_estorno=""):

    caminho = garantir_arquivo_baixas(base_path)

    try:
        df_baixas = pd.read_excel(caminho, dtype=str)
    except Exception as e:
        return False, f"Erro ao abrir histórico: {e}"

    df_baixas = _padronizar_df_baixas(df_baixas)

    chave = (
        str(pv).strip().upper() + "||" +
        str(processo).strip().upper() + "||" +
        str(codigo_pv).strip().upper()
    )

    filtro = (
        (df_baixas["CHAVE_OPERACAO"] == chave) &
        (df_baixas["Status_Baixa"].isin(["ATIVA", "TERCEIRIZADA"]))
    )

    if not filtro.any():
        return False, "Nenhuma baixa ativa encontrada."

    idx = df_baixas[filtro].index[0]

    df_baixas.at[idx, "Status_Baixa"] = "ESTORNADA"
    df_baixas.at[idx, "Data_Estorno"] = pd.Timestamp.now().strftime("%d/%m/%Y %H:%M")
    df_baixas.at[idx, "Motivo_Estorno"] = str(motivo_estorno).strip()

    with pd.ExcelWriter(caminho, engine="openpyxl", mode="w") as writer:
        df_baixas[COLUNAS_BAIXAS].to_excel(writer, index=False)

    try:
        _criar_backup()
    except Exception:
        pass

    return True, "Baixa estornada com sucesso."


# ============================================================
# HISTÓRICO (SEM DUPLICAÇÃO DE FUNÇÕES)
# ============================================================

def historico_baixas_completo(df_baixas):
    """
    Retorna o histórico completo consolidado (ativas + terceirizadas + estornadas).
    """
    if df_baixas.empty:
        return pd.DataFrame(columns=COLUNAS_BAIXAS + ["CHAVE_OPERACAO"])

    return _padronizar_df_baixas(df_baixas.copy())





# ===============================
# AJUSTES DOS GARGALOS CORRETOS
# ===============================

df_base_aps = df_operacional.copy()

df_base_gargalo = df_base_aps[
    df_base_aps["Status Operacional"] == "⏳ Pendente"
].copy()




# ===============================
# COLAPSO DO GARGALO (BASE EXECUTIVA)
# ===============================

# 🔒 GARANTIA DE COLUNAS (EVITA KEYERROR)
for col in ["Fila Acumulada (h)", "Fila (dias)"]:
    if col not in df.columns:
        df[col] = 0

fila_resumo = (
    df.groupby("Processo", as_index=False)
    .agg({
        "Fila Acumulada (h)": "max",
        "Fila (dias)": "max"
    })
    .rename(columns={
        "Fila Acumulada (h)": "Fila Acumulada Max (h)",
        "Fila (dias)": "Fila Max (dias)"
    })
)

# 🔒 GARANTIA DE COLUNAS NO DEM
for col in ["Horas", "Capacidade", "Ocupacao", "Saldo (h)"]:
    if col not in dem.columns:
        dem[col] = 0

dem_colapso = dem.groupby("Processo", as_index=False).agg({
    "Horas": "sum",
    "Capacidade": "sum",
    "Ocupacao": "max",
    "Saldo (h)": "sum"
})

dem_colapso = dem_colapso.merge(fila_resumo, on="Processo", how="left")

# 🔒 GARANTE VALORES
dem_colapso["Fila Acumulada Max (h)"] = dem_colapso["Fila Acumulada Max (h)"].fillna(0)
dem_colapso["Fila Max (dias)"] = dem_colapso["Fila Max (dias)"].fillna(0)

# ===============================
# CLASSIFICAÇÃO DE COLAPSO
# ===============================
dem_colapso["Semáforo Colapso"] = np.select(
    [
        (dem_colapso["Ocupacao"] >= 120) | (dem_colapso["Fila Max (dias)"] >= 10) | (dem_colapso["Saldo (h)"] < -40),
        (dem_colapso["Ocupacao"] >= 100) | (dem_colapso["Fila Max (dias)"] >= 6) | (dem_colapso["Saldo (h)"] < 0),
        (dem_colapso["Ocupacao"] >= 85) | (dem_colapso["Fila Max (dias)"] >= 3)
    ],
    [
        "🔥 Colapso Severo",
        "🔴 Colapso",
        "🟡 Atenção"
    ],
    default="🟢 Sob Controle"
)

# ===============================
# RANKING
# ===============================
ranking_colapso = dem_colapso.sort_values(
    by=["Ocupacao", "Fila Max (dias)", "Fila Acumulada Max (h)"],
    ascending=[False, False, False]
).reset_index(drop=True)




# ===============================
# CAPACIDADE POR PROCESSO
# ===============================

# 🔒 Garantias críticas
if dem_proc is None or dem_proc.empty:
    st.error("Erro: dem_proc vazio.")
    st.stop()

if "Processo" not in dem_proc.columns:
    st.error("Erro: coluna 'Processo' não encontrada em dem_proc.")
    st.stop()

if "Horas" not in dem_proc.columns:
    dem_proc["Horas"] = 0

# -------------------------------
# CÁLCULO DE CAPACIDADE
# -------------------------------
if tipo == "Mensal":

    capacidade_proc = {
        proc: horas_uteis_mes(ano_ref, mes_ref) * MAQUINAS.get(proc, 0) * EFICIENCIA
        for proc in processos
    }

    dem_proc["Capacidade Processo"] = dem_proc["Processo"].map(capacidade_proc)

else:
    if dem is not None and not dem.empty and "Capacidade" in dem.columns:
        capacidade_proc = (
            dem.groupby("Processo", as_index=False)["Capacidade"]
            .sum()
            .rename(columns={"Capacidade": "Capacidade Processo"})
        )

        dem_proc = dem_proc.merge(capacidade_proc, on="Processo", how="left")

    else:
        dem_proc["Capacidade Processo"] = 0

# -------------------------------
# BLINDAGEM DA CAPACIDADE
# -------------------------------
if "Capacidade Processo" not in dem_proc.columns:
    dem_proc["Capacidade Processo"] = 0

dem_proc["Capacidade Processo"] = pd.to_numeric(
    dem_proc["Capacidade Processo"], errors="coerce"
).fillna(0)

# -------------------------------
# CÁLCULO DE UTILIZAÇÃO
# -------------------------------
dem_proc["Utilização (%)"] = np.where(
    dem_proc["Capacidade Processo"] > 0,
    (dem_proc["Horas"] / dem_proc["Capacidade Processo"]) * 100,
    0
)

dem_proc["Utilização (%)"] = (
    dem_proc["Utilização (%)"]
    .replace([float("inf"), -float("inf")], 0)
    .fillna(0)
    .round(0)
    .astype(int)
)

# -------------------------------
# CLASSIFICAÇÃO
# -------------------------------
def faixa_utilizacao(x):
    if x >= 100:
        return "Crítico"
    elif x >= 80:
        return "Atenção"
    else:
        return "OK"

dem_proc["Faixa"] = dem_proc["Utilização (%)"].apply(faixa_utilizacao)


# ============================================================
# 🔥 ALERTA DE COLAPSO FUTURO (APS INTELIGENTE)
# ============================================================

df_colapso = dem_proc.copy()

if (
    not df_colapso.empty
    and "Capacidade Processo" in df_colapso.columns
    and "Horas" in df_colapso.columns
):

    # 🔒 garante numérico
    df_colapso["Horas"] = pd.to_numeric(
        df_colapso["Horas"], errors="coerce"
    ).fillna(0)

    df_colapso["Capacidade Processo"] = pd.to_numeric(
        df_colapso["Capacidade Processo"], errors="coerce"
    ).fillna(0)

    # 🔥 dias de fila real (base APS)
    df_colapso["Dias de Fila"] = np.where(
        df_colapso["Capacidade Processo"] > 0,
        df_colapso["Horas"] / df_colapso["Capacidade Processo"],
        0
    )

    # 🔥 classificação futura (mais inteligente que Faixa)
    df_colapso["Risco Futuro"] = np.select(
        [
            df_colapso["Dias de Fila"] >= 10,
            df_colapso["Dias de Fila"] >= 5,
            df_colapso["Dias de Fila"] >= 3
        ],
        [
            "🔥 Colapso iminente",
            "🔴 Alto risco",
            "🟡 Atenção"
        ],
        default="🟢 Sob controle"
    )

    # 🔥 ordena para uso executivo
    df_colapso = df_colapso.sort_values(
        "Dias de Fila",
        ascending=False
    ).reset_index(drop=True)

else:
    df_colapso = pd.DataFrame(
        columns=["Processo", "Dias de Fila", "Risco Futuro"]
    )




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


# ============================================================
# ===================== ANÁLISE OPERACIONAL ==================
# ============================================================
with st.expander("🏭 Análise Operacional Detalhada", expanded=False):

    st.caption("Visões complementares da carga operacional por processo e cliente.")

    # ===============================
    # BACKLOG POR PROCESSO
    # ===============================
    st.subheader("📊 Backlog por Processo")

    backlog = df.groupby("Processo", as_index=False).agg(
        PVs=("PV", "nunique"),
        Horas=("Horas", "sum")
    )

    backlog["Horas"] = backlog["Horas"].round(1)

    fig_backlog = px.bar(
        backlog.sort_values("Horas", ascending=False),
        x="Processo",
        y="Horas",
        text="Horas"
    )

    fig_backlog.update_traces(
        marker_color="#FF7A00",
        texttemplate="%{y:.1f}",
        textposition="outside",
        textfont=dict(size=11, color="white")
    )

    fig_backlog.update_layout(
        xaxis_title="Processo",
        yaxis_title="Horas em Backlog",
        height=550
    )

    st.plotly_chart(fig_backlog, use_container_width=True, key="grafico_backlog_processo")

    # ===============================
    # CARGA POR CLIENTE
    # ===============================
    st.subheader("📊 Carga por Cliente")

    hoje = pd.Timestamp.today().normalize()

    base_op = df.copy()

    if "ENTREGA" in base_op.columns:
        base_op["ENTREGA"] = pd.to_datetime(base_op["ENTREGA"], errors="coerce")
        base_op["Dias para Entrega"] = (base_op["ENTREGA"] - hoje).dt.days
    else:
        base_op["Dias para Entrega"] = None

    carga_cliente = base_op.groupby("Cliente", as_index=False).agg(
        Horas=("Horas", "sum"),
        PVs=("PV", "nunique")
    )

    carga_cliente["Horas"] = carga_cliente["Horas"].round(1)

    fig_cliente_carga = px.bar(
        carga_cliente.sort_values("Horas", ascending=False),
        x="Cliente",
        y="Horas",
        text="Horas"
    )

    fig_cliente_carga.update_traces(
        marker_color="#1f3b73",
        texttemplate="%{y:.1f}",
        textposition="outside",
        textfont=dict(color="white")
    )

    fig_cliente_carga.update_layout(height=500)

    st.plotly_chart(fig_cliente_carga, use_container_width=True)

# ============================================================
# ===================== PAINEL OPERACIONAL ===================
# ============================================================
st.markdown("## ⚡ Painel Operacional")
st.caption("Prioridades imediatas de produção — foco no que precisa ser feito agora.")

base_op = df.copy()
hoje = pd.Timestamp.today().normalize()

if "DATA_ENTREGA_APS" in base_op.columns:
    base_op["DATA_ENTREGA_APS"] = pd.to_datetime(
        base_op["DATA_ENTREGA_APS"], errors="coerce"
    )

    base_op["Dias para Entrega"] = (
        base_op["DATA_ENTREGA_APS"] - hoje
    ).dt.days

    base_op["ENTREGA"] = base_op["DATA_ENTREGA_APS"]
else:
    base_op["Dias para Entrega"] = None
    base_op["ENTREGA"] = pd.NaT

# ===============================
# PVs QUE VENCEM HOJE
# ===============================
st.subheader("📅 PVs que vencem HOJE")

pvs_hoje = base_op[base_op["Dias para Entrega"] == 0].copy()

if not pvs_hoje.empty:
    pvs_hoje["Horas"] = pd.to_numeric(pvs_hoje["Horas"], errors="coerce").fillna(0).round(1)
    pvs_hoje["ENTREGA"] = pd.to_datetime(
        pvs_hoje["ENTREGA"], errors="coerce"
    ).dt.strftime("%d/%m/%Y")

    st.dataframe(
        pvs_hoje.sort_values("Horas", ascending=False),
        use_container_width=True
    )
else:
    st.success("Nenhuma PV vence hoje ✅")

# ===============================
# TOP 10 PVS MAIS CRÍTICAS
# ===============================
st.subheader("🔥 Top 10 PVs mais críticas")

criticas = base_op.copy()

if "Horas" in criticas.columns:
    criticas["Horas"] = pd.to_numeric(criticas["Horas"], errors="coerce").fillna(0)

if "Dias para Entrega" not in criticas.columns:
    criticas["Dias para Entrega"] = None

criticas = criticas.sort_values(
    ["Dias para Entrega", "Horas"],
    ascending=[True, False]
).head(10)

criticas["Horas"] = criticas["Horas"].round(1)

if "ENTREGA" in criticas.columns:
    criticas["ENTREGA"] = pd.to_datetime(
        criticas["ENTREGA"], errors="coerce"
    ).dt.strftime("%d/%m/%Y")

st.dataframe(criticas, use_container_width=True)

# ===============================
# PVS URGENTES DA SEMANA
# ===============================
st.subheader("🚨 PVs Urgentes da Semana")

pvs_urgentes = base_op.copy()

if "Dias para Entrega" in pvs_urgentes.columns:
    pvs_urgentes["Semáforo"] = pvs_urgentes["Dias para Entrega"].apply(semaforo_entrega)

    urgentes = pvs_urgentes[
        pvs_urgentes["Dias para Entrega"].between(-9999, 7, inclusive="both")
    ].copy()

    if not urgentes.empty:
        urgentes["Horas"] = pd.to_numeric(urgentes["Horas"], errors="coerce").fillna(0).round(1)

        if "ENTREGA" in urgentes.columns:
            urgentes["ENTREGA"] = pd.to_datetime(
                urgentes["ENTREGA"], errors="coerce"
            ).dt.strftime("%d/%m/%Y")

        colunas_urgentes = [
            "Semáforo",
            "PV",
            "Cliente",
            "CODIGO_PV",
            "Processo",
            "Horas",
            "Dias para Entrega",
            "ENTREGA"
        ]
        colunas_urgentes = [c for c in colunas_urgentes if c in urgentes.columns]

        st.dataframe(
            urgentes[colunas_urgentes].sort_values(
                ["Dias para Entrega", "Horas"],
                ascending=[True, False]
            ),
            use_container_width=True
        )
    else:
        st.success("Nenhuma PV urgente para os próximos 7 dias ✅")
else:
    st.info("Não foi possível gerar o painel de urgência porque a coluna DATA_ENTREGA_APS não está disponível.")

# ============================================================
# ===================== FILA POR PROCESSO ====================
# ============================================================
st.subheader("📌 Fila por Processo")

fila = df.copy()

if "ENTREGA" in fila.columns:
    fila["ENTREGA"] = pd.to_datetime(fila["ENTREGA"], errors="coerce")
    fila["Dias para Entrega"] = (fila["ENTREGA"] - hoje).dt.days
else:
    fila["Dias para Entrega"] = None

fila["Semáforo"] = fila["Dias para Entrega"].apply(semaforo_entrega)

# ---------------------------------------
# FILTROS
# ---------------------------------------
col_f1, col_f2, col_f3 = st.columns(3)

processos_fila = sorted(fila["Processo"].dropna().astype(str).str.strip().unique().tolist())
processo_fila_sel = col_f1.selectbox("Filtrar por Processo", ["Todos"] + processos_fila)

pvs_fila = sorted(fila["PV"].dropna().astype(str).str.strip().unique().tolist())
pv_fila_sel = col_f2.selectbox("Filtrar por PV específica", ["Todas"] + pvs_fila)

tipo_corte_sel = col_f3.selectbox(
    "Filtrar por Tipo de Corte",
    ["Todos", "Apenas Corte", "Apenas Serra", "Apenas Laser", "Apenas Plasma"]
)

if processo_fila_sel != "Todos":
    fila = fila[fila["Processo"].astype(str).str.strip() == processo_fila_sel].copy()

if pv_fila_sel != "Todas":
    fila = fila[fila["PV"].astype(str).str.strip() == pv_fila_sel].copy()

fila["Processo"] = fila["Processo"].astype(str).str.strip().str.upper()

if tipo_corte_sel == "Apenas Corte":
    fila = fila[fila["Processo"].str.contains("CORTE", na=False)].copy()
elif tipo_corte_sel == "Apenas Serra":
    fila = fila[fila["Processo"] == "CORTE - SERRA"].copy()
elif tipo_corte_sel == "Apenas Laser":
    fila = fila[fila["Processo"] == "CORTE - LASER"].copy()
elif tipo_corte_sel == "Apenas Plasma":
    fila = fila[fila["Processo"] == "CORTE - PLASMA"].copy()

# ---------------------------------------
# KPIs
# ---------------------------------------
col_k1, col_k2, col_k3 = st.columns(3)
col_k1.metric("PVs na Fila", fila["PV"].astype(str).str.strip().nunique())
col_k2.metric("Processos na Fila", fila["Processo"].nunique())
col_k3.metric("Horas na Fila", f"{pd.to_numeric(fila['Horas'], errors='coerce').fillna(0).sum():.1f} h")

st.markdown("### 📋 PVs na Fila")

fila_detalhe = fila.copy()
fila_detalhe["Horas"] = pd.to_numeric(fila_detalhe["Horas"], errors="coerce").fillna(0).round(1)

if "ENTREGA" in fila_detalhe.columns:
    fila_detalhe["ENTREGA"] = pd.to_datetime(fila_detalhe["ENTREGA"], errors="coerce")
    fila_detalhe["ENTREGA"] = fila_detalhe["ENTREGA"].dt.strftime("%d/%m/%Y")

colunas_fila = ["Semáforo","PV","Cliente","CODIGO_PV","Processo","Horas","Dias para Entrega","ENTREGA"]
colunas_fila = [c for c in colunas_fila if c in fila_detalhe.columns]

fila_detalhe_exib = fila_detalhe[colunas_fila].copy().reset_index(drop=True)

st.dataframe(fila_detalhe_exib, use_container_width=True, hide_index=True)


# ============================================================
# ✂️ BAIXAS DE CORTE (VERSÃO FINAL ESTÁVEL)
# ============================================================

st.markdown("### ⚡ Módulo de Corte — Baixa, Lote e Estorno")

# ------------------------------------------------------------
# BASE DE CORTE
# ------------------------------------------------------------
base_corte = df_operacional.copy()
base_corte["Processo"] = base_corte["Processo"].astype(str).str.upper().str.strip()

base_corte = base_corte[
    base_corte["Processo"].str.contains("SERRA|LASER|PLASMA", na=False)
].copy()

if base_corte.empty:
    st.info("Nenhuma operação de corte encontrada.")
else:

    base_corte["Horas"] = pd.to_numeric(base_corte["Horas"], errors="coerce").fillna(0).round(1)

    base_corte = base_corte.reset_index(drop=True)
    base_corte["ID_UNICO"] = base_corte.index.astype(str)

    base_corte["LABEL"] = (
        "PV " + base_corte["PV"].astype(str) +
        " | " + base_corte["Processo"].astype(str) +
        " | " + base_corte["CODIGO_PV"].astype(str) +
        " | " + base_corte["Horas"].astype(str) + " h"
    )

    base_corte_pendente = base_corte[
        base_corte["Status Operacional"] == "⏳ Pendente"
    ].copy()

    if base_corte_pendente.empty:
        st.info("Nenhuma operação pendente de corte.")
    else:

        opcoes = base_corte_pendente["LABEL"].tolist()

        # ------------------------------------------------------------
        # CONTROLE DE RESET
        # ------------------------------------------------------------
        if "reset_corte_unitario" not in st.session_state:
            st.session_state["reset_corte_unitario"] = False

        if "reset_corte_lote" not in st.session_state:
            st.session_state["reset_corte_lote"] = False

        if st.session_state["reset_corte_unitario"]:
            if opcoes:
                st.session_state["corte_unitario"] = opcoes[0]
            st.session_state["reset_corte_unitario"] = False

        if st.session_state["reset_corte_lote"]:
            st.session_state["corte_lote"] = []
            st.session_state["reset_corte_lote"] = False

        # ------------------------------------------------------------
        # 🔹 BAIXA UNITÁRIA
        # ------------------------------------------------------------
        st.markdown("#### 🔹 Baixa Unitária")

        escolha = st.selectbox("Operação", opcoes, key="corte_unitario")

        linha_sel = base_corte_pendente[
            base_corte_pendente["LABEL"] == escolha
        ]

        if not linha_sel.empty:
            linha = linha_sel.iloc[0]

            if st.button("💾 Confirmar Baixa", key="btn_corte_unitario"):

                resultado = salvar_baixa_operacional(BASE_PATH, {
                    "PV": linha["PV"],
                    "Cliente": linha.get("Cliente", ""),
                    "CODIGO_PV": linha["CODIGO_PV"],
                    "Processo": linha["Processo"],
                    "Horas": linha["Horas"],
                    "Data_Baixa": pd.Timestamp.now(),
                    "Usuario": "Sistema",
                    "Observacao": "UNITARIO_CORTE",
                    "Status_Baixa": "ATIVA",
                    "Data_Estorno": "",
                    "Motivo_Estorno": ""
                })

                if resultado.get("ok"):

                    st.cache_data.clear()

                    caminho_baixas = garantir_arquivo_baixas(BASE_PATH)
                    file_mtime_baixas = os.path.getmtime(caminho_baixas)

                    df_baixas = carregar_baixas_operacionais(BASE_PATH, file_mtime_baixas)

                    df_baixas_ativas = df_baixas[
                        df_baixas["Status_Baixa"].isin(["ATIVA", "TERCEIRIZADA"])
                    ].copy()

                    st.session_state["df_baixas_ativas"] = df_baixas_ativas

                    st.session_state["reset_corte_unitario"] = True

                    st.success("Baixa registrada com sucesso")

                    st.rerun()

                else:
                    st.error(resultado.get("erro", "Erro ao registrar baixa"))

        st.divider()

        # ------------------------------------------------------------
        # 📦 BAIXA EM LOTE
        # ------------------------------------------------------------
        st.markdown("#### 📦 Baixa em Lote")

        selecao = st.multiselect("Selecionar operações", opcoes, key="corte_lote")

        if selecao:
            if st.button("📦 Baixar Corte em Lote", key="btn_corte_lote"):

                sucessos = 0
                erros = 0

                for label in selecao:
                    linha = base_corte_pendente[
                        base_corte_pendente["LABEL"] == label
                    ].iloc[0]

                    resultado = salvar_baixa_operacional(BASE_PATH, {
                        "PV": linha["PV"],
                        "Cliente": linha.get("Cliente", ""),
                        "CODIGO_PV": linha["CODIGO_PV"],
                        "Processo": linha["Processo"],
                        "Horas": linha["Horas"],
                        "Data_Baixa": pd.Timestamp.now(),
                        "Usuario": "Sistema",
                        "Observacao": "LOTE_CORTE",
                        "Status_Baixa": "ATIVA",
                        "Data_Estorno": "",
                        "Motivo_Estorno": ""
                    })

                    if resultado.get("ok"):
                        sucessos += 1
                    else:
                        erros += 1

                # 🔥 RECARREGA BASE
                st.cache_data.clear()

                caminho_baixas = garantir_arquivo_baixas(BASE_PATH)
                file_mtime_baixas = os.path.getmtime(caminho_baixas)

                df_baixas = carregar_baixas_operacionais(BASE_PATH, file_mtime_baixas)

                df_baixas_ativas = df_baixas[
                    df_baixas["Status_Baixa"].isin(["ATIVA", "TERCEIRIZADA"])
                ].copy()

                st.session_state["df_baixas_ativas"] = df_baixas_ativas

                if sucessos:
                    st.session_state["reset_corte_lote"] = True

                    st.success(f"{sucessos} operações baixadas")

                    # ✅ CORRETO: NÃO mexer direto no multiselect
                    st.rerun()

                if erros:
                    st.warning(f"{erros} não foram baixadas")

# =========================================================
# DASHBOARD DO CORTE (CORRIGIDO DEFINITIVO)
# =========================================================
st.markdown("## 📊 Dashboard do Corte")
st.caption("Indicadores operacionais e gerenciais do setor de corte.")

# ---------------------------------------
# BASES DO DASHBOARD DE CORTE
# ---------------------------------------

# 🔥 USA BASE CORRETA (COM STATUS)
fila_corte_dash = df_operacional.copy()

fila_corte_dash["PROC_UPPER"] = fila_corte_dash["Processo"].astype(str).str.strip().str.upper()

fila_corte_dash = fila_corte_dash[
    (
        fila_corte_dash["PROC_UPPER"].str.contains("SERRA", na=False) |
        fila_corte_dash["PROC_UPPER"].str.contains("LASER", na=False) |
        fila_corte_dash["PROC_UPPER"].str.contains("PLASMA", na=False)
    )
].copy()

# 🔥 REMOVE O QUE JÁ FOI BAIXADO
fila_corte_dash = fila_corte_dash[
    fila_corte_dash["Status Operacional"] == "⏳ Pendente"
].copy()

fila_corte_dash["Horas"] = pd.to_numeric(fila_corte_dash["Horas"], errors="coerce").fillna(0)

# 🔥 HISTÓRICO REAL
hist_corte_dash = df_baixas.copy()

if not hist_corte_dash.empty:

    hist_corte_dash["PROC_UPPER"] = hist_corte_dash["Processo"].astype(str).str.strip().str.upper()
    hist_corte_dash["STATUS_UPPER"] = hist_corte_dash["Status_Baixa"].astype(str).str.strip().str.upper()

    hist_corte_dash = hist_corte_dash[
        (
            hist_corte_dash["PROC_UPPER"].str.contains("SERRA", na=False) |
            hist_corte_dash["PROC_UPPER"].str.contains("LASER", na=False) |
            hist_corte_dash["PROC_UPPER"].str.contains("PLASMA", na=False)
        )
    ].copy()

    hist_corte_dash["Horas"] = pd.to_numeric(hist_corte_dash["Horas"], errors="coerce").fillna(0)
    hist_corte_dash["Data_Baixa"] = pd.to_datetime(hist_corte_dash["Data_Baixa"], errors="coerce")

# ---------------------------------------
# KPIs DO CORTE
# ---------------------------------------
ops_fila_corte = len(fila_corte_dash)
horas_fila_corte = fila_corte_dash["Horas"].sum()

if not hist_corte_dash.empty:

    baixas_ativas_corte = hist_corte_dash[
        hist_corte_dash["STATUS_UPPER"].isin(["ATIVA", "TERCEIRIZADA"])
    ].copy()

    baixas_estornadas_corte = hist_corte_dash[
        hist_corte_dash["STATUS_UPPER"] == "ESTORNADA"
    ].copy()

    qtd_baixadas_corte = len(baixas_ativas_corte)
    horas_baixadas_corte = baixas_ativas_corte["Horas"].sum()
    qtd_estornadas_corte = len(baixas_estornadas_corte)

else:
    qtd_baixadas_corte = 0
    horas_baixadas_corte = 0
    qtd_estornadas_corte = 0

col_dc1, col_dc2, col_dc3, col_dc4, col_dc5 = st.columns(5)
col_dc1.metric("📋 Ops na Fila", f"{ops_fila_corte:,.0f}")
col_dc2.metric("⏱️ Horas na Fila", f"{horas_fila_corte:,.1f} h")
col_dc3.metric("✅ Baixas Ativas", f"{qtd_baixadas_corte:,.0f}")
col_dc4.metric("🏁 Horas Baixadas", f"{horas_baixadas_corte:,.1f} h")
col_dc5.metric("🔄 Estornos", f"{qtd_estornadas_corte:,.0f}")



# ============================================================
# =========== CONTROLE DOS 3 PRINCIPAIS GARGALOS =============
# ============================================================

# 🔒 GARANTE COLUNA CRÍTICA
if "Status Operacional" not in df_operacional.columns:
    df_operacional["Status Operacional"] = "⏳ Pendente"

# 🔥 BASE CORRETA DE GARGALO
df_base_aps = df_operacional.copy()

df_base_gargalo = df_base_aps[
    df_base_aps["Status Operacional"] == "⏳ Pendente"
].copy()

# 🔒 GARANTE COLUNAS ESSENCIAIS
for col in ["PV", "Processo", "CODIGO_PV", "Horas"]:
    if col not in df_base_gargalo.columns:
        df_base_gargalo[col] = ""

with st.expander("🎯 Controle dos 3 Principais Gargalos", expanded=True):

    st.subheader("🏭 Operações mais carregadas do APS")
    st.caption("Controle operacional dos 3 processos mais carregados com baixa direta de operação concluída.")

    gargalos_top3 = (
        df_base_gargalo.groupby("Processo", as_index=False)
        .agg(Horas_Pendentes=("Horas", "sum"), PVs_Pendentes=("PV", "nunique"))
        .merge(
            dem_proc[["Processo", "Capacidade Processo", "Utilização (%)"]],
            on="Processo",
            how="left"
        )
    )

    # 🔥 CORREÇÃO REAL DO GARGALO
    gargalos_top3["Capacidade Processo"] = pd.to_numeric(gargalos_top3["Capacidade Processo"], errors="coerce").fillna(0)
    gargalos_top3["Horas_Pendentes"] = pd.to_numeric(gargalos_top3["Horas_Pendentes"], errors="coerce").fillna(0)

    gargalos_top3["Carga_Relativa"] = np.where(
        gargalos_top3["Capacidade Processo"] > 0,
        gargalos_top3["Horas_Pendentes"] / gargalos_top3["Capacidade Processo"],
        0
    )

    # 🔥 ORDENAÇÃO CORRETA (GARGALO REAL)
    gargalos_top3 = (
        gargalos_top3
        .sort_values(["Carga_Relativa", "Horas_Pendentes"], ascending=[False, False])
        .head(3)
        .reset_index(drop=True)
    )

    if gargalos_top3.empty:
        st.info("Nenhum gargalo pendente encontrado no APS.")
    else:
        gargalos_top3["Capacidade Processo"] = gargalos_top3["Capacidade Processo"].round(1)
        gargalos_top3["Horas_Pendentes"] = gargalos_top3["Horas_Pendentes"].round(1)
        gargalos_top3["Utilização (%)"] = pd.to_numeric(gargalos_top3["Utilização (%)"], errors="coerce").fillna(0).round(0).astype(int)
        gargalos_top3["Ranking"] = gargalos_top3.index + 1

        gargalos_top3["Dias de Fila"] = np.where(
            gargalos_top3["Capacidade Processo"] > 0,
            (gargalos_top3["Horas_Pendentes"] / gargalos_top3["Capacidade Processo"]).round(1),
            np.nan
        )

        st.markdown("### 📌 Top 3 Gargalos Atuais")

        exib_top3 = gargalos_top3.copy()
        exib_top3["Horas Pendentes (h)"] = exib_top3["Horas_Pendentes"].apply(lambda x: fmt_br_num(x, 1))
        exib_top3["Capacidade Processo (h)"] = exib_top3["Capacidade Processo"].apply(lambda x: fmt_br_num(x, 1))
        exib_top3["Utilização (%)"] = exib_top3["Utilização (%)"].apply(lambda x: f"{int(x)}%")
        exib_top3["Dias de Fila"] = exib_top3["Dias de Fila"].apply(
            lambda x: f"{fmt_br_num(x, 1)} dias" if pd.notna(x) else "-"
        )

        st.dataframe(
            exib_top3[
                ["Ranking", "Processo", "Horas Pendentes (h)", "PVs_Pendentes",
                 "Capacidade Processo (h)", "Dias de Fila", "Utilização (%)"]
            ].rename(columns={"PVs_Pendentes": "PVs Pendentes"}),
            use_container_width=True,
            hide_index=True
        )

        st.divider()

        processos_top3 = gargalos_top3["Processo"].dropna().astype(str).tolist()

        base_gargalos = df_base_gargalo[
            df_base_gargalo["Processo"].isin(processos_top3)
        ].copy()

        for col in ["PV", "Processo", "CODIGO_PV"]:
            if col not in base_gargalos.columns:
                base_gargalos[col] = ""

        base_gargalos["CHAVE_OPERACAO"] = (
            base_gargalos["PV"].astype(str).str.upper().str.strip() + "||" +
            base_gargalos["Processo"].astype(str).str.upper().str.strip() + "||" +
            base_gargalos["CODIGO_PV"].astype(str).str.upper().str.strip()
        )

        if "ENTREGA" not in base_gargalos.columns:
            base_gargalos["ENTREGA"] = pd.NaT

        base_gargalos["ENTREGA"] = pd.to_datetime(base_gargalos["ENTREGA"], errors="coerce")
        base_gargalos["Dias para Entrega"] = (base_gargalos["ENTREGA"] - hoje).dt.days
        base_gargalos["Semáforo"] = base_gargalos["Dias para Entrega"].apply(semaforo_entrega)
        base_gargalos["ENTREGA_FMT"] = base_gargalos["ENTREGA"].dt.strftime("%d/%m/%Y")

        st.markdown("### 📋 PVs dos Gargalos")

        processo_baixa_sel = st.selectbox(
            "Selecione o gargalo",
            processos_top3,
            key="selectbox_gargalo_processo"
        )

        fila_gargalo = base_gargalos[
            base_gargalos["Processo"] == processo_baixa_sel
        ].copy()

        fila_gargalo_pendente = fila_gargalo[
            fila_gargalo["Status Operacional"] == "⏳ Pendente"
        ].copy()

        st.dataframe(fila_gargalo, use_container_width=True, height=360)

        st.divider()

        # 🔥 (RESTANTE DO BLOCO DE BAIXAS CONTINUA EXATAMENTE IGUAL — NÃO ALTERADO)



        # =========================================================
        # BAIXA / TERCEIRIZAÇÃO / LOTE (CORRIGIDO)
        # =========================================================
        st.markdown("### ✅ Dar Baixa em Operação Concluída")

        if fila_gargalo_pendente.empty:
            st.info("Nenhuma PV pendente disponível.")
        else:
            base_baixa = fila_gargalo_pendente.copy()

            base_baixa["ROTULO_BAIXA"] = (
                "PV " + base_baixa["PV"] +
                " | " + base_baixa["Processo"] +
                " | " + base_baixa["CODIGO_PV"] +
                " | " + base_baixa["Horas"].astype(str) + " h"
            )

            opcoes_baixa = base_baixa["ROTULO_BAIXA"].tolist()

            # 🔹 UNITÁRIO
            st.markdown("#### 🔹 Ação Unitária")

            col_bx1, col_bx2 = st.columns(2)

            baixa_sel = col_bx1.selectbox(
                "Selecione operação",
                opcoes_baixa,
                key="selectbox_baixa_gargalo"
            )
            observacao_baixa = col_bx2.text_input("Observação")

            registro_baixa_df = base_baixa[base_baixa["ROTULO_BAIXA"] == baixa_sel]

            if not registro_baixa_df.empty:
                linha = registro_baixa_df.iloc[0]

                col_btn1, col_btn2 = st.columns(2)

                if col_btn1.button("💾 Baixar"):
                    salvar_baixa_operacional(BASE_PATH, {
                        "PV": linha["PV"],
                        "Cliente": linha.get("Cliente", ""),
                        "CODIGO_PV": linha["CODIGO_PV"],
                        "Processo": linha["Processo"],
                        "Horas": linha["Horas"],
                        "Data_Baixa": pd.Timestamp.now(),
                        "Usuario": "Sistema",
                        "Observacao": observacao_baixa,
                        "Status_Baixa": "ATIVA",
                        "Data_Estorno": "",
                        "Motivo_Estorno": ""
                    })
                    st.cache_data.clear()
                    st.rerun()

                if col_btn2.button("🟣 Terceirizar"):
                    salvar_baixa_operacional(BASE_PATH, {
                        "PV": linha["PV"],
                        "Cliente": linha.get("Cliente", ""),
                        "CODIGO_PV": linha["CODIGO_PV"],
                        "Processo": linha["Processo"],
                        "Horas": linha["Horas"],
                        "Data_Baixa": pd.Timestamp.now(),
                        "Usuario": "Sistema",
                        "Observacao": observacao_baixa,
                        "Status_Baixa": "TERCEIRIZADA",
                        "Data_Estorno": "",
                        "Motivo_Estorno": ""
                    })
                    st.cache_data.clear()
                    st.rerun()

            st.divider()

            # 📦 LOTE
            st.markdown("#### 📦 Ação em Lote")

            selecao_lote = st.multiselect("Selecionar lote", opcoes_baixa)

            if selecao_lote:
                if st.button("📦 Baixar Lote"):
                    for label in selecao_lote:
                        linha = base_baixa[base_baixa["ROTULO_BAIXA"] == label].iloc[0]

                        salvar_baixa_operacional(BASE_PATH, {
                            "PV": linha["PV"],
                            "Cliente": linha.get("Cliente", ""),
                            "CODIGO_PV": linha["CODIGO_PV"],
                            "Processo": linha["Processo"],
                            "Horas": linha["Horas"],
                            "Data_Baixa": pd.Timestamp.now(),
                            "Usuario": "Sistema",
                            "Observacao": "",
                            "Status_Baixa": "ATIVA",
                            "Data_Estorno": "",
                            "Motivo_Estorno": ""
                        })

                    st.cache_data.clear()
                    st.rerun()

        st.divider()



# ============================================================
# MINI DASHBOARD POR GARGALO 
# ============================================================

st.markdown("## 🔥 Mini Dashboard por Gargalo")

# 🔒 GARANTIA ABSOLUTA DA BASE DE BAIXAS
if "df_baixas_ativas" not in st.session_state:
    df_baixas_ativas = pd.DataFrame()
else:
    df_baixas_ativas = st.session_state["df_baixas_ativas"]

# 🔒 GARANTIA DA FILA (USA df — BASE REAL DO APS)
if df is None or df.empty:
    df_mini_gargalos = pd.DataFrame()
else:
    df_mini_gargalos = montar_mini_dashboard_gargalos(
        fila=df,
        df_baixas_ativas=df_baixas_ativas
    )

# 🔒 GARANTIA DE ORDENAÇÃO
if not df_mini_gargalos.empty:
    df_mini_gargalos = df_mini_gargalos.sort_values(
        by=["Score", "Horas_Fila", "Qtd_Fila"],
        ascending=[False, False, False]
    ).reset_index(drop=True)

    df_mini_gargalos["Ranking"] = df_mini_gargalos.index + 1

cards_gargalos = resumo_cards_gargalos(df_mini_gargalos)

if df_mini_gargalos.empty:
    st.info("Nenhum dado disponível para análise de gargalos.")
else:

    # ============================================================
    # 🚨 ALERTA INTELIGENTE DE GARGALO
    # ============================================================

    st.markdown("## 🚨 Alerta Inteligente de Produção")

    gargalo_top = df_mini_gargalos.iloc[0]

    processo = gargalo_top.get("Processo", "N/A")
    horas = float(gargalo_top.get("Horas_Fila", 0))
    qtd = int(gargalo_top.get("Qtd_Fila", 0))
    score = float(gargalo_top.get("Score", 0))

    col_a1, col_a2, col_a3 = st.columns(3)

    col_a1.metric("Processo Crítico", f"🔴 {processo}")
    col_a2.metric("Horas Acumuladas", f"{horas:.1f} h")
    col_a3.metric("Itens na Fila", qtd)

    st.divider()

    # CLASSIFICAÇÃO
    if score >= 80:
        st.error("🚨 AÇÃO IMEDIATA: Gargalo crítico impactando diretamente os prazos.")
    elif score >= 50:
        st.warning("⚠️ Atenção: Gargalo em crescimento, priorizar na sequência.")
    else:
        st.info("🟢 Situação controlada.")

    # SUGESTÃO
    st.markdown("### 💡 Ação Recomendada")

    if qtd > 10 and horas > 20:
        st.markdown(f"➡️ Priorizar equipe adicional no processo **{processo}** imediatamente.")
    elif horas > 15:
        st.markdown(f"➡️ Avaliar redistribuição de carga para o processo **{processo}**.")
    else:
        st.markdown(f"➡️ Monitorar evolução do processo **{processo}**.")

    # ------------------------------------------------------------
    # CARDS PRINCIPAIS
    # ------------------------------------------------------------
    col_g1, col_g2, col_g3, col_g4, col_g5 = st.columns(5)

    with col_g1:
        st.metric("Processos", cards_gargalos["total_processos"])

    with col_g2:
        st.metric("Itens na Fila", cards_gargalos["total_itens_fila"])

    with col_g3:
        st.metric("Horas na Fila", f"{cards_gargalos['total_horas_fila']:.1f}h")

    with col_g4:
        st.metric("Baixas Ativas", cards_gargalos["total_baixas_ativas"])

    with col_g5:
        st.metric("Gargalo Crítico", f"🔴 {cards_gargalos['gargalo_critico']}")

    # ------------------------------------------------------------
    # CLASSIFICAÇÃO
    # ------------------------------------------------------------
    st.markdown("### 🚨 Classificação dos Gargalos")

    col_s1, col_s2, col_s3 = st.columns(3)

    with col_s1:
        st.metric("🔴 Críticos", cards_gargalos["qtd_criticos"])

    with col_s2:
        st.metric("🟡 Atenção", cards_gargalos["qtd_atencao"])

    with col_s3:
        st.metric("🟢 Controlados", cards_gargalos["qtd_controlados"])

    # ------------------------------------------------------------
    # TOP 3
    # ------------------------------------------------------------
    st.markdown("### 🔥 Top 3 Gargalos Prioritários")

    top3 = df_mini_gargalos.head(3)
    top3_cols = st.columns(3)

    for i in range(3):
        with top3_cols[i]:
            if i < len(top3):
                row = top3.iloc[i]

                st.metric(
                    label=f"{row['Processo']}",
                    value=f"{int(row['Qtd_Fila'])} itens",
                    delta=f"{row['Horas_Fila']:.1f}h | Score {row['Score']:.1f}"
                )
            else:
                st.metric(label="-", value="-", delta="-")

    # ------------------------------------------------------------
    # TABELA
    # ------------------------------------------------------------
    st.markdown("### 📊 Ranking Inteligente de Gargalos")

    st.dataframe(
        df_mini_gargalos[[
            "Ranking",
            "Processo",
            "Qtd_Fila",
            "Horas_Fila",
            "Qtd_Baixas_Ativas",
            "Carga_Total",
            "Score"
        ]],
        use_container_width=True,
        hide_index=True
    )


# ------------------------------------------------------------
# FILA ATUAL DE CORTE (COM ORDENAÇÃO GARANTIDA)
# ------------------------------------------------------------
st.markdown("### 🧾 Fila Atual de Corte")

if (
    "fila_corte_dash" not in locals()
    or fila_corte_dash is None
    or not isinstance(fila_corte_dash, pd.DataFrame)
):
    fila_corte_dash = pd.DataFrame()

if not fila_corte_dash.empty:

    fila_corte_exib = fila_corte_dash.copy()

    if "ENTREGA" in fila_corte_exib.columns:
        fila_corte_exib["ENTREGA"] = pd.to_datetime(
            fila_corte_exib["ENTREGA"], errors="coerce"
        )
        fila_corte_exib["ENTREGA"] = fila_corte_exib["ENTREGA"].dt.strftime("%d/%m/%Y")

    fila_corte_exib["Horas"] = pd.to_numeric(
        fila_corte_exib["Horas"], errors="coerce"
    ).fillna(0).round(1)

    colunas_corte_fila = [
        "PV",
        "Cliente",
        "CODIGO_PV",
        "Processo",
        "Horas",
        "Dias para Entrega",
        "ENTREGA"
    ]

    colunas_corte_fila = [
        c for c in colunas_corte_fila if c in fila_corte_exib.columns
    ]

    if "ENTREGA" in fila_corte_exib.columns:
        df_exib = fila_corte_exib[colunas_corte_fila] \
            .sort_values(["Processo", "ENTREGA"], ascending=[True, True])
    else:
        df_exib = fila_corte_exib[colunas_corte_fila] \
            .sort_values(["Processo"], ascending=[True])

    df_exib = df_exib.reset_index(drop=True)

    st.dataframe(
        df_exib,
        use_container_width=True,
        hide_index=True,
        height=320
    )

else:
    st.success("Nenhuma operação de corte pendente no momento. 🎯")

st.divider()

st.subheader("🔎 Busca rápida de PV / Cliente")

col_b1, col_b2 = st.columns(2)

busca_pv = col_b1.text_input("Buscar por PV")
busca_cliente = col_b2.text_input("Buscar por Cliente")

busca_df = base_op.copy()

if busca_pv:
    busca_df = busca_df[busca_df["PV"].astype(str).str.contains(busca_pv, case=False, na=False)]

if busca_cliente:
    busca_df = busca_df[busca_df["Cliente"].astype(str).str.contains(busca_cliente, case=False, na=False)]

if busca_pv or busca_cliente:
    busca_df["Horas"] = busca_df["Horas"].round(1)

    if "ENTREGA" in busca_df.columns:
        busca_df["ENTREGA"] = busca_df["ENTREGA"].dt.strftime("%d/%m/%Y")

    st.dataframe(busca_df, use_container_width=True)

st.subheader("📥 Exportar dados filtrados")

@st.cache_data
def converter_excel(df_export):
    from io import BytesIO
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df_export.to_excel(writer, index=False)
    return buffer.getvalue()

if not busca_df.empty:
    excel_bytes = converter_excel(busca_df)

    st.download_button(
        label="📥 Baixar Excel",
        data=excel_bytes,
        file_name="consulta_pvs.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

st.divider()



# --------------------------------------------------------
# HISTÓRICO PREMIUM DE BAIXA (CORRIGIDO)
# --------------------------------------------------------
st.markdown("## 🧾 Histórico Premium de Baixas Operacionais")
st.caption("Rastreabilidade completa das baixas operacionais, terceirizações e estornos.")

# 🔥 FONTE REAL DOS DADOS
df_baixas_exib = df_baixas.copy()

if not df_baixas_exib.empty:

    for col in [
        "PV", "Cliente", "CODIGO_PV", "Processo", "Usuario",
        "Observacao", "Status_Baixa", "Motivo_Estorno", "Data_Estorno"
    ]:
        if col in df_baixas_exib.columns:
            df_baixas_exib[col] = (
                df_baixas_exib[col]
                .fillna("")
                .astype(str)
                .str.strip()
            )

    if "Status_Baixa" in df_baixas_exib.columns:
        df_baixas_exib["Status_Baixa"] = (
            df_baixas_exib["Status_Baixa"]
            .replace("", "ATIVA")
            .astype(str)
            .str.strip()
            .str.upper()
        )
    else:
        df_baixas_exib["Status_Baixa"] = "ATIVA"

    if "Data_Baixa" in df_baixas_exib.columns:
        df_baixas_exib["Data_Baixa"] = pd.to_datetime(
            df_baixas_exib["Data_Baixa"],
            errors="coerce"
        )

    if "Data_Estorno" in df_baixas_exib.columns:
        df_baixas_exib["Data_Estorno"] = pd.to_datetime(
            df_baixas_exib["Data_Estorno"],
            errors="coerce"
        )

    col_hist1, col_hist2, col_hist3 = st.columns([2, 2, 2])

    status_hist_sel = col_hist1.selectbox(
        "Filtrar por status",
        ["Todos", "ATIVA", "TERCEIRIZADA", "ESTORNADA"],
        key="filtro_status_historico_baixas"
    )

    processo_hist_sel = col_hist2.selectbox(
        "Filtrar por processo",
        ["Todos"] + sorted(
            df_baixas_exib["Processo"]
            .dropna()
            .astype(str)
            .str.strip()
            .unique()
            .tolist()
        ),
        key="filtro_processo_historico_baixas"
    )

    cliente_hist_sel = col_hist3.selectbox(
        "Filtrar por cliente",
        ["Todos"] + sorted(
            df_baixas_exib["Cliente"]
            .dropna()
            .astype(str)
            .str.strip()
            .unique()
            .tolist()
        ),
        key="filtro_cliente_historico_baixas"
    )

    if status_hist_sel != "Todos":
        df_baixas_exib = df_baixas_exib[
            df_baixas_exib["Status_Baixa"] == status_hist_sel
        ].copy()

    if processo_hist_sel != "Todos":
        df_baixas_exib = df_baixas_exib[
            df_baixas_exib["Processo"].astype(str).str.strip() == processo_hist_sel
        ].copy()

    if cliente_hist_sel != "Todos":
        df_baixas_exib = df_baixas_exib[
            df_baixas_exib["Cliente"].astype(str).str.strip() == cliente_hist_sel
        ].copy()

    col_hk1, col_hk2, col_hk3, col_hk4 = st.columns(4)
    col_hk1.metric("Total de Registros", fmt_br_int(len(df_baixas_exib)))
    col_hk2.metric("Baixas Ativas", fmt_br_int((df_baixas_exib["Status_Baixa"] == "ATIVA").sum()))
    col_hk3.metric("Terceirizadas", fmt_br_int((df_baixas_exib["Status_Baixa"] == "TERCEIRIZADA").sum()))
    col_hk4.metric(
        "Horas Registradas",
        fmt_br_num(
            pd.to_numeric(df_baixas_exib["Horas"], errors="coerce").fillna(0).sum(),
            1
        ) + " h"
    )

    def status_historico_label(x):
        x = str(x).strip().upper()
        if x == "ATIVA":
            return "✅ Baixada"
        elif x == "TERCEIRIZADA":
            return "🟣 Terceirizada"
        elif x == "ESTORNADA":
            return "🔁 Estornada"
        return "⚪ Indefinido"

    df_baixas_exib["Status Exibição"] = df_baixas_exib["Status_Baixa"].apply(status_historico_label)

    if "Data_Baixa" in df_baixas_exib.columns:
        df_baixas_exib["Data_Baixa"] = df_baixas_exib["Data_Baixa"].dt.strftime("%d/%m/%Y %H:%M")

    if "Data_Estorno" in df_baixas_exib.columns:
        df_baixas_exib["Data_Estorno"] = df_baixas_exib["Data_Estorno"].dt.strftime("%d/%m/%Y %H:%M")

    df_baixas_exib = df_baixas_exib.sort_values(
        by=["Data_Baixa"],
        ascending=False,
        na_position="last"
    ).copy()

    colunas_exibir = [
        "Status Exibição",
        "PV",
        "Cliente",
        "CODIGO_PV",
        "Processo",
        "Horas",
        "Data_Baixa",
        "Usuario",
        "Observacao",
        "Data_Estorno",
        "Motivo_Estorno"
    ]
    colunas_exibir = [c for c in colunas_exibir if c in df_baixas_exib.columns]

    st.dataframe(
        df_baixas_exib[colunas_exibir].rename(columns={
            "Status Exibição": "Status",
            "Data_Baixa": "Data da Baixa",
            "Usuario": "Usuário",
            "Observacao": "Observação",
            "Data_Estorno": "Data do Estorno",
            "Motivo_Estorno": "Motivo do Estorno"
        }),
        use_container_width=True,
        hide_index=True,
        height=340
    )
else:
    st.info("Nenhuma baixa operacional registrada até o momento.")

# ============================================================
# 🚨 DASHBOARD DE ERROS OPERACIONAIS
# ============================================================

st.markdown("## 🚨 Inteligência de Erros Operacionais")

try:
    caminho = garantir_arquivo_baixas(BASE_PATH)
    df_baixas_full = pd.read_excel(caminho, dtype=str)
    df_baixas_full = _padronizar_df_baixas(df_baixas_full)
except Exception:
    df_baixas_full = pd.DataFrame()

if df_baixas_full.empty:
    st.info("Sem dados para análise de erros.")
else:

    df_baixas_full["Status_Baixa"] = df_baixas_full["Status_Baixa"].astype(str).str.upper()

    df_erros = df_baixas_full[
        df_baixas_full["Status_Baixa"] == "TENTATIVA_DUPLICADA"
    ].copy()

    if df_erros.empty:
        st.success("Nenhuma tentativa duplicada registrada 👍")
    else:

        # ------------------------------------------------------------
        # MÉTRICAS
        # ------------------------------------------------------------
        total_erros = len(df_erros)
        total_operacoes = len(df_baixas_full)

        taxa_erro = (total_erros / total_operacoes * 100) if total_operacoes > 0 else 0

        col_e1, col_e2, col_e3 = st.columns(3)

        col_e1.metric("Tentativas Duplicadas", total_erros)
        col_e2.metric("Total de Registros", total_operacoes)
        col_e3.metric("Taxa de Erro (%)", f"{taxa_erro:.2f}%")

        st.divider()

        # ------------------------------------------------------------
        # POR PROCESSO
        # ------------------------------------------------------------
        st.markdown("### ⚙️ Erros por Processo")

        erros_processo = (
            df_erros.groupby("Processo")
            .size()
            .reset_index(name="Qtd_Erros")
            .sort_values("Qtd_Erros", ascending=False)
        )

        st.dataframe(erros_processo, use_container_width=True, hide_index=True)

        # ------------------------------------------------------------
        # POR USUÁRIO
        # ------------------------------------------------------------
        if "Usuario" in df_erros.columns:

            st.markdown("### 👤 Erros por Usuário")

            erros_usuario = (
                df_erros.groupby("Usuario")
                .size()
                .reset_index(name="Qtd_Erros")
                .sort_values("Qtd_Erros", ascending=False)
            )

            st.dataframe(erros_usuario, use_container_width=True, hide_index=True)

        st.divider()

        # ------------------------------------------------------------
        # ÚLTIMAS OCORRÊNCIAS
        # ------------------------------------------------------------
        st.markdown("### 🕒 Últimas Tentativas")

        st.dataframe(
            df_erros.sort_values("Data_Baixa", ascending=False).head(20),
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# ============ TABELAS ANALÍTICAS DE CAPACIDADE ==============
# ============================================================
st.markdown("## 📋 Tabelas Analíticas de Capacidade")
st.caption("Leitura técnica de colapso, pressão de fila e criticidade de capacidade.")

# ===============================
# BASE EXECUTIVA DE COLAPSO
# ===============================
if "Semáforo Colapso" not in ranking_colapso.columns:
    ranking_colapso["Semáforo Colapso"] = "🟢 Sob Controle"

for col in ["Ocupacao", "Fila Max (dias)", "Fila Acumulada Max (h)", "Saldo (h)"]:
    if col not in ranking_colapso.columns:
        ranking_colapso[col] = 0

ranking_colapso["Ocupacao"] = pd.to_numeric(ranking_colapso["Ocupacao"], errors="coerce").fillna(0)
ranking_colapso["Fila Max (dias)"] = pd.to_numeric(ranking_colapso["Fila Max (dias)"], errors="coerce").fillna(0)
ranking_colapso["Fila Acumulada Max (h)"] = pd.to_numeric(ranking_colapso["Fila Acumulada Max (h)"], errors="coerce").fillna(0)
ranking_colapso["Saldo (h)"] = pd.to_numeric(ranking_colapso["Saldo (h)"], errors="coerce").fillna(0)

# ===============================
# ALERTA DE COLAPSO DO GARGALO
# ===============================
st.subheader("🚨 Semáforo de Colapso dos Gargalos")

if not ranking_colapso.empty:
    colapso_exib = ranking_colapso.copy()

    if "Semáforo Colapso" not in colapso_exib.columns:
        colapso_exib["Semáforo Colapso"] = "🟢 Sob Controle"
    if "Processo" not in colapso_exib.columns:
        colapso_exib["Processo"] = "N/D"
    if "Ocupacao" not in colapso_exib.columns:
        colapso_exib["Ocupacao"] = 0
    if "Fila Acumulada Max (h)" not in colapso_exib.columns:
        colapso_exib["Fila Acumulada Max (h)"] = 0
    if "Fila Max (dias)" not in colapso_exib.columns:
        colapso_exib["Fila Max (dias)"] = 0
    if "Saldo (h)" not in colapso_exib.columns:
        colapso_exib["Saldo (h)"] = 0

    colapso_exib["Ocupação (%)"] = colapso_exib["Ocupacao"].apply(lambda x: fmt_br_pct(x, 1))
    colapso_exib["Fila Acumulada (h)"] = colapso_exib["Fila Acumulada Max (h)"].apply(lambda x: fmt_br_num(x, 1))
    colapso_exib["Fila (dias)"] = colapso_exib["Fila Max (dias)"].apply(lambda x: fmt_br_num(x, 1))
    colapso_exib["Saldo Exibição (h)"] = colapso_exib["Saldo (h)"].apply(lambda x: fmt_br_num(x, 1))

    st.dataframe(
        colapso_exib[
            ["Semáforo Colapso", "Processo", "Ocupação (%)", "Fila Acumulada (h)", "Fila (dias)", "Saldo Exibição (h)"]
        ].rename(columns={"Saldo Exibição (h)": "Saldo (h)"}),
        use_container_width=True
    )

    topo_colapso = str(colapso_exib.iloc[0]["Semáforo Colapso"])
    processo_topo = str(colapso_exib.iloc[0]["Processo"])

    if "🔥" in topo_colapso or "🔴" in topo_colapso:
        st.error(f"Risco elevado detectado no processo: {processo_topo}")
    elif "🟡" in topo_colapso:
        st.warning(f"Atenção para pressão crescente no processo: {processo_topo}")
    else:
        st.success("Nenhum gargalo em risco de colapso no momento.")
else:
    st.info("Sem dados suficientes para cálculo de colapso.")


# ============================================================
# 🔮 COLAPSO FUTURO (NOVO)
# ============================================================
st.subheader("🔮 Colapso Futuro (Previsão)")

st.caption("Projeção baseada na carga atual versus capacidade produtiva.")

if df_colapso is not None and not df_colapso.empty:

    colapso_futuro = df_colapso.copy()

    if "Processo" not in colapso_futuro.columns:
        colapso_futuro["Processo"] = "N/D"

    if "Dias de Fila" not in colapso_futuro.columns:
        colapso_futuro["Dias de Fila"] = 0

    if "Risco Futuro" not in colapso_futuro.columns:
        colapso_futuro["Risco Futuro"] = "🟢 Sob controle"

    colapso_futuro["Dias de Fila"] = pd.to_numeric(
        colapso_futuro["Dias de Fila"], errors="coerce"
    ).fillna(0)

    colapso_futuro["Dias de Fila_fmt"] = colapso_futuro["Dias de Fila"].apply(
        lambda x: fmt_br_num(x, 1)
    )

    st.dataframe(
        colapso_futuro[
            ["Processo", "Dias de Fila_fmt", "Risco Futuro"]
        ].rename(columns={"Dias de Fila_fmt": "Dias de Fila"}),
        use_container_width=True
    )

else:
    st.info("Sem dados suficientes para previsão de colapso futuro.")


# ===============================
# ALERTA DE CAPACIDADE CRÍTICA
# ===============================
st.subheader("⚠️ Capacidade Crítica")
critico = dem[dem["Ocupacao"] > 95].copy()

if not critico.empty:
    st.error("Capacidade próxima ou acima do limite detectada.")

    critico_exib = critico.copy()

    # saneamento forte das colunas numéricas
    for col in ["Ocupacao", "Horas", "Capacidade"]:
        if col not in critico_exib.columns:
            critico_exib[col] = 0

        critico_exib[col] = pd.to_numeric(
            critico_exib[col],
            errors="coerce"
        ).fillna(0)

    critico_exib["Semáforo"] = critico_exib["Ocupacao"].apply(
    lambda x: "🔴" if x >= 100 else "🟠" if x >= 90 else "🟡" if x >= 75 else "🟢"
    )
    critico_exib["Horas_fmt"] = critico_exib["Horas"].apply(lambda x: fmt_br_num(x, 1))
    critico_exib["Capacidade_fmt"] = critico_exib["Capacidade"].apply(lambda x: fmt_br_num(x, 1))
    critico_exib["Ocupação_fmt"] = critico_exib["Ocupacao"].apply(lambda x: fmt_br_pct(x, 1))

    critico_exib = critico_exib.sort_values(
        ["Ocupacao", "Horas"],
        ascending=[False, False]
    ).reset_index(drop=True)

    st.dataframe(
        critico_exib[
            ["Semáforo", "Periodo", "Processo", "Horas_fmt", "Capacidade_fmt", "Ocupação_fmt"]
        ].rename(columns={
            "Horas_fmt": "Horas",
            "Capacidade_fmt": "Capacidade",
            "Ocupação_fmt": "Ocupação (%)"
        }),
        use_container_width=True
    )
else:
    st.success("Capacidade sob controle.")


# ============================================================
# ===================== VISÃO OPERACIONAL ====================
# ============================================================
st.markdown("## ⚙️ Visão Operacional")
st.caption("Consulta detalhada, filtros, fila de produção e auditorias.")

with st.expander("📋 Tabelas, Filtros e Auditoria", expanded=True):

    st.subheader("📌 Auditoria de Capacidade")

    auditoria = dem.copy()

    # ------------------------------
    # SANEAMENTO NUMÉRICO ROBUSTO
    # ------------------------------
    for col in ["Ocupacao", "Horas", "Capacidade", "Saldo (h)"]:
        if col not in auditoria.columns:
            auditoria[col] = 0

        auditoria[col] = pd.to_numeric(
            auditoria[col],
            errors="coerce"
        ).fillna(0)

    # ------------------------------
    # SEMÁFORO (INLINE - SEGURO)
    # ------------------------------
    auditoria["Semáforo"] = auditoria["Ocupacao"].apply(
        lambda x: "🔴" if x >= 100
        else "🟠" if x >= 90
        else "🟡" if x >= 75
        else "🟢"
    )

    # ------------------------------
    # FORMATAÇÃO VISUAL
    # ------------------------------
    auditoria["Ocupação (%)"] = auditoria["Ocupacao"].apply(lambda x: fmt_br_pct(x, 1))
    auditoria["Horas"] = auditoria["Horas"].apply(lambda x: fmt_br_num(x, 1))
    auditoria["Capacidade"] = auditoria["Capacidade"].apply(lambda x: fmt_br_num(x, 1))
    auditoria["Saldo (h)"] = auditoria["Saldo (h)"].apply(lambda x: fmt_br_num(x, 1))

    # ------------------------------
    # EXIBIÇÃO
    # ------------------------------
    st.dataframe(
        auditoria[
            ["Periodo", "Semáforo", "Processo", "Horas", "Capacidade", "Ocupação (%)", "Saldo (h)"]
        ],
        use_container_width=True
    )

    st.subheader("⏱️ Previsão de Atraso por PV")

    pv_carga_exibicao = pv_carga.copy()
    pv_carga_exibicao["Horas"] = pv_carga_exibicao["Horas"].round(1)
    pv_carga_exibicao["Dias Necessários"] = pv_carga_exibicao["Dias Necessários"].round(1)
    pv_carga_exibicao["Dias Disponíveis"] = pv_carga_exibicao["Dias Disponíveis"].round(1)
    pv_carga_exibicao["Atraso (dias)"] = pv_carga_exibicao["Atraso (dias)"].astype(int)

    if "Data" in pv_carga_exibicao.columns:
        pv_carga_exibicao["Data"] = pd.to_datetime(pv_carga_exibicao["Data"], errors="coerce").dt.strftime("%d/%m/%Y")

    st.dataframe(pv_carga_exibicao, use_container_width=True)

    st.subheader("⚠️ PVs em Risco")

    risco_exibicao = risco.copy()
    if not risco_exibicao.empty:
        risco_exibicao["Horas"] = risco_exibicao["Horas"].round(1)
        risco_exibicao["Dias Necessários"] = risco_exibicao["Dias Necessários"].round(1)
        risco_exibicao["Dias Disponíveis"] = risco_exibicao["Dias Disponíveis"].round(1)

        if "Data" in risco_exibicao.columns:
            risco_exibicao["Data"] = pd.to_datetime(risco_exibicao["Data"], errors="coerce").dt.strftime("%d/%m/%Y")

    st.dataframe(risco_exibicao, use_container_width=True)

    st.subheader("📅 Calendário Industrial")
    st.dataframe(cal, use_container_width=True)

    st.subheader("🏭 Capacidade x Carga por Processo")
    st.dataframe(dem_proc, use_container_width=True)

    st.divider()


        
# ============================================================
# ================= SIMULAÇÃO DE GARGALO =====================
# ============================================================
with st.expander("🚨 Simulação de Gargalo por Processo", expanded=False):

    st.subheader("🔎 Verificar quais PVs estouram a capacidade do processo")

    processo_gargalo_sel = st.selectbox(
        "Selecione o processo gargalo",
        sorted(df["Processo"].dropna().unique().tolist()),
        key="gargalo_processo_select"
    )

    df_gargalo = df[df["Processo"] == processo_gargalo_sel].copy()

    if not df_gargalo.empty:
        gargalo_pv = (
            df_gargalo.groupby(["PV", "Cliente", "Data"], as_index=False)["Horas"]
            .sum()
            .sort_values(["Data", "PV"])
            .reset_index(drop=True)
        )

        gargalo_pv["Carga Acumulada (h)"] = gargalo_pv["Horas"].cumsum()

        recursos_gargalo = MAQUINAS.get(processo_gargalo_sel, 0)
        capacidade_dia_gargalo = capacidade_diaria_real(processo_gargalo_sel)

        hoje = pd.Timestamp.today().normalize()

        gargalo_pv["Horas Disponíveis até Entrega"] = gargalo_pv["Data"].apply(
            lambda x: horas_uteis_periodo(hoje, x) * recursos_gargalo * EFICIENCIA
        )

        gargalo_pv["Saldo Gargalo (h)"] = (
            gargalo_pv["Horas Disponíveis até Entrega"] - gargalo_pv["Carga Acumulada (h)"]
        ).round(1)

        gargalo_pv["Estoura Gargalo?"] = np.where(
            gargalo_pv["Saldo Gargalo (h)"] < 0,
            "SIM",
            "NÃO"
        )

        gargalo_pv["Dias de Estouro"] = np.where(
            capacidade_dia_gargalo > 0,
            np.ceil(np.abs(np.minimum(gargalo_pv["Saldo Gargalo (h)"], 0)) / capacidade_dia_gargalo),
            0
        )

        gargalo_pv["Dias de Estouro"] = gargalo_pv["Dias de Estouro"].astype(int)

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
        exib_gargalo["Saldo Gargalo (h)"] = exib_gargalo["Saldo Gargalo (h)"].round(1)

        if "Data" in exib_gargalo.columns:
            exib_gargalo["Data"] = pd.to_datetime(exib_gargalo["Data"], errors="coerce").dt.strftime("%d/%m/%Y")

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
            ],
            use_container_width=True
        )

        total_estouro = (gargalo_pv["Estoura Gargalo?"] == "SIM").sum()
        total_ok = (gargalo_pv["Estoura Gargalo?"] == "NÃO").sum()

        g1, g2, g3 = st.columns(3)
        g1.metric("🔴 PVs que Estouram", int(total_estouro))
        g2.metric("🟢 PVs Viáveis", int(total_ok))
        g3.metric("⚙️ Recursos do Processo", int(recursos_gargalo))

    else:
        st.info("Não há carga para o processo selecionado.")