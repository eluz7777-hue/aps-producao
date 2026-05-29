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

    # ========================================================
    # 🔥 PV
    # ========================================================
    pv = (
        str(pv)
        .replace(".0", "")
        .replace("\xa0", "")
        .strip()
        .upper()
    )

    # ========================================================
    # 🔥 PROCESSO
    # ========================================================
    processo = (
        str(processo)
        .replace(".0", "")
        .replace("\xa0", "")
        .strip()
        .upper()
    )

    processo = normalizar_processo(processo)

    # ========================================================
    # 🔥 CÓDIGO
    # ========================================================
    codigo = (
        str(codigo)
        .replace(".0", "")
        .replace("\xa0", "")
        .strip()
        .upper()
    )

    # ========================================================
    # 🔥 LIMPEZA DE VALORES INVÁLIDOS
    # ========================================================
    invalidos = {

        "",
        "NONE",
        "NAN",
        "NULL"
    }

    if pv in invalidos:
        pv = "SEM_PV"

    if processo in invalidos:
        processo = "SEM_PROCESSO"

    if codigo in invalidos:
        codigo = "SEM_CODIGO"

    # ========================================================
    # 🔥 CHAVE FINAL
    # ========================================================
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

    if df_baixas is None or len(df_baixas) == 0:

        return pd.DataFrame(columns=colunas_obrigatorias)

    # ========================================================
    # 🔥 CÓPIA SEGURA
    # ========================================================
    df_baixas = df_baixas.copy()



    # ========================================================
    # 🔥 NORMALIZA NOMES DAS COLUNAS
    # ========================================================
    df_baixas.columns = [

        str(col)
        .strip()
        .replace(" ", "_")
        .replace("-", "_")
        .upper()

        for col in df_baixas.columns
    ]

    # ========================================================
    # 🔥 MAPEAMENTO OFICIAL
    # ========================================================
    mapeamento_colunas = {

        "PV": "PV",

        "CLIENTE": "Cliente",

        "CODIGO": "CODIGO_PV",
        "CODIGO_PV": "CODIGO_PV",

        "PROCESSO": "Processo",

        "HORAS": "Horas",

        "DATA_BAIXA": "Data_Baixa",

        "USUARIO": "Usuario",

        "OBSERVACAO": "Observacao",

        "STATUS_BAIXA": "Status_Baixa",

        "DATA_ESTORNO": "Data_Estorno",

        "MOTIVO_ESTORNO": "Motivo_Estorno",

        "CHAVE_OPERACAO": "CHAVE_OPERACAO"
    }

    df_baixas = df_baixas.rename(
        columns=mapeamento_colunas
    ) 

    
    # ========================================================
    # 🔥 REMOVE COLUNAS DUPLICADAS
    # ========================================================
    df_baixas = df_baixas.loc[
        :,
        ~df_baixas.columns.duplicated()
    ].copy()
       



    # ========================================================
    # 🔒 GARANTE COLUNAS
    # ========================================================
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
    # 🔥 PROCESSO ORIGINAL
    # ========================================================
    df_baixas["Processo_Original"] = (
        df_baixas["Processo"]
    )

    # ========================================================
    # 🔥 NORMALIZA PROCESSO
    # ========================================================
    df_baixas["Processo"] = (

        df_baixas["Processo"]

        .fillna("")

        .astype(str)

        .str.strip()

        .apply(normalizar_processo)
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
    # 🔥 NORMALIZA CHAVE
    # ========================================================
    df_baixas["CHAVE_OPERACAO"] = (

        df_baixas["CHAVE_OPERACAO"]

        .fillna("")

        .astype(str)

        .str.strip()

        .str.upper()
    )

    # ========================================================
    # 🔥 REGERA CHAVES INVÁLIDAS
    # ========================================================
    mascara_chave_invalida = (

        (df_baixas["CHAVE_OPERACAO"] == "")

        |

        (df_baixas["CHAVE_OPERACAO"] == "|||")

        |

        (df_baixas["CHAVE_OPERACAO"].isna())
    )

    if mascara_chave_invalida.any():

        df_baixas.loc[
            mascara_chave_invalida,
            "CHAVE_OPERACAO"
        ] = df_baixas.loc[
            mascara_chave_invalida
        ].apply(

            lambda r: gerar_chave_operacao(

                str(r["PV"]).strip(),

                str(r["Processo"]).strip(),

                str(r["CODIGO_PV"]).strip()

            ),

            axis=1
        )

    # ========================================================
    # 🔥 FALLBACK DE CHAVE
    # ========================================================
    df_baixas["CHAVE_OPERACAO"] = (

        df_baixas["CHAVE_OPERACAO"]

        .fillna("")

        .replace("|||", "")
    )

    # ========================================================
    # 🔒 NÃO REMOVE MAIS LINHAS SILENCIOSAMENTE
    # ========================================================
    # Apenas marca inconsistências
    df_baixas["CHAVE_INVALIDA"] = (

        df_baixas["CHAVE_OPERACAO"] == ""
    )

    

    # ========================================================
    # 🔥 ORDENAÇÃO FINAL
    # ========================================================
    if "Data_Baixa" in df_baixas.columns:

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