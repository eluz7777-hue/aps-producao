import os
import shutil

import numpy as np

import pandas as pd
import streamlit as st

from sqlalchemy import create_engine
from sqlalchemy import text

from datetime import datetime
from zoneinfo import ZoneInfo

from aps_utils import *
from aps_utils import _padronizar_df_baixas

print("🔥 APS_BANCO REAL CARREGADO 🔥")


# ============================================================
# 🔥 BASE OPERACIONAL GLOBAL APS
# ============================================================
if "df_operacional" not in globals():

    df_operacional = pd.DataFrame()



def _norm(valor):

    if pd.isna(valor):
        return ""

    return (
        str(valor)
        .strip()
        .upper()
        .replace(".0", "")
        .replace("\xa0", "")
    )


# =============================== 
# BAIXAS OPERACIONAIS APS
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



# ============================================================
# 🔥 POSTGRESQL SUPABASE - BANCO OFICIAL APS
# ============================================================

# ------------------------------------------------------------
# 🔒 CONFIGURAÇÕES SEGURAS STREAMLIT
# ------------------------------------------------------------
SUPABASE_HOST = st.secrets["SUPABASE_HOST"]

SUPABASE_PORT = st.secrets["SUPABASE_PORT"]

SUPABASE_DB = st.secrets["SUPABASE_DB"]

SUPABASE_USER = st.secrets["SUPABASE_USER"]

SUPABASE_PASSWORD = st.secrets["SUPABASE_PASSWORD"]


# ------------------------------------------------------------
# 🔥 DATABASE URL APS
# ------------------------------------------------------------
DATABASE_URL = (

    f"postgresql+psycopg2://"

    f"{SUPABASE_USER}:"

    f"{SUPABASE_PASSWORD}@"

    f"{SUPABASE_HOST}:"

    f"{SUPABASE_PORT}/"

    f"{SUPABASE_DB}"
)


# ============================================================
# 🔥 ENGINE GLOBAL APS
# ============================================================
engine = create_engine(

    DATABASE_URL,

    pool_pre_ping=True,

    pool_size=10,

    max_overflow=20,

    pool_recycle=1800,

    pool_timeout=30
)


# ============================================================
# 🔥 TESTE VISUAL APS
# ============================================================
try:

    with engine.connect() as conn:

        conn.execute(
            text("SELECT 1")
        )

    st.success(
        "✅ PostgreSQL Supabase conectado"
    )

except Exception as e:

    st.error(
        f"❌ Erro conexão PostgreSQL: {e}"
    )

    st.stop()


# ============================================================
# 🔥 CONEXÃO GLOBAL APS
# ============================================================
def get_connection():

    return engine.connect()



# ============================================================
# 🔥 DEBUG POSTGRESQL APS
# ============================================================
DEBUG_POSTGRES = False


# ============================================================
# 🔥 INICIALIZAÇÃO BANCO APS POSTGRESQL
# ============================================================
def inicializar_banco():

    conn = None

    try:

        # ====================================================
        # 🔥 CONEXÃO
        # ====================================================
        conn = engine.connect()

        # ====================================================
        # 🔥 TRANSAÇÃO
        # ====================================================
        trans = conn.begin()

        # ====================================================
        # 🔥 TABELA PRINCIPAL APS
        # ====================================================
        conn.execute(text("""

            CREATE TABLE IF NOT EXISTS baixas (

                id SERIAL PRIMARY KEY,

                PV TEXT,

                Cliente TEXT,

                CODIGO_PV TEXT,

                Processo TEXT,

                Horas DOUBLE PRECISION,

                Horas_Planejadas DOUBLE PRECISION,

                Data_Baixa TIMESTAMP,

                Usuario TEXT,

                Observacao TEXT,

                Status_Baixa TEXT,

                Data_Estorno TEXT,

                Motivo_Estorno TEXT,

                CHAVE_OPERACAO TEXT

            )

        """))

        # ====================================================
        # 🔥 ÍNDICES PERFORMANCE APS
        # ====================================================
        conn.execute(text("""

            CREATE INDEX IF NOT EXISTS idx_baixas_chave

            ON baixas (CHAVE_OPERACAO)

        """))

        conn.execute(text("""

            CREATE INDEX IF NOT EXISTS idx_baixas_status

            ON baixas (Status_Baixa)

        """))

        conn.execute(text("""

            CREATE INDEX IF NOT EXISTS idx_baixas_data

            ON baixas (Data_Baixa)

        """))

        # ====================================================
        # 🔥 COMMIT
        # ====================================================
        trans.commit()

        if DEBUG_POSTGRES:

            st.success(
                "✅ Estrutura PostgreSQL inicializada"
            )

    except Exception as e:

        try:

            trans.rollback()

        except:
            pass

        st.error(
            f"❌ Erro inicialização PostgreSQL: {e}"
        )

        st.stop()

    finally:

        try:

            conn.close()

        except:
            pass





