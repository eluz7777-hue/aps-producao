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
    "SOLDAGEM AÇO": 2,
    "SOLDAGEM ALUMINIO":2,
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

# 🔧 horário Brasil sem pytz
from datetime import datetime
from zoneinfo import ZoneInfo

agora_br = datetime.now(ZoneInfo("America/Sao_Paulo"))

st.write("Última atualização:", agora_br.strftime("%d/%m/%Y %H:%M:%S"))



# ===============================
# LEITURA
# ===============================
PAGE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(PAGE_DIR)

arquivo_pv = os.path.join(ROOT_DIR, "PV.xlsx")
BASE_PATH = ROOT_DIR


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
    "SOLDAGEM AÇO",
    "SOLDAGEM ALUMINIO",
    "ACABAMENTO",
    "JATEAMENTO",
    "PINTURA",
    "MONTAGEM",
    "DIVERSOS"
]


# ============================================================
# 🔥 NORMALIZAÇÃO GLOBAL DE PROCESSOS APS
# ============================================================

MAPEAMENTO_PROCESSOS = {

    # --------------------------------------------------------
    # CORTE - SERRA
    # --------------------------------------------------------
    "CORTE-SERRA": "CORTE - SERRA",
    "CORTE / SERRA": "CORTE - SERRA",
    "CORTE_SERRA": "CORTE - SERRA",
    "CORTE SERRA": "CORTE - SERRA",

    # --------------------------------------------------------
    # CORTE-LASER
    # --------------------------------------------------------
    "CORTE LASER": "CORTE-LASER",
    "LASER": "CORTE-LASER",

    # --------------------------------------------------------
    # CORTE-PLASMA
    # --------------------------------------------------------
    "CORTE PLASMA": "CORTE-PLASMA",
    "PLASMA": "CORTE-PLASMA",

    # --------------------------------------------------------
    # TORNO CONVENCIONAL
    # --------------------------------------------------------
    "TORNO": "TORNO CONVENCIONAL",

    # --------------------------------------------------------
    # FRESADORAS
    # --------------------------------------------------------
    "FRESA": "FRESADORAS",
    "FRESADORA": "FRESADORAS",

    # --------------------------------------------------------
    # SOLDAGEM
    # --------------------------------------------------------
    "SOLDA": "SOLDAGEM",

    # --------------------------------------------------------
    # CENTRO DE USINAGEM
    # --------------------------------------------------------
    "USINAGEM": "CENTRO DE USINAGEM",
    "CENTRO USINAGEM": "CENTRO DE USINAGEM",

    # --------------------------------------------------------
    # ACABAMENTO
    # --------------------------------------------------------
    "FINALIZACAO": "ACABAMENTO",
    "FINALIZAÇÃO": "ACABAMENTO"
}


# ============================================================
# 🔥 FUNÇÃO GLOBAL NORMALIZAÇÃO PROCESSOS
# ============================================================

def normalizar_processo(valor):

    if pd.isna(valor):
        return "DIVERSOS"

    valor = (

        str(valor)

        .strip()

        .upper()
    )

    valor = (
        MAPEAMENTO_PROCESSOS.get(
            valor,
            valor
        )
    )

    return valor


# ============================================================
# 🔥 NORMALIZA NOMES DE COLUNAS DA PV
# ============================================================

df_pv.columns = [

    normalizar_processo(col)

    if col != "Processo"

    else col

    for col in df_pv.columns
]


# ============================================================
# 🔥 PROCESSOS EXISTENTES NA PV
# ============================================================

processos = [

    p

    for p in PROCESSOS_VALIDOS

    if p in df_pv.columns
]


# ============================================================
# 🔥 CONVERSÃO NUMÉRICA DOS TEMPOS
# ============================================================

for proc in processos:

    df_pv[proc] = (

        df_pv[proc]

        .astype(str)

        .str.replace(",", ".", regex=False)

        .str.strip()
    )

    df_pv[proc] = pd.to_numeric(

        df_pv[proc],

        errors="coerce"

    ).fillna(0)





# ===============================
# EXPANSÃO CORRIGIDA (SEM ERRO)
# 🔥 VERSÃO DEFINITIVA APS
# 🔥 CHAVE_OPERACAO INTEGRADA
# ===============================
pvs_totais_excel = df_pv["PV"].astype(str).str.strip().nunique()

