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
# 🧪 QUALIDADE — PAINEL COMPLETO FINAL (TODOS INDICADORES)
# ============================================================

with tab2:

    import pandas as pd
    import streamlit as st
    import plotly.express as px

    st.header("🧪 Indicadores de Qualidade")

    ANO = "2026"
    meses_ordem = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]

    # ============================================================
    # 🔧 FUNÇÃO PADRÃO GLOBAL
    # ============================================================

    def montar_indicador(titulo, meta, dados, tipo="percentual", menor_melhor=True):

        st.subheader(titulo)

        if tipo == "percentual":
            st.caption(f"Meta: ≤ {meta*100:.0f}%")
        elif tipo == "valor":
            st.caption(f"Meta: ≤ R$ {meta:,.0f}")
        else:
            st.caption(f"Meta: ≤ {meta}")

        valores = [dados.get(m, None) for m in meses_ordem]
        valores_validos = [v for v in valores if v is not None]

        media = sum(valores_validos)/len(valores_validos) if valores_validos else None

        df = pd.DataFrame({"Mês": meses_ordem, "Valor": valores})
        df = pd.concat([df, pd.DataFrame([{"Mês": "ACM", "Valor": media}])], ignore_index=True)

        df_plot = df.copy()

        if tipo == "percentual":
            df_plot["Valor"] = df_plot["Valor"] * 100

        df_meses = df_plot[df_plot["Mês"] != "ACM"].copy()
        df_acm = df_plot[df_plot["Mês"] == "ACM"].copy()

        df_meses["Mês"] = pd.Categorical(df_meses["Mês"], categories=meses_ordem, ordered=True)
        df_meses = df_meses.sort_values("Mês")

        df_plot = pd.concat([df_meses, df_acm])

        def label(row):
            if pd.isna(row["Valor"]):
                return ""
            if row["Mês"] == "ACM":
                if tipo == "percentual":
                    return f"{row['Valor']:.1f}%"
                elif tipo == "valor":
                    return f"R$ {row['Valor']:.1f}"
                else:
                    return f"{row['Valor']:.1f}"
            else:
                if tipo == "percentual":
                    return f"{row['Valor']:.0f}%"
                elif tipo == "valor":
                    return f"R$ {row['Valor']:.0f}"
                else:
                    return f"{row['Valor']:.0f}"

        df_plot["Label"] = df_plot.apply(label, axis=1)

        fig = px.bar(df_plot, x="Mês", y="Valor", text="Label")

        fig.update_traces(textposition="outside")

        max_val = df_plot["Valor"].max()

        fig.update_yaxes(
            tickformat=".0f",
            range=[0, max_val * 1.2 if max_val else 1]
        )

        fig.update_layout(
            title=f"{titulo} - {ANO}",
            showlegend=False,
            height=450
        )

        st.plotly_chart(fig, use_container_width=True)

        # KPI
        if valores_validos:
            ultimo = valores_validos[-1]
            gap = ultimo - meta

            c1, c2, c3 = st.columns(3)

            if tipo == "percentual":
                c1.metric("Resultado", f"{ultimo*100:.0f}%")
                c2.metric("Meta", f"{meta*100:.0f}%")
                c3.metric("Desvio", f"{gap*100:.0f}%", delta_color="inverse")
            elif tipo == "valor":
                c1.metric("Resultado", f"R$ {ultimo:,.0f}")
                c2.metric("Meta", f"R$ {meta:,.0f}")
                c3.metric("Desvio", f"R$ {gap:,.0f}", delta_color="inverse")
            else:
                c1.metric("Resultado", f"{ultimo:.0f}")
                c2.metric("Meta", f"{meta:.0f}")
                c3.metric("Desvio", f"{gap:.0f}", delta_color="inverse")

            if menor_melhor:
                status = ultimo <= meta
            else:
                status = ultimo >= meta

            if status:
                st.success("🟢 Dentro da meta")
            else:
                st.error("🔴 Fora da meta")

        # REGRA ISO
        if len(valores_validos) >= 3:
            ultimos_3 = valores_validos[-3:]

            if menor_melhor:
                cond = all(v > meta for v in ultimos_3)
            else:
                cond = all(v < meta for v in ultimos_3)

            if cond:
                st.error("🚨 3 meses consecutivos fora da meta — AÇÃO OBRIGATÓRIA")
            else:
                st.success("Indicador sob controle recente")

        st.divider()

    # ============================================================
    # 📊 TODOS OS INDICADORES
    # ============================================================

    montar_indicador("🧪 NC Externas (%)", 0.02,
                     {"Jan": 0.012, "Fev": 0.018, "Mar": 0.015})

    montar_indicador("💰 Custo Total de NC (R$)", 15000,
                     {"Jan": 12000, "Fev": 18000, "Mar": 14000},
                     tipo="valor")

    montar_indicador("♻️ Refugo (%)", 0.03,
                     {"Jan": 0.025, "Fev": 0.028, "Mar": 0.031})

    montar_indicador("🔧 Retrabalho (%)", 0.05,
                     {"Jan": 0.04, "Fev": 0.045, "Mar": 0.052})

    montar_indicador("📦 NC Internas (nº)", 50,
                     {"Jan": 40, "Fev": 55, "Mar": 48},
                     tipo="numero")

    montar_indicador("🚨 NC Externas (nº peças)", 20,
                     {"Jan": 12, "Fev": 18, "Mar": 22},
                     tipo="numero")

    montar_indicador("💸 Refugo (R$)", 8000,
                     {"Jan": 6000, "Fev": 7500, "Mar": 8200},
                     tipo="valor")

    montar_indicador("🔧 Retrabalho (R$)", 10000,
                     {"Jan": 9000, "Fev": 11000, "Mar": 9500},
                     tipo="valor")



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