# ============================================================
# 🔥 EXECUÇÃO AUTOMÁTICA APS
# ============================================================
inicializar_banco()



# ============================================================
# 🔥 FUNÇÃO GLOBAL POSTGRESQL (VERSÃO DEFINITIVA APS)
# ============================================================
def carregar_baixas_postgresql():

    try:

        st.warning("🔥 ENTROU carregar_baixas_postgresql")
        

        # ====================================================
        # 🔥 LEITURA POSTGRESQL
        # ====================================================
        with engine.begin() as conn:

            df = pd.read_sql(

                text("""

                    SELECT *

                    FROM baixas

                """),

                conn
            )

        # ====================================================
        # 🔥 DEBUG DF BRUTO
        # ====================================================
        print("\n======================")
        print("🔥 DF BRUTO POSTGRESQL")
        print("======================")

        st.warning(f"🔥 DF BRUTO: {df.shape}")

        try:

            print(df.head())

        except:
            pass



        # ====================================================
        # 🔥 GARANTE COLUNAS PADRÃO APS
        # ====================================================
        for col in [

            "id",
            "PV",
            "Cliente",
            "CODIGO_PV",
            "Processo",
            "Horas",
            "Horas_Planejadas",
            "Data_Baixa",
            "Usuario",
            "Observacao",
            "Status_Baixa",
            "Data_Estorno",
            "Motivo_Estorno",
            "CHAVE_OPERACAO"

        ]:

            if col not in df.columns:

                if col in [

                    "Horas",
                    "Horas_Planejadas"

                ]:

                    df[col] = 0

                else:

                    df[col] = ""

        if df is None or df.empty:

            st.error("⚠️ DF VEIO VAZIO DO POSTGRESQL")

            try:

                st.warning(f"🔥 DF VAZIO: {df.shape}")

            except:
                pass


            return pd.DataFrame(
                columns=COLUNAS_BAIXAS + [
                    "CHAVE_OPERACAO"
                ]
            )

        # ====================================================
        # 🔥 GARANTE COLUNA
        # ====================================================
        if "CHAVE_OPERACAO" not in df.columns:

            df["CHAVE_OPERACAO"] = ""

        # ====================================================
        # 🔥 NORMALIZA CAMPOS
        # ====================================================
        for col in [

            "PV",
            "CODIGO_PV",
            "Processo",
            "CHAVE_OPERACAO"

        ]:

            df[col] = (

                df[col]

                .fillna("")

                .astype(str)

                .str.strip()

                .str.upper()
            )

        # ====================================================
        # 🔥 CONVERSÕES NUMÉRICAS
        # ====================================================
        df["Horas"] = pd.to_numeric(
            df["Horas"],
            errors="coerce"
        ).fillna(0)

        df["Horas_Planejadas"] = pd.to_numeric(
            df["Horas_Planejadas"],
            errors="coerce"
        ).fillna(0)

        # ====================================================
        # 🔥 RECUPERA CHAVES ANTIGAS
        # ====================================================
        mascara_chave_vazia = (

            df["CHAVE_OPERACAO"]

            .astype(str)

            .str.strip()

            == ""
        )

        if mascara_chave_vazia.any():

            df.loc[
                mascara_chave_vazia,
                "CHAVE_OPERACAO"
            ] = (

                df.loc[
                    mascara_chave_vazia,
                    "PV"
                ]

                + "||"

                + df.loc[
                    mascara_chave_vazia,
                    "Processo"
                ]

                + "||"

                + df.loc[
                    mascara_chave_vazia,
                    "CODIGO_PV"
                ]
            )

            # ================================================
            # 🔥 ATUALIZA CHAVES RECUPERADAS
            # ================================================
            try:

                with engine.begin() as trans_conn:

                    for _, row in df.loc[
                        mascara_chave_vazia
                    ].iterrows():

                        if str(row["id"]).strip() != "":

                            trans_conn.execute(

                                text("""

                                    UPDATE baixas

                                    SET CHAVE_OPERACAO = :chave

                                    WHERE id = :id

                                """),

                                {
                                    "chave": row["CHAVE_OPERACAO"],
                                    "id": int(row["id"])
                                }
                            )

            except Exception as e:

                st.warning(
                    f"Erro atualização chaves PostgreSQL: {e}"
                )

        # ====================================================
        # 🔥 PADRONIZA
        # ====================================================
        df = _padronizar_df_baixas(df)

        # ====================================================
        # 🔥 REMOVE DUPLICIDADES
        # ====================================================
        df = (

            df

            .drop_duplicates()

            .reset_index(drop=True)
        )

        # ====================================================
        # 🔥 ORDENAÇÃO FINAL
        # ====================================================
        df = (

            df

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

        print("\n======================")
        print("🔥 DF FINAL RETORNADO")
        print("======================")

        print(df.shape)

        try:

            print(df.head())

        except:
            pass



        return df

    except Exception as e:

        import traceback

        print("\n======================")
        print("❌ ERRO carregar_baixas_postgresql")
        print("======================")


        print(traceback.format_exc())

        st.warning(
            f"Erro PostgreSQL baixas: {e}"
        )

        return pd.DataFrame(
            columns=COLUNAS_BAIXAS + [
                "CHAVE_OPERACAO"
            ]
        )





## ============================================================
# 🔥 SALVAR BAIXA POSTGRESQL (VERSÃO DEFINITIVA BLINDADA APS)
# ============================================================
def salvar_baixa_postgresql(nova_baixa):

    print("\n🔥🔥🔥 ENTROU EM salvar_baixa_postgresql 🔥🔥🔥")

    try:

        # ====================================================
        # 🔥 TRANSAÇÃO OFICIAL SQLALCHEMY 2.x
        # ====================================================
        with engine.connect() as conn:
   
            trans = conn.begin()

            # ====================================================
            # 🔥 NORMALIZAÇÃO TOTAL
            # ====================================================
            pv = _norm(
                nova_baixa.get("PV", "")
            )

            cliente = str(
                nova_baixa.get("Cliente", "")
            ).strip()

            codigo_pv = _norm(
                nova_baixa.get("CODIGO_PV", "")
            )

            # ----------------------------------------------------
            # 🔥 PROCESSO NORMALIZADO APS
            # ----------------------------------------------------
            processo = normalizar_processo(
                nova_baixa.get("Processo", "")
            )

            usuario = str(
                nova_baixa.get("Usuario", "Sistema")
            ).strip()

            observacao = str(
                nova_baixa.get("Observacao", "")
            ).strip()

            status_baixa = str(
                nova_baixa.get("Status_Baixa", "ATIVA")
            ).strip().upper()

            motivo_estorno = str(
                nova_baixa.get("Motivo_Estorno", "")
            ).strip()

            chave_operacao = str(
                nova_baixa.get("CHAVE_OPERACAO", "")
            ).strip()



            # ====================================================
            # 🔥 HORAS SEGURAS
            # ====================================================
            horas = pd.to_numeric(
                nova_baixa.get("Horas", 0),
                errors="coerce"
            )

            if pd.isna(horas):

                horas = 0

            horas = float(horas)



            # ====================================================
            # 🔥 HORAS PLANEJADAS
            # ====================================================
            horas_planejadas = float(
                nova_baixa.get(
                    "Horas_Planejadas",
                    0
                )
            )

            # ====================================================
            # 🔥 DATA BAIXA REAL
            # ====================================================
            data_baixa = nova_baixa.get(
                "Data_Baixa"
            )

            # ----------------------------------------------------
            # datetime
            # ----------------------------------------------------
            if isinstance(
                data_baixa,
                datetime
            ):

                data_baixa = data_baixa.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )

            # ----------------------------------------------------
            # vazio
            # ----------------------------------------------------
            elif (
                data_baixa is None
                or str(data_baixa).strip() == ""
                or str(data_baixa).strip().upper() == "NONE"
                or str(data_baixa).strip().upper() == "NAT"
            ):

                data_baixa = datetime.now(
                    ZoneInfo("America/Sao_Paulo")
                ).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )

            else:

                try:

                    data_baixa = pd.to_datetime(
                        data_baixa,
                        errors="coerce"
                    )

                    if pd.isna(data_baixa):

                        data_baixa = datetime.now(
                            ZoneInfo("America/Sao_Paulo")
                        )

                    data_baixa = data_baixa.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )

                except:

                    data_baixa = datetime.now(
                        ZoneInfo("America/Sao_Paulo")
                    ).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )

            # ====================================================
            # 🔥 DATA ESTORNO
            # ====================================================
            data_estorno = nova_baixa.get(
                "Data_Estorno",
                ""
            )

            if (
                data_estorno is None
                or str(data_estorno).strip().upper() in [
                    "",
                    "NONE",
                    "NAT"
                ]
            ):

                data_estorno = ""

            else:

                try:

                    data_estorno = pd.to_datetime(
                        data_estorno,
                        errors="coerce"
                    )

                    if pd.isna(data_estorno):

                        data_estorno = ""

                    else:

                        data_estorno = (
                            data_estorno.strftime(
                                "%Y-%m-%d %H:%M:%S"
                            )
                        )

                except:

                    data_estorno = ""

            # ====================================================
            # 🔒 CHAVE OPERACIONAL
            # ====================================================
            if chave_operacao.strip() == "":

                chave_operacao = gerar_chave_operacao(
                    pv,
                    processo,
                    codigo_pv
                )

            # ====================================================
            # 🔥 NORMALIZA CHAVE FINAL
            # ====================================================
            chave_operacao = (

                str(chave_operacao)

                .replace(".0", "")

                .replace("\xa0", "")

                .replace(" | ", "|")

                .replace("|| ", "||")

                .replace(" ||", "||")

                .upper()

                .strip()
            )

            # ====================================================
            # 🔒 BLOQUEIO CHAVE INVÁLIDA
            # ====================================================
            if (
                chave_operacao == ""
                or chave_operacao == "|||"
            ):

                return {
                    "ok": False,
                    "erro": "CHAVE_OPERACAO inválida"
                }

            # ====================================================
            # 🔒 BLOQUEIO DADOS VAZIOS
            # ====================================================
            if (
                pv == ""
                or processo == ""
                or codigo_pv == ""
            ):

                return {
                    "ok": False,
                    "erro": "Dados operacionais inválidos"
                }

            # ====================================================
            # 🔒 BLOQUEIO DUPLICIDADE
            # ====================================================
            resultado_existente = conn.execute(

                text("""

                    SELECT
                        COALESCE(SUM(Horas), 0)

                    FROM baixas

                    WHERE CHAVE_OPERACAO = :chave

                    AND UPPER(Status_Baixa)
                    IN ('ATIVA', 'TERCEIRIZADA')

                """),

                {
                    "chave": chave_operacao
                }

            ).fetchone()

            horas_existentes = resultado_existente[0]

            if horas_existentes is None:

                horas_existentes = 0

            horas_existentes = float(
                horas_existentes
            )

            

            # ====================================================
            # 🔒 BLINDAGEM INDUSTRIAL
            # ====================================================
            if horas_planejadas <= 0:

                resultado_planejado = conn.execute(

                    text("""

                        SELECT
                            COALESCE(MAX(Horas_Planejadas), 0)

                        FROM baixas

                        WHERE CHAVE_OPERACAO = :chave

                    """),

                    {
                        "chave": chave_operacao
                    }

                ).fetchone()

                horas_antigas = resultado_planejado[0]

                if horas_antigas is None:

                    horas_antigas = 0

                horas_antigas = float(
                    horas_antigas
                )

                horas_planejadas = max(
                    horas_antigas,
                    horas_existentes,
                    horas
                )

                print("\n===============================")
                print("🔥 DEBUG PERSISTÊNCIA")
                print("===============================")

                print("CHAVE_OPERACAO:")
                print(chave_operacao)

                print("HORAS RECEBIDAS:")
                print(horas)

                print("HORAS EXISTENTES:")
                print(horas_existentes)

                print("HORAS PLANEJADAS:")
                print(horas_planejadas)

            # ====================================================
            # 🔥 SALDO RESTANTE
            # ====================================================
            saldo_restante = max(

                horas_planejadas

                - horas_existentes,

                0
            )

            # ====================================================
            # 🔒 EVITA DUPLICIDADE
            # ====================================================
            print("SALDO_RESTANTE:")
            print(saldo_restante)

            if saldo_restante <= 0:

                return {
                    "ok": False,
                    "erro": "Operação já totalmente baixada"
                }

            # ====================================================
            # 🔥 AJUSTA HORAS
            # ====================================================
            horas = min(
                horas,
                saldo_restante
            )

            # ====================================================
            # 💾 INSERT POSTGRESQL
            # ====================================================

            st.warning("🔥 ANTES DO EXECUTE")



            resultado_insert = conn.execute(

                text("""

                    
                    INSERT INTO baixas (

                        PV,
                        Cliente,
                        CODIGO_PV,
                        Processo,
                        Horas,
                        Horas_Planejadas,
                        Data_Baixa,
                        Usuario,
                        Observacao,
                        Status_Baixa,
                        Data_Estorno,
                        Motivo_Estorno,
                        CHAVE_OPERACAO

                    )

                    VALUES (

                        :PV,
                        :Cliente,
                        :CODIGO_PV,
                        :Processo,
                        :Horas,
                        :Horas_Planejadas,
                        :Data_Baixa,
                        :Usuario,
                        :Observacao,
                        :Status_Baixa,
                        :Data_Estorno,
                        :Motivo_Estorno,
                        :CHAVE_OPERACAO

                    )

                """),

                {

                    "PV": pv,
                    "Cliente": cliente,
                    "CODIGO_PV": codigo_pv,
                    "Processo": processo,
                    "Horas": horas,
                    "Horas_Planejadas": horas_planejadas,
                    "Data_Baixa": data_baixa,
                    "Usuario": usuario,
                    "Observacao": observacao,
                    "Status_Baixa": status_baixa,
                    "Data_Estorno": data_estorno,
                    "Motivo_Estorno": motivo_estorno,
                    "CHAVE_OPERACAO": chave_operacao

                }
            )

            st.warning("🔥 EXECUTE PASSOU")            

            
            trans.commit()

            conn.commit()


            print("🔥 ROWCOUNT:")
            print(resultado_insert.rowcount)

            st.warning(
                f"🔥 ROWCOUNT: {resultado_insert.rowcount}"
            )

            print("🔥 INSERT EXECUTADO")
            print("🔥 RETORNANDO OK TRUE")

            resultado_final = {
                "ok": True
            }

        return resultado_final

    except Exception as e:

        import traceback

        st.error(
            f"🔥 ERRO REAL: {e}"
        )

        st.code(
            traceback.format_exc()
        )


        print("\n===============================")
        print("❌ EXCEPTION salvar_baixa_postgresql")
        print("===============================")

        print(traceback.format_exc())


        return {
            "ok": False,
            "erro": str(e)
        }