pvs_excel_set = set(
    df_pv["PV"]
    .astype(str)
    .str.strip()
    .unique()
)

linhas = []

pvs_excluidas = []

pvs_sem_carga = []

auditoria_pv = []

for _, row in df_pv.iterrows():

    pv_atual = str(
        row["PV"]
    ).strip()

    cliente_atual = row.get(
        "CLIENTE",
        "SEM CLIENTE"
    )

    codigo_atual = str(
        row["CODIGO_PV"]
    ).strip()

    status_pv = "OK"

    qtde_processos_validos = 0

    horas_totais_pv = 0

    motivos_pv = []

    tempos_debug = []

    # -------------------------------
    # Validações básicas
    # -------------------------------
    data_valida = not pd.isna(
        row["ENTREGA"]
    )

    qtd_valida = (

        pd.notna(row["QTD"])

        and

        float(row["QTD"]) > 0
    )

    if not data_valida:

        motivos_pv.append(
            "Data de entrega inválida"
        )

    if not qtd_valida:

        motivos_pv.append(
            "Quantidade zero ou inválida"
        )

    # --------------------------------------------------------
    # 🔒 DATA/QTD INVÁLIDA
    # --------------------------------------------------------
    if not data_valida or not qtd_valida:

        status_pv = "Inconsistente"

        registro = {

            "PV": pv_atual,

            "Cliente": cliente_atual,

            "CODIGO": codigo_atual,

            "CODIGO_PV": codigo_atual,

            "DATA_ENTREGA_APS": row.get(
                "DATA_ENTREGA_APS",
                pd.NaT
            ),

            "Motivo": " | ".join(
                motivos_pv
            )
        }

        pvs_excluidas.append(
            registro
        )

        pvs_sem_carga.append(
            registro
        )

        auditoria_pv.append({

            "PV": pv_atual,

            "Cliente": cliente_atual,

            "CODIGO": codigo_atual,

            "CODIGO_PV": codigo_atual,

            "DATA_ENTREGA_APS": row.get(
                "DATA_ENTREGA_APS",
                pd.NaT
            ),

            "Status": status_pv,

            "Qtd": row["QTD"],

            "Total Processos Válidos": 0,

            "Horas Totais": 0,

            "Motivo": " | ".join(
                motivos_pv
            )
        })

        continue

    # --------------------------------------------------------
    # 🔥 EXPANSÃO DOS PROCESSOS
    # --------------------------------------------------------
    for proc in processos:

        valor_original = row.get(proc)

        tempo = pd.to_numeric(
            valor_original,
            errors="coerce"
        )

        if pd.notna(tempo) and tempo > 0:

            qtde_processos_validos += 1

            # ------------------------------------------------
            # 🔥 HORAS OPERACIONAIS
            # ------------------------------------------------
            horas = (

                tempo

                * float(row["QTD"])

            ) / 60

            horas_totais_pv += horas

            # ------------------------------------------------
            # 🔥 PROCESSO NORMALIZADO
            # ------------------------------------------------
            processo_normalizado = (
                normalizar_processo(proc)
            )

            # ------------------------------------------------
            # 🔥 CHAVE OPERACIONAL APS
            # ------------------------------------------------
            chave_operacao = (

                str(pv_atual)

                .strip()

                .upper()

                + "||"

                + str(
                    processo_normalizado
                )

                .strip()

                .upper()

                + "||"

                + str(codigo_atual)

                .strip()

                .upper()
            )

            # ------------------------------------------------
            # 🔥 REGISTRO OPERACIONAL
            # ------------------------------------------------
            linhas.append({

                "PV": pv_atual,

                "Cliente": cliente_atual,

                "CODIGO_PV": codigo_atual,

                # =============================================
                # 🔥 PROCESSO NORMALIZADO APS
                # =============================================
                "Processo": processo_normalizado,

                "Data": row["ENTREGA"],

                "ENTREGA": row["ENTREGA"],

                "DATA_ENTREGA_APS": row.get(
                    "DATA_ENTREGA_APS",
                    row["ENTREGA"]
                ),

                "Horas": horas,

                # =============================================
                # 🔥 CHAVE OPERACIONAL OFICIAL APS
                # =============================================
                "CHAVE_OPERACAO": chave_operacao
            })

        else:

            tempos_debug.append(
                f"{proc}={valor_original}"
            )

    # --------------------------------------------------------
    # 🔒 SEM PROCESSOS VÁLIDOS
    # --------------------------------------------------------
    if qtde_processos_validos == 0:

        status_pv = "Sem processo válido"

        motivo_sem_processo = (
            "Nenhum processo com tempo > 0"
        )

        if tempos_debug:

            motivo_sem_processo += (

                " | "

                + " ; ".join(
                    tempos_debug[:10]
                )
            )

        registro = {

            "PV": pv_atual,

            "Cliente": cliente_atual,

            "CODIGO": codigo_atual,

            "CODIGO_PV": codigo_atual,

            "DATA_ENTREGA_APS": row.get(
                "DATA_ENTREGA_APS",
                pd.NaT
            ),

            "Motivo": motivo_sem_processo
        }

        pvs_excluidas.append(
            registro
        )

        pvs_sem_carga.append(
            registro
        )

        auditoria_pv.append({

            "PV": pv_atual,

            "Cliente": cliente_atual,

            "CODIGO": codigo_atual,

            "CODIGO_PV": codigo_atual,

            "DATA_ENTREGA_APS": row.get(
                "DATA_ENTREGA_APS",
                pd.NaT
            ),

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

            "DATA_ENTREGA_APS": row.get(
                "DATA_ENTREGA_APS",
                pd.NaT
            ),

            "Status": status_pv,

            "Qtd": row["QTD"],

            "Total Processos Válidos": (
                qtde_processos_validos
            ),

            "Horas Totais": (
                horas_totais_pv
            ),

            "Motivo": ""
        })

