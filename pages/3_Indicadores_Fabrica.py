import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Indicadores da Fábrica", layout="wide")

# ============================================================
# 🔒 BASE APS (ÚNICA E PROTEGIDA)
# ============================================================

df_raw = st.session_state.get("df", pd.DataFrame())

if df_raw is None or not isinstance(df_raw, pd.DataFrame):
    df_raw = pd.DataFrame()

df_aps = df_raw.copy()

# ============================================================
# 🚦 VISÃO EXECUTIVA (ALINHADA COM PRODUÇÃO)
# ============================================================

st.subheader("🚦 Visão Executiva")
st.caption("Indicador consolidado baseado em entregas vencidas no APS (tempo real)")

pct_atraso = 0

required_cols = ["PV", "DATA_ENTREGA_APS"]

if not df_aps.empty and all(c in df_aps.columns for c in required_cols):

    base = df_aps.copy()

    # 🔒 garante formato correto
    base["DATA_ENTREGA_APS"] = pd.to_datetime(base["DATA_ENTREGA_APS"], errors="coerce")

    hoje = pd.Timestamp.today().normalize()

    # 📦 consolidação por PV
    pv = base.groupby("PV", as_index=False).agg(
        data_entrega=("DATA_ENTREGA_APS", "min")
    )

    pv = pv.dropna(subset=["data_entrega"])

    # 🚨 atraso em tempo real
    pv["Atraso_dias"] = (hoje - pv["data_entrega"]).dt.days
    pv["Atrasada"] = pv["Atraso_dias"] > 0

    total = len(pv)
    atrasadas = pv["Atrasada"].sum()

    pct_atraso = (atrasadas / total * 100) if total > 0 else 0

# ============================================================
# 🔥 CLASSIFICAÇÃO EXECUTIVA
# ============================================================

def classificar(valor):
    if valor > 15:
        return "🔴 Crítico"
    elif valor > 5:
        return "🟡 Atenção"
    else:
        return "🟢 Saudável"

# ============================================================
# 📊 KPIs EXECUTIVOS
# ============================================================

c1, c2 = st.columns(2)

c1.metric("🚨 Entregas em Risco (%)", f"{pct_atraso:.1f}%")
c2.metric("Status Geral", classificar(pct_atraso))

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
# 💰 COMERCIAL — COMPLETO (ISO + EVIDÊNCIA + KPI + REGRA)
# ============================================================

with tab1:

    import os

    st.subheader("💰 Indicador Comercial (Orçamentos → Pedidos)")
    st.caption("Meta: ≥ 25%")

    ANO = "2026"
    META = 0.25

    # ========================================================
    # 📊 BASE CONTROLADA (ATUALIZAR MÊS A MÊS)
    # ========================================================
    indicador_comercial = {
        "Jan": {"valor": 0.1463, "arquivo": "INDC. COMERCIAL - JANEIRO.docx"},
        "Fev": {"valor": 0.1282, "arquivo": "INDI. COMERCIAL - FEVEREIRO.docx"},
        "Mar": {"valor": 0.1875, "arquivo": "INDC. COMERCIAL - MARÇO.docx"},
    }

    meses_ordem = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]

    valores = []
    arquivos = []

    for mes in meses_ordem:
        if mes in indicador_comercial:
            valores.append(indicador_comercial[mes]["valor"])
            arquivos.append(indicador_comercial[mes]["arquivo"])
        else:
            valores.append(None)
            arquivos.append(None)

    # ========================================================
    # 📊 MÉDIA ACUMULADA (ACM)
    # ========================================================
    valores_validos = [v for v in valores if v is not None]
    media_acm = sum(valores_validos) / len(valores_validos) if valores_validos else None

    df_plot = pd.DataFrame({
        "Mês": meses_ordem,
        "Valor": valores
    })

    df_plot = pd.concat([
        df_plot,
        pd.DataFrame([{"Mês": "ACM", "Valor": media_acm}])
    ], ignore_index=True)

    df_plot["Valor"] = df_plot["Valor"] * 100

    # ========================================================
    # 🏷️ RÓTULOS
    # ========================================================
    def formatar(row):
        if pd.isna(row["Valor"]):
            return ""
        if row["Mês"] == "ACM":
            return f"{row['Valor']:.1f}%"
        return f"{row['Valor']:.0f}%"

    df_plot["Label"] = df_plot.apply(formatar, axis=1)

    # ========================================================
    # 📊 GRÁFICO
    # ========================================================
    fig = px.bar(
        df_plot,
        x="Mês",
        y="Valor",
        text="Label"
    )

    fig.update_traces(textposition="outside")

    fig.add_hline(
        y=META * 100,
        line_dash="dash",
        line_color="red",
        annotation_text="Meta",
        annotation_position="top left"
    )

    max_val = df_plot["Valor"].max()

    fig.update_yaxes(
        tickformat=".0f",
        range=[0, max(max_val * 1.2 if pd.notna(max_val) else 1, META*100*1.2)]
    )

    fig.update_layout(
        title=f"📊 Desempenho Comercial - {ANO}",
        yaxis_title="% Conversão",
        showlegend=False,
        height=500
    )

    st.plotly_chart(fig, use_container_width=True)

    # ========================================================
    # 🎯 SELECT MÊS
    # ========================================================
    meses_com_dado = [m for m in meses_ordem if m in indicador_comercial]

    mes_sel = st.selectbox(
        "Selecionar mês para análise",
        meses_com_dado,
        index=len(meses_com_dado) - 1
    )

    valor = indicador_comercial[mes_sel]["valor"]
    arquivo = indicador_comercial[mes_sel]["arquivo"]

    gap = valor - META

    # ========================================================
    # 📊 KPI
    # ========================================================
    c1, c2, c3 = st.columns(3)

    c1.metric("Resultado", f"{valor*100:.0f}%")
    c2.metric("Meta", f"{META*100:.0f}%")
    c3.metric("Desvio", f"{gap*100:.0f}%", delta_color="inverse")

    if valor >= META:
        st.success("🟢 Dentro da meta")
    else:
        st.error("🔴 Fora da meta")

    # ========================================================
    # 📎 EVIDÊNCIA ISO
    # ========================================================
    caminho_base = "data/Indicadores Comerciais"
    caminho_arquivo = os.path.join(caminho_base, arquivo)

    if os.path.exists(caminho_arquivo):
        with open(caminho_arquivo, "rb") as file:
            st.download_button(
                label="📎 Baixar evidência do mês",
                data=file,
                file_name=arquivo
            )
    else:
        st.warning("Arquivo de evidência não encontrado.")

    # ========================================================
    # 🚨 REGRA ISO (3 MESES FORA DA META)
    # ========================================================
    if len(valores_validos) >= 3:
        ultimos_3 = valores_validos[-3:]

        if all(v < META for v in ultimos_3):
            st.error("🚨 3 meses consecutivos fora da meta — AÇÃO OBRIGATÓRIA")
        else:
            st.success("Indicador sob controle recente")




