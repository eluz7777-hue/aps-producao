import streamlit as st
import pandas as pd

st.set_page_config(page_title="Indicadores da Fábrica", layout="wide")

st.title("📊 Indicadores da Fábrica")
st.caption("Painel estratégico alinhado à ISO 9001")

# ============================================================
# 🔒 BASE APS (APENAS PARA INDICADORES)
# ============================================================

df = st.session_state.get("df", pd.DataFrame())

# ============================================================
# 🚦 VISÃO GERAL (SAÚDE DA FÁBRICA)
# ============================================================

st.subheader("🚦 Saúde da Fábrica")

total_pvs = df["PV"].nunique() if "PV" in df.columns else 0

# 🔴 atraso (único dado vindo do APS)
if "Dias para Entrega" in df.columns:
    atrasos = df[df["Dias para Entrega"] < 0]
    pct_atraso = (len(atrasos) / total_pvs * 100) if total_pvs > 0 else 0
else:
    pct_atraso = 0

# 🟡 classificação simples (ISO mindset)
def classificar(valor):
    if valor > 20:
        return "🔴 Crítico"
    elif valor > 5:
        return "🟡 Atenção"
    else:
        return "🟢 Controlado"

c1, c2 = st.columns(2)

c1.metric("🚨 Atraso (%)", f"{pct_atraso:.1f}%")
c2.metric("Status Produção", classificar(pct_atraso))

st.divider()

# ============================================================
# 📊 ABAS ESTRATÉGICAS
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
# 💰 COMERCIAL (INDICADOR ESTRATÉGICO COMPLETO - PADRÃO FINAL)
# ============================================================

with tab1:

    import os
    import pandas as pd
    import streamlit as st
    import plotly.express as px

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
        # "Abr": {"valor": 0.22, "arquivo": "INDC. COMERCIAL - ABRIL.docx"},
    }

    # ========================================================
    # 📅 ORDEM FIXA DOS MESES
    # ========================================================
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

    if valores_validos:
        media_acm = sum(valores_validos) / len(valores_validos)
    else:
        media_acm = None

    # ========================================================
    # 📊 DATAFRAME BASE
    # ========================================================
    df = pd.DataFrame({
        "Mês": meses_ordem,
        "Valor": valores
    })

    # adiciona ACM
    df = pd.concat([
        df,
        pd.DataFrame([{"Mês": "ACM", "Valor": media_acm}])
    ], ignore_index=True)

    # ========================================================
    # 📊 PREPARAÇÃO PARA GRÁFICO
    # ========================================================
    df_plot = df.copy()
    df_plot["Valor"] = df_plot["Valor"] * 100  # converte para %

    # separar meses e ACM
    df_meses = df_plot[df_plot["Mês"] != "ACM"].copy()
    df_acm = df_plot[df_plot["Mês"] == "ACM"].copy()

    # ordenar meses corretamente
    df_meses["Mês"] = pd.Categorical(df_meses["Mês"], categories=meses_ordem, ordered=True)
    df_meses = df_meses.sort_values("Mês")

    # juntar novamente
    df_plot = pd.concat([df_meses, df_acm])

    # ========================================================
    # 🏷️ RÓTULOS (SEM DECIMAL / ACM COM 1 CASA)
    # ========================================================
    def formatar(row):
        if pd.isna(row["Valor"]):
            return ""
        if row["Mês"] == "ACM":
            return f"{row['Valor']:.1f}%"
        return f"{row['Valor']:.0f}%"

    df_plot["Label"] = df_plot.apply(formatar, axis=1)

    # ========================================================
    # 📊 GRÁFICO DE COLUNAS PROFISSIONAL
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

    fig.update_layout(
        title=f"📊 Desempenho Comercial - {ANO}",
        yaxis_title="% Conversão",
        xaxis_title="",
        showlegend=False,
        height=500
    )

    # eixo Y sem casas decimais
    fig.update_yaxes(tickformat=".0f")

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
# 🧪 QUALIDADE — PAINEL ESTRATÉGICO COMPLETO
# ============================================================

