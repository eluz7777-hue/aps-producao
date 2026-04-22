import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Indicadores da Fábrica", layout="wide")

st.title("📊 Indicadores da Fábrica")
st.caption("Painel estratégico alinhado à ISO 9001")

# ============================================================
# 🔒 BASE APS (APENAS PARA INDICADORES) — CORRETO
# ============================================================

df = st.session_state.get("df", pd.DataFrame())

if df is None or not isinstance(df, pd.DataFrame):
    df = pd.DataFrame()

df_base = df.copy()

# ============================================================
# 🚦 VISÃO GERAL
# ============================================================
st.subheader("🚦 Saúde da Fábrica")

pct_atraso = 0

if not df.empty:
    try:
        col_pv = [c for c in df.columns if "pv" in c.lower()][0]
        col_dias = [c for c in df.columns if "dias" in c.lower() or "atraso" in c.lower()][0]

        total = df[col_pv].nunique()
        atrasos = pd.to_numeric(df[col_dias], errors="coerce") < 0

        pct_atraso = (atrasos.sum() / total * 100) if total > 0 else 0
    except:
        pct_atraso = 0

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

if df.empty:
    st.info("Abra o APS para habilitar indicadores de produção.")

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
# 💰 COMERCIAL
# ============================================================

with tab1:

    st.subheader("💰 Indicador Comercial (Orçamentos → Pedidos)")
    META = 0.25

    meses = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]

    dados = {"Jan":0.1463,"Fev":0.1282,"Mar":0.1875}

    vals = [dados.get(m,None) for m in meses]
    validos = [v for v in vals if v is not None]
    media = sum(validos)/len(validos) if validos else None

    df_plot = pd.DataFrame({"Mês":meses,"Valor":vals})
    df_plot = pd.concat([df_plot, pd.DataFrame([{"Mês":"ACM","Valor":media}])])

    df_plot["Valor"] *= 100
    df_plot["Label"] = df_plot["Valor"].apply(lambda x: "" if pd.isna(x) else f"{x:.1f}%")

    fig = px.bar(df_plot, x="Mês", y="Valor", text="Label")
    fig.add_hline(y=META*100, line_dash="dash", line_color="red")
    fig.update_traces(textposition="outside")

    st.plotly_chart(fig, use_container_width=True)

# ============================================================
# 🧪 QUALIDADE
# ============================================================

with tab2:

    st.header("🧪 Indicadores de Qualidade")

    def indicador(nome, meta, dados):

        meses = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]

        vals = [dados.get(m,None) for m in meses]
        validos = [v for v in vals if v is not None]
        media = sum(validos)/len(validos) if validos else None

        df_plot = pd.DataFrame({"Mês":meses,"Valor":vals})
        df_plot = pd.concat([df_plot, pd.DataFrame([{"Mês":"ACM","Valor":media}])])

        df_plot["Valor"] *= 100
        df_plot["Label"] = df_plot["Valor"].apply(lambda x: "" if pd.isna(x) else f"{x:.1f}%")

        fig = px.bar(df_plot, x="Mês", y="Valor", text="Label")
        fig.add_hline(y=meta*100, line_dash="dash", line_color="red")
        fig.update_traces(textposition="outside")

        st.subheader(nome)
        st.plotly_chart(fig, use_container_width=True)
        st.divider()

    indicador("NC Externas (%)",0.02,{"Jan":0.012,"Fev":0.018,"Mar":0.015})
    indicador("Refugo (%)",0.03,{"Jan":0.025,"Fev":0.028,"Mar":0.031})
    indicador("Retrabalho (%)",0.05,{"Jan":0.04,"Fev":0.045,"Mar":0.052})

# ============================================================
# 🏭 PRODUÇÃO (ROBUSTO FINAL)
# ============================================================