# ============================================================
# 🔐 CONTROLE OFICIAL DE HISTÓRICO + BACKUP AUTOMÁTICO
# 🔥 POSTGRESQL + EXCEL + BLINDAGEM APS
# ============================================================

PASTA_BACKUP_BAIXAS = "backup_baixas"

ARQUIVO_HISTORICO_BAIXAS = (
    "APS_BAIXAS_OPERACIONAIS.xlsx"
)


# ============================================================
# 🔥 GARANTE PASTA
# ============================================================
def _garantir_pasta_backup():

    os.makedirs(
        PASTA_BACKUP_BAIXAS,
        exist_ok=True
    )


# ============================================================
# 🔥 NOME BACKUP
# ============================================================
def _gerar_nome_backup():

    timestamp = datetime.now().strftime(
        "%Y-%m-%d_%H-%M-%S"
    )

    return (
        f"APS_BAIXAS_OPERACIONAIS_{timestamp}.xlsx"
    )


# ============================================================
# 🔥 CRIA BACKUP
# ============================================================
def _criar_backup():

    try:

        if not os.path.exists(
            ARQUIVO_HISTORICO_BAIXAS
        ):

            return (
                False,
                "Primeira gravação"
            )

        _garantir_pasta_backup()

        destino = os.path.join(

            PASTA_BACKUP_BAIXAS,

            _gerar_nome_backup()
        )

        shutil.copy2(
            ARQUIVO_HISTORICO_BAIXAS,
            destino
        )

        return (
            True,
            destino
        )

    except Exception as e:

        return (
            False,
            str(e)
        )