with tab2:

    import pandas as pd
    import streamlit as st
    import plotly.express as px

    st.header("🧪 Indicadores de Qualidade")

    ANO = "2026"

    # ============================================================
    # 🔹 1) NC EXTERNAS (%)
    # ============================================================

    st.subheader("🧪 NC Externas (%)")
    st.caption("Meta: ≤ 2%")

    META_NC_EXT = 0.02

    indicador_nc_externa = {
        "Jan": 0.00,
        "Fev": 0.00,
        "Mar": 0.00,
    }

    meses_ordem = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]

    valores_nc = [indicador_nc_externa.get(m, None) for m in meses_ordem]

    valores_validos_nc = [v for v in valores_nc if v is not None]

    media_nc = sum(valores_validos_nc)/len(valores_validos_nc) if valores_validos_nc else None

    df_nc = pd.DataFrame({"Mês": meses_ordem, "Valor": valores_nc})

    df_nc = pd.concat([
        df_nc,
        pd.DataFrame([{"Mês": "ACM", "Valor": media_nc}])
    ], ignore_index=True)

    df_plot_nc = df_nc.copy()
    df_plot_nc["Valor"] = df_plot_nc["Valor"] * 100

    df_meses_nc = df_plot_nc[df_plot_nc["Mês"] != "ACM"].copy()
    df_acm_nc = df_plot_nc[df_plot_nc["Mês"] == "ACM"].copy()

    df_meses_nc["Mês"] = pd.Categorical(df_meses_nc["Mês"], categories=meses_ordem, ordered=True)
    df_meses_nc = df_meses_nc.sort_values("Mês")

    df_plot_nc = pd.concat([df_meses_nc, df_acm_nc])

    def formatar_nc(row):
        if pd.isna(row["Valor"]):
            return ""
        if row["Mês"] == "ACM":
            return f"{row['Valor']:.1f}%"
        return f"{row['Valor']:.0f}%"

    df_plot_nc["Label"] = df_plot_nc.apply(formatar_nc, axis=1)

    fig_nc = px.bar(df_plot_nc, x="Mês", y="Valor", text="Label")

    fig_nc.update_traces(textposition="outside")

    fig_nc.update_layout(
        title=f"📊 NC Externas (%) - {ANO}",
        yaxis_title="% NC",
        showlegend=False,
        height=450
    )

    fig_nc.update_yaxes(tickformat=".0f")

    st.plotly_chart(fig_nc, use_container_width=True)

    # KPI
    if valores_validos_nc:
        ultimo = valores_validos_nc[-1]
        gap = ultimo - META_NC_EXT

        c1, c2, c3 = st.columns(3)
        c1.metric("Resultado", f"{ultimo*100:.0f}%")
        c2.metric("Meta", f"{META_NC_EXT*100:.0f}%")
        c3.metric("Desvio", f"{gap*100:.0f}%", delta_color="inverse")

        if ultimo <= META_NC_EXT:
            st.success("🟢 Dentro da meta")
        else:
            st.error("🔴 Fora da meta")

    # Regra ISO
    if len(valores_validos_nc) >= 3:
        if all(v > META_NC_EXT for v in valores_validos_nc[-3:]):
            st.error("🚨 3 meses consecutivos fora da meta — AÇÃO OBRIGATÓRIA")
        else:
            st.success("Indicador sob controle recente")

    st.divider()

    # ============================================================
    # 🔹 2) CUSTO TOTAL DE NC (R$)
    # ============================================================

    st.subheader("💰 Custo Total de NC (R$)")
    st.caption("Meta: ≤ R$ 15.000")

    META_CUSTO = 15000

    indicador_custo = {
        "Jan": 0,
        "Fev": 0,
        "Mar": 0,
    }

    valores_custo = [indicador_custo.get(m, None) for m in meses_ordem]

    valores_validos_custo = [v for v in valores_custo if v is not None]

    media_custo = sum(valores_validos_custo)/len(valores_validos_custo) if valores_validos_custo else None

    df_custo = pd.DataFrame({"Mês": meses_ordem, "Valor": valores_custo})

    df_custo = pd.concat([
        df_custo,
        pd.DataFrame([{"Mês": "ACM", "Valor": media_custo}])
    ], ignore_index=True)

    df_plot_custo = df_custo.copy()

    df_meses_custo = df_plot_custo[df_plot_custo["Mês"] != "ACM"].copy()
    df_acm_custo = df_plot_custo[df_plot_custo["Mês"] == "ACM"].copy()

    df_meses_custo["Mês"] = pd.Categorical(df_meses_custo["Mês"], categories=meses_ordem, ordered=True)
    df_meses_custo = df_meses_custo.sort_values("Mês")

    df_plot_custo = pd.concat([df_meses_custo, df_acm_custo])

    def formatar_custo(row):
        if pd.isna(row["Valor"]):
            return ""
        if row["Mês"] == "ACM":
            return f"R$ {row['Valor']:.1f}"
        return f"R$ {row['Valor']:.0f}"

    df_plot_custo["Label"] = df_plot_custo.apply(formatar_custo, axis=1)

    fig_custo = px.bar(df_plot_custo, x="Mês", y="Valor", text="Label")

    fig_custo.update_traces(textposition="outside")

    fig_custo.update_layout(
        title=f"📊 Custo Total de NC - {ANO}",
        yaxis_title="R$",
        showlegend=False,
        height=450
    )

    fig_custo.update_yaxes(tickformat=".0f")

    st.plotly_chart(fig_custo, use_container_width=True)

    # KPI
    if valores_validos_custo:
        ultimo = valores_validos_custo[-1]
        gap = ultimo - META_CUSTO

        c1, c2, c3 = st.columns(3)
        c1.metric("Resultado", f"R$ {ultimo:,.0f}")
        c2.metric("Meta", f"R$ {META_CUSTO:,.0f}")
        c3.metric("Desvio", f"R$ {gap:,.0f}", delta_color="inverse")

        if ultimo <= META_CUSTO:
            st.success("🟢 Dentro da meta")
        else:
            st.error("🔴 Fora da meta")

    # Regra ISO
    if len(valores_validos_custo) >= 3:
        if all(v > META_CUSTO for v in valores_validos_custo[-3:]):
            st.error("🚨 3 meses consecutivos fora da meta — AÇÃO OBRIGATÓRIA")
        else:
            st.success("Indicador sob controle recente")





# ============================================================
# 🏭 PRODUÇÃO (SÓ ATRASO)
# ============================================================

with tab3:
    st.subheader("🏭 Produção (Indicadores Estratégicos)")

    st.metric("Atraso (%)", f"{pct_atraso:.1f}%")

# ============================================================
# 🔧 MANUTENÇÃO
# ============================================================

with tab4:
    st.subheader("🔧 Indicadores de Manutenção")

    st.info("➡️ Aqui entra: custo manutenção, preventiva vs corretiva")

# ============================================================
# 📦 FORNECEDORES
# ============================================================

with tab5:
    st.subheader("📦 Compras / Fornecedores")

    st.info("➡️ Aqui entra: atraso fornecedor, qualidade fornecedor")

# ============================================================
# 👷 RH
# ============================================================

with tab6:
    st.subheader("👷 Indicadores de RH")

    st.info("➡️ Aqui entra: absenteísmo, treinamento, horas extras")