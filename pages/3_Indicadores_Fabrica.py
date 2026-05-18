import streamlit as st
import pandas as pd
import os
import sqlite3
import plotly.express as px
from datetime import datetime


# ============================================================
# 🗄️ SQLITE — INDICADORES ISO
# ============================================================

CAMINHO_DB_INDICADORES = "data/indicadores_iso.db"

# ------------------------------------------------------------
# 🔥 CONEXÃO
# ------------------------------------------------------------
def get_conn_indicadores():

    conn = sqlite3.connect(
        CAMINHO_DB_INDICADORES,
        check_same_thread=False
    )

    return conn

# ------------------------------------------------------------
# 🔥 CRIA TABELA OFICIAL
# ------------------------------------------------------------
def criar_tabela_indicadores():

    conn = get_conn_indicadores()

    cursor = conn.cursor()

    cursor.execute("""

        CREATE TABLE IF NOT EXISTS indicadores_iso (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            setor TEXT,
            indicador TEXT,

            ano INTEGER,
            mes TEXT,

            valor REAL,
            meta REAL,

            tipo TEXT,

            arquivo_evidencia TEXT,

            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )

    """)

    conn.commit()

    conn.close()

# ------------------------------------------------------------
# 🔥 GARANTE ESTRUTURA
# ------------------------------------------------------------
criar_tabela_indicadores()





# ============================================================
# 📊 BASE APS (OBRIGATÓRIA)
# ============================================================

df_raw = st.session_state.get("df", pd.DataFrame())

if df_raw is None or not isinstance(df_raw, pd.DataFrame):
    df_raw = pd.DataFrame()

df_aps = df_raw.copy()


# ============================================================
# 🔧 FUNÇÃO SEGURA
# ============================================================

def safe_value(v):
    try:
        if v is None or pd.isna(v):
            return None
        return float(v)
    except:
        return None


# ============================================================
# 📉 APS - ATRASOS (%)
# ============================================================

pct_atraso = None

if not df_aps.empty and "PV" in df_aps.columns and "DATA_ENTREGA_APS" in df_aps.columns:

    base = df_aps.copy()
    base["DATA_ENTREGA_APS"] = pd.to_datetime(base["DATA_ENTREGA_APS"], errors="coerce")

    hoje = pd.Timestamp.today().normalize()

    pv = base.groupby("PV", as_index=False).agg(
        data_entrega=("DATA_ENTREGA_APS", "min")
    )

    pv = pv.dropna(subset=["data_entrega"])

    pv["Atrasada"] = (hoje - pv["data_entrega"]).dt.days > 0

    total = len(pv)
    atrasadas = pv["Atrasada"].sum()

    pct_atraso = safe_value((atrasadas / total * 100) if total > 0 else None)


# ============================================================
# 🚀 HEADER LIMPO (SEM INDICADOR SOLTO)
# ============================================================

st.markdown("## 📊 ELOHIM APS — Visão Geral")

c1, c2 = st.columns([3,1])

c1.markdown("Sistema de Planejamento e Performance Industrial")

from datetime import datetime
from zoneinfo import ZoneInfo

agora_br = datetime.now(ZoneInfo("America/Sao_Paulo"))

c2.metric("Atualizado em", agora_br.strftime("%d/%m %H:%M"))

st.divider()

# ============================================================
# 📊 ABAS
# ============================================================

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "💰 Comercial",
    "🧪 Qualidade",
    "🏭 Produção",
    "🔧 Manutenção",
    "📦 Fornecedores",
    "👷 RH"
])






# ============================================================
# 💰 COMERCIAL — LEITURA DIRETA DA TABELA EXCEL
# ============================================================

with tab1:

    import os

    st.subheader("💰 Indicador Comercial (Orçamentos → Pedidos)")
    st.caption("Meta: ≥ 25%")

    ANO = "2026"
    META = 0.25

    # ========================================================
    # 📁 ARQUIVO OFICIAL
    # ========================================================
    caminho_excel = (
        "data/Indicadores Comerciais/INDICADOR  COMERCIAL.xlsx"
    )

    # ========================================================
    # 📊 ORDEM DOS MESES
    # ========================================================
    meses_ordem = [
        "Jan","Fev","Mar","Abr","Mai","Jun",
        "Jul","Ago","Set","Out","Nov","Dez"
    ]

    # ========================================================
    # 🔥 MAPA MESES
    # ========================================================
    mapa_meses = {

        "JANEIRO": "Jan",
        "FEVEREIRO": "Fev",
        "MARÇO": "Mar",
        "MARCO": "Mar",
        "ABRIL": "Abr",
        "MAIO": "Mai",
        "JUNHO": "Jun",
        "JULHO": "Jul",
        "AGOSTO": "Ago",
        "SETEMBRO": "Set",
        "OUTUBRO": "Out",
        "NOVEMBRO": "Nov",
        "DEZEMBRO": "Dez"
    }

    # ========================================================
    # 🔥 BASE OFICIAL
    # ========================================================
    indicador_comercial = {}

    media_acm = None

    # ========================================================
    # 🔥 LEITURA EXCEL
    # ========================================================
    if os.path.exists(caminho_excel):

        try:

            # ------------------------------------------------
            # 🔥 LEITURA DA PLANILHA
            # ------------------------------------------------
            df_excel = pd.read_excel(

                caminho_excel,

                header=None
            )

            # ------------------------------------------------
            # 🔥 PERCORRE LINHAS
            # ------------------------------------------------
            for _, row in df_excel.iterrows():

                col_mes = str(
                    row[0]
                ).strip().upper()

                col_valor = row[1]

                # --------------------------------------------
                # 🔥 IGNORA VAZIOS
                # --------------------------------------------
                if (
                    col_mes == "NAN"
                    or pd.isna(col_valor)
                ):
                    continue

                # --------------------------------------------
                # 🔥 ACM
                # --------------------------------------------
                if "MÉDIA ACUMULADA" in col_mes:

                    try:

                        media_acm = (
                            float(col_valor) / 100
                        )

                    except:
                        pass

                    continue

                # --------------------------------------------
                # 🔥 MESES
                # --------------------------------------------
                if col_mes in mapa_meses:

                    try:

                        valor = (
                            float(col_valor) / 100
                        )

                        if valor <= 0:
                            continue

                        mes_curto = (
                            mapa_meses[col_mes]
                        )

                        indicador_comercial[
                            mes_curto
                        ] = {

                            "valor": valor,

                            "arquivo": (
                                "INDICADOR  COMERCIAL.xlsx"
                            )
                        }

                    except:
                        continue

        except Exception as e:

            st.error(
                f"Erro ao ler Excel Comercial: {e}"
            )

    else:

        st.warning(
            "Arquivo Excel do Comercial não encontrado."
        )

    # ========================================================
    # 🔥 GARANTE ORDEM
    # ========================================================
    indicador_comercial = {

        mes: indicador_comercial[mes]

        for mes in meses_ordem

        if mes in indicador_comercial
    }

    # ========================================================
    # 📊 VALORES
    # ========================================================
    valores = []
    arquivos = []

    for mes in meses_ordem:

        if mes in indicador_comercial:

            valores.append(
                indicador_comercial[mes]["valor"]
            )

            arquivos.append(
                indicador_comercial[mes]["arquivo"]
            )

        else:

            valores.append(None)
            arquivos.append(None)

    # ========================================================
    # 📊 ACM
    # ========================================================
    valores_validos = [

        v for v in valores

        if v is not None
    ]

    # --------------------------------------------------------
    # 🔥 FALLBACK ACM
    # --------------------------------------------------------
    if media_acm is None:

        media_acm = (

            sum(valores_validos)

            /

            len(valores_validos)

            if valores_validos else None
        )

    # ========================================================
    # 📊 DATAFRAME
    # ========================================================
    df_plot = pd.DataFrame({

        "Mês": meses_ordem,

        "Valor": valores

    })

    df_plot = pd.concat([

        df_plot,

        pd.DataFrame([{
            "Mês": "ACM",
            "Valor": media_acm
        }])

    ], ignore_index=True)

    # --------------------------------------------------------
    # 🔥 PERCENTUAL
    # --------------------------------------------------------
    df_plot["Valor"] = (

        pd.to_numeric(
            df_plot["Valor"],
            errors="coerce"
        )

        * 100
    )

    # ========================================================
    # 🏷️ LABELS
    # ========================================================
    def formatar(row):

        if pd.isna(row["Valor"]):
            return ""

        if row["Mês"] == "ACM":

            return f"{row['Valor']:.1f}%"

        return f"{row['Valor']:.0f}%"

    df_plot["Label"] = (
        df_plot.apply(
            formatar,
            axis=1
        )
    )

    # ========================================================
    # 📊 GRÁFICO
    # ========================================================
    fig = px.bar(

        df_plot,

        x="Mês",

        y="Valor",

        text="Label"
    )

    fig.update_traces(
        textposition="outside"
    )

    # --------------------------------------------------------
    # 🔥 META 25%
    # --------------------------------------------------------
    fig.add_hline(

        y=25,

        line_dash="dash",

        line_color="red",

        annotation_text="Meta 25%",

        annotation_position="top left"
    )

    # --------------------------------------------------------
    # 🔥 ESCALA
    # --------------------------------------------------------
    max_val = df_plot["Valor"].max()

    fig.update_yaxes(

        tickformat=".0f",

        range=[
            0,
            max(
                max_val * 1.2 if pd.notna(max_val) else 30,
                30
            )
        ]
    )

    # --------------------------------------------------------
    # 🔥 LAYOUT
    # --------------------------------------------------------
    fig.update_layout(

        title=f"📊 Desempenho Comercial - {ANO}",

        yaxis_title="% Conversão",

        showlegend=False,

        height=500
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    # ========================================================
    # 🎯 SELECT
    # ========================================================
    meses_com_dado = [

        m for m in meses_ordem

        if (
            m in indicador_comercial
            and indicador_comercial[m]["valor"] is not None
        )
    ]

    if not meses_com_dado:

        st.warning(
            "Nenhum dado válido encontrado no Excel Comercial."
        )

        st.stop()

    mes_sel = st.selectbox(

        "Selecionar mês para análise",

        meses_com_dado,

        index=len(meses_com_dado) - 1
    )

    valor = (
        indicador_comercial[mes_sel]["valor"]
    )

    arquivo = (
        indicador_comercial[mes_sel]["arquivo"]
    )

    gap = valor - META

    # ========================================================
    # 📊 KPI
    # ========================================================
    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Resultado",
        f"{valor*100:.0f}%"
    )

    c2.metric(
        "Meta",
        f"{META*100:.0f}%"
    )

    c3.metric(
        "Desvio",
        f"{gap*100:.0f}%",
        delta_color="inverse"
    )

    # --------------------------------------------------------
    # 🔥 STATUS
    # --------------------------------------------------------
    if valor >= META:

        st.success(
            "🟢 Dentro da meta"
        )

    else:

        st.error(
            "🔴 Fora da meta"
        )

    # ========================================================
    # 📎 DOWNLOAD EXCEL
    # ========================================================
    if os.path.exists(caminho_excel):

        with open(caminho_excel, "rb") as file:

            st.download_button(

                label="📎 Baixar indicador comercial",

                data=file,

                file_name="INDICADOR  COMERCIAL.xlsx"
            )

    # ========================================================
    # 🚨 REGRA ISO
    # ========================================================
    if len(valores_validos) >= 3:

        ultimos_3 = valores_validos[-3:]

        if all(v < META for v in ultimos_3):

            st.error(
                "🚨 3 meses consecutivos fora da meta — AÇÃO OBRIGATÓRIA"
            )

        else:

            st.success(
                "Indicador sob controle recente"
            )






