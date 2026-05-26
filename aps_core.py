import pandas as pd
import streamlit as st

from aps_utils import *
from aps_utils import _padronizar_df_baixas

from aps_utils import gerar_chave_operacao

from aps_banco import *


# ============================================================
# 🔥 BASE OPERACIONAL RECEBIDA DO APS
# ============================================================
try:

    df_operacional

except NameError:

    df_operacional = pd.DataFrame()


# ============================================================
# 🔒 GARANTE DATAFRAME VÁLIDO
# ============================================================
if df_operacional is None:

    df_operacional = pd.DataFrame()


# --------------------------------------------
# 🔥 GARANTE CHAVE OPERACIONAL OFICIAL APS
# --------------------------------------------
if not df_operacional.empty:

    # ========================================================
    # 🔒 BLINDAGEM DEFINITIVA DE COLUNAS
    # ========================================================
    for col in [
        "PV",
        "Processo",
        "CODIGO_PV"
    ]:

        if col not in df_operacional.columns:

            df_operacional[col] = ""

    # ========================================================
    # 🔥 NORMALIZAÇÃO TOTAL
    # ========================================================
    for col in [
        "PV",
        "Processo",
        "CODIGO_PV"
    ]:

        # ----------------------------------------------------
        # 🔥 PROCESSOS
        # ----------------------------------------------------
        if col == "Processo":

            df_operacional[col] = (

                df_operacional[col]

                .fillna("")

                .astype(str)

                .str.replace("\xa0", "", regex=False)

                .str.replace("  ", " ", regex=False)

                .str.strip()

                .apply(normalizar_processo)

                .str.upper()
            )

        # ----------------------------------------------------
        # 🔥 DEMAIS CAMPOS
        # ----------------------------------------------------
        else:

            df_operacional[col] = (

                df_operacional[col]

                .fillna("")

                .astype(str)

                .str.upper()

                .str.strip()

                .str.replace(".0", "", regex=False)

                .str.replace("  ", " ", regex=False)

                .str.replace(" - ", "-", regex=False)

                .str.replace("- ", "-", regex=False)

                .str.replace(" -", "-", regex=False)

                .str.replace("\xa0", "", regex=False)
            )

    # ========================================================
    # 🔥 GARANTE COLUNAS OPERACIONAIS
    # ========================================================
    colunas_obrigatorias_operacional = {

        "Horas": 0,
        "Cliente": "",
        "Data": pd.NaT,
        "DATA_ENTREGA_APS": pd.NaT
    }

    for col, valor_default in colunas_obrigatorias_operacional.items():

        if col not in df_operacional.columns:

            df_operacional[col] = valor_default

    # ========================================================
    # 🔥 NORMALIZA HORAS
    # ========================================================
    df_operacional["Horas"] = (

        pd.to_numeric(
            df_operacional["Horas"],
            errors="coerce"
        )

        .fillna(0)
    )

    # ========================================================
    # 🔥 NORMALIZA CLIENTE
    # ========================================================
    df_operacional["Cliente"] = (

        df_operacional["Cliente"]

        .fillna("SEM CLIENTE")

        .astype(str)

        .str.strip()

        .str.upper()
    )

    # ========================================================
    # 🔥 CHAVE OPERACIONAL DEFINITIVA APS
    # ========================================================
    df_operacional["CHAVE_OPERACAO"] = df_operacional.apply(

        lambda r: gerar_chave_operacao(
            r["PV"],
            r["Processo"],
            r["CODIGO_PV"]
        ),

        axis=1
    )

    # ========================================================
    # 🔒 NORMALIZA CHAVE FINAL
    # ========================================================
    df_operacional["CHAVE_OPERACAO"] = (

        df_operacional["CHAVE_OPERACAO"]

        .fillna("")

        .astype(str)

        .str.replace(".0", "", regex=False)

        .str.replace("\xa0", "", regex=False)

        .str.replace(" | ", "|", regex=False)

        .str.replace("|| ", "||", regex=False)

        .str.replace(" ||", "||", regex=False)

        .str.strip()

        .str.upper()
    )

    # ========================================================
    # 🔒 REMOVE CHAVES INVÁLIDAS
    # ========================================================
    df_operacional = (

        df_operacional[

            df_operacional["CHAVE_OPERACAO"] != ""

        ]

        .copy()
    )

    df_operacional = (

        df_operacional[

            df_operacional["CHAVE_OPERACAO"] != "|||"

        ]

        .copy()
    )

    # ========================================================
    # 🔒 REMOVE LINHAS OPERACIONAIS VAZIAS
    # ========================================================
    df_operacional = (

        df_operacional[

            (df_operacional["PV"] != "")

            &

            (df_operacional["Processo"] != "")

            &

            (df_operacional["CODIGO_PV"] != "")

        ]

        .copy()
    )

    # ========================================================
    # 🔥 CONSOLIDA DUPLICAÇÕES DA PV.xlsx
    # ========================================================
    df_operacional = (

        df_operacional

        .groupby(
            [
                "CHAVE_OPERACAO",
                "PV",
                "Cliente",
                "CODIGO_PV",
                "Processo"
            ],
            as_index=False,
            dropna=False
        )

        .agg({
            "Horas": "sum"
        })

        .reset_index(drop=True)
    )

    # ========================================================
    # 🔥 AUDITORIA DE DUPLICIDADES
    # ========================================================
    df_operacional["CHAVE_DUPLICADA"] = (

        df_operacional

        .duplicated(
            subset=["CHAVE_OPERACAO"],
            keep=False
        )
    )