# ============================================================
# 🧪 QUALIDADE — COMPLETO (ISO + % + R$ + META + ACM)
# ============================================================

with tab2:

    st.header("🧪 Indicadores de Qualidade")

    ANO = "2026"

    meses_ordem = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]

    # ========================================================
    # 🔧 FUNÇÃO PADRÃO (ROBUSTA E SEGURA)
    # ========================================================
    def montar_indicador(titulo, meta, dados, tipo="percentual", menor_melhor=True):

        st.subheader(titulo)

        valores = [dados.get(m, None) for m in meses_ordem]
        valores_validos = [v for v in valores if v is not None]

        media = sum(valores_validos)/len(valores_validos) if valores_validos else None

        df_plot = pd.DataFrame({
            "Mês": meses_ordem,
            "Valor": valores
        })

        df_plot = pd.concat([
            df_plot,
            pd.DataFrame([{"Mês": "ACM", "Valor": media}])
        ], ignore_index=True)

        # ====================================================
        # 📊 TRATAMENTO POR TIPO
        # ====================================================
        if tipo == "percentual":
            df_plot["Valor"] = df_plot["Valor"] * 100
            meta_plot = meta * 100
        else:
            meta_plot = meta

        # ====================================================
        # 📊 ORDENAÇÃO (ACM SEMPRE NO FINAL)
        # ====================================================
        df_meses = df_plot[df_plot["Mês"] != "ACM"].copy()
        df_acm = df_plot[df_plot["Mês"] == "ACM"].copy()

        df_meses["Mês"] = pd.Categorical(
            df_meses["Mês"],
            categories=meses_ordem,
            ordered=True
        )

        df_meses = df_meses.sort_values("Mês")
        df_plot = pd.concat([df_meses, df_acm])

        # ====================================================
        # 🏷️ RÓTULOS
        # ====================================================
        def label(row):
            if pd.isna(row["Valor"]):
                return ""

            if tipo == "percentual":
                return f"{row['Valor']:.1f}%"
            elif tipo == "valor":
                return f"R$ {row['Valor']:.1f}" if row["Mês"] == "ACM" else f"R$ {row['Valor']:.0f}"
            else:
                return f"{row['Valor']:.1f}"

        df_plot["Label"] = df_plot.apply(label, axis=1)

        # ====================================================
        # 📊 GRÁFICO
        # ====================================================
        fig = px.bar(
            df_plot,
            x="Mês",
            y="Valor",
            text="Label"
        )

        fig.update_traces(textposition="outside")

        # 🔥 LINHA DE META
        fig.add_hline(
            y=meta_plot,
            line_dash="dash",
            line_color="red",
            annotation_text="Meta",
            annotation_position="top left"
        )

        # 🔥 ESCALA CORRETA (SEM NEGATIVO)
        max_val = df_plot["Valor"].max()

        fig.update_yaxes(
            range=[0, max(max_val * 1.2 if pd.notna(max_val) else 1, meta_plot * 1.2)],
            tickformat=".1f"
        )

        fig.update_layout(
            title=f"{titulo} - {ANO}",
            showlegend=False,
            height=450
        )

        st.plotly_chart(fig, use_container_width=True)

        # ====================================================
        # 🚨 REGRA ISO (3 MESES FORA DA META)
        # ====================================================
        if len(valores_validos) >= 3:
            ultimos_3 = valores_validos[-3:]

            if menor_melhor:
                fora_meta = all(v > meta for v in ultimos_3)
            else:
                fora_meta = all(v < meta for v in ultimos_3)

            if fora_meta:
                st.error("🚨 3 meses consecutivos fora da meta — AÇÃO OBRIGATÓRIA")
            else:
                st.success("Indicador sob controle recente")

        st.divider()

    # ========================================================
    # 📊 INDICADORES
    # ========================================================

    montar_indicador(
        "🧪 NC Externas (%)",
        0.02,
        {"Jan":0.012,"Fev":0.018,"Mar":0.015},
        tipo="percentual",
        menor_melhor=True
    )

    montar_indicador(
        "💰 Custo Total de NC (R$)",
        15000,
        {"Jan":12000,"Fev":18000,"Mar":14000},
        tipo="valor",
        menor_melhor=True
    )

    montar_indicador(
        "♻️ Refugo (%)",
        0.03,
        {"Jan":0.025,"Fev":0.028,"Mar":0.031},
        tipo="percentual",
        menor_melhor=True
    )

    montar_indicador(
        "🔧 Retrabalho (%)",
        0.05,
        {"Jan":0.04,"Fev":0.045,"Mar":0.052},
        tipo="percentual",
        menor_melhor=True
    )