# ============================================================
# 🔥 BASE PRINCIPAL OPERACIONAL APS
# ============================================================
df_original = pd.DataFrame(
    linhas
)

# ============================================================
# 🔥 BLINDAGEM DE COLUNAS CRÍTICAS
# ============================================================
if not df_original.empty:

    # --------------------------------------------------------
    # 🔥 DATA_ENTREGA_APS
    # --------------------------------------------------------
    if "DATA_ENTREGA_APS" in df_original.columns:

        df_original[
            "DATA_ENTREGA_APS"
        ] = pd.to_datetime(

            df_original[
                "DATA_ENTREGA_APS"
            ],

            errors="coerce",

            dayfirst=True
        )

    # --------------------------------------------------------
    # 🔥 ENTREGA
    # --------------------------------------------------------
    if "ENTREGA" in df_original.columns:

        df_original[
            "ENTREGA"
        ] = pd.to_datetime(

            df_original[
                "ENTREGA"
            ],

            errors="coerce",

            dayfirst=True
        )

    # --------------------------------------------------------
    # 🔥 DATA
    # --------------------------------------------------------
    if "Data" in df_original.columns:

        df_original[
            "Data"
        ] = pd.to_datetime(

            df_original[
                "Data"
            ],

            errors="coerce",

            dayfirst=True
        )

    # --------------------------------------------------------
    # 🔥 NORMALIZA PROCESSO FINAL
    # --------------------------------------------------------
    if "Processo" in df_original.columns:

        df_original[
            "Processo"
        ] = (

            df_original[
                "Processo"
            ]

            .fillna("")

            .astype(str)

            .apply(
                normalizar_processo
            )
        )

    # --------------------------------------------------------
    # 🔥 NORMALIZA CHAVE FINAL
    # --------------------------------------------------------
    if "CHAVE_OPERACAO" in df_original.columns:

        df_original[
            "CHAVE_OPERACAO"
        ] = (

            df_original[
                "CHAVE_OPERACAO"
            ]

            .fillna("")

            .astype(str)

            .str.upper()

            .str.strip()
        )