with tab3:

    st.header("🏭 Indicadores de Produção")

    if df.empty:
        st.warning("Abra o APS primeiro.")
        st.stop()

    base = df.copy()
    base.columns = base.columns.str.strip()

    try:
        col_pv = [c for c in base.columns if "pv" in c.lower()][0]
        col_entrega = [c for c in base.columns if "entrega" in c.lower()][0]
        col_dias = [c for c in base.columns if "dias" in c.lower() or "atraso" in c.lower()][0]
    except:
        st.error("Colunas não identificadas.")
        st.write(base.columns)
        st.stop()

    base[col_dias] = pd.to_numeric(base[col_dias], errors="coerce")
    base[col_entrega] = pd.to_datetime(base[col_entrega], errors="coerce")

    base = base.dropna(subset=[col_entrega])

    pv_base = base.groupby(col_pv, as_index=False).agg(
        ENTREGA=(col_entrega,"max"),
        DIAS=(col_dias,"min")
    )

    pv_base["Atrasado"] = pv_base["DIAS"] < 0
    pv_base["Mes"] = pv_base["ENTREGA"].dt.month

    mapa = {1:"Jan",2:"Fev",3:"Mar",4:"Abr",5:"Mai",6:"Jun",
            7:"Jul",8:"Ago",9:"Set",10:"Out",11:"Nov",12:"Dez"}

    pv_base["Mes"] = pv_base["Mes"].map(mapa)

    resumo = pv_base.groupby("Mes").agg(
        Total=("Mes","count"),
        Atrasados=("Atrasado","sum")
    ).reset_index()

    resumo["Atraso_%"] = (resumo["Atrasados"]/resumo["Total"])*100
    resumo["Label"] = resumo["Atraso_%"].apply(lambda x: f"{x:.1f}%")

    fig = px.bar(resumo, x="Mes", y="Atraso_%", text="Label")
    fig.add_hline(y=5, line_dash="dash", line_color="red")
    fig.update_traces(textposition="outside")

    st.plotly_chart(fig, use_container_width=True)



# ============================================================
# 💰 COMERCIAL
# ============================================================

with tab1:

    st.subheader("💰 Indicador Comercial (Orçamentos → Pedidos)")
    st.caption("Meta: ≥ 25%")

    ANO = "2026"
    META = 0.25

    meses_ordem = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]

    indicador = {
        "Jan": 0.1463,
        "Fev": 0.1282,
        "Mar": 0.1875,
    }

    valores = [indicador.get(m, None) for m in meses_ordem]
    valores_validos = [v for v in valores if v is not None]

    media = sum(valores_validos)/len(valores_validos) if valores_validos else None

    df_plot = pd.DataFrame({"Mês": meses_ordem, "Valor": valores})
    df_plot = pd.concat([df_plot, pd.DataFrame([{"Mês":"ACM","Valor":media}])])

    df_plot["Valor"] = df_plot["Valor"] * 100

    def label(row):
        if pd.isna(row["Valor"]):
            return ""
        return f"{row['Valor']:.1f}%" if row["Mês"]=="ACM" else f"{row['Valor']:.0f}%"

    df_plot["Label"] = df_plot.apply(label, axis=1)

    fig = px.bar(df_plot, x="Mês", y="Valor", text="Label")

    fig.add_hline(
        y=META*100,
        line_dash="dash",
        line_color="red",
        annotation_text="Meta"
    )

    max_val = df_plot["Valor"].max()

    fig.update_yaxes(range=[0, max(max_val*1.2, META*100*1.2)], tickformat=".0f")

    fig.update_traces(textposition="outside")

    st.plotly_chart(fig, use_container_width=True)

# ============================================================
# 🧪 QUALIDADE
# ============================================================

with tab2:

    st.header("🧪 Indicadores de Qualidade")

    meses_ordem = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]

    def indicador_padrao(titulo, meta, dados, percentual=True):

        st.subheader(titulo)

        valores = [dados.get(m, None) for m in meses_ordem]
        valores_validos = [v for v in valores if v is not None]

        media = sum(valores_validos)/len(valores_validos) if valores_validos else None

        df_plot = pd.DataFrame({"Mês": meses_ordem, "Valor": valores})
        df_plot = pd.concat([df_plot, pd.DataFrame([{"Mês":"ACM","Valor":media}])])

        if percentual:
            df_plot["Valor"] = df_plot["Valor"] * 100
            meta_plot = meta * 100
        else:
            meta_plot = meta

        def label(row):
            if pd.isna(row["Valor"]):
                return ""
            return f"{row['Valor']:.1f}%"

        df_plot["Label"] = df_plot.apply(label, axis=1)

        fig = px.bar(df_plot, x="Mês", y="Valor", text="Label")

        fig.add_hline(
            y=meta_plot,
            line_dash="dash",
            line_color="red",
            annotation_text="Meta"
        )

        max_val = df_plot["Valor"].max()

        fig.update_yaxes(range=[0, max(max_val*1.2, meta_plot*1.2)], tickformat=".1f")

        fig.update_traces(textposition="outside")

        st.plotly_chart(fig, use_container_width=True)

        st.divider()

    indicador_padrao("🧪 NC Externas (%)", 0.02,
                    {"Jan":0.012,"Fev":0.018,"Mar":0.015})

    indicador_padrao("♻️ Refugo (%)", 0.03,
                    {"Jan":0.025,"Fev":0.028,"Mar":0.031})

    indicador_padrao("🔧 Retrabalho (%)", 0.05,
                    {"Jan":0.04,"Fev":0.045,"Mar":0.052})




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

    media_acm = sum(valores_validos) / len(valores_validos) if valores_validos else None

    # ========================================================
    # 📊 DATAFRAME BASE
    # ========================================================
    df = pd.DataFrame({
        "Mês": meses_ordem,
        "Valor": valores
    })

    df = pd.concat([
        df,
        pd.DataFrame([{"Mês": "ACM", "Valor": media_acm}])
    ], ignore_index=True)

    # ========================================================
    # 📊 PREPARAÇÃO PARA GRÁFICO
    # ========================================================
    df_plot = df.copy()
    df_plot["Valor"] = df_plot["Valor"] * 100

    df_meses = df_plot[df_plot["Mês"] != "ACM"].copy()
    df_acm = df_plot[df_plot["Mês"] == "ACM"].copy()

    df_meses["Mês"] = pd.Categorical(df_meses["Mês"], categories=meses_ordem, ordered=True)
    df_meses = df_meses.sort_values("Mês")

    df_plot = pd.concat([df_meses, df_acm])

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

    # 🔥 LINHA DE META
    fig.add_hline(
        y=META * 100,
        line_dash="dash",
        line_color="red",
        annotation_text="Meta",
        annotation_position="top left"
    )

    # 🔥 ESCALA CORRIGIDA (SEM NEGATIVO)
    max_val = df_plot["Valor"].max()

    fig.update_yaxes(
        tickformat=".0f",
        range=[0, max(max_val * 1.2 if pd.notna(max_val) else 1, META*100*1.2)]
    )

    fig.update_layout(
        title=f"📊 Desempenho Comercial - {ANO}",
        yaxis_title="% Conversão",
        xaxis_title="",
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
# 🧪 QUALIDADE — PAINEL COMPLETO COM LINHA DE META
# ============================================================

with tab2:

    import pandas as pd
    import plotly.express as px
    import streamlit as st

    st.header("🧪 Indicadores de Qualidade")

    ANO = "2026"
    meses_ordem = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]

    # ============================================================
    # 🔧 FUNÇÃO PADRÃO COM LINHA DE META
    # ============================================================

    def montar_indicador(titulo, meta, dados, tipo="percentual", menor_melhor=True):

        st.subheader(titulo)

        valores = [dados.get(m, None) for m in meses_ordem]
        valores_validos = [v for v in valores if v is not None]

        media = sum(valores_validos)/len(valores_validos) if valores_validos else None

        df = pd.DataFrame({"Mês": meses_ordem, "Valor": valores})
        df = pd.concat([df, pd.DataFrame([{"Mês": "ACM", "Valor": media}])])

        df_plot = df.copy()

        if tipo == "percentual":
            df_plot["Valor"] = df_plot["Valor"] * 100
            meta_plot = meta * 100
        else:
            meta_plot = meta

        df_meses = df_plot[df_plot["Mês"] != "ACM"].copy()
        df_acm = df_plot[df_plot["Mês"] == "ACM"].copy()

        df_meses["Mês"] = pd.Categorical(df_meses["Mês"], categories=meses_ordem, ordered=True)
        df_meses = df_meses.sort_values("Mês")

        df_plot = pd.concat([df_meses, df_acm])

        def label(row):
            if pd.isna(row["Valor"]):
                return ""
            if tipo == "percentual":
                return f"{row['Valor']:.1f}%" if row["Mês"] == "ACM" else f"{row['Valor']:.0f}%"
            elif tipo == "valor":
                return f"R$ {row['Valor']:.1f}" if row["Mês"] == "ACM" else f"R$ {row['Valor']:.0f}"
            else:
                return f"{row['Valor']:.0f}"

        df_plot["Label"] = df_plot.apply(label, axis=1)

        fig = px.bar(df_plot, x="Mês", y="Valor", text="Label")

        # 🔥 LINHA DE META
        fig.add_hline(
            y=meta_plot,
            line_dash="dash",
            line_color="red",
            annotation_text="Meta",
            annotation_position="top left"
        )

        max_val = df_plot["Valor"].max()

        fig.update_yaxes(
            tickformat=".0f",
            range=[0, max(max_val * 1.2, meta_plot * 1.2)]
        )

        fig.update_traces(textposition="outside")

        fig.update_layout(
            title=f"{titulo} - {ANO}",
            showlegend=False,
            height=450
        )

        st.plotly_chart(fig, use_container_width=True)

        st.divider()

    # ============================================================
    # 📊 INDICADORES
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




# ============================================================
# 🏭 PRODUÇÃO — DEFINITIVO E ROBUSTO (SEM ERRO)
# ============================================================

with tab3:

    st.subheader("🏭 Produção (Indicadores Estratégicos)")

    base = df.copy()

    # ========================================================
    # 🔒 VALIDAÇÃO REAL
    # ========================================================
    required_cols = ["PV", "Data", "DATA_ENTREGA_APS"]

    missing = [c for c in required_cols if c not in base.columns]

    if missing:
        st.error(f"Colunas faltando: {missing}")
        st.write("Colunas atuais:", list(base.columns))
        st.stop()

    # ========================================================
    # 🔧 LIMPEZA DE DADOS
    # ========================================================
    base["Data"] = pd.to_datetime(base["Data"], errors="coerce")
    base["DATA_ENTREGA_APS"] = pd.to_datetime(base["DATA_ENTREGA_APS"], errors="coerce")

    # remove linhas inválidas
    base = base.dropna(subset=["Data", "DATA_ENTREGA_APS"])

    if base.empty:
        st.warning("Sem dados válidos após tratamento.")
        st.stop()

    # ========================================================
    # 📦 CONSOLIDAÇÃO POR PV
    # ========================================================
    pv = base.groupby("PV", as_index=False).agg(
        Data_real=("Data", "max"),
        Data_planejada=("DATA_ENTREGA_APS", "min")
    )

    # ========================================================
    # ⏱️ CÁLCULO DE ATRASO
    # ========================================================
    pv["Atraso_dias"] = (pv["Data_real"] - pv["Data_planejada"]).dt.days

    pv["Atraso_dias"] = pv["Atraso_dias"].fillna(0)

    # ========================================================
    # 📊 KPIs
    # ========================================================
    total = len(pv)
    atrasadas = pv[pv["Atraso_dias"] > 0]

    pct = (len(atrasadas) / total * 100) if total > 0 else 0

    c1, c2, c3 = st.columns(3)

    c1.metric("🚨 Atraso (%)", f"{pct:.1f}%")
    c2.metric("📦 PVs Atrasadas", len(atrasadas))
    c3.metric("📦 Total PVs", total)

    st.divider()

    # ========================================================
    # 📅 AGRUPAMENTO POR MÊS
    # ========================================================
    pv["Mes"] = pv["Data_planejada"].dt.month

    resumo = pv.groupby("Mes").agg(
        Total=("PV", "count"),
        Atrasadas=("Atraso_dias", lambda x: (x > 0).sum())
    ).reset_index()

    resumo["Pct"] = (resumo["Atrasadas"] / resumo["Total"] * 100).round(1)

    # garante meses 1–12
    meses = pd.DataFrame({"Mes": list(range(1, 13))})
    resumo = meses.merge(resumo, on="Mes", how="left")

    resumo["Pct"] = resumo["Pct"].fillna(0)

    nomes = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]
    resumo["Mes_nome"] = resumo["Mes"].apply(lambda x: nomes[x-1])

    # ========================================================
    # 📊 GRÁFICO
    # ========================================================
    import plotly.graph_objects as go

    META = 5

    fig = go.Figure()

    fig.add_bar(
        x=resumo["Mes_nome"],
        y=resumo["Pct"],
        text=resumo["Pct"].astype(str) + "%",
        textposition="outside"
    )

    fig.add_hline(y=META, line_dash="dash", annotation_text=f"Meta {META}%")

    fig.update_layout(
        title="Atraso por Mês (%)",
        yaxis_title="% Atraso"
    )

    st.plotly_chart(fig, use_container_width=True)

    # ========================================================
    # 🚨 REGRA ISO
    # ========================================================
    ultimos = resumo["Pct"].tail(3)

    if len(ultimos) == 3 and all(v > META for v in ultimos):
        st.error("🚨 3 meses consecutivos acima da meta — ação necessária")


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