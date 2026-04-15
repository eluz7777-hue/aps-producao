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
@st.cache_data(ttl=0)
def carregar_dados(arquivo_pv, file_mtime):
    df = pd.read_excel(arquivo_pv)
    return df

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
    """
    Garante que o arquivo físico de baixas exista com a estrutura correta.
    """
    os.makedirs(base_path, exist_ok=True)
    caminho = caminho_arquivo_baixas(base_path)

    if not os.path.exists(caminho):
        df_vazio = pd.DataFrame(columns=COLUNAS_BAIXAS)
        df_vazio.to_excel(caminho, index=False)

    return caminho

def _padronizar_df_baixas(df_baixas):
    """
    Padroniza a estrutura e os tipos do histórico de baixas operacionais.
    Mantém histórico completo (ativas + terceirizadas + estornadas).
    """
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

    # Padronização forte
    df_baixas["PV"] = df_baixas["PV"].astype(str).str.strip().str.upper()
    df_baixas["CODIGO_PV"] = df_baixas["CODIGO_PV"].astype(str).str.strip().str.upper()
    df_baixas["Processo"] = df_baixas["Processo"].astype(str).str.strip().str.upper()

    df_baixas["Cliente"] = df_baixas["Cliente"].replace("", "SEM CLIENTE")

    df_baixas["Status_Baixa"] = (
        df_baixas["Status_Baixa"]
        .replace("", "ATIVA")
        .astype(str)
        .str.strip()
        .str.upper()
    )

    df_baixas["Horas"] = pd.to_numeric(df_baixas["Horas"], errors="coerce").fillna(0)
    df_baixas["Data_Baixa"] = pd.to_datetime(df_baixas["Data_Baixa"], errors="coerce")
    df_baixas["Data_Estorno"] = df_baixas["Data_Estorno"].fillna("").astype(str).str.strip()

    # CHAVE OPERACIONAL OFICIAL
    df_baixas["CHAVE_OPERACAO"] = (
        df_baixas["PV"].astype(str).str.strip().str.upper() + "||" +
        df_baixas["Processo"].astype(str).str.strip().str.upper() + "||" +
        df_baixas["CODIGO_PV"].astype(str).str.strip().str.upper()
    )

    df_baixas = df_baixas.sort_values(
        by=["Data_Baixa", "PV", "Processo"],
        ascending=[False, True, True]
    ).reset_index(drop=True)

    return df_baixas

@st.cache_data(ttl=0)
def carregar_baixas_operacionais(base_path):
    caminho = garantir_arquivo_baixas(base_path)

    print("📥 LENDO BAIXAS DE:", caminho)

    try:
        df_baixas = pd.read_excel(caminho, dtype=str)
        print("📥 TOTAL DE REGISTROS LIDOS:", len(df_baixas))
        return _padronizar_df_baixas(df_baixas)
    except Exception as e:
        print("❌ ERRO AO LER BAIXAS:", e)
        st.warning(f"Não foi possível ler o arquivo de baixas operacionais: {e}")
        return pd.DataFrame(columns=COLUNAS_BAIXAS + ["CHAVE_OPERACAO"])

def salvar_baixa_operacional(base_path, registro_baixa):
    """
    Salva uma nova baixa operacional SEM apagar histórico anterior.
    Também evita duplicidade ativa/terceirizada da mesma operação.
    """
    caminho = garantir_arquivo_baixas(base_path)

    print("💾 SALVANDO BAIXA EM:", caminho)
    print("🧾 REGISTRO RECEBIDO:", registro_baixa)

    try:
        df_existente = pd.read_excel(caminho, dtype=str)
        print("📂 REGISTROS JÁ EXISTENTES:", len(df_existente))
    except Exception as e:
        print("⚠️ ARQUIVO AINDA NÃO EXISTIA OU NÃO FOI LIDO:", e)
        df_existente = pd.DataFrame(columns=COLUNAS_BAIXAS)

    df_existente = _padronizar_df_baixas(df_existente)

    novo_registro = pd.DataFrame([registro_baixa])

    for col in COLUNAS_BAIXAS:
        if col not in novo_registro.columns:
            novo_registro[col] = None

    if "Data_Baixa" not in novo_registro.columns or novo_registro["Data_Baixa"].isna().all():
        novo_registro["Data_Baixa"] = pd.Timestamp.now()

    novo_registro = _padronizar_df_baixas(novo_registro)

    print("🆕 NOVO REGISTRO PADRONIZADO:")
    print(novo_registro.to_dict(orient="records"))

    # --------------------------------------------
    # EVITA DUPLICIDADE ATIVA / TERCEIRIZADA
    # --------------------------------------------
    if not df_existente.empty:
        chave_nova = str(novo_registro.iloc[0]["CHAVE_OPERACAO"]).strip().upper()

        duplicado = df_existente[
            (df_existente["CHAVE_OPERACAO"].astype(str).str.strip().str.upper() == chave_nova) &
            (
                df_existente["Status_Baixa"]
                .astype(str)
                .str.strip()
                .str.upper()
                .isin(["ATIVA", "TERCEIRIZADA"])
            )
        ]

        if not duplicado.empty:
            print("⚠️ DUPLICIDADE DETECTADA - BAIXA NÃO SALVA")
            print(duplicado[["PV", "Processo", "CODIGO_PV", "Status_Baixa"]].to_dict(orient="records"))
            return df_existente

    # --------------------------------------------
    # CONCATENA E SALVA
    # --------------------------------------------
    df_final = pd.concat(
        [df_existente[COLUNAS_BAIXAS], novo_registro[COLUNAS_BAIXAS]],
        ignore_index=True
    )

    df_final = _padronizar_df_baixas(df_final)

    print("💾 TOTAL DE REGISTROS APÓS CONCATENAR:", len(df_final))

    # Persistência física garantida
    with pd.ExcelWriter(caminho, engine="openpyxl", mode="w") as writer:
        df_final.to_excel(writer, index=False)

    print("✅ ARQUIVO SALVO COM SUCESSO:", caminho)

    st.cache_data.clear()

    return df_final