# ============================================================
# 🔥 BASE OPERACIONAL OFICIAL APS
# ============================================================
df_operacional = df_original.copy()




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

    # ========================================================
    # 🔒 DATAFRAME VAZIO
    # ========================================================
    if df_baixas is None or df_baixas.empty:

        return pd.DataFrame(
            columns=COLUNAS_BAIXAS + ["CHAVE_OPERACAO"]
        )

    # ========================================================
    # 🔥 CÓPIA SEGURA
    # ========================================================
    df_baixas = df_baixas.copy()

    # ========================================================
    # 🔥 GARANTE TODAS AS COLUNAS
    # ========================================================
    for col in COLUNAS_BAIXAS:

        if col not in df_baixas.columns:
            df_baixas[col] = None

    # 🔥 CHAVE OPERACIONAL
    if "CHAVE_OPERACAO" not in df_baixas.columns:
        df_baixas["CHAVE_OPERACAO"] = ""

    # ========================================================
    # 🔥 MANTÉM TODAS AS COLUNAS NECESSÁRIAS
    # ========================================================
    df_baixas = df_baixas[
        COLUNAS_BAIXAS + ["CHAVE_OPERACAO"]
    ].copy()

    # ========================================================
    # 🔥 COLUNAS TEXTO
    # ========================================================
    colunas_texto = [

        "PV",
        "Cliente",
        "CODIGO_PV",
        "Processo",
        "Usuario",
        "Observacao",
        "Status_Baixa",
        "Data_Estorno",
        "Motivo_Estorno",
        "CHAVE_OPERACAO"
    ]

    for col in colunas_texto:

        df_baixas[col] = (

            df_baixas[col]

            .fillna("")

            .astype(str)

            .str.strip()
        )

    # ========================================================
    # 🔥 NORMALIZAÇÃO
    # ========================================================
    df_baixas["PV"] = (
        df_baixas["PV"]
        .str.upper()
    )

    df_baixas["CODIGO_PV"] = (
        df_baixas["CODIGO_PV"]
        .str.upper()
    )

    # ========================================================
    # 🔥 NORMALIZAÇÃO INDUSTRIAL PROCESSOS APS
    # ========================================================
    df_baixas["Processo"] = (

        df_baixas["Processo"]

        .fillna("")

        .astype(str)

        .str.strip()

        .apply(normalizar_processo)
    )

    df_baixas["Cliente"] = (
        df_baixas["Cliente"]
        .replace("", "SEM CLIENTE")
    )

    # ========================================================
    # 🔥 STATUS
    # ========================================================
    df_baixas["Status_Baixa"] = (

        df_baixas["Status_Baixa"]

        .replace("", "ATIVA")

        .str.upper()
    )

    # ========================================================
    # 🔥 NUMÉRICOS
    # ========================================================
    df_baixas["Horas"] = (

        pd.to_numeric(
            df_baixas["Horas"],
            errors="coerce"
        )

        .fillna(0)
    )

    # ========================================================
    # 🔥 DATAS
    # ========================================================
    df_baixas["Data_Baixa"] = pd.to_datetime(

        df_baixas["Data_Baixa"],

        errors="coerce"
    )

    df_baixas["Data_Estorno"] = (
        df_baixas["Data_Estorno"]
        .fillna("")
        .astype(str)
    )

    # ========================================================
    # 🔥 RECRIA CHAVE SE NECESSÁRIO
    # ========================================================
    df_baixas["CHAVE_OPERACAO"] = np.where(

        df_baixas["CHAVE_OPERACAO"].astype(str).str.strip() == "",

        (
            df_baixas["PV"]
            + "||"
            + df_baixas["Processo"]
            + "||"
            + df_baixas["CODIGO_PV"]
        ),

        df_baixas["CHAVE_OPERACAO"]
    )

    # ========================================================
    # 🔥 REMOVE DUPLICIDADES
    # ========================================================
    df_baixas = (

        df_baixas

        .drop_duplicates()

        .reset_index(drop=True)
    )

    # ========================================================
    # 🔥 ORDENAÇÃO
    # ========================================================
    df_baixas = (

        df_baixas

        .sort_values(

            by=[
                "Data_Baixa",
                "PV",
                "Processo"
            ],

            ascending=[
                False,
                True,
                True
            ]
        )

        .reset_index(drop=True)
    )

    return df_baixas



# ============================================================
# BASE OPERACIONAL VISUAL
# ============================================================

# 🔒 GARANTIA DA BASE PRINCIPAL
if "df" not in locals() or df is None:
    df = df_original.copy()

# 🔒 BASE OPERACIONAL
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