# ============================================================
# 🏭 PRODUÇÃO — TEMPO REAL (ATRASO DE ENTREGAS)
# ============================================================

with tab3:

    st.header("🏭 Atraso de Entregas (Tempo Real)")
    st.caption("PVs com data de entrega vencida e ainda em aberto")

    # ========================================================
    # 🔒 VALIDAÇÃO DA BASE
    # ========================================================
    if df_aps.empty:
        st.warning("Abra o APS para visualizar os indicadores de produção.")
        st.stop()

    base = df_aps.copy()

    required_cols = ["PV", "DATA_ENTREGA_APS"]

    if not all(col in base.columns for col in required_cols):
        st.error("Colunas obrigatórias não encontradas na base do APS")
        st.write("Colunas disponíveis:", base.columns.tolist())
        st.stop()

    # ========================================================
    # 📅 TRATAMENTO DE DATA
    # ========================================================
    base["DATA_ENTREGA_APS"] = pd.to_datetime(base["DATA_ENTREGA_APS"], errors="coerce")

    hoje = pd.Timestamp.today().normalize()

    # ========================================================
    # 📦 AGRUPAMENTO POR PV
    # ========================================================
    pv = base.groupby("PV", as_index=False).agg(
        data_entrega=("DATA_ENTREGA_APS", "min")
    )

    pv = pv.dropna(subset=["data_entrega"])

    # ========================================================
    # 🚨 REGRA DE ATRASO (TEMPO REAL)
    # ========================================================
    pv["Atraso_dias"] = (hoje - pv["data_entrega"]).dt.days
    pv["Atrasada"] = pv["Atraso_dias"] > 0

    atrasadas = pv[pv["Atrasada"]].copy()

    # ========================================================
    # 📊 KPIs
    # ========================================================
    total = len(pv)
    qtd_atrasadas = len(atrasadas)
    pct = (qtd_atrasadas / total * 100) if total > 0 else 0

    c1, c2, c3 = st.columns(3)

    c1.metric("🚨 Atraso (%)", f"{pct:.1f}%")
    c2.metric("📦 PVs Atrasadas", qtd_atrasadas)
    c3.metric("📦 Total PVs", total)

    st.divider()

    # ========================================================
    # 📊 DISTRIBUIÇÃO POR FAIXAS (CORRETO)
    # ========================================================
    st.subheader("📊 Distribuição do atraso por faixa (dias)")

    if qtd_atrasadas > 0:

        # 🔒 GARANTE INTEIRO
        atrasadas["Atraso_dias"] = atrasadas["Atraso_dias"].astype(int)

        # 🔥 FAIXAS FIXAS (GESTÃO)
        bins = [0, 2, 4, 6, 8, 10, 15, 20, 30, 9999]
        labels = [
            "1-2", "3-4", "5-6", "7-8", "9-10",
            "11-15", "16-20", "21-30", "30+"
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
            .reindex(labels, fill_value=0)
            .reset_index(name="Quantidade")
        )

        # ====================================================
        # 🎨 GRÁFICO EM COLUNAS COM GRADIENTE
        # ====================================================
        fig = px.bar(
            resumo,
            x="Faixa",
            y="Quantidade",
            color="Quantidade",
            color_continuous_scale="Reds",
            text="Quantidade"
        )

        fig.update_traces(textposition="outside")

        fig.update_layout(
            title="Distribuição de Atraso por Faixa",
            xaxis_title="Faixa de atraso (dias)",
            yaxis_title="Quantidade de PVs",
            coloraxis_showscale=False,
            height=500
        )

        st.plotly_chart(fig, use_container_width=True)

    else:
        st.success("Nenhuma PV em atraso no momento")