def estornar_baixa_operacional(base_path, pv, processo, codigo_pv="", motivo_estorno=""):
    """
    Estorna a última baixa ATIVA ou TERCEIRIZADA daquela operação sem apagar histórico.
    """
    caminho = garantir_arquivo_baixas(base_path)

    try:
        df_baixas = pd.read_excel(caminho, dtype=str)
    except Exception as e:
        return False, f"Erro ao ler arquivo de baixas: {e}"

    df_baixas = _padronizar_df_baixas(df_baixas)

    if df_baixas.empty:
        return False, "Nenhuma baixa operacional encontrada."

    pv = str(pv).strip().upper()
    processo = str(processo).strip().upper()
    codigo_pv = str(codigo_pv).strip().upper()

    filtro = (
        (df_baixas["PV"].astype(str).str.strip().str.upper() == pv) &
        (df_baixas["Processo"].astype(str).str.strip().str.upper() == processo) &
        (df_baixas["CODIGO_PV"].astype(str).str.strip().str.upper() == codigo_pv) &
        (
            df_baixas["Status_Baixa"]
            .astype(str)
            .str.strip()
            .str.upper()
            .isin(["ATIVA", "TERCEIRIZADA"])
        )
    )

    if not filtro.any():
        return False, "Nenhuma baixa ativa encontrada para estorno."

    idx_estorno = df_baixas.loc[filtro].sort_values("Data_Baixa", ascending=False).index[0]

    df_baixas.loc[idx_estorno, "Status_Baixa"] = "ESTORNADA"
    df_baixas.loc[idx_estorno, "Data_Estorno"] = pd.Timestamp.now().strftime("%d/%m/%Y %H:%M:%S")
    df_baixas.loc[idx_estorno, "Motivo_Estorno"] = motivo_estorno.strip() if motivo_estorno else ""

    df_baixas = _padronizar_df_baixas(df_baixas)

    # Persistência física garantida
    with pd.ExcelWriter(caminho, engine="openpyxl", mode="w") as writer:
        df_baixas.to_excel(writer, index=False)

    st.cache_data.clear()

    return True, "Baixa operacional estornada com sucesso."

def historico_baixas_ativas(df_baixas):
    """
    Retorna apenas as operações que devem sair da fila operacional:
    ATIVA + TERCEIRIZADA
    """
    if df_baixas.empty:
        return pd.DataFrame(columns=COLUNAS_BAIXAS + ["CHAVE_OPERACAO"])

    df_baixas = _padronizar_df_baixas(df_baixas)

    return df_baixas[
        df_baixas["Status_Baixa"].astype(str).str.strip().str.upper().isin(["ATIVA", "TERCEIRIZADA"])
    ].copy()

def historico_baixas_completo(df_baixas):
    """
    Retorna o histórico completo consolidado (ativas + terceirizadas + estornadas).
    """
    if df_baixas.empty:
        return pd.DataFrame(columns=COLUNAS_BAIXAS + ["CHAVE_OPERACAO"])

    return _padronizar_df_baixas(df_baixas.copy())

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
# INTEGRAÇÃO DO HISTÓRICO DE BAIXAS OPERACIONAIS
# ===============================
if "BASE_PATH" in globals():
    caminho_baixas = caminho_arquivo_baixas(BASE_PATH)

    if os.path.exists(caminho_baixas):
        try:
            df_baixas_raw = pd.read_excel(caminho_baixas, dtype=str)
        except Exception as e:
            st.warning(f"Erro ao ler histórico físico de baixas: {e}")
            df_baixas_raw = pd.DataFrame(columns=COLUNAS_BAIXAS)
    else:
        df_baixas_raw = pd.DataFrame(columns=COLUNAS_BAIXAS)

    df_baixas = _padronizar_df_baixas(df_baixas_raw)
    df_baixas_historico = historico_baixas_completo(df_baixas)
    df_baixas_ativas = historico_baixas_ativas(df_baixas)

    for _df in [df_baixas, df_baixas_historico, df_baixas_ativas]:
        if not _df.empty:
            for col in ["PV", "Processo", "CODIGO_PV", "CHAVE_OPERACAO"]:
                if col in _df.columns:
                    _df[col] = (
                        _df[col]
                        .fillna("")
                        .astype(str)
                        .str.strip()
                        .str.upper()
                    )

    if not df_baixas_ativas.empty and "CHAVE_OPERACAO" in df_baixas_ativas.columns:
        chaves_baixadas = set(
            df_baixas_ativas["CHAVE_OPERACAO"]
            .dropna()
            .astype(str)
            .str.strip()
            .str.upper()
            .unique()
        )
    else:
        chaves_baixadas = set()

    st.caption(f"📁 Histórico físico carregado: {len(df_baixas_historico)} registro(s)")
else:
    df_baixas = pd.DataFrame(columns=COLUNAS_BAIXAS + ["CHAVE_OPERACAO"])
    df_baixas_historico = pd.DataFrame(columns=COLUNAS_BAIXAS + ["CHAVE_OPERACAO"])
    df_baixas_ativas = pd.DataFrame(columns=COLUNAS_BAIXAS + ["CHAVE_OPERACAO"])
    chaves_baixadas = set()

# ===============================
# HISTÓRICO PREMIUM DE BAIXAS OPERACIONAIS
# ===============================
st.subheader("🧾 Histórico Premium de Baixas Operacionais")

if df_baixas_historico is not None and not df_baixas_historico.empty:

    hist_exib = df_baixas_historico.copy()

    # ----------------------------
    # FORMATAÇÕES
    # ----------------------------
    if "Data_Baixa" in hist_exib.columns:
        hist_exib["Data_Baixa"] = pd.to_datetime(hist_exib["Data_Baixa"], errors="coerce")
        hist_exib = hist_exib.sort_values("Data_Baixa", ascending=False)
        hist_exib["Data_Baixa"] = hist_exib["Data_Baixa"].dt.strftime("%d/%m/%Y %H:%M")

    if "Horas" in hist_exib.columns:
        hist_exib["Horas"] = pd.to_numeric(hist_exib["Horas"], errors="coerce").fillna(0).round(1)

    if "Status_Baixa" in hist_exib.columns:
        hist_exib["Status_Baixa"] = (
            hist_exib["Status_Baixa"]
            .astype(str)
            .str.strip()
            .str.upper()
            .replace({
                "ATIVA": "🟢 ATIVA",
                "TERCEIRIZADA": "🟣 TERCEIRIZADA",
                "ESTORNADA": "🔴 ESTORNADA"
            })
        )

    # ----------------------------
    # FILTROS
    # ----------------------------
    col1, col2 = st.columns(2)

    with col1:
        filtro_status = st.selectbox(
            "Filtrar por status",
            ["Todos", "🟢 ATIVA", "🟣 TERCEIRIZADA", "🔴 ESTORNADA"],
            key="filtro_status_historico_premium"
        )

    with col2:
        filtro_pv = st.text_input(
            "Buscar PV",
            key="buscar_pv_historico_premium"
        ).strip()

    if filtro_status != "Todos":
        hist_exib = hist_exib[hist_exib["Status_Baixa"] == filtro_status]

    if filtro_pv:
        hist_exib = hist_exib[
            hist_exib["PV"].astype(str).str.contains(filtro_pv, case=False, na=False)
        ]

    # ----------------------------
    # EXIBIÇÃO
    # ----------------------------
    colunas = [
        "Status_Baixa",
        "Data_Baixa",
        "PV",
        "Cliente",
        "CODIGO_PV",
        "Processo",
        "Horas",
        "Usuario",
        "Observacao"
    ]

    colunas = [c for c in colunas if c in hist_exib.columns]

    st.dataframe(hist_exib[colunas], use_container_width=True)

    st.caption(f"Total de registros: {len(hist_exib)}")

