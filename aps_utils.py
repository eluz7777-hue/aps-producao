import pandas as pd

import numpy as np

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





# ============================================================
# 🔥 CHAVE OPERACIONAL OFICIAL APS
# ============================================================
def gerar_chave_operacao(pv, processo, codigo):

    pv = (
        str(pv)
        .replace(".0", "")
        .replace("\xa0", "")
        .strip()
        .upper()
    )

    processo = (
        normalizar_processo(processo)
        .replace(".0", "")
        .replace("\xa0", "")
        .strip()
        .upper()
    )

    codigo = (
        str(codigo)
        .replace(".0", "")
        .replace("\xa0", "")
        .strip()
        .upper()
    )

    return f"{pv}||{processo}||{codigo}"


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

# ===============================
# NORMALIZAÇÃO DE CÓDIGO
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
# BAIXAS APS
# ===============================
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


# ===============================
# PADRONIZAÇÃO DE BAIXAS APS
# ===============================
def _padronizar_df_baixas(df_baixas):

    if df_baixas is None or df_baixas.empty:

        return pd.DataFrame(
            columns=COLUNAS_BAIXAS + ["CHAVE_OPERACAO"]
        )

    df_baixas = df_baixas.copy()

    for col in COLUNAS_BAIXAS:

        if col not in df_baixas.columns:
            df_baixas[col] = None

    if "CHAVE_OPERACAO" not in df_baixas.columns:
        df_baixas["CHAVE_OPERACAO"] = ""

    df_baixas = df_baixas[
        COLUNAS_BAIXAS + ["CHAVE_OPERACAO"]
    ].copy()

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

    df_baixas["PV"] = (
        df_baixas["PV"]
        .str.upper()
    )

    df_baixas["CODIGO_PV"] = (
        df_baixas["CODIGO_PV"]
        .str.upper()
    )

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

    df_baixas["Status_Baixa"] = (
        df_baixas["Status_Baixa"]
        .replace("", "ATIVA")
        .str.upper()
    )

    df_baixas["Horas"] = (
        pd.to_numeric(
            df_baixas["Horas"],
            errors="coerce"
        )
        .fillna(0)
    )

    df_baixas["Data_Baixa"] = pd.to_datetime(
        df_baixas["Data_Baixa"],
        errors="coerce"
    )

    df_baixas["Data_Estorno"] = (
        df_baixas["Data_Estorno"]
        .fillna("")
        .astype(str)
    )

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

    df_baixas = (
        df_baixas
        .drop_duplicates()
        .reset_index(drop=True)
    )

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




