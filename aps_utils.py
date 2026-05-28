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

    # ========================================================
    # 🔒 DATAFRAME VAZIO SEGURO
    # ========================================================
    if df_baixas is None or len(df_baixas) == 0:

        return pd.DataFrame({

            "PV": [],
            "Cliente": [],
            "CODIGO_PV": [],
            "Processo": [],
            "Horas": [],
            "Data_Baixa": [],
            "Usuario": [],
            "Observacao": [],
            "Status_Baixa": [],
            "Data_Estorno": [],
            "Motivo_Estorno": [],
            "CHAVE_OPERACAO": []
        })

    # ========================================================
    # 🔥 CÓPIA SEGURA
    # ========================================================
    df_baixas = df_baixas.copy()

    # ========================================================
    # 🔒 GARANTE COLUNAS
    # ========================================================
    colunas_obrigatorias = [

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
        "Motivo_Estorno",
        "CHAVE_OPERACAO"
    ]

    for col in colunas_obrigatorias:

        if col not in df_baixas.columns:

            if col == "Horas":

                df_baixas[col] = 0

            else:

                df_baixas[col] = ""

    # ========================================================
    # 🔥 MANTÉM SOMENTE COLUNAS OFICIAIS
    # ========================================================
    df_baixas = df_baixas[
        colunas_obrigatorias
    ].copy()

    # ========================================================
    # 🔥 NORMALIZAÇÃO TEXTO
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

            .str.replace(".0", "", regex=False)

            .str.replace("\xa0", "", regex=False)

            .str.replace("  ", " ", regex=False)

            .str.strip()

            .str.upper()
        )

    # ========================================================
    # 🔥 PROCESSO OFICIAL APS
    # ========================================================
    df_baixas["Processo_Original"] = (
        df_baixas["Processo"]
    )

    df_baixas["Processo"] = (

        df_baixas["Processo"]

        .fillna("")

        .astype(str)

        .str.strip()

        .apply(normalizar_processo)
    )

    st.warning(
        f"🔥 PROCESSOS APÓS NORMALIZAÇÃO: "
        f"{df_baixas['Processo'].unique()[:10]}"
    )

    # ========================================================
    # 🔥 CLIENTE PADRÃO
    # ========================================================
    df_baixas["Cliente"] = (

        df_baixas["Cliente"]

        .replace("", "SEM CLIENTE")
    )

    # ========================================================
    # 🔥 STATUS PADRÃO
    # ========================================================
    df_baixas["Status_Baixa"] = (

        df_baixas["Status_Baixa"]

        .replace("", "ATIVA")

        .str.upper()
    )

    # ========================================================
    # 🔥 HORAS
    # ========================================================
    df_baixas["Horas"] = (

        pd.to_numeric(
            df_baixas["Horas"],
            errors="coerce"
        )

        .fillna(0)
    )

    # ========================================================
    # 🔥 DATA BAIXA
    # ========================================================
    df_baixas["Data_Baixa"] = pd.to_datetime(

        df_baixas["Data_Baixa"],

        errors="coerce"
    )

    # ========================================================
    # 🔥 CHAVE OPERACIONAL
    # ========================================================
    df_baixas["CHAVE_OPERACAO"] = (

        df_baixas["CHAVE_OPERACAO"]

        .fillna("")

        .astype(str)

        .str.strip()

        .str.upper()
    )

    mascara_chave_vazia = (

        (df_baixas["CHAVE_OPERACAO"] == "")

        |

        (df_baixas["CHAVE_OPERACAO"] == "|||")
    )

    if mascara_chave_vazia.any():

        df_baixas.loc[
            mascara_chave_vazia,
            "CHAVE_OPERACAO"
        ] = df_baixas.loc[
            mascara_chave_vazia
        ].apply(

            lambda r: gerar_chave_operacao(
                r["PV"],
                r["Processo"],
                r["CODIGO_PV"]
            ),

            axis=1
        )

    # ========================================================
    # 🔒 REMOVE CHAVES INVÁLIDAS
    # ========================================================
    df_baixas = (

        df_baixas[

            (df_baixas["CHAVE_OPERACAO"] != "")

            &

            (df_baixas["CHAVE_OPERACAO"] != "|||")

        ]

        .copy()
    )

    # ========================================================
    # 🔒 REMOVE LINHAS VAZIAS
    # ========================================================
    for col in [

        "PV",
        "Processo",
        "CODIGO_PV"

    ]:

        df_baixas[col] = (

            df_baixas[col]

            .fillna("")

            .astype(str)

            .str.strip()

            .replace("NAN", "")

            .replace("NONE", "")

            .replace("NULL", "")
        )

    df_baixas = (

        df_baixas[

            (df_baixas["PV"] != "")

            &

            (df_baixas["Processo"] != "")

            &

            (df_baixas["CODIGO_PV"] != "")

        ]

        .copy()
    )

    # ========================================================
    # 🔥 REMOVE DUPLICADOS
    # ========================================================
    df_baixas = (

        df_baixas

        .drop_duplicates()

        .reset_index(drop=True)
    )

    # ========================================================
    # 🔥 ORDENAÇÃO FINAL
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