else:
    st.info("Nenhuma baixa operacional registrada até o momento.")

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

# ============================================================
# BASE OPERACIONAL VISUAL (MOSTRA TUDO, MAS COM STATUS)
# ============================================================

df_operacional = df_original.copy()

# --------------------------------------------
# FUNÇÃO OFICIAL DE NORMALIZAÇÃO DA CHAVE
# --------------------------------------------
def normalizar_chave_operacao(pv, processo, codigo):
    return (
        str(pv).strip().upper() + "||" +
        str(processo).strip().upper() + "||" +
        str(codigo).strip().upper()
    )

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
        lambda r: normalizar_chave_operacao(r["PV"], r["Processo"], r["CODIGO_PV"]),
        axis=1
    )
else:
    df_operacional["CHAVE_OPERACAO"] = ""

# --------------------------------------------
# BASE OFICIAL PARA TIRAR DA FILA
# SOMENTE BAIXAS ATIVAS / TERCEIRIZADAS
# --------------------------------------------
if "df_baixas_ativas" in locals() and df_baixas_ativas is not None and not df_baixas_ativas.empty:
    df_baixas_status = df_baixas_ativas.copy()

    for col in ["PV", "Processo", "CODIGO_PV"]:
        if col not in df_baixas_status.columns:
            df_baixas_status[col] = ""

        df_baixas_status[col] = (
            df_baixas_status[col]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.upper()
        )

    df_baixas_status["CHAVE_OPERACAO"] = df_baixas_status.apply(
        lambda r: normalizar_chave_operacao(r["PV"], r["Processo"], r["CODIGO_PV"]),
        axis=1
    )

    chaves_baixadas_ativas = set(
        df_baixas_status["CHAVE_OPERACAO"]
        .dropna()
        .astype(str)
        .str.strip()
        .str.upper()
        .unique()
    )

    mapa_status_operacao = (
        df_baixas_status
        .groupby("CHAVE_OPERACAO")["Status_Baixa"]
        .last()
        .to_dict()
    )
else:
    chaves_baixadas_ativas = set()
    mapa_status_operacao = {}

# --------------------------------------------
# CLASSIFICAÇÃO FINAL OFICIAL
# --------------------------------------------
def classificar_status_operacional(chave):
    chave = str(chave).strip().upper()

    if chave not in chaves_baixadas_ativas:
        return "⏳ Pendente"

    status = str(mapa_status_operacao.get(chave, "")).strip().upper()

    if status == "TERCEIRIZADA":
        return "🟣 Terceirizada"
    else:
        return "✅ Baixado"

# --------------------------------------------
# APLICA STATUS OPERACIONAL
# --------------------------------------------
if not df_operacional.empty:
    df_operacional["Status Operacional"] = df_operacional["CHAVE_OPERACAO"].apply(
        classificar_status_operacional
    )
else:
    df_operacional["Status Operacional"] = ""

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
# COLAPSO DO GARGALO (BASE EXECUTIVA)
# ===============================
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

dem_colapso = dem.groupby("Processo", as_index=False).agg({
    "Horas": "sum",
    "Capacidade": "sum",
    "Ocupacao": "max",
    "Saldo (h)": "sum"
})

dem_colapso = dem_colapso.merge(fila_resumo, on="Processo", how="left")

dem_colapso["Fila Acumulada Max (h)"] = dem_colapso["Fila Acumulada Max (h)"].fillna(0)
dem_colapso["Fila Max (dias)"] = dem_colapso["Fila Max (dias)"].fillna(0)

# Classificação inline (blindada contra NameError)
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

ranking_colapso = dem_colapso.sort_values(
    by=["Ocupacao", "Fila Max (dias)", "Fila Acumulada Max (h)"],
    ascending=[False, False, False]
).reset_index(drop=True)

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

# ============================================================
# ====================== VISÃO GERENCIAL =====================
# ============================================================
st.markdown("## 📊 Visão Gerencial")
st.caption("Indicadores estratégicos, gargalos, capacidade e visão consolidada da produção.")

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

# ===============================
# BASE EXECUTIVA DE COLAPSO (REAPROVEITA A BASE JÁ CALCULADA)
# ===============================
# Blindagem para garantir que a coluna exista sempre
if "Semáforo Colapso" not in ranking_colapso.columns:
    ranking_colapso["Semáforo Colapso"] = "🟢 Sob Controle"

# Blindagem para garantir colunas numéricas
for col in ["Ocupacao", "Fila Max (dias)", "Fila Acumulada Max (h)", "Saldo (h)"]:
    if col not in ranking_colapso.columns:
        ranking_colapso[col] = 0

ranking_colapso["Ocupacao"] = pd.to_numeric(ranking_colapso["Ocupacao"], errors="coerce").fillna(0)
ranking_colapso["Fila Max (dias)"] = pd.to_numeric(ranking_colapso["Fila Max (dias)"], errors="coerce").fillna(0)
ranking_colapso["Fila Acumulada Max (h)"] = pd.to_numeric(ranking_colapso["Fila Acumulada Max (h)"], errors="coerce").fillna(0)
ranking_colapso["Saldo (h)"] = pd.to_numeric(ranking_colapso["Saldo (h)"], errors="coerce").fillna(0)

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

# ===============================
# ALERTA DE COLAPSO DO GARGALO
# ===============================
st.subheader("🚨 Semáforo de Colapso dos Gargalos")

if not ranking_colapso.empty:
    colapso_exib = ranking_colapso.copy()

    # Blindagem estrutural
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
        ].rename(columns={
            "Saldo Exibição (h)": "Saldo (h)"
        }),
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

# ===============================
# ALERTA DE CAPACIDADE CRÍTICA
# ===============================
st.subheader("⚠️ Capacidade Crítica")

critico = dem[dem["Ocupacao"] > 95].copy()

if not critico.empty:
    st.error("Capacidade próxima ou acima do limite detectada.")

    critico_exib = critico.copy()
    critico_exib["Semáforo"] = critico_exib["Ocupacao"].apply(status)
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
# ======================= GRÁFICOS ============================
# ============================================================
with st.expander("📈 Ver gráficos e indicadores visuais", expanded=True):

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
# DISTRIBUIÇÃO DE ATRASO (NOVA VISÃO EXECUTIVA)
# ===============================
st.subheader("📊 Distribuição de Atraso por Faixa")

df_atraso = atrasos.copy()

# Blindagem
if "Atraso (dias)" not in df_atraso.columns:
    df_atraso["Atraso (dias)"] = 0

df_atraso["Atraso (dias)"] = (
    pd.to_numeric(df_atraso["Atraso (dias)"], errors="coerce")
    .fillna(0)
    .clip(lower=0)
)