# ============================================================
# 🧪 QUALIDADE — BLOCO FINAL OFICIAL
# ============================================================

with tab2:

    import os
    import pandas as pd
    import numpy as np
    import plotly.express as px

    st.header("🧪 Indicadores de Qualidade")

    ANO = "2026"

    # ========================================================
    # 📁 ARQUIVO OFICIAL
    # ========================================================
    pastas_possiveis = [

        os.path.abspath(
            "data/Indicadores de Qualidade"
        ),

        os.path.abspath(
            "data/Indicadores_qualidade"
        )
    ]

    caminho_excel = None

    # ========================================================
    # 🔍 PROCURA AUTOMÁTICA
    # ========================================================
    for pasta in pastas_possiveis:

        if not os.path.exists(pasta):
            continue

        arquivos_xlsx = [

            arq for arq in os.listdir(pasta)

            if arq.lower().endswith(".xlsx")
        ]

        if not arquivos_xlsx:
            continue

        caminho_excel = os.path.join(

            pasta,

            arquivos_xlsx[0]
        )

        break

    # ========================================================
    # 🚨 EXISTÊNCIA
    # ========================================================
    if caminho_excel is None:

        st.error(
            "Arquivo da Qualidade não encontrado."
        )

        st.stop()

    # ========================================================
    # 📊 LEITURA EXCEL
    # ========================================================
    try:

        xls = pd.ExcelFile(
            caminho_excel
        )

    except Exception as e:

        st.error(
            f"Erro ao abrir Excel da Qualidade: {e}"
        )

        st.stop()

    # ========================================================
    # 📊 ORDEM DOS MESES
    # ========================================================
    meses_ordem = [
        "Jan","Fev","Mar","Abr","Mai","Jun",
        "Jul","Ago","Set","Out","Nov","Dez"
    ]

    # ========================================================
    # 🔥 MAPA DATAS
    # ========================================================
    mapa_datas = {
        1: "Jan",
        2: "Fev",
        3: "Mar",
        4: "Abr",
        5: "Mai",
        6: "Jun",
        7: "Jul",
        8: "Ago",
        9: "Set",
        10: "Out",
        11: "Nov",
        12: "Dez"
    }

    # ========================================================
    # 🔧 FUNÇÃO PADRÃO
    # ========================================================
    def montar_indicador(

        titulo,
        meta,
        dados,
        tipo="percentual",
        menor_melhor=True
    ):

        st.subheader(titulo)

        valores = [

            dados.get(m, None)

            for m in meses_ordem
        ]

        valores_validos = [

            v for v in valores

            if v is not None
        ]

        media = (

            sum(valores_validos)

            /

            len(valores_validos)

            if valores_validos else None
        )

        # ====================================================
        # 📊 DATAFRAME
        # ====================================================
        df_plot = pd.DataFrame({

            "Mês": meses_ordem,

            "Valor": valores
        })

        df_plot = pd.concat([

            df_plot,

            pd.DataFrame([{
                "Mês": "ACM",
                "Valor": media
            }])

        ], ignore_index=True)

        # ====================================================
        # 📊 CONVERSÃO
        # ====================================================
        if tipo == "percentual":

            df_plot["Valor"] = (
                df_plot["Valor"] * 100
            )

            meta_plot = meta * 100

        else:

            meta_plot = meta

        # ====================================================
        # 🏷️ LABELS
        # ====================================================
        def label(row):

            if pd.isna(row["Valor"]):
                return ""

            if tipo == "percentual":

                return (
                    f"{row['Valor']:.2f}%"
                )

            return (

                f"R$ {row['Valor']:,.0f}"
                .replace(",", ".")
            )

        df_plot["Label"] = (
            df_plot.apply(
                label,
                axis=1
            )
        )

        # ====================================================
        # 📊 GRÁFICO
        # ====================================================
        fig = px.bar(

            df_plot,

            x="Mês",

            y="Valor",

            text="Label"
        )

        fig.update_traces(
            textposition="outside"
        )

        # ----------------------------------------------------
        # 🔥 META
        # ----------------------------------------------------
        fig.add_hline(

            y=meta_plot,

            line_dash="dash",

            line_color="red",

            annotation_text="Meta",

            annotation_position="top left"
        )

        # ----------------------------------------------------
        # 🔥 ESCALA
        # ----------------------------------------------------
        max_val = df_plot["Valor"].max()

        fig.update_yaxes(

            range=[
                0,
                max(
                    max_val * 1.2
                    if pd.notna(max_val)
                    else 1,

                    meta_plot * 1.2
                )
            ]
        )

        # ----------------------------------------------------
        # 🔥 LAYOUT
        # ----------------------------------------------------
        fig.update_layout(

            title=f"{titulo} - {ANO}",

            showlegend=False,

            height=450
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        # ====================================================
        # 🚨 REGRA ISO
        # ====================================================
        if len(valores_validos) >= 3:

            ultimos_3 = (
                valores_validos[-3:]
            )

            if menor_melhor:

                fora_meta = all(
                    v > meta
                    for v in ultimos_3
                )

            else:

                fora_meta = all(
                    v < meta
                    for v in ultimos_3
                )

            if fora_meta:

                st.error(
                    "🚨 3 meses consecutivos fora da meta — AÇÃO OBRIGATÓRIA"
                )

            else:

                st.success(
                    "Indicador sob controle recente"
                )

        st.divider()

    # ========================================================
    # 🧪 NC EXTERNAS
    # ========================================================
    dados_nc = {}

    try:

        df_nc = pd.read_excel(

            caminho_excel,

            sheet_name="NC - EXTERNAS",

            header=None
        )

        for idx in range(4, 16):

            mes = str(
                df_nc.iloc[idx, 1]
            ).strip().upper()

            total = df_nc.iloc[idx, 5]

            mapa = {

                "JAN": "Jan",
                "FEV": "Fev",
                "MAR": "Mar",
                "ABR": "Abr",
                "MAI": "Mai",
                "JUN": "Jun",
                "JUL": "Jul",
                "AGO": "Ago",
                "SET": "Set",
                "OUT": "Out",
                "NOV": "Nov",
                "DEZ": "Dez"
            }

            if mes not in mapa:
                continue

            try:

                valor = float(total)

            except:

                valor = 0

            dados_nc[
                mapa[mes]
            ] = valor / 100

    except Exception as e:

        st.warning(
            f"Erro NC Externas: {e}"
        )

    # ========================================================
    # 💰 CUSTO NC TOTAL
    # ========================================================
    dados_custo = {}

    try:

        df_custo = pd.read_excel(

            caminho_excel,

            sheet_name="Custo NC Total"
        )

        for _, row in df_custo.iterrows():

            data = row.iloc[0]

            if pd.isna(data):
                continue

            if not hasattr(data, "month"):
                continue

            mes = mapa_datas.get(
                data.month
            )

            if mes is None:
                continue

            externa = row.iloc[1]
            interna = row.iloc[2]

            externa = (
                0 if pd.isna(externa)
                else float(externa)
            )

            interna = (
                0 if pd.isna(interna)
                else float(interna)
            )

            dados_custo[mes] = (
                externa + interna
            )

    except Exception as e:

        st.warning(
            f"Erro Custo NC: {e}"
        )

    # ========================================================
    # ♻️ REFUGO
    # ========================================================
    dados_refugo = {}

    try:

        df_refugo = pd.read_excel(

            caminho_excel,

            sheet_name="Refugo Produto x R$"
        )

        for _, row in df_refugo.iterrows():

            data = row.iloc[0]

            if pd.isna(data):
                continue

            if not hasattr(data, "month"):
                continue

            mes = mapa_datas.get(
                data.month
            )

            if mes is None:
                continue

            valor_total = row.iloc[1]
            faturamento = row.iloc[5]

            if (
                pd.isna(valor_total)
                or
                pd.isna(faturamento)
                or
                faturamento == 0
            ):
                continue

            dados_refugo[mes] = (
                float(valor_total)
                /
                float(faturamento)
            )

    except Exception as e:

        st.warning(
            f"Erro Refugo: {e}"
        )

    # ========================================================
    # 🔧 RETRABALHO
    # ========================================================
    dados_retrabalho = {}

    try:

        df_retrabalho = pd.read_excel(

            caminho_excel,

            sheet_name="Retrabalho Produto x R$"
        )

        for _, row in df_retrabalho.iterrows():

            data = row.iloc[0]

            if pd.isna(data):
                continue

            if not hasattr(data, "month"):
                continue

            mes = mapa_datas.get(
                data.month
            )

            if mes is None:
                continue

            valor_total = row.iloc[1]
            faturamento = row.iloc[5]

            if (
                pd.isna(valor_total)
                or
                pd.isna(faturamento)
                or
                faturamento == 0
            ):
                continue

            dados_retrabalho[mes] = (
                float(valor_total)
                /
                float(faturamento)
            )

    except Exception as e:

        st.warning(
            f"Erro Retrabalho: {e}"
        )

    # ========================================================
    # 📊 INDICADORES
    # ========================================================
    montar_indicador(

        "🧪 NC Externas (%)",

        0.02,

        dados_nc,

        tipo="percentual",

        menor_melhor=True
    )

    montar_indicador(

        "💰 Custo Total de NC (R$)",

        15000,

        dados_custo,

        tipo="valor",

        menor_melhor=True
    )

    montar_indicador(

        "♻️ Refugo (%)",

        0.0025,

        dados_refugo,

        tipo="percentual",

        menor_melhor=True
    )

    montar_indicador(

        "🔧 Retrabalho (%)",

        0.005,

        dados_retrabalho,

        tipo="percentual",

        menor_melhor=True
    )







# ============================================================
# 🏭 PRODUÇÃO — TEMPO REAL (ATRASO + CARGA x CAPACIDADE)
# ============================================================

with tab3:

    import os
    import plotly.express as px
    import plotly.graph_objects as go
    import pandas as pd
    import numpy as np
    import holidays
    import calendar

    from datetime import datetime

    st.header("🏭 Atraso de Entregas (Tempo Real)")

    st.caption(
        "PVs com data de entrega vencida e ainda em aberto"
    )

    # ========================================================
    # 🔒 VALIDAÇÃO APS
    # ========================================================
    if df_aps.empty:

        st.warning(
            "Abra o APS para visualizar os indicadores."
        )

        st.stop()

    # ========================================================
    # 🔥 BASE APS
    # ========================================================
    base = df_aps.copy()

    # ========================================================
    # 🔒 COLUNAS OBRIGATÓRIAS APS
    # ========================================================
    required_cols = [

        "PV",
        "Processo",
        "Horas"
    ]

    faltando = [

        c for c in required_cols

        if c not in base.columns
    ]

    if faltando:

        st.error(
            f"Colunas obrigatórias ausentes no APS: {faltando}"
        )

        st.stop()

    # ========================================================
    # 🔥 NORMALIZAÇÃO APS
    # ========================================================
    base["PV"] = (

        base["PV"]

        .astype(str)

        .str.strip()
    )

    base["Processo"] = (

        base["Processo"]

        .astype(str)

        .str.upper()

        .str.strip()
    )

    base["Horas"] = pd.to_numeric(

        base["Horas"],

        errors="coerce"

    ).fillna(0)

    # ========================================================
    # 🔥 REMOVE PVs INVÁLIDAS
    # ========================================================
    base = base[

        base["PV"].notna()
    ]

    base = base[

        base["PV"] != ""
    ]

    base = base[

        base["PV"].str.lower() != "nan"
    ]

    # ========================================================
    # 📅 DATA APS
    # ========================================================
    if "DATA_ENTREGA_APS" in base.columns:

        base["DATA_ENTREGA_APS"] = pd.to_datetime(

            base["DATA_ENTREGA_APS"],

            errors="coerce"
        )

    else:

        base["DATA_ENTREGA_APS"] = pd.NaT

    # ========================================================
    # 📅 DATA HOJE
    # ========================================================
    hoje = pd.Timestamp.today().normalize()

    # ========================================================
    # 🚨 ATRASOS
    # ========================================================
    base_data = base.dropna(
        subset=["DATA_ENTREGA_APS"]
    ).copy()

    base_data["Atraso_dias"] = (

        hoje - base_data["DATA_ENTREGA_APS"]

    ).dt.days

    base_data["Atrasada"] = (

        base_data["Atraso_dias"] > 0
    )

    atrasadas = base_data[

        base_data["Atrasada"]
    ].copy()

    # ========================================================
    # 🔥 LEITURA PV.xlsx
    # ========================================================
    caminho_pv = os.path.abspath(
        "PV.xlsx"
    )

    if not os.path.exists(caminho_pv):

        st.error(
            f"Arquivo PV.xlsx não encontrado em: {caminho_pv}"
        )

        st.stop()

    try:

        df_pv = pd.read_excel(
            caminho_pv
        )

    except Exception as e:

        st.error(
            f"Erro ao ler PV.xlsx: {e}"
        )

        st.stop()

    # ========================================================
    # 🔥 NORMALIZAÇÃO COLUNAS
    # ========================================================
    df_pv.columns = [

        str(c).strip()

        for c in df_pv.columns
    ]

    # ========================================================
    # 🔥 COLUNAS FIXAS
    # ========================================================
    coluna_pv = "PV"
    coluna_data = "DATA DE ENTREGA"
    coluna_qtd = "QUANTIDADE"

    # ========================================================
    # 🔒 VALIDAÇÃO
    # ========================================================
    colunas_necessarias = [

        coluna_pv,
        coluna_data,
        coluna_qtd
    ]

    faltando_excel = [

        c for c in colunas_necessarias

        if c not in df_pv.columns
    ]

    if faltando_excel:

        st.error(
            f"Colunas ausentes no PV.xlsx: {faltando_excel}"
        )

        st.write(df_pv.columns.tolist())

        st.stop()

    # ========================================================
    # 🔥 TOTAL REAL DE PVs
    # ========================================================
    total_pvs = (

        df_pv[coluna_pv]

        .astype(str)

        .str.strip()

        .replace("", np.nan)

        .replace("nan", np.nan)

        .dropna()

        .nunique()
    )

    # ========================================================
    # 📊 KPIs
    # ========================================================
    qtd_atrasadas = (

        atrasadas["PV"]

        .astype(str)

        .str.strip()

        .nunique()
    )

    pct = (

        (qtd_atrasadas / total_pvs) * 100

        if total_pvs > 0

        else 0
    )

    # ========================================================
    # 📊 CARDS
    # ========================================================
    c1, c2, c3 = st.columns(3)

    c1.metric(
        "🚨 Atraso (%)",
        f"{pct:.1f}%"
    )

    c2.metric(
        "📦 PVs Atrasadas",
        qtd_atrasadas
    )

    c3.metric(
        "📦 Total PVs",
        total_pvs
    )

    st.divider()

    # ========================================================
    # 📊 DISTRIBUIÇÃO ATRASO
    # ========================================================
    st.subheader(
        "📊 Distribuição do atraso por faixa (dias)"
    )

    if qtd_atrasadas > 0:

        atrasadas = (

            atrasadas[
                [
                    "PV",
                    "Atraso_dias"
                ]
            ]

            .drop_duplicates()
        )

        atrasadas["Atraso_dias"] = (

            atrasadas["Atraso_dias"]

            .astype(int)
        )

        bins = [

            0,
            2,
            4,
            6,
            8,
            10,
            15,
            20,
            30,
            9999
        ]

        labels = [

            "1-2",
            "3-4",
            "5-6",
            "7-8",
            "9-10",
            "11-15",
            "16-20",
            "21-30",
            "30+"
        ]

        atrasadas["Faixa"] = pd.cut(

            atrasadas["Atraso_dias"],

            bins=bins,

            labels=labels,

            right=True
        )

        resumo = (

            atrasadas.groupby("Faixa")

            .size()

            .reindex(
                labels,
                fill_value=0
            )

            .reset_index(
                name="Quantidade"
            )
        )

        fig = px.bar(

            resumo,

            x="Faixa",

            y="Quantidade",

            color="Quantidade",

            color_continuous_scale="Reds",

            text="Quantidade"
        )

        fig.update_traces(
            textposition="outside"
        )

        fig.update_layout(

            title="Distribuição de Atraso por Faixa",

            xaxis_title="Faixa",

            yaxis_title="Quantidade",

            coloraxis_showscale=False,

            height=500
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    else:

        st.success(
            "Nenhuma PV em atraso no momento"
        )

    st.divider()

    # ========================================================
    # 📅 SELEÇÃO DE MÊS
    # ========================================================
    meses_nomes = {

        1: "Janeiro",
        2: "Fevereiro",
        3: "Março",
        4: "Abril",
        5: "Maio",
        6: "Junho",
        7: "Julho",
        8: "Agosto",
        9: "Setembro",
        10: "Outubro",
        11: "Novembro",
        12: "Dezembro"
    }

    st.markdown(
        "### 📅 Planejamento por Mês"
    )

    col_mes, col_info = st.columns([1, 3])

    with col_mes:

        mes_selecionado = st.selectbox(

            "Selecionar mês planejado",

            options=list(meses_nomes.keys()),

            format_func=lambda x: meses_nomes[x],

            index=datetime.today().month - 1
        )

    with col_info:

        st.info(
            "A capacidade disponível diminui automaticamente "
            "conforme os dias úteis restantes do mês."
        )

    st.divider()

    # ========================================================
    # 📊 CARGA x CAPACIDADE
    # ========================================================
    st.subheader(
        "📊 Carga Planejada x Capacidade Disponível"
    )

    # ========================================================
    # 🔥 RECURSOS
    # ========================================================
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

    # ========================================================
    # 📅 CALENDÁRIO BRASILEIRO
    # ========================================================
    hoje_real = datetime.today()

    ano = hoje_real.year

    mes = mes_selecionado

    brasil_feriados = holidays.Brazil(
        years=ano
    )

    total_dias_mes = calendar.monthrange(
        ano,
        mes
    )[1]

    # ========================================================
    # 🔥 DIAS ÚTEIS RESTANTES
    # ========================================================
    dias_uteis_restantes = 0

    if mes == hoje_real.month:

        dia_inicio = hoje_real.day

    else:

        dia_inicio = 1

    for dia in range(

        dia_inicio,

        total_dias_mes + 1

    ):

        data = datetime(
            ano,
            mes,
            dia
        )

        if (

            data.weekday() < 5

            and

            data.date() not in brasil_feriados

        ):

            dias_uteis_restantes += 1

    # ========================================================
    # 🔥 CAPACIDADE REAL
    # ========================================================
    #
    # 1 recurso:
    #
    # (4×9)+(1×8)
    # = 44h semana
    #
    # 44 × 0.8
    # = 35.2h semana
    #
    # 35.2 / 5
    # = 7.04h dia
    #
    # ========================================================
    horas_semana_recurso = 44

    horas_semana_efetiva = (

        horas_semana_recurso
        *
        0.8
    )

    horas_dia_recurso = round(

        horas_semana_efetiva
        / 5,

        2
    )

    # ========================================================
    # 🔥 BASE MENSAL
    # ========================================================
    carga = df_pv.copy()

    carga[coluna_data] = pd.to_datetime(

        carga[coluna_data],

        errors="coerce"
    )

    carga = carga.dropna(
        subset=[coluna_data]
    )

    carga = carga[

        (
            carga[coluna_data].dt.month == mes
        )

        &

        (
            carga[coluna_data].dt.year == ano
        )
    ]

    # ========================================================
    # 🔥 QUANTIDADE
    # ========================================================
    carga[coluna_qtd] = pd.to_numeric(

        carga[coluna_qtd],

        errors="coerce"

    ).fillna(0)

    # ========================================================
    # 🔥 PROCESSOS
    # ========================================================
    processos_excel = [

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

    # ========================================================
    # 🔥 NORMALIZAÇÃO TEMPOS
    # ========================================================
    for proc in processos_excel:

        if proc in carga.columns:

            carga[proc] = pd.to_numeric(

                carga[proc],

                errors="coerce"

            ).fillna(0)

    # ========================================================
    # 🔥 SOMA TEMPOS ROTEIRO
    # ========================================================
    #
    # TEMPOS DO PV.xlsx ESTÃO EM MINUTOS
    #
    # REGRA:
    #
    # quantidade × soma dos tempos
    #
    # depois:
    #
    # ÷ 60 para converter em horas
    #
    # ========================================================

    carga["TEMPO_TOTAL_ROTEIRO"] = (

        carga[processos_excel]

        .sum(axis=1)
    )

    # ========================================================
    # 🔥 CARGA TOTAL DA PV (HORAS)
    # ========================================================

    carga["CARGA_TOTAL_PV"] = (

        (
            carga[coluna_qtd]

            *

            carga["TEMPO_TOTAL_ROTEIRO"]
        )

        / 60
    ).round(2)

    # ========================================================
    # 🔥 RESUMO PROCESSOS
    # ========================================================

    lista_resumo = []

    for processo in processos_excel:

        # ====================================================
        # 🔥 HORAS PLANEJADAS DO PROCESSO
        # ====================================================
        #
        # quantidade × tempo do processo
        #
        # dividido por 60
        #
        # ====================================================

        horas_processo = (

            (
                carga[coluna_qtd]

                *

                carga[processo]
            )

            / 60

        ).sum()

        horas_processo = round(
            horas_processo,
            2
        )

        # ====================================================
        # 🔥 CAPACIDADE DISPONÍVEL
        # ====================================================

        recursos = MAQUINAS.get(
            processo,
            0
        )

        capacidade_total = (

            horas_dia_recurso

            *

            dias_uteis_restantes

            *

            recursos
        )

        capacidade_total = round(
            capacidade_total,
            2
        )

        # ====================================================
        # 🔥 UTILIZAÇÃO
        # ====================================================

        utilizacao = (

            (
                horas_processo
                /
                capacidade_total
            ) * 100

            if capacidade_total > 0

            else 0
        )

        utilizacao = round(
            utilizacao,
            2
        )

        # ====================================================
        # 🔥 RESUMO
        # ====================================================

        lista_resumo.append({

            "PROCESSO_REAL": processo,

            "Carga": horas_processo,

            "Capacidade": capacidade_total,

            "Utilizacao": utilizacao,

            "Recursos": recursos
        })

    # ========================================================
    # 🔥 DATAFRAME FINAL
    # ========================================================
    resumo_cap = pd.DataFrame(
        lista_resumo
    )

    # ========================================================
    # 🔥 REMOVE ZERADOS
    # ========================================================
    resumo_cap = resumo_cap[

        (
            resumo_cap["Carga"] > 0
        )

        |

        (
            resumo_cap["Capacidade"] > 0
        )
    ]

    # ========================================================
    # 🔥 ORDENA
    # ========================================================
    resumo_cap = resumo_cap.sort_values(

        "Utilizacao",

        ascending=False
    )

    # ========================================================
    # 📊 GRÁFICO
    # ========================================================
    fig2 = go.Figure()

    # 🔴 CARGA
    fig2.add_bar(

        name="Carga Planejada",

        x=resumo_cap["PROCESSO_REAL"],

        y=resumo_cap["Carga"],

        marker_color="#d62728",

        text=resumo_cap["Carga"],

        textposition="outside"
    )

    # 🔵 CAPACIDADE
    fig2.add_bar(

        name="Capacidade Disponível",

        x=resumo_cap["PROCESSO_REAL"],

        y=resumo_cap["Capacidade"],

        marker_color="#1f77b4",

        text=resumo_cap["Capacidade"],

        textposition="outside"
    )

    fig2.update_layout(

        barmode="group",

        height=750,

        title=(
            f"Carga Planejada x Capacidade Disponível "
            f"({dias_uteis_restantes} dias úteis restantes)"
        ),

        xaxis_title="Processo",

        yaxis_title="Horas",

        legend_title="Indicadores"
    )

    st.plotly_chart(
        fig2,
        use_container_width=True
    )

    # ========================================================
    # 📋 RESUMO EXECUTIVO
    # ========================================================
    st.markdown(
        "### 📋 Resumo Executivo"
    )

    total_carga_mes = round(

        carga["CARGA_TOTAL_PV"].sum(),

        2
    )

    total_capacidade_mes = round(

        resumo_cap["Capacidade"].sum(),

        2
    )

    utilizacao_global = round(

        (
            total_carga_mes
            /
            total_capacidade_mes
        ) * 100,

        2

    ) if total_capacidade_mes > 0 else 0

    r1, r2, r3 = st.columns(3)

    r1.metric(
        "🔥 Carga Planejada Total",
        f"{total_carga_mes:,.2f} h"
    )

    r2.metric(
        "⚙️ Capacidade Disponível",
        f"{total_capacidade_mes:,.2f} h"
    )

    r3.metric(
        "📈 Utilização Global",
        f"{utilizacao_global:.2f}%"
    )

    # ========================================================
    # 📋 DETALHAMENTO
    # ========================================================
    with st.expander(
        "📋 Detalhamento por Processo"
    ):

        tabela = resumo_cap.copy()

        tabela = tabela.rename(columns={

            "PROCESSO_REAL": "Processo",

            "Carga": "Carga Planejada (h)",

            "Capacidade": "Capacidade Disponível (h)",

            "Utilizacao": "Utilização (%)",

            "Recursos": "Qtd Recursos"
        })

        st.dataframe(

            tabela[
                [
                    "Processo",
                    "Qtd Recursos",
                    "Carga Planejada (h)",
                    "Capacidade Disponível (h)",
                    "Utilização (%)"
                ]
            ],

            use_container_width=True
        )







# ============================================================
# 🔧 MANUTENÇÃO — BLOCO FINAL OFICIAL
# ============================================================

with tab4:

    import os
    import pandas as pd
    import plotly.graph_objects as go
    import numpy as np

    st.header("🔧 Custo de Manutenção")

    # ========================================================
    # 📁 CAMINHO
    # ========================================================
    caminho = os.path.abspath(
        "data/Indicadores_manutencao/manutencao.xlsx"
    )

    # ========================================================
    # 🚨 EXISTÊNCIA
    # ========================================================
    if not os.path.exists(caminho):

        st.error(
            "Arquivo de manutenção não encontrado"
        )

        st.stop()

    # ========================================================
    # 📊 LEITURA
    # ========================================================
    try:

        df = pd.read_excel(
            caminho,
            dtype=str
        )

    except Exception as e:

        st.error(
            f"Erro ao ler arquivo de manutenção: {e}"
        )

        st.stop()

    # ========================================================
    # 🧹 NORMALIZAÇÃO COLUNAS
    # ========================================================
    df.columns = [

        str(c).strip()

        for c in df.columns
    ]

    # ========================================================
    # 🔍 COLUNAS OFICIAIS
    # ========================================================
    col_mes   = "Mês"
    col_fat   = "Faturamento Mensal"
    col_np    = "Corretiva não programada"
    col_cp    = "Corretiva programada"
    col_prev  = "Preventiva"
    col_pred  = "Preditiva"
    col_melh  = "Melhoria de Máquinas"

    colunas_necessarias = [

        col_mes,
        col_fat,
        col_np,
        col_cp,
        col_prev,
        col_pred,
        col_melh
    ]

    # ========================================================
    # 🚨 VALIDAÇÃO
    # ========================================================
    faltando = [

        c for c in colunas_necessarias

        if c not in df.columns
    ]

    if faltando:

        st.error(
            f"Colunas ausentes: {faltando}"
        )

        st.stop()

    # ========================================================
    # 🧹 LIMPEZA MONETÁRIA
    # ========================================================
    def limpar_moeda(v):

        if pd.isna(v):
            return 0.0

        v = str(v).strip()

        if v == "":
            return 0.0

        v = (
            v.replace("R$", "")
             .replace(" ", "")
             .replace("\xa0", "")
        )

        if "," in v:

            v = (
                v.replace(".", "")
                 .replace(",", ".")
            )

        try:

            return float(v)

        except:

            return 0.0

    # ========================================================
    # 🔥 CONVERSÃO NUMÉRICA
    # ========================================================
    for col in [

        col_fat,
        col_np,
        col_cp,
        col_prev,
        col_pred,
        col_melh
    ]:

        df[col] = (

            df[col]
            .apply(limpar_moeda)
            .fillna(0)
        )

    # ========================================================
    # 🧹 REMOVE LINHAS VAZIAS
    # ========================================================
    df = df[

        df[col_mes]
        .notna()
    ].copy()

    # ========================================================
    # 📊 TOTAL MENSAL
    # ========================================================
    df["Total"] = (

        df[col_np]

        + df[col_cp]

        + df[col_prev]

        + df[col_pred]

        + df[col_melh]
    )

    # ========================================================
    # 🎯 META
    # ========================================================
    df["Meta"] = (

        df[col_fat] * 0.005
    )

    # ========================================================
    # 📊 ACUMULADOS
    # ========================================================
    df["NP_acum"] = (
        df[col_np].cumsum()
    )

    df["CP_acum"] = (
        df[col_cp].cumsum()
    )

    df["Prev_acum"] = (
        df[col_prev].cumsum()
    )

    df["Pred_acum"] = (
        df[col_pred].cumsum()
    )

    df["Melh_acum"] = (
        df[col_melh].cumsum()
    )

    df["Total_acum"] = (
        df["Total"].cumsum()
    )

    df["Meta_acum"] = (
        df["Meta"].cumsum()
    )

    # ========================================================
    # 🚨 STATUS ISO
    # ========================================================
    df["Status_ISO"] = (

        df["Total"]

        <=

        df["Meta"]
    )

    df["Status_ISO_acum"] = (

        df["Total_acum"]

        <=

        df["Meta_acum"]
    )

    # ========================================================
    # 📊 ESCALA DINÂMICA
    # ========================================================
    max_valor = max(

        df["Total"].max(),

        df["Total_acum"].max(),

        df["Meta"].max(),

        df["Meta_acum"].max()
    )

    limite_y = (

        max_valor * 1.25

        if max_valor > 0

        else 1
    )

    # ========================================================
    # 💰 FORMATAÇÃO
    # ========================================================
    def moeda(v):

        return (

            f"R$ {v:,.0f}"
            .replace(",", ".")
        )

    def moeda_kpi(v):

        return (

            f"R$ {v:,.2f}"
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )

    # ========================================================
    # 📊 GRÁFICO
    # ========================================================
    fig = go.Figure()

    # ========================================================
    # 📊 BARRAS MENSAIS
    # ========================================================
    fig.add_bar(

        name="NP",

        x=df[col_mes],

        y=df[col_np],

        text=[

            moeda(v)

            for v in df[col_np]
        ],

        textposition="outside"
    )

    fig.add_bar(

        name="CP",

        x=df[col_mes],

        y=df[col_cp],

        text=[

            moeda(v)

            for v in df[col_cp]
        ],

        textposition="outside"
    )

    fig.add_bar(

        name="Prev",

        x=df[col_mes],

        y=df[col_prev],

        text=[

            moeda(v)

            for v in df[col_prev]
        ],

        textposition="outside"
    )

    fig.add_bar(

        name="Pred",

        x=df[col_mes],

        y=df[col_pred],

        text=[

            moeda(v)

            for v in df[col_pred]
        ],

        textposition="outside"
    )

    fig.add_bar(

        name="Melh",

        x=df[col_mes],

        y=df[col_melh],

        text=[

            moeda(v)

            for v in df[col_melh]
        ],

        textposition="outside"
    )

    # ========================================================
    # 📊 TOTAL MENSAL
    # ========================================================
    cores_total = [

        "green"

        if ok

        else "red"

        for ok in df["Status_ISO"]
    ]

    fig.add_bar(

        name="Total",

        x=df[col_mes],

        y=df["Total"],

        text=[

            moeda(v)

            for v in df["Total"]
        ],

        textposition="outside",

        marker_color=cores_total
    )

    # ========================================================
    # 📊 TOTAL ACUMULADO
    # ========================================================
    fig.add_bar(

        name="Total Acum",

        x=df[col_mes],

        y=df["Total_acum"],

        text=[

            moeda(v)

            for v in df["Total_acum"]
        ],

        textposition="outside",

        marker_color="darkgreen"
    )

    # ========================================================
    # 📈 META MENSAL
    # ========================================================
    fig.add_scatter(

        name="Meta",

        x=df[col_mes],

        y=df["Meta"],

        mode="lines+markers",

        line=dict(

            color="red",

            dash="dash"
        )
    )

    # ========================================================
    # 📈 META ACUMULADA
    # ========================================================
    fig.add_scatter(

        name="Meta Acum",

        x=df[col_mes],

        y=df["Meta_acum"],

        mode="lines+markers",

        line=dict(

            color="orange",

            dash="dot"
        )
    )

    # ========================================================
    # 📊 LAYOUT
    # ========================================================
    fig.update_layout(

        barmode="group",

        height=650,

        yaxis=dict(
            range=[0, limite_y]
        ),

        yaxis_title="R$",

        xaxis_title="Mês",

        legend_title="Indicadores"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    # ========================================================
    # 📊 KPI FINAL
    # ========================================================
    ultimo = df.iloc[-1]

    status_mes = (

        "🟢 OK"

        if ultimo["Status_ISO"]

        else "🔴 ACIMA"
    )

    status_acum = (

        "🟢 OK"

        if ultimo["Status_ISO_acum"]

        else "🔴 ACIMA"
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(

        "💸 Custo Mês",

        moeda_kpi(
            ultimo["Total"]
        )
    )

    c2.metric(

        "🎯 Meta Mês",

        moeda_kpi(
            ultimo["Meta"]
        )
    )

    c3.metric(

        "📊 Custo Acumulado",

        moeda_kpi(
            ultimo["Total_acum"]
        )
    )

    c4.metric(

        "📈 Meta Acumulada",

        moeda_kpi(
            ultimo["Meta_acum"]
        )
    )

    # ========================================================
    # 🚨 STATUS FINAL
    # ========================================================
    if ultimo["Status_ISO_acum"]:

        st.success(
            f"Status ISO acumulado: {status_acum}"
        )

    else:

        st.error(
            f"Status ISO acumulado: {status_acum}"
        )





# ============================================================
# 📦 Indicadores de Compras & Fornecedores
# ============================================================

with tab5:

    import os
    import pandas as pd
    import plotly.graph_objects as go

    st.subheader("📦 Indicadores de Compras & Fornecedores")

    # ========================================================
    # 📂 CAMINHO DO EXCEL
    # ========================================================
    caminho_excel = "data/Indicadores_Compras_Fornecedores/INDICADOR_PROVEDORES.xlsx"

    # ========================================================
    # 🔒 VALIDAÇÃO
    # ========================================================
    if not os.path.exists(caminho_excel):

        st.error("❌ Arquivo INDICADOR_PROVEDORES.xlsx não encontrado.")

    else:

        try:

            # ====================================================
            # 📥 LEITURA DAS ABAS
            # ====================================================
            xls = pd.ExcelFile(caminho_excel)

            df_prazo = pd.read_excel(
                xls,
                sheet_name=xls.sheet_names[0]
            )

            df_devolucao = pd.read_excel(
                xls,
                sheet_name=xls.sheet_names[1]
            )

            df_geral = pd.read_excel(
                xls,
                sheet_name=xls.sheet_names[2]
            )

            # ====================================================
            # 🧹 LIMPEZA
            # ====================================================
            df_prazo = df_prazo.dropna(how="all")
            df_devolucao = df_devolucao.dropna(how="all")
            df_geral = df_geral.dropna(how="all")

            # ====================================================
            # 🧹 AJUSTE NOMES COLUNAS
            # ====================================================
            df_prazo.columns = [str(c).strip() for c in df_prazo.columns]
            df_devolucao.columns = [str(c).strip() for c in df_devolucao.columns]
            df_geral.columns = [str(c).strip() for c in df_geral.columns]

            # ====================================================
            # 📊 FUNÇÃO ACM
            # ====================================================
            def media_apenas_com_dados(lista):

                dados_validos = [
                    v for v in lista
                    if v is not None and v > 0
                ]

                if len(dados_validos) == 0:
                    return 0

                return round(
                    sum(dados_validos) / len(dados_validos),
                    1
                )

            # ====================================================
            # 📊 DADOS PRAZO PROVEDOR
            # ====================================================
            meses_prazo = (
                df_prazo.iloc[:, 0]
                .astype(str)
                .tolist()
            )

            prazo_ok = (
                pd.to_numeric(
                    df_prazo.iloc[:, 2],
                    errors="coerce"
                )
                .fillna(0) * 100
            ).round(1).tolist()

            meta_prazo = [90] * len(meses_prazo)

            acm_prazo = media_apenas_com_dados(
                prazo_ok
            )

            meses_prazo.append("ACM")
            prazo_ok.append(acm_prazo)
            meta_prazo.append(90)

            # ====================================================
            # 📊 DADOS DEVOLUÇÕES
            # ====================================================
            meses_dev = (
                df_devolucao.iloc[:, 0]
                .astype(str)
                .tolist()
            )

            entregas_total = pd.to_numeric(
                df_devolucao.iloc[:, 1],
                errors="coerce"
            ).fillna(0)

            qtd_devolucoes = pd.to_numeric(
                df_devolucao.iloc[:, 2],
                errors="coerce"
            ).fillna(0)

            percentual_sem_devolucao = []

            for total, devolucao in zip(
                entregas_total,
                qtd_devolucoes
            ):

                if total > 0:

                    valor = (
                        (total - devolucao)
                        / total
                    ) * 100

                else:

                    valor = 0

                percentual_sem_devolucao.append(
                    round(valor, 1)
                )

            meta_dev = [90] * len(meses_dev)

            acm_devolucao = media_apenas_com_dados(
                percentual_sem_devolucao
            )

            meses_dev.append("ACM")
            percentual_sem_devolucao.append(
                acm_devolucao
            )
            meta_dev.append(90)

            # ====================================================
            # 📊 DADOS VISÃO GERAL
            # ====================================================
            meses_geral = (
                df_geral.iloc[:, 0]
                .astype(str)
                .tolist()
            )

            percentual_prazo_geral = (
                pd.to_numeric(
                    df_geral.iloc[:, 3],
                    errors="coerce"
                )
                .fillna(0) * 100
            ).round(1).tolist()

            meta_geral = [98] * len(meses_geral)

            acm_geral = media_apenas_com_dados(
                percentual_prazo_geral
            )

            meses_geral.append("ACM")
            percentual_prazo_geral.append(
                acm_geral
            )
            meta_geral.append(98)

            # ====================================================
            # 📊 1 - PRAZO DO PROVEDOR
            # ====================================================
            st.subheader(
                "📊 Índice de Entrega do Provedor Externo no Prazo"
            )

            fig1 = go.Figure()

            # 🔶 BARRAS
            fig1.add_trace(go.Bar(
                x=meses_prazo,
                y=prazo_ok,
                text=[
                    f"<b>{v:.0f}%</b>"
                    for v in prazo_ok
                ],
                textposition="inside",
                insidetextanchor="middle",
                textfont=dict(
                    size=14,
                    color="white"
                ),
                cliponaxis=False,
                name="% Prazo e Antecipado"
            ))

            # 🔴 META
            fig1.add_trace(go.Scatter(
                x=meses_prazo,
                y=meta_prazo,
                mode="lines+markers+text",
                text=[
                    f"{v:.0f}%"
                    for v in meta_prazo
                ],
                textposition="top center",
                textfont=dict(
                    size=11
                ),
                marker=dict(
                    size=7
                ),
                name="Meta",
                line=dict(
                    color="red",
                    dash="dash",
                    width=3
                )
            ))

            fig1.update_layout(
                height=520,
                margin=dict(
                    t=100
                ),
                yaxis_title="%",
                xaxis_title="Mês",
                yaxis=dict(
                    range=[0, 120]
                ),
                xaxis=dict(
                    type="category"
                )
            )

            st.plotly_chart(
                fig1,
                use_container_width=True
            )

            if prazo_ok[-2] >= 90:

                st.success(
                    "🟢 Fornecedor dentro do prazo"
                )

            else:

                st.error(
                    "🔴 Problemas de prazo"
                )

            st.info(
                f"ACM Prazo: {acm_prazo:.1f}%"
            )

            # ====================================================
            # 📊 2 - DEVOLUÇÕES
            # ====================================================
            st.subheader(
                "📊 Índice de Devoluções ao Provedor Externo"
            )

            fig2 = go.Figure()

            # 🔶 BARRAS
            fig2.add_trace(go.Bar(
                x=meses_dev,
                y=percentual_sem_devolucao,
                text=[
                    f"<b>{v:.1f}%</b>"
                    for v in percentual_sem_devolucao
                ],
                textposition="inside",
                insidetextanchor="middle",
                textfont=dict(
                    size=14,
                    color="white"
                ),
                cliponaxis=False,
                name="% Sem Devoluções"
            ))

            # 🔴 META
            fig2.add_trace(go.Scatter(
                x=meses_dev,
                y=meta_dev,
                mode="lines+markers+text",
                text=[
                    f"{v:.0f}%"
                    for v in meta_dev
                ],
                textposition="top center",
                textfont=dict(
                    size=11
                ),
                marker=dict(
                    size=7
                ),
                name="Meta",
                line=dict(
                    color="red",
                    dash="dash",
                    width=3
                )
            ))

            fig2.update_layout(
                height=520,
                margin=dict(
                    t=100
                ),
                yaxis_title="%",
                xaxis_title="Mês",
                yaxis=dict(
                    range=[0, 120]
                ),
                xaxis=dict(
                    type="category"
                )
            )

            st.plotly_chart(
                fig2,
                use_container_width=True
            )

            if percentual_sem_devolucao[-2] >= 90:

                st.success(
                    "🟢 Qualidade adequada"
                )

            else:

                st.error(
                    "🔴 Problema de qualidade"
                )

            st.info(
                f"ACM Devolução: {acm_devolucao:.1f}%"
            )

            # ====================================================
            # 📊 3 - VISÃO COMPLETA
            # ====================================================
            st.subheader(
                "📊 Entregas no Prazo (Visão Completa) - GE"
            )

            fig3 = go.Figure()

            # 🔵 BARRAS
            fig3.add_trace(go.Bar(
                x=meses_geral,
                y=percentual_prazo_geral,
                text=[
                    f"<b>{v:.1f}%</b>"
                    for v in percentual_prazo_geral
                ],
                textposition="inside",
                insidetextanchor="middle",
                textfont=dict(
                    size=14,
                    color="white"
                ),
                cliponaxis=False,
                name="% Entregue no Prazo"
            ))

            # 🔴 META
            fig3.add_trace(go.Scatter(
                x=meses_geral,
                y=meta_geral,
                mode="lines+markers+text",
                text=[
                    f"{v:.0f}%"
                    for v in meta_geral
                ],
                textposition="top center",
                textfont=dict(
                    size=11
                ),
                marker=dict(
                    size=7
                ),
                name="Meta",
                line=dict(
                    color="red",
                    dash="dash",
                    width=3
                )
            ))

            fig3.update_layout(
                height=550,
                margin=dict(
                    t=100
                ),
                yaxis_title="% Entregas no Prazo",
                xaxis_title="Mês",
                yaxis=dict(
                    range=[0, 120]
                ),
                xaxis=dict(
                    type="category"
                )
            )

            st.plotly_chart(
                fig3,
                use_container_width=True
            )

            if percentual_prazo_geral[-2] >= 98:

                st.success(
                    "🟢 Performance dentro da meta"
                )

            else:

                st.error(
                    "🔴 Performance abaixo da meta"
                )

            st.info(
                f"ACM Geral: {acm_geral:.1f}%"
            )

            # ====================================================
            # 📎 DOWNLOAD EVIDÊNCIA
            # ====================================================
            with open(
                caminho_excel,
                "rb"
            ) as f:

                st.download_button(
                    "📎 Baixar evidência",
                    f,
                    file_name="INDICADOR_PROVEDORES.xlsx"
                )

        except Exception as e:

            st.error(
                f"❌ Erro ao carregar indicadores: {e}"
            )





# ============================================================
# 👥 INDICADORES DE RH (PADRÃO ISO COMPLETO)
# ============================================================

with tab6:

    import os
    import pandas as pd
    import plotly.graph_objects as go

    st.subheader("👥 Indicadores de RH")

    # ========================================================
    # 📂 CAMINHO EXCEL
    # ========================================================
    caminho_excel = "data/Indicadores_RH/Indicadores_RH_2026 ATUAL.xlsx"

    # ========================================================
    # 🔒 VALIDAÇÃO
    # ========================================================
    if not os.path.exists(caminho_excel):

        st.error("❌ Arquivo Indicadores_RH_2026 ATUAL.xlsx não encontrado.")

    else:

        try:

            # ====================================================
            # 📥 LEITURA DAS ABAS
            # ====================================================
            xls = pd.ExcelFile(caminho_excel)

            df_abs = pd.read_excel(
                xls,
                sheet_name="ABSENTEISMO X HHT"
            )

            df_trein = pd.read_excel(
                xls,
                sheet_name="HORAS TERINAMENTOS X HHT"
            )

            df_faltas = pd.read_excel(
                xls,
                sheet_name="FALTAS INJUSTIFICADAS X HHT"
            )

            df_extra = pd.read_excel(
                xls,
                sheet_name="HORAS EXTRAS X HHT"
            )

            # ====================================================
            # 🧹 LIMPEZA PADRÃO
            # ====================================================
            def preparar_df(df):

                df = df.dropna(
                    how="all"
                ).reset_index(drop=True)

                df.columns = [
                    str(c).strip()
                    for c in df.columns
                ]

                # remove cabeçalhos extras
                df = df.iloc[2:].copy()

                df.columns = [
                    "MES",
                    "VALOR",
                    "META"
                ]

                df["MES"] = (
                    df["MES"]
                    .astype(str)
                    .str.strip()
                )

                # remove linhas inválidas
                meses_validos = [
                    "Jan","Fev","Mar","Abr",
                    "Mai","Jun","Jul","Ago",
                    "Set","Out","Nov","Dez"
                ]

                df = df[
                    df["MES"].isin(
                        meses_validos
                    )
                ].copy()

                df["VALOR"] = (
                    pd.to_numeric(
                        df["VALOR"],
                        errors="coerce"
                    ).fillna(0) * 100
                ).round(2)

                df["META"] = (
                    pd.to_numeric(
                        df["META"],
                        errors="coerce"
                    ).fillna(0) * 100
                ).round(2)

                return df

            df_abs = preparar_df(df_abs)
            df_trein = preparar_df(df_trein)
            df_faltas = preparar_df(df_faltas)
            df_extra = preparar_df(df_extra)

            # ====================================================
            # 📊 FUNÇÃO ACM
            # ====================================================
            def calcular_acm(lista):

                dados_validos = [
                    v for v in lista
                    if v > 0
                ]

                if len(dados_validos) == 0:
                    return 0

                return round(
                    sum(dados_validos)
                    / len(dados_validos),
                    2
                )

            # ====================================================
            # 📊 FUNÇÃO PADRÃO ISO
            # ====================================================
            def grafico_iso(
                titulo,
                descricao,
                df,
                tipo_meta
            ):

                meses = df["MES"].tolist()

                valores = (
                    df["VALOR"]
                    .tolist()
                )

                metas = (
                    df["META"]
                    .tolist()
                )

                # ================================================
                # 📊 ACM
                # ================================================
                acm = calcular_acm(
                    valores
                )

                meta_padrao = (
                    metas[0]
                    if len(metas) > 0
                    else 0
                )

                # ================================================
                # ➕ ACUMULADO
                # ================================================
                meses.append("ACM")
                valores.append(acm)
                metas.append(meta_padrao)

                # ================================================
                # 📊 GRÁFICO
                # ================================================
                st.subheader(titulo)

                fig = go.Figure()

                # ================================================
                # 🔵 BARRAS
                # ================================================
                fig.add_trace(go.Bar(
                    x=meses,
                    y=valores,
                    text=[
                        f"<b>{v:.2f}%</b>"
                        for v in valores
                    ],
                    textposition="inside",
                    insidetextanchor="middle",
                    textfont=dict(
                        size=14,
                        color="white"
                    ),
                    cliponaxis=False,
                    name="Indicador"
                ))

                # ================================================
                # 🔴 META
                # ================================================
                fig.add_trace(go.Scatter(
                    x=meses,
                    y=metas,
                    mode="lines+markers+text",
                    text=[
                        f"{v:.2f}%"
                        for v in metas
                    ],
                    textposition="top center",
                    textfont=dict(
                        size=11
                    ),
                    marker=dict(
                        size=7
                    ),
                    name="Meta",
                    line=dict(
                        color="red",
                        dash="dash",
                        width=3
                    )
                ))

                # ================================================
                # 📐 LAYOUT
                # ================================================
                max_valor = max(
                    max(valores),
                    max(metas)
                )

                fig.update_layout(
                    height=520,
                    margin=dict(
                        t=100
                    ),
                    yaxis_title="%",
                    xaxis_title="Mês",
                    showlegend=False,
                    yaxis=dict(
                        range=[
                            0,
                            max_valor * 1.25
                        ]
                    ),
                    xaxis=dict(
                        type="category"
                    )
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True
                )

                # ================================================
                # 📌 STATUS ISO
                # ================================================
                ultimo = valores[-2]

                if tipo_meta == "max":

                    if ultimo <= meta_padrao:

                        st.success(
                            "🟢 Indicador sob controle, sem impacto relevante na operação"
                        )

                    else:

                        st.error(
                            "🔴 Indicador fora da meta, com impacto potencial na operação e necessidade de ação corretiva"
                        )

                else:

                    if ultimo >= meta_padrao:

                        st.success(
                            "🟢 Indicador adequado para sustentação operacional"
                        )

                    else:

                        st.error(
                            "🔴 Indicador abaixo do esperado, podendo comprometer desempenho e qualidade"
                        )

                st.caption(
                    descricao
                )

                st.info(
                    f"ACM: {acm:.2f}%"
                )

            # ====================================================
            # 1️⃣ ABSENTEÍSMO
            # ====================================================
            grafico_iso(
                "📊 Índice de Absenteísmo (HHT)",
                "Mede a ausência de colaboradores em relação às horas trabalhadas.",
                df_abs,
                "max"
            )

            # ====================================================
            # 2️⃣ TREINAMENTO
            # ====================================================
            grafico_iso(
                "📊 Índice de Treinamento (HHT)",
                "Mede o volume de treinamento aplicado em relação às horas trabalhadas.",
                df_trein,
                "min"
            )

            # ====================================================
            # 3️⃣ FALTAS INJUSTIFICADAS
            # ====================================================
            grafico_iso(
                "📊 Índice de Faltas Injustificadas (HHT)",
                "Mede faltas sem justificativa em relação às horas trabalhadas.",
                df_faltas,
                "max"
            )

            # ====================================================
            # 4️⃣ HORAS EXTRAS
            # ====================================================
            grafico_iso(
                "📊 Índice de Horas Extras (HHT)",
                "Mede o uso de horas extras sobre o total de horas trabalhadas.",
                df_extra,
                "max"
            )

            # ====================================================
            # 📎 DOWNLOAD EVIDÊNCIA
            # ====================================================
            with open(
                caminho_excel,
                "rb"
            ) as f:

                st.download_button(
                    "📎 Baixar evidência",
                    f,
                    file_name="Indicadores_RH_2026 ATUAL.xlsx"
                )

        except Exception as e:

            st.error(
                f"❌ Erro ao carregar indicadores de RH: {e}"
            )