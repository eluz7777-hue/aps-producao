import pandas as pd
import numpy as np
import streamlit as st

from aps_utils import *
from aps_banco import *



# --------------------------------------------
# 🔥 GARANTE CHAVE OPERACIONAL OFICIAL APS
# --------------------------------------------
if not df_operacional.empty:

    # ========================================================
    # 🔒 NORMALIZAÇÃO TOTAL
    # ========================================================
    for col in [
        "PV",
        "Processo",
        "CODIGO_PV"
    ]:

        if col not in df_operacional.columns:
            df_operacional[col] = ""

        # ----------------------------------------------------
        # 🔥 PROCESSOS
        # ----------------------------------------------------
        if col == "Processo":

            df_operacional[col] = (

                df_operacional[col]

                .fillna("")

                .astype(str)

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
    # 🔥 CHAVE OPERACIONAL DEFINITIVA
    # ========================================================
    df_operacional["CHAVE_OPERACAO"] = (

        df_operacional["PV"]

        + "||"

        + df_operacional["Processo"]

        + "||"

        + df_operacional["CODIGO_PV"]
    )

    # ========================================================
    # 🔥 NORMALIZA CHAVE FINAL
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
    # 🔥 CONSOLIDA DUPLICAÇÕES DA PV.xlsx
    # ========================================================
    colunas_base_operacional = [

        "CHAVE_OPERACAO",
        "PV",
        "Cliente",
        "CODIGO_PV",
        "Processo",
        "Data",
        "DATA_ENTREGA_APS"
    ]

    colunas_existentes_operacional = [

        c for c in colunas_base_operacional

        if c in df_operacional.columns
    ]

    agregacoes_operacionais = {
        "Horas": "sum"
    }

    df_operacional = (

        df_operacional

        .sort_values(
            by=[
                "PV",
                "Processo",
                "CODIGO_PV"
            ]
        )

        .groupby(
            colunas_existentes_operacional,
            as_index=False
        )

        .agg(agregacoes_operacionais)

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

    df_operacional["CHAVE_OPERACAO"] = ""

    df_operacional["CHAVE_DUPLICADA"] = False


# ============================================================
# BASE OPERACIONAL REAL (EXECUÇÃO SOBERANA APS)
# ============================================================

# ------------------------------------------------------------
# 🔥 LEITURA OFICIAL POSTGRESQL APS
# ------------------------------------------------------------
df_baixas = carregar_baixas_postgresql()

# ------------------------------------------------------------
# 🔒 GARANTE PADRONIZAÇÃO
# ------------------------------------------------------------
df_baixas = _padronizar_df_baixas(
    df_baixas
)

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
# 🔥 SESSION STATE OFICIAL APS
# ------------------------------------------------------------
st.session_state["df_baixas_ativas"] = (
    df_baixas_ativas.copy()
)


# ------------------------------------------------------------
# 🔥 BASE ORIGINAL PV
# ------------------------------------------------------------
df_planejamento = df_operacional.copy()


# ------------------------------------------------------------
# 🔥 NORMALIZA BASE PLANEJAMENTO
# ------------------------------------------------------------
for col in ["PV", "Processo", "CODIGO_PV"]:

    if col not in df_planejamento.columns:
        df_planejamento[col] = ""

    df_planejamento[col] = (

        df_planejamento[col]

        .fillna("")

        .astype(str)

        .str.strip()

        .str.upper()
    )


df_planejamento["CHAVE_OPERACAO"] = (

    df_planejamento["PV"]

    .astype(str)

    .str.strip()

    .str.upper()

    + "||"

    + df_planejamento["Processo"]

    .astype(str)

    .apply(normalizar_processo)

    + "||"

    + df_planejamento["CODIGO_PV"]

    .astype(str)

    .str.strip()

    .str.upper()
)