# ============================================================
# 🔥 EXPORTAÇÃO OFICIAL HISTÓRICO APS
# ============================================================
def salvar_historico_baixas(df):

    """
    🔴 EXPORTAÇÃO OFICIAL APS

    PostgreSQL = banco oficial
    Excel = backup/exportação operacional
    """

    try:

        # ====================================================
        # 🔒 PROTEÇÃO
        # ====================================================
        if df is None or df.empty:

            return {

                "ok": False,

                "erro": (
                    "DataFrame vazio."
                ),

                "backup_ok": False,

                "backup_msg": None
            }

        # ====================================================
        # 🔥 CÓPIA SEGURA
        # ====================================================
        df = df.copy()

        # ====================================================
        # 🔥 REMOVE TIMEZONE
        # ====================================================
        for col in df.columns:

            if pd.api.types.is_datetime64_any_dtype(
                df[col]
            ):

                try:

                    df[col] = (
                        df[col]
                        .dt.tz_localize(None)
                    )

                except:
                    pass

        # ====================================================
        # 🔥 REMOVE COLUNAS INVÁLIDAS
        # ====================================================
        cols_invalidas = [

            c for c in df.columns

            if c.endswith("_x")
            or c.endswith("_y")
        ]

        if cols_invalidas:

            df = df.drop(
                columns=cols_invalidas,
                errors="ignore"
            )

        # ====================================================
        # 🔥 BACKUP LOCAL
        # ====================================================
        backup_ok, backup_msg = (
            _criar_backup()
        )

        # ====================================================
        # 🔥 EXPORTAÇÃO EXCEL
        # ====================================================
        df.to_excel(
            ARQUIVO_HISTORICO_BAIXAS,
            index=False
        )

        # ====================================================
        # 🔥 VALIDA EXPORTAÇÃO
        # ====================================================
        if not os.path.exists(
            ARQUIVO_HISTORICO_BAIXAS
        ):

            return {

                "ok": False,

                "erro": (
                    "Falha ao salvar arquivo."
                ),

                "backup_ok": backup_ok,

                "backup_msg": backup_msg
            }

        # ====================================================
        # 🔥 RETORNO
        # ====================================================
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