else:

    df_operacional = pd.DataFrame({

        "PV": [],
        "Processo": [],
        "CODIGO_PV": [],
        "Horas": [],
        "Cliente": [],
        "CHAVE_OPERACAO": [],
        "CHAVE_DUPLICADA": []
    })
        


# ============================================================
# 🔥 LEITURA OFICIAL POSTGRESQL APS
# ============================================================
df_baixas = carregar_baixas_postgresql()

# ------------------------------------------------------------
# 🔒 GARANTE DATAFRAME VÁLIDO
# ------------------------------------------------------------
if df_baixas is None:

    df_baixas = pd.DataFrame()

# ------------------------------------------------------------
# 🔒 GARANTE PADRONIZAÇÃO
# ------------------------------------------------------------
df_baixas = _padronizar_df_baixas(
    df_baixas
)

# ------------------------------------------------------------
# 🔒 GARANTE COLUNAS OBRIGATÓRIAS
# ------------------------------------------------------------
for col in [
    "CHAVE_OPERACAO",
    "Status_Baixa"
]:

    if col not in df_baixas.columns:

        df_baixas[col] = ""

# ------------------------------------------------------------
# 🔥 SESSION STATE OFICIAL
# ------------------------------------------------------------
st.session_state["df_baixas"] = (
    df_baixas.copy()
)

# ------------------------------------------------------------
# 🔥 FILTRA SOMENTE BAIXAS ATIVAS
# ------------------------------------------------------------
df_baixas_ativas = (

    df_baixas[

        df_baixas["Status_Baixa"]

        .fillna("")

        .astype(str)

        .str.strip()

        .str.upper()

        .isin([

            "ATIVA",
            "TERCEIRIZADA"

        ])
    ]

    .copy()
)

# ------------------------------------------------------------
# 🔒 GARANTE PADRONIZAÇÃO FINAL
# ------------------------------------------------------------
df_baixas_ativas = (
    _padronizar_df_baixas(
        df_baixas_ativas
    )
)

# ------------------------------------------------------------
# 🔒 GARANTE CHAVE OPERACIONAL
# ------------------------------------------------------------
if "CHAVE_OPERACAO" not in df_baixas_ativas.columns:

    df_baixas_ativas["CHAVE_OPERACAO"] = ""

# ------------------------------------------------------------
# 🔥 NORMALIZA CHAVE DAS BAIXAS
# ------------------------------------------------------------
df_baixas_ativas["CHAVE_OPERACAO"] = (

    df_baixas_ativas["CHAVE_OPERACAO"]

    .fillna("")

    .astype(str)

    .str.replace(".0", "", regex=False)

    .str.replace("\xa0", "", regex=False)

    .str.strip()

    .str.upper()
)

# ------------------------------------------------------------
# 🔒 REMOVE CHAVES INVÁLIDAS
# ------------------------------------------------------------
df_baixas_ativas = (

    df_baixas_ativas[

        df_baixas_ativas["CHAVE_OPERACAO"] != ""

    ]

    .copy()
)

df_baixas_ativas = (

    df_baixas_ativas[

        df_baixas_ativas["CHAVE_OPERACAO"] != "|||"

    ]

    .copy()
)

# ------------------------------------------------------------
# 🔥 SESSION STATE OFICIAL APS
# ------------------------------------------------------------
st.session_state["df_baixas_ativas"] = (
    df_baixas_ativas.copy()
)

# ============================================================
# 🔥 CHAVES BAIXADAS APS
# ============================================================
if not df_baixas_ativas.empty:

    chaves_baixadas = set(

        df_baixas_ativas[
            "CHAVE_OPERACAO"
        ]

        .fillna("")

        .astype(str)

        .str.strip()

        .str.upper()
    )

else:

    chaves_baixadas = set()

# ============================================================
# 🔥 REMOVE OPERAÇÕES BAIXADAS DA FILA
# ============================================================
if "CHAVE_OPERACAO" not in df_operacional.columns:

    df_operacional["CHAVE_OPERACAO"] = ""

df_operacional = (

    df_operacional[

        ~df_operacional["CHAVE_OPERACAO"]

        .isin(chaves_baixadas)
    ]

    .copy()
)

# ============================================================
# 🔥 RESET FINAL
# ============================================================
df_operacional = (
    df_operacional
    .reset_index(drop=True)
)

# ============================================================
# 🔥 EXPORTAÇÃO FINAL APS
# ============================================================
CORE_APS = {
    "df_operacional": df_operacional
}