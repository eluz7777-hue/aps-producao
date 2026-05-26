import pandas as pd
import streamlit as st

from aps_utils import *
from aps_utils import _padronizar_df_baixas

from aps_banco import *



# ============================================================
# 🔥 BASE OPERACIONAL RECEBIDA DO APS
# ============================================================
if "df_operacional" not in globals():

    df_operacional = pd.DataFrame()



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
    # 🔒 REMOVE CHAVES VAZIAS
    # ========================================================
    df_operacional = (

        df_operacional[

            df_operacional["CHAVE_OPERACAO"] != ""

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


# ============================================================
# 🔒 GARANTE COLUNAS OPERACIONAIS
# ============================================================
if "Horas" not in df_planejamento.columns:

    df_planejamento["Horas"] = 0

if "CHAVE_OPERACAO" not in df_planejamento.columns:

    df_planejamento["CHAVE_OPERACAO"] = ""

if "Processo" not in df_planejamento.columns:

    df_planejamento["Processo"] = ""

if "PV" not in df_planejamento.columns:

    df_planejamento["PV"] = ""

if "CODIGO_PV" not in df_planejamento.columns:

    df_planejamento["CODIGO_PV"] = ""




# ============================================================
# 🔥 CONSOLIDA BAIXAS REAIS APS
# ============================================================

df_baixas_consolidadas = (

    df_baixas_ativas

    .groupby(
        "CHAVE_OPERACAO",
        as_index=False
    )

    .agg(
        Horas_Baixadas=("Horas", "sum")
    )
)



# ------------------------------------------------------------
# 🔥 MERGE BAIXAS x PLANEJAMENTO
# ------------------------------------------------------------
df_planejamento = pd.merge(

    df_planejamento,

    df_baixas_consolidadas,

    on="CHAVE_OPERACAO",

    how="left"
)





# ------------------------------------------------------------
# 🔒 BLINDAGEM
# ------------------------------------------------------------
df_planejamento["Horas_Baixadas"] = (

    pd.to_numeric(
        df_planejamento["Horas_Baixadas"],
        errors="coerce"
    )

    .fillna(0)
)

df_planejamento["Horas"] = (

    pd.to_numeric(
        df_planejamento["Horas"],
        errors="coerce"
    )

    .fillna(0)
)

# ------------------------------------------------------------
# 🔥 SALDO REAL APS
# ------------------------------------------------------------
df_planejamento["Saldo_Horas"] = (

    df_planejamento["Horas"]

    -

    df_planejamento["Horas_Baixadas"]
)

# ------------------------------------------------------------
# 🔒 IMPEDE NEGATIVOS
# ------------------------------------------------------------
df_planejamento["Saldo_Horas"] = (

    df_planejamento["Saldo_Horas"]

    .clip(lower=0)
)

# ------------------------------------------------------------
# 🔥 BASE OPERACIONAL FINAL APS
# ------------------------------------------------------------
df_operacional = df_planejamento.copy()

# ------------------------------------------------------------
# 🔥 SOMENTE PENDÊNCIAS REAIS
# ------------------------------------------------------------
df_operacional = (

    df_operacional[
        df_operacional["Saldo_Horas"] > 0.0001
    ]

    .copy()
)

df_operacional = (
    df_operacional
    .reset_index(drop=True)
)




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



CORE_APS = {
    "df_operacional": df_operacional
}