# Considera apenas atrasos reais
df_atraso = df_atraso[df_atraso["Atraso (dias)"] > 0].copy()

if not df_atraso.empty:

    max_atraso = int(df_atraso["Atraso (dias)"].max())

    # Cria faixas de 2 em 2 dias dinamicamente
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

    # Ordenação correta das faixas
    dist["Ordem"] = dist["Faixa"].astype(str).str.extract(r"(\d+)").astype(int)
    dist = dist.sort_values("Ordem")

    # GRÁFICO DE COLUNAS
    fig_bar = px.bar(
        dist,
        x="Faixa",
        y="Quantidade",
        text="Quantidade",
        title="Escalonamento de Atraso (em dias)",
    )

    fig_bar.update_traces(
        textposition="outside"
    )

    fig_bar.update_layout(
        xaxis_title="Faixa de Atraso (dias)",
        yaxis_title="Quantidade de PVs",
        height=450,
        showlegend=False,
        uniformtext_minsize=8,
        uniformtext_mode='hide'
    )

    st.plotly_chart(fig_bar, use_container_width=True)

    # KPI rápido abaixo do gráfico
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Maior atraso", f"{df_atraso['Atraso (dias)'].max():.0f} dias")

    with col2:
        st.metric("Média", f"{df_atraso['Atraso (dias)'].mean():.1f} dias")

    with col3:
        st.metric("Total em atraso", f"{len(df_atraso)} PVs")

    # DETALHAMENTO
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

# ============================================================
# ===================== ANÁLISE OPERACIONAL ==================
# ============================================================
with st.expander("🏭 Análise Operacional Detalhada", expanded=True):

    st.subheader("🔥 Gargalos do Período")

    gargalos = dem.sort_values(
        by=["Periodo", "Ocupacao", "Horas"],
        ascending=[True, False, False]
    ).copy()

    top_gargalos = gargalos.groupby("Periodo").head(3).reset_index(drop=True)
    top_gargalos["Semáforo"] = top_gargalos["Ocupacao"].apply(status)
    top_gargalos["Ocupação (%)"] = top_gargalos["Ocupacao"].apply(lambda x: fmt_br_pct(x, 1))
    top_gargalos["Horas"] = top_gargalos["Horas"].apply(lambda x: fmt_br_num(x, 1))
    top_gargalos["Capacidade"] = top_gargalos["Capacidade"].apply(lambda x: fmt_br_num(x, 1))
    top_gargalos["Saldo (h)"] = top_gargalos["Saldo (h)"].apply(lambda x: fmt_br_num(x, 1))

    st.dataframe(
        top_gargalos[["Periodo", "Semáforo", "Processo", "Horas", "Capacidade", "Ocupação (%)", "Saldo (h)"]],
        use_container_width=True
    )

    st.subheader("🏭 Carga Real x Capacidade por Processo (h)")

    dem_proc_plot = dem_proc.copy()

    fig_cap_proc = px.bar(
        dem_proc_plot.sort_values("Capacidade Processo", ascending=False),
        x="Processo",
        y=["Horas", "Capacidade Processo"],
        barmode="group"
    )

    fig_cap_proc.update_traces(
        selector=dict(name="Horas"),
        name="Horas Aplicadas",
        marker_color="#FF7A00",
        texttemplate="%{y:.0f}",
        textposition="outside",
        textfont=dict(size=11, color="white")
    )

    fig_cap_proc.update_traces(
        selector=dict(name="Capacidade Processo"),
        marker_color="#1f3b73",
        texttemplate="%{y:.0f}",
        textposition="outside",
        textfont=dict(size=11, color="white")
    )

    fig_cap_proc.update_layout(
        yaxis_title="Horas",
        xaxis_title="Processo",
        legend_title_text="Tipo",
        legend=dict(orientation="h", y=1.1),
        uniformtext_minsize=8,
        uniformtext_mode="show",
        height=650
    )

    st.plotly_chart(
        fig_cap_proc,
        use_container_width=True,
        key="grafico_capacidade_carga_processo"
    )

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

st.subheader("📅 PVs que vencem HOJE")

base_op = df.copy()

if "DATA_ENTREGA_APS" in base_op.columns:
    base_op["DATA_ENTREGA_APS"] = pd.to_datetime(base_op["DATA_ENTREGA_APS"], errors="coerce")
    base_op["Dias para Entrega"] = (base_op["DATA_ENTREGA_APS"] - hoje).dt.days
    base_op["ENTREGA"] = base_op["DATA_ENTREGA_APS"]
else:
    base_op["Dias para Entrega"] = None
    base_op["ENTREGA"] = pd.NaT

pvs_hoje = base_op[base_op["Dias para Entrega"] == 0].copy()

if not pvs_hoje.empty:
    pvs_hoje["Horas"] = pvs_hoje["Horas"].round(1)
    pvs_hoje["ENTREGA"] = pd.to_datetime(pvs_hoje["ENTREGA"], errors="coerce").dt.strftime("%d/%m/%Y")

    st.dataframe(
        pvs_hoje.sort_values("Horas", ascending=False),
        use_container_width=True
    )
else:
    st.success("Nenhuma PV vence hoje ✅")

st.subheader("🔥 Top 10 PVs mais críticas")

criticas = base_op.copy()

criticas = criticas.sort_values(
    ["Dias para Entrega", "Horas"],
    ascending=[True, False]
).head(10)

criticas["Horas"] = criticas["Horas"].round(1)

if "ENTREGA" in criticas.columns:
    criticas["ENTREGA"] = pd.to_datetime(criticas["ENTREGA"], errors="coerce").dt.strftime("%d/%m/%Y")

st.dataframe(criticas, use_container_width=True)

st.subheader("🚨 PVs Urgentes da Semana")

pvs_urgentes = df.copy()

if "DATA_ENTREGA_APS" in pvs_urgentes.columns:
    pvs_urgentes["DATA_ENTREGA_APS"] = pd.to_datetime(
        pvs_urgentes["DATA_ENTREGA_APS"],
        errors="coerce"
    )

    pvs_urgentes["Dias para Entrega"] = (
        pvs_urgentes["DATA_ENTREGA_APS"] - hoje
    ).dt.days

    pvs_urgentes["Semáforo"] = pvs_urgentes["Dias para Entrega"].apply(semaforo_entrega)
    pvs_urgentes["ENTREGA"] = pvs_urgentes["DATA_ENTREGA_APS"]

    urgentes = pvs_urgentes[
        pvs_urgentes["Dias para Entrega"].between(-9999, 7, inclusive="both")
    ].copy()

    urgentes["Horas"] = urgentes["Horas"].round(1)
    urgentes["ENTREGA"] = pd.to_datetime(urgentes["ENTREGA"], errors="coerce").dt.strftime("%d/%m/%Y")

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
    st.info("Não foi possível gerar o painel de urgência porque a coluna DATA_ENTREGA_APS não está disponível.")

# ============================================================
# ===================== VISÃO OPERACIONAL ====================
# ============================================================
st.markdown("## ⚙️ Visão Operacional")
st.caption("Consulta detalhada, filtros, fila de produção e auditorias.")

with st.expander("📋 Tabelas, Filtros e Auditoria", expanded=True):

    st.subheader("📌 Auditoria de Capacidade")

    auditoria = dem.copy()
    auditoria["Semáforo"] = auditoria["Ocupacao"].apply(status)
    auditoria["Ocupação (%)"] = auditoria["Ocupacao"].apply(lambda x: fmt_br_pct(x, 1))
    auditoria["Horas"] = auditoria["Horas"].apply(lambda x: fmt_br_num(x, 1))
    auditoria["Capacidade"] = auditoria["Capacidade"].apply(lambda x: fmt_br_num(x, 1))
    auditoria["Saldo (h)"] = auditoria["Saldo (h)"].apply(lambda x: fmt_br_num(x, 1))

    st.dataframe(
        auditoria[["Periodo", "Semáforo", "Processo", "Horas", "Capacidade", "Ocupação (%)", "Saldo (h)"]],
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
    st.subheader("📌 Fila por Processo")

    fila = df.copy()

    if "ENTREGA" in fila.columns:
        fila["ENTREGA"] = pd.to_datetime(fila["ENTREGA"], errors="coerce")
        fila["Dias para Entrega"] = (fila["ENTREGA"] - hoje).dt.days
    else:
        fila["Dias para Entrega"] = None

    fila["Semáforo"] = fila["Dias para Entrega"].apply(semaforo_entrega)

    col_f1, col_f2 = st.columns(2)

    processos_fila = sorted(fila["Processo"].dropna().unique().tolist())
    processo_fila_sel = col_f1.selectbox(
        "Filtrar por Processo",
        ["Todos"] + processos_fila,
        key="filtro_fila_processo_unico"
    )

    pvs_fila = sorted(fila["PV"].dropna().astype(str).str.strip().unique().tolist())
    pv_fila_sel = col_f2.selectbox(
        "Filtrar por PV específica",
        ["Todas"] + pvs_fila,
        key="filtro_fila_pv_unico"
    )

    if processo_fila_sel != "Todos":
        fila = fila[fila["Processo"] == processo_fila_sel].copy()

    if pv_fila_sel != "Todas":
        fila = fila[fila["PV"].astype(str).str.strip() == pv_fila_sel].copy()

    col_k1, col_k2, col_k3 = st.columns(3)
    col_k1.metric("PVs na Fila", fila["PV"].astype(str).str.strip().nunique())
    col_k2.metric("Processos na Fila", fila["Processo"].nunique())
    col_k3.metric("Horas na Fila", f"{fila['Horas'].sum():.1f} h")

    st.markdown("### 📋 PVs na Fila")

    fila_detalhe = fila.copy()
    fila_detalhe["Horas"] = pd.to_numeric(fila_detalhe["Horas"], errors="coerce").fillna(0).round(1)

    if "ENTREGA" in fila_detalhe.columns:
        fila_detalhe["ENTREGA"] = pd.to_datetime(fila_detalhe["ENTREGA"], errors="coerce")
        fila_detalhe["ENTREGA"] = fila_detalhe["ENTREGA"].dt.strftime("%d/%m/%Y")

    colunas_fila = [
        "Semáforo",
        "PV",
        "Cliente",
        "CODIGO_PV",
        "Processo",
        "Horas",
        "Dias para Entrega",
        "ENTREGA"
    ]
    colunas_fila = [c for c in colunas_fila if c in fila_detalhe.columns]

    ordenacao_fila = [c for c in ["Dias para Entrega", "Processo", "Horas"] if c in fila_detalhe.columns]
    asc_fila = [True, True, False][:len(ordenacao_fila)]

    fila_detalhe_exib = fila_detalhe[colunas_fila].copy()

    if ordenacao_fila:
        fila_detalhe_exib = fila_detalhe_exib.sort_values(
            ordenacao_fila,
            ascending=asc_fila
        )

    fila_detalhe_exib = fila_detalhe_exib.reset_index(drop=True)

    st.dataframe(
        fila_detalhe_exib,
        use_container_width=True,
        hide_index=True
    )

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
# =========== CONTROLE DOS 3 PRINCIPAIS GARGALOS ============
# ============================================================
with st.expander("🎯 Controle dos 3 Principais Gargalos", expanded=True):

    st.subheader("🏭 Operações mais carregadas do APS")
    st.caption("Controle operacional dos 3 processos mais carregados com baixa direta de operação concluída.")

    # --------------------------------------------------------
    # BASE DOS GARGALOS ATUAIS (usa apenas pendentes reais)
    # --------------------------------------------------------
    gargalos_top3 = (
        df.groupby("Processo", as_index=False)
        .agg(
            Horas_Pendentes=("Horas", "sum"),
            PVs_Pendentes=("PV", "nunique")
        )
        .merge(
            dem_proc[["Processo", "Capacidade Processo", "Utilização (%)"]],
            on="Processo",
            how="left"
        )
        .sort_values(["Horas_Pendentes", "PVs_Pendentes"], ascending=[False, False])
        .head(3)
        .reset_index(drop=True)
    )

    if gargalos_top3.empty:
        st.info("Nenhum gargalo pendente encontrado no APS.")
    else:
        gargalos_top3["Horas_Pendentes"] = pd.to_numeric(gargalos_top3["Horas_Pendentes"], errors="coerce").fillna(0).round(1)
        gargalos_top3["Capacidade Processo"] = pd.to_numeric(gargalos_top3["Capacidade Processo"], errors="coerce").fillna(0).round(1)
        gargalos_top3["Utilização (%)"] = pd.to_numeric(gargalos_top3["Utilização (%)"], errors="coerce").fillna(0).round(0).astype(int)
        gargalos_top3["Ranking"] = gargalos_top3.index + 1

        # --------------------------------------------------------
        # DIAS DE FILA DO GARGALO
        # --------------------------------------------------------
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
                [
                    "Ranking",
                    "Processo",
                    "Horas Pendentes (h)",
                    "PVs_Pendentes",
                    "Capacidade Processo (h)",
                    "Dias de Fila",
                    "Utilização (%)"
                ]
            ].rename(columns={
                "PVs_Pendentes": "PVs Pendentes"
            }),
            use_container_width=True,
            hide_index=True
        )

        st.divider()

        # --------------------------------------------------------
        # FILA DOS GARGALOS (usa base visual completa)
        # --------------------------------------------------------
        processos_top3 = gargalos_top3["Processo"].dropna().astype(str).tolist()

        base_gargalos = df_operacional[df_operacional["Processo"].isin(processos_top3)].copy()

        # Blindagem estrutural
        for col in ["PV", "Cliente", "CODIGO_PV", "Processo", "Status Operacional"]:
            if col not in base_gargalos.columns:
                base_gargalos[col] = ""
            base_gargalos[col] = base_gargalos[col].fillna("").astype(str).str.strip()

        if "CHAVE_OPERACAO" not in base_gargalos.columns:
            base_gargalos["CHAVE_OPERACAO"] = (
                base_gargalos["PV"].astype(str).str.strip().str.upper() + "||" +
                base_gargalos["Processo"].astype(str).str.strip().str.upper() + "||" +
                base_gargalos["CODIGO_PV"].astype(str).str.strip().str.upper()
            )
        else:
            base_gargalos["CHAVE_OPERACAO"] = (
                base_gargalos["CHAVE_OPERACAO"].fillna("").astype(str).str.strip().str.upper()
            )

        if "ENTREGA" in base_gargalos.columns:
            base_gargalos["ENTREGA"] = pd.to_datetime(base_gargalos["ENTREGA"], errors="coerce")
            base_gargalos["Dias para Entrega"] = (base_gargalos["ENTREGA"] - hoje).dt.days
            base_gargalos["Semáforo"] = base_gargalos["Dias para Entrega"].apply(semaforo_entrega)
            base_gargalos["ENTREGA_FMT"] = base_gargalos["ENTREGA"].dt.strftime("%d/%m/%Y")
        else:
            base_gargalos["Dias para Entrega"] = None
            base_gargalos["Semáforo"] = "⚪ Sem data"
            base_gargalos["ENTREGA_FMT"] = ""

        base_gargalos["Horas"] = pd.to_numeric(base_gargalos["Horas"], errors="coerce").fillna(0).round(1)

        st.markdown("### 📋 PVs dos Gargalos (Pendentes + Baixadas)")

        processo_baixa_sel = st.selectbox(
            "Selecione o gargalo para trabalhar",
            processos_top3,
            key="gargalo_top3_select_operacional"
        )

        fila_gargalo = base_gargalos[
            base_gargalos["Processo"] == processo_baixa_sel
        ].copy()

        fila_gargalo = fila_gargalo.sort_values(
            ["Status Operacional", "Dias para Entrega", "Horas", "PV"],
            ascending=[True, True, False, True]
        ).reset_index(drop=True)

        # --------------------------------------------------------
        # TEMPO ACUMULADO DE FILA
        # --------------------------------------------------------
        capacidade_dia_gargalo = np.nan

        if "Capacidade/Dia" in gargalos_top3.columns:
            capacidade_tmp = gargalos_top3.loc[
                gargalos_top3["Processo"] == processo_baixa_sel,
                "Capacidade/Dia"
            ]
            if not capacidade_tmp.empty:
                capacidade_dia_gargalo = pd.to_numeric(capacidade_tmp.iloc[0], errors="coerce")

        elif "Capacidade" in gargalos_top3.columns:
            capacidade_tmp = gargalos_top3.loc[
                gargalos_top3["Processo"] == processo_baixa_sel,
                "Capacidade"
            ]
            if not capacidade_tmp.empty:
                capacidade_dia_gargalo = pd.to_numeric(capacidade_tmp.iloc[0], errors="coerce")

        fila_gargalo["Horas"] = pd.to_numeric(fila_gargalo["Horas"], errors="coerce").fillna(0)

        fila_gargalo["Horas_Pendentes_Acumuladas"] = np.where(
            fila_gargalo["Status Operacional"] == "⏳ Pendente",
            fila_gargalo["Horas"],
            0
        )

        fila_gargalo["Fila Acumulada (h)"] = fila_gargalo["Horas_Pendentes_Acumuladas"].cumsum().round(1)

        if pd.notna(capacidade_dia_gargalo) and capacidade_dia_gargalo > 0:
            fila_gargalo["Dias até Entrada"] = (
                fila_gargalo["Fila Acumulada (h)"] / capacidade_dia_gargalo
            ).round(1)

            fila_gargalo["Entrada Prevista"] = fila_gargalo["Dias até Entrada"].apply(
                lambda x: "Hoje" if x <= 1 else f"{int(np.ceil(x))} dias"
            )
        else:
            fila_gargalo["Dias até Entrada"] = np.nan
            fila_gargalo["Entrada Prevista"] = "Sem capacidade"

        fila_gargalo_pendente = fila_gargalo[
            fila_gargalo["Status Operacional"] == "⏳ Pendente"
        ].copy()

        col_g1, col_g2, col_g3, col_g4 = st.columns(4)

        col_g1.metric("Processo Selecionado", processo_baixa_sel)
        col_g2.metric("PVs Pendentes", fmt_br_int(fila_gargalo_pendente["PV"].nunique()))
        col_g3.metric("Horas Pendentes", fmt_br_num(fila_gargalo_pendente["Horas"].sum(), 1) + " h")

        if not fila_gargalo_pendente.empty and "Fila Acumulada (h)" in fila_gargalo_pendente.columns:
            fila_total_h = pd.to_numeric(fila_gargalo_pendente["Fila Acumulada (h)"], errors="coerce").max()
        else:
            fila_total_h = 0

        col_g4.metric("Fila Total do Gargalo", fmt_br_num(fila_total_h, 1) + " h")

        fila_gargalo_exib = fila_gargalo.copy()

        st.dataframe(
            fila_gargalo_exib[
                [
                    "Status Operacional",
                    "Semáforo",
                    "PV",
                    "Cliente",
                    "CODIGO_PV",
                    "Processo",
                    "Horas",
                    "Fila Acumulada (h)",
                    "Entrada Prevista",
                    "Dias para Entrega",
                    "ENTREGA_FMT"
                ]
            ].rename(columns={
                "ENTREGA_FMT": "Entrega"
            }),
            use_container_width=True,
            hide_index=True,
            height=360
        )

        st.divider()

        # --------------------------------------------------------
        # BAIXA OPERACIONAL (usa CHAVE_OPERACAO REAL da linha)
        # --------------------------------------------------------
        st.markdown("### ✅ Dar Baixa em Operação Concluída")

        if fila_gargalo_pendente.empty:
            st.info("Nenhuma PV pendente disponível para baixa neste gargalo.")
        else:
            base_baixa = fila_gargalo_pendente.copy()

            # blindagem estrutural
            for col in ["PV", "Cliente", "CODIGO_PV", "Processo", "Horas", "CHAVE_OPERACAO"]:
                if col not in base_baixa.columns:
                    base_baixa[col] = ""

            base_baixa["PV"] = base_baixa["PV"].fillna("").astype(str).str.strip().str.upper()
            base_baixa["Cliente"] = base_baixa["Cliente"].fillna("SEM CLIENTE").astype(str).str.strip()
            base_baixa["CODIGO_PV"] = base_baixa["CODIGO_PV"].fillna("").astype(str).str.strip().str.upper()
            base_baixa["Processo"] = base_baixa["Processo"].fillna("").astype(str).str.strip().str.upper()
            base_baixa["Horas"] = pd.to_numeric(base_baixa["Horas"], errors="coerce").fillna(0)

            # garante CHAVE_OPERACAO real e padronizada
            base_baixa["CHAVE_OPERACAO"] = (
                base_baixa["PV"].astype(str).str.strip().str.upper() + "||" +
                base_baixa["Processo"].astype(str).str.strip().str.upper() + "||" +
                base_baixa["CODIGO_PV"].astype(str).str.strip().str.upper()
            )

            # remove duplicidade visual da mesma operação
            base_baixa = base_baixa.drop_duplicates(subset=["CHAVE_OPERACAO"]).copy()

            # rótulo único e estável
            base_baixa["ROTULO_BAIXA"] = (
                "PV " + base_baixa["PV"] +
                " | " + base_baixa["Processo"] +
                " | " + base_baixa["CODIGO_PV"] +
                " | " + base_baixa["Horas"].round(1).astype(str) + " h"
            )

            opcoes_baixa = base_baixa["ROTULO_BAIXA"].dropna().astype(str).tolist()

            col_bx1, col_bx2 = st.columns([2, 2])

            baixa_sel = col_bx1.selectbox(
                "Selecione a operação concluída",
                opcoes_baixa,
                key="pv_baixa_top3_select"
            )

            observacao_baixa = col_bx2.text_input(
                "Observação da baixa (opcional)",
                key="obs_baixa_top3_input"
            )

            registro_baixa_df = base_baixa[
                base_baixa["ROTULO_BAIXA"] == baixa_sel
            ].copy()

            if not registro_baixa_df.empty:
                linha_baixa = registro_baixa_df.iloc[0]

                chave_selecionada = str(linha_baixa["CHAVE_OPERACAO"]).strip().upper()

                st.info(
                    f"Você está prestes a registrar a operação **{linha_baixa['Processo']}** "
                    f"da PV **{linha_baixa['PV']}** "
                    f"({fmt_br_num(linha_baixa['Horas'], 1)} h)."
                )

                st.caption(f"🔑 CHAVE_OPERACAO: {chave_selecionada}")

                col_btn1, col_btn2 = st.columns(2)

                # --------------------------------------------
                # BOTÃO BAIXA NORMAL
                # --------------------------------------------
                if col_btn1.button("💾 Confirmar Baixa Operacional", key="btn_confirmar_baixa_top3"):

                    registro_baixa = {
                        "PV": str(linha_baixa["PV"]).strip().upper(),
                        "Cliente": str(linha_baixa.get("Cliente", "SEM CLIENTE")).strip(),
                        "CODIGO_PV": str(linha_baixa.get("CODIGO_PV", "")).strip().upper(),
                        "Processo": str(linha_baixa["Processo"]).strip().upper(),
                        "Horas": float(linha_baixa["Horas"]),
                        "Data_Baixa": pd.Timestamp.now(),
                        "Usuario": "APS",
                        "Observacao": observacao_baixa.strip() if observacao_baixa else "",
                        "Status_Baixa": "ATIVA",
                        "Data_Estorno": pd.NaT,
                        "Motivo_Estorno": ""
                    }

                    try:
                        df_baixas_salvo = salvar_baixa_operacional(BASE_PATH, registro_baixa)
                        st.cache_data.clear()

                        st.success("✅ Baixa operacional registrada com sucesso.")
                        st.info(
                            f"Registro salvo: PV {registro_baixa['PV']} | "
                            f"{registro_baixa['Processo']} | "
                            f"{fmt_br_num(registro_baixa['Horas'], 1)} h"
                        )

                        if df_baixas_salvo is not None and not df_baixas_salvo.empty:
                            st.caption(f"📁 Total de baixas registradas: {len(df_baixas_salvo)}")

                            # auditoria rápida pós-gravação
                            df_baixas_teste = df_baixas_salvo.copy()

                            for col in ["PV", "Processo", "CODIGO_PV"]:
                                if col not in df_baixas_teste.columns:
                                    df_baixas_teste[col] = ""

                                df_baixas_teste[col] = (
                                    df_baixas_teste[col]
                                    .fillna("")
                                    .astype(str)
                                    .str.strip()
                                    .str.upper()
                                )

                            df_baixas_teste["CHAVE_OPERACAO"] = (
                                df_baixas_teste["PV"].astype(str).str.strip().str.upper() + "||" +
                                df_baixas_teste["Processo"].astype(str).str.strip().str.upper() + "||" +
                                df_baixas_teste["CODIGO_PV"].astype(str).str.strip().str.upper()
                            )

                            if chave_selecionada in df_baixas_teste["CHAVE_OPERACAO"].tolist():
                                st.success("🧠 Validação: a operação foi localizada corretamente no histórico.")
                            else:
                                st.error("❌ Validação falhou: a operação não foi localizada no histórico após salvar.")

                        st.rerun()

                    except Exception as e:
                        st.error(f"Erro ao salvar baixa operacional: {e}")

                # --------------------------------------------
                # BOTÃO TERCEIRIZADA
                # --------------------------------------------
                if col_btn2.button("🟣 Marcar como Terceirizada", key="btn_terceirizada_top3"):

                    registro_baixa = {
                        "PV": str(linha_baixa["PV"]).strip().upper(),
                        "Cliente": str(linha_baixa.get("Cliente", "SEM CLIENTE")).strip(),
                        "CODIGO_PV": str(linha_baixa.get("CODIGO_PV", "")).strip().upper(),
                        "Processo": str(linha_baixa["Processo"]).strip().upper(),
                        "Horas": float(linha_baixa["Horas"]),
                        "Data_Baixa": pd.Timestamp.now(),
                        "Usuario": "APS",
                        "Observacao": f"TERCEIRIZADA | {observacao_baixa.strip()}" if observacao_baixa else "TERCEIRIZADA",
                        "Status_Baixa": "TERCEIRIZADA",
                        "Data_Estorno": pd.NaT,
                        "Motivo_Estorno": ""
                    }

                    try:
                        df_baixas_salvo = salvar_baixa_operacional(BASE_PATH, registro_baixa)
                        st.cache_data.clear()

                        st.success("🟣 Operação marcada como terceirizada.")
                        st.info(
                            f"Registro salvo: PV {registro_baixa['PV']} | "
                            f"{registro_baixa['Processo']} | "
                            f"{fmt_br_num(registro_baixa['Horas'], 1)} h"
                        )

                        if df_baixas_salvo is not None and not df_baixas_salvo.empty:
                            st.caption(f"📁 Total de registros operacionais: {len(df_baixas_salvo)}")

                            # auditoria rápida pós-gravação
                            df_baixas_teste = df_baixas_salvo.copy()

                            for col in ["PV", "Processo", "CODIGO_PV"]:
                                if col not in df_baixas_teste.columns:
                                    df_baixas_teste[col] = ""

                                df_baixas_teste[col] = (
                                    df_baixas_teste[col]
                                    .fillna("")
                                    .astype(str)
                                    .str.strip()
                                    .str.upper()
                                )

                            df_baixas_teste["CHAVE_OPERACAO"] = (
                                df_baixas_teste["PV"].astype(str).str.strip().str.upper() + "||" +
                                df_baixas_teste["Processo"].astype(str).str.strip().str.upper() + "||" +
                                df_baixas_teste["CODIGO_PV"].astype(str).str.strip().str.upper()
                            )

                            if chave_selecionada in df_baixas_teste["CHAVE_OPERACAO"].tolist():
                                st.success("🧠 Validação: a operação terceirizada foi localizada corretamente no histórico.")
                            else:
                                st.error("❌ Validação falhou: a operação terceirizada não foi localizada no histórico após salvar.")

                        st.rerun()

                    except Exception as e:
                        st.error(f"Erro ao registrar terceirização: {e}")

        st.divider()

        # --------------------------------------------------------
        # DESFAZER BAIXA OPERACIONAL
        # --------------------------------------------------------
        st.markdown("### 🔁 Desfazer Baixa Operacional")

        if "df_baixas_historico" not in locals() or df_baixas_historico is None or df_baixas_historico.empty:
            st.info("Nenhuma baixa operacional disponível para estorno.")
        else:
            df_baixas_ativas_ui = df_baixas_historico.copy()

            if "Status_Baixa" not in df_baixas_ativas_ui.columns:
                df_baixas_ativas_ui["Status_Baixa"] = "ATIVA"

            df_baixas_ativas_ui["Status_Baixa"] = (
                df_baixas_ativas_ui["Status_Baixa"]
                .fillna("ATIVA")
                .astype(str)
                .str.strip()
                .str.upper()
            )

            df_baixas_ativas_ui = df_baixas_ativas_ui[
                df_baixas_ativas_ui["Status_Baixa"].isin(["ATIVA", "TERCEIRIZADA"])
            ].copy()

            if cliente_sel != "Todos" and "Cliente" in df_baixas_ativas_ui.columns:
                df_baixas_ativas_ui = df_baixas_ativas_ui[
                    df_baixas_ativas_ui["Cliente"].astype(str).str.strip() == cliente_sel
                ].copy()

            if df_baixas_ativas_ui.empty:
                st.info("Nenhuma baixa ativa disponível para estorno.")
            else:
                df_baixas_ativas_ui["ROTULO_ESTORNO"] = (
                    "PV " + df_baixas_ativas_ui["PV"].astype(str).str.strip() +
                    " | " + df_baixas_ativas_ui["Processo"].astype(str).str.strip() +
                    " | " + df_baixas_ativas_ui["CODIGO_PV"].astype(str).str.strip() +
                    " | " + df_baixas_ativas_ui["Horas"].astype(str)
                )

                opcoes_estorno = df_baixas_ativas_ui["ROTULO_ESTORNO"].dropna().astype(str).tolist()

                col_est1, col_est2 = st.columns([2, 2])

                baixa_estorno_sel = col_est1.selectbox(
                    "Selecione a baixa para desfazer",
                    opcoes_estorno,
                    key="select_estorno_baixa_operacional"
                )

                motivo_estorno = col_est2.text_input(
                    "Motivo do estorno",
                    key="motivo_estorno_baixa_operacional"
                )

                linha_estorno = df_baixas_ativas_ui[
                    df_baixas_ativas_ui["ROTULO_ESTORNO"] == baixa_estorno_sel
                ].copy()

                if not linha_estorno.empty:
                    linha_estorno = linha_estorno.iloc[0]

                    st.warning(
                        f"Você está prestes a desfazer a baixa da PV **{linha_estorno['PV']}** "
                        f"no processo **{linha_estorno['Processo']}**."
                    )

                    if st.button("🔁 Confirmar Estorno da Baixa", key="btn_estornar_baixa_operacional"):
                        try:
                            ok_estorno, msg_estorno = estornar_baixa_operacional(
                                BASE_PATH,
                                pv=linha_estorno["PV"],
                                processo=linha_estorno["Processo"],
                                codigo_pv=linha_estorno.get("CODIGO_PV", ""),
                                motivo_estorno=motivo_estorno
                            )

                            if ok_estorno:
                                st.cache_data.clear()
                                st.success(f"✅ {msg_estorno}")
                                st.rerun()
                            else:
                                st.warning(f"⚠️ {msg_estorno}")

                        except Exception as e:
                            st.error(f"Erro ao estornar baixa operacional: {e}")

        # --------------------------------------------------------
        # HISTÓRICO PREMIUM DE BAIXAS
        # --------------------------------------------------------
        st.markdown("### 🧾 Histórico Premium de Baixas Operacionais")

        if "df_baixas_historico" not in locals() or df_baixas_historico is None:
            df_baixas_exib = pd.DataFrame(columns=COLUNAS_BAIXAS)
        else:
            df_baixas_exib = df_baixas_historico.copy()

        if not df_baixas_exib.empty:
            for col in ["PV", "Cliente", "CODIGO_PV", "Processo", "Usuario", "Observacao", "Status_Baixa", "Motivo_Estorno", "Data_Estorno"]:
                if col in df_baixas_exib.columns:
                    df_baixas_exib[col] = df_baixas_exib[col].fillna("").astype(str).str.strip()

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

            col_hist1, col_hist2, col_hist3 = st.columns([2, 2, 2])

            status_hist_sel = col_hist1.selectbox(
                "Filtrar por status",
                ["Todos", "ATIVA", "TERCEIRIZADA", "ESTORNADA"],
                key="filtro_status_historico_baixas"
            )

            processo_hist_sel = col_hist2.selectbox(
                "Filtrar por processo",
                ["Todos"] + sorted(df_baixas_exib["Processo"].dropna().astype(str).str.strip().unique().tolist()),
                key="filtro_processo_historico_baixas"
            )

            cliente_hist_sel = col_hist3.selectbox(
                "Filtrar por cliente",
                ["Todos"] + sorted(df_baixas_exib["Cliente"].dropna().astype(str).str.strip().unique().tolist()),
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
            col_hk4.metric("Horas Registradas", fmt_br_num(pd.to_numeric(df_baixas_exib["Horas"], errors="coerce").fillna(0).sum(), 1) + " h")

            if "Data_Baixa" in df_baixas_exib.columns:
                df_baixas_exib["Data_Baixa"] = df_baixas_exib["Data_Baixa"].dt.strftime("%d/%m/%Y %H:%M")

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

            df_baixas_exib = df_baixas_exib.sort_values(
                by=["Data_Baixa"],
                ascending=False,
                na_position="last"
            ).copy()

            st.dataframe(
                df_baixas_exib[
                    [
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
                ].rename(columns={
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