# ============================================================
# 🔥 PADRONIZAR BAIXAS OPERACIONAIS APS
# ============================================================
def _padronizar_df_baixas(df_baixas):

    # ========================================================
    # 🔒 DATAFRAME VAZIO BLINDADO
    # ========================================================
    if df_baixas is None or df_baixas.empty:

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
    # 🔒 GARANTE TODAS AS COLUNAS
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

            .str.replace(".0", "", regex=False)

            .str.replace("\xa0", "", regex=False)

            .str.replace("  ", " ", regex=False)

            .str.strip()

            .str.upper()
        )

    # ========================================================
    # 🔥 PROCESSO OFICIAL APS
    # ========================================================
    df_baixas["Processo"] = (

        df_baixas["Processo"]

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
    # 🔥 CHAVE OPERACIONAL OFICIAL APS
    # ========================================================
    df_baixas["CHAVE_OPERACAO"] = df_baixas.apply(

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
    df_baixas["CHAVE_OPERACAO"] = (

        df_baixas["CHAVE_OPERACAO"]

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
    df_baixas = (

        df_baixas[

            df_baixas["CHAVE_OPERACAO"] != ""

        ]

        .copy()
    )

    df_baixas = (

        df_baixas[

            df_baixas["CHAVE_OPERACAO"] != "|||"

        ]

        .copy()
    )

    # ========================================================
    # 🔒 REMOVE LINHAS OPERACIONAIS VAZIAS
    # ========================================================
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