import streamlit as st
import pandas as pd
import os
import plotly.express as px

# ============================================================
# BASE APS
# ============================================================

df_raw = st.session_state.get("df", pd.DataFrame())

if df_raw is None or not isinstance(df_raw, pd.DataFrame):
    df_raw = pd.DataFrame()

df_aps = df_raw.copy()

# ============================================================
# FUNÇÃO SEGURA
# ============================================================

def safe_value(v):
    try:
        if v is None or pd.isna(v):
            return None
        return float(v)
    except:
        return None

# ============================================================
# APS - ATRASOS
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
# DADOS (POR ENQUANTO SEM INTEGRAÇÃO COMPLETA)
# ============================================================

rh_abs = None
nc_externas = None
forn_prazo = None

# ============================================================
# PAINEL EXECUTIVO
# ============================================================

st.subheader("🚦 Painel Executivo")
st.caption("Status consolidado dos principais indicadores da fábrica")

def classificar(valor, meta, tipo="max"):

    if valor is None or pd.isna(valor):
        return "⚪ Sem dados"

    if tipo == "max":
        if valor <= meta:
            return "🟢 OK"
        elif valor <= meta * 1.2:
            return "🟡 Atenção"
        else:
            return "🔴 Crítico"
    else:
        if valor >= meta:
            return "🟢 OK"
        elif valor >= meta * 0.8:
            return "🟡 Atenção"
        else:
            return "🔴 Crítico"

dados = [
    ["Produção (Atrasos %)", pct_atraso, 5, "max"],
    ["Qualidade (NC %)", nc_externas, 2, "max"],
    ["Fornecedores (Prazo %)", forn_prazo, 98, "min"],
    ["RH (Absenteísmo %)", rh_abs, 2, "max"],
]

df_exec = pd.DataFrame(dados, columns=["Indicador", "Valor", "Meta", "Tipo"])
df_exec["Valor"] = df_exec["Valor"].apply(safe_value)

# ============================================================
# RENDER
# ============================================================

for _, row in df_exec.iterrows():

    c1, c2, c3 = st.columns([2,1,2])

    c1.write(f"**{row['Indicador']}**")

    if row["Valor"] is None:
        c2.write("-")
    else:
        c2.write(f"{row['Valor']:.2f}")

    c3.write(classificar(row["Valor"], row["Meta"], row["Tipo"]))

st.divider()

# ============================================================
# STATUS GERAL
# ============================================================

criticos = 0
validos = 0

for _, r in df_exec.iterrows():
    if r["Valor"] is not None:
        validos += 1
        if classificar(r["Valor"], r["Meta"], r["Tipo"]) == "🔴 Crítico":
            criticos += 1

if validos == 0:
    st.info("⚪ Sem dados suficientes para análise")
elif criticos == 0:
    st.success("🟢 Operação Controlada")
elif criticos <= 2:
    st.warning("🟡 Atenção em alguns indicadores")
else:
    st.error("🔴 Operação em risco")

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
# 💰 COMERCIAL (PROTEGIDO)
# ============================================================

with tab1:

    st.subheader("💰 Indicador Comercial (Orçamentos → Pedidos)")
    st.caption("Meta: ≥ 25%")

    try:
        caminho = "data/Indicadores_Comerciais/Indicadores_Comerciais_2026.xlsx"

        if os.path.exists(caminho):

            df = pd.read_excel(caminho)

            if not df.empty and len(df.columns) >= 2:

                df.columns = [str(c).strip() for c in df.columns]

                x_col = df.columns[0]
                y_col = df.columns[1]

                df = df.dropna(subset=[y_col])

                if not df.empty:

                    fig = px.bar(
                        df,
                        x=x_col,
                        y=y_col,
                        title="Orçamentos → Pedidos (%)",
                        text_auto=True
                    )

                    st.plotly_chart(fig, use_container_width=True)

                else:
                    st.warning("⚠️ Sem dados válidos")

            else:
                st.warning("⚠️ Planilha inválida")

        else:
            st.warning("⚠️ Arquivo não encontrado")

    except Exception as e:
        st.error(f"Erro no módulo comercial: {e}")



# ============================================================
# ABAS
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





# ============================================================
# 🔧 MANUTENÇÃO — BLOCO FINAL COM ACUMULADOS
# ============================================================

with tab4:

    import os
    import pandas as pd
    import plotly.graph_objects as go

    st.header("🔧 Custo de Manutenção")

    caminho = os.path.abspath("data/Indicadores_manutencao/manutencao.xlsx")

    if not os.path.exists(caminho):
        st.error("Arquivo de manutenção não encontrado")
        st.stop()

    # ========================================================
    # 📊 LEITURA
    # ========================================================
    df = pd.read_excel(caminho, dtype=str)
    df.columns = [str(c).strip() for c in df.columns]

    # ========================================================
    # 🔍 COLUNAS
    # ========================================================
    col_mes   = "Mês"
    col_fat   = "Faturamento Mensal"
    col_np    = "Corretiva não programada"
    col_cp    = "Corretiva programada"
    col_prev  = "Preventiva"
    col_pred  = "Preditiva"
    col_melh  = "Melhoria de Máquinas"

    # ========================================================
    # 🧹 LIMPEZA
    # ========================================================
    def limpar(v):
        if pd.isna(v):
            return 0.0
        v = str(v).strip().replace("R$", "").replace(" ", "")
        if "," in v:
            v = v.replace(".", "").replace(",", ".")
        try:
            return float(v)
        except:
            return 0.0

    for col in [col_fat, col_np, col_cp, col_prev, col_pred, col_melh]:
        df[col] = df[col].apply(limpar)

    # ========================================================
    # 📊 TOTAL E META
    # ========================================================
    df["Total"] = (
        df[col_np] +
        df[col_cp] +
        df[col_prev] +
        df[col_pred] +
        df[col_melh]
    )

    df["Meta"] = df[col_fat] * 0.005

    # ========================================================
    # 📊 ACUMULADOS
    # ========================================================
    df["NP_acum"]   = df[col_np].cumsum()
    df["CP_acum"]   = df[col_cp].cumsum()
    df["Prev_acum"] = df[col_prev].cumsum()
    df["Pred_acum"] = df[col_pred].cumsum()
    df["Melh_acum"] = df[col_melh].cumsum()

    df["Total_acum"] = df["Total"].cumsum()
    df["Meta_acum"]  = df["Meta"].cumsum()

    # ========================================================
    # 🚨 STATUS ISO
    # ========================================================
    df["Status_ISO"] = df["Total"] <= df["Meta"]
    df["Status_ISO_acum"] = df["Total_acum"] <= df["Meta_acum"]

    # ========================================================
    # 📊 ESCALA
    # ========================================================
    max_valor = max(df["Total"].max(), df["Total_acum"].max())
    limite_y = max_valor * 1.25 if max_valor > 0 else 1

    # ========================================================
    # 📊 GRÁFICO
    # ========================================================
    fig = go.Figure()

    def moeda(v):
        return f"R$ {v:,.0f}".replace(",", ".")

    # ===== MENSAIS =====
    fig.add_bar(name="NP", x=df[col_mes], y=df[col_np], text=[moeda(v) for v in df[col_np]], textposition="outside")
    fig.add_bar(name="CP", x=df[col_mes], y=df[col_cp], text=[moeda(v) for v in df[col_cp]], textposition="outside")
    fig.add_bar(name="Prev", x=df[col_mes], y=df[col_prev], text=[moeda(v) for v in df[col_prev]], textposition="outside")
    fig.add_bar(name="Pred", x=df[col_mes], y=df[col_pred], text=[moeda(v) for v in df[col_pred]], textposition="outside")
    fig.add_bar(name="Melh", x=df[col_mes], y=df[col_melh], text=[moeda(v) for v in df[col_melh]], textposition="outside")

    # TOTAL mensal
    cores_total = ["green" if ok else "red" for ok in df["Status_ISO"]]
    fig.add_bar(name="Total", x=df[col_mes], y=df["Total"],
                text=[moeda(v) for v in df["Total"]],
                textposition="outside",
                marker_color=cores_total)

    # ===== ACUMULADOS =====
    fig.add_bar(name="Total Acum", x=df[col_mes], y=df["Total_acum"],
                text=[moeda(v) for v in df["Total_acum"]],
                textposition="outside",
                marker_color="darkgreen")

    # META mensal
    fig.add_scatter(
        name="Meta",
        x=df[col_mes],
        y=df["Meta"],
        mode="lines+markers",
        line=dict(color="red", dash="dash")
    )

    # META acumulada
    fig.add_scatter(
        name="Meta Acum",
        x=df[col_mes],
        y=df["Meta_acum"],
        mode="lines+markers",
        line=dict(color="orange", dash="dot")
    )

    fig.update_layout(
        barmode="group",
        height=600,
        yaxis=dict(range=[0, limite_y]),
        yaxis_title="R$",
        xaxis_title="Mês",
        legend_title="Indicadores"
    )

    st.plotly_chart(fig, use_container_width=True)

    # ========================================================
    # 📊 KPI FINAL
    # ========================================================
    ultimo = df.iloc[-1]

    def formatar(v):
        return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    status = "🟢 OK" if ultimo["Total"] <= ultimo["Meta"] else "🔴 ACIMA"
    status_acum = "🟢 OK" if ultimo["Total_acum"] <= ultimo["Meta_acum"] else "🔴 ACIMA"

    c1, c2, c3 = st.columns(3)

    c1.metric("💸 Custo Mês", formatar(ultimo["Total"]))
    c2.metric("📊 Custo Acumulado", formatar(ultimo["Total_acum"]))
    c3.metric("Status ISO Acumulado", status_acum)



# ============================================================
# 📦 Indicadores de Compras & Fornecedores
# ============================================================

with tab5:

    import os
    import plotly.graph_objects as go

    st.subheader("📦 Indicadores de Compras & Fornecedores")

    meses = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]

    # ========================================================
    # 📊 BASE CONTROLADA
    # ========================================================
    dados = {
        "Jan": {"itens": 69, "prazo": 87, "atraso": 9, "devolucao": 2},
        "Fev": {"itens": 76, "prazo": 100, "atraso": 0, "devolucao": 0},
        "Mar": {"itens": 93, "prazo": 100, "atraso": 0, "devolucao": 0},
    }

    def get_val(mes, chave):
        return dados[mes][chave] if mes in dados else None

    itens = [get_val(m, "itens") for m in meses]
    prazo = [get_val(m, "prazo") for m in meses]
    atraso = [get_val(m, "atraso") for m in meses]
    devolucao = [get_val(m, "devolucao") for m in meses]

    # ========================================================
    # 📊 FUNÇÃO ACM
    # ========================================================
    def media(vals):
        v = [x for x in vals if x is not None]
        return sum(v)/len(v) if v else None

    acm_prazo = media(prazo)
    acm_devolucao = media(devolucao)

    # ========================================================
    # 📊 1 - PRAZO DO PROVEDOR
    # ========================================================
    st.subheader("📊 Índice de Entrega do Provedor no Prazo")

    fig1 = go.Figure()

    fig1.add_bar(
        x=meses,
        y=prazo,
        text=[f"{v}%" if v else "" for v in prazo],
        textposition="outside",
        name="Prazo (%)"
    )

    fig1.add_trace(go.Scatter(
        x=meses,
        y=[90]*len(meses),
        mode="lines",
        name="Meta 90%",
        line=dict(color="red", dash="dash")
    ))

    fig1.update_layout(height=450, yaxis_title="%")

    st.plotly_chart(fig1, use_container_width=True)

    if prazo[2] >= 90:
        st.success("🟢 Fornecedor dentro do prazo")
    else:
        st.error("🔴 Problemas de prazo")

    st.info(f"ACM Prazo: {acm_prazo:.1f}%" if acm_prazo else "Sem dados")

    # ========================================================
    # 📊 2 - DEVOLUÇÕES
    # ========================================================
    st.subheader("📊 Índice de Devoluções ao Provedor Externo")

    fig2 = go.Figure()

    fig2.add_bar(
        x=meses,
        y=devolucao,
        text=[f"{v}%" if v else "" for v in devolucao],
        textposition="outside",
        name="Devolução (%)"
    )

    fig2.add_trace(go.Scatter(
        x=meses,
        y=[2]*len(meses),
        mode="lines",
        name="Meta 2%",
        line=dict(color="red", dash="dash")
    ))

    fig2.update_layout(height=450, yaxis_title="%")

    st.plotly_chart(fig2, use_container_width=True)

    if devolucao[2] <= 2:
        st.success("🟢 Qualidade adequada")
    else:
        st.error("🔴 Problema de qualidade")

    st.info(f"ACM Devolução: {acm_devolucao:.1f}%" if acm_devolucao else "Sem dados")

    # ========================================================
    # 📊 3 - VISÃO COMPLETA
    # ========================================================
    st.subheader("📊 Entregas no Prazo (Visão Completa)")

    fig3 = go.Figure()

    fig3.add_bar(
        name="Itens",
        x=meses,
        y=itens,
        text=[str(v) if v else "" for v in itens],
        textposition="outside"
    )

    fig3.add_bar(
        name="No Prazo (%)",
        x=meses,
        y=prazo,
        text=[f"{v}%" if v else "" for v in prazo],
        textposition="outside"
    )

    fig3.add_bar(
        name="Atraso",
        x=meses,
        y=atraso,
        text=[str(v) if v else "" for v in atraso],
        textposition="outside"
    )

    fig3.add_trace(go.Scatter(
        x=meses,
        y=[98]*len(meses),
        mode="lines",
        name="Meta 98%",
        line=dict(color="red", dash="dash")
    ))

    fig3.update_layout(
        barmode="group",
        height=500
    )

    st.plotly_chart(fig3, use_container_width=True)

    if prazo[2] >= 98:
        st.success("🟢 Performance dentro da meta")
    else:
        st.error("🔴 Performance abaixo da meta")

    # ========================================================
    # 📎 EVIDÊNCIA
    # ========================================================
    caminho = "data/Indicadores_Compras_Fornecedores/COMPRAS_FORNECEDORES.docx"

    if os.path.exists(caminho):
        with open(caminho, "rb") as f:
            st.download_button("📎 Baixar evidência", f, file_name="COMPRAS_FORNECEDORES.docx")




# ============================================================
# 👥 INDICADORES DE RH (PADRÃO ISO COMPLETO)
# ============================================================

with tab6:

    import os
    import pandas as pd
    import plotly.express as px

    st.subheader("👥 Indicadores de RH")

    meses = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]

    # ========================================================
    # BASE CONTROLADA
    # ========================================================
    dados = {
        "Jan": {"abs": 2.19, "trein": 2.62, "faltas": 2.29, "extra": 3.76},
        "Fev": {"abs": 3.16, "trein": 2.78, "faltas": 0.40, "extra": 5.45},
        "Mar": {"abs": 2.85, "trein": 2.77, "faltas": 0.35, "extra": 2.33},
    }

    def get_lista(chave):
        return [dados[m][chave] if m in dados else None for m in meses]

    def media(vals):
        v = [x for x in vals if x is not None]
        return sum(v)/len(v) if v else None

    def ultimo_valido(vals):
        v = [x for x in vals if x is not None]
        return v[-1] if v else None

    # ========================================================
    # FUNÇÃO PADRÃO ISO
    # ========================================================
    def grafico_iso(titulo, descricao, valores, meta, tipo_meta):

        st.subheader(titulo)

        acm = media(valores)

        df = pd.DataFrame({
            "Mês": meses,
            "Valor": valores
        })

        df = pd.concat([
            df,
            pd.DataFrame([{"Mês": "ACM", "Valor": acm}])
        ], ignore_index=True)

        df["Label"] = df["Valor"].apply(lambda x: f"{x:.2f}%" if pd.notna(x) else "")

        fig = px.bar(df, x="Mês", y="Valor", text="Label")

        fig.add_hline(
            y=meta,
            line_dash="dash",
            line_color="red",
            annotation_text=f"Meta {'≤' if tipo_meta=='max' else '≥'} {meta}%"
        )

        max_val = df["Valor"].max()

        fig.update_yaxes(
            range=[0, max(max_val * 1.2 if pd.notna(max_val) else meta*1.2, meta*1.2)]
        )

        fig.update_traces(textposition="outside")
        fig.update_layout(height=450, showlegend=False)

        st.plotly_chart(fig, use_container_width=True)

        # ====================================================
        # ANÁLISE ISO
        # ====================================================
        ultimo = ultimo_valido(valores)

        if ultimo is not None:

            if tipo_meta == "max":
                if ultimo <= meta:
                    st.success("🟢 Indicador sob controle, sem impacto relevante na operação")
                else:
                    st.error("🔴 Indicador fora da meta, com impacto potencial na operação e necessidade de ação corretiva")

            else:
                if ultimo >= meta:
                    st.success("🟢 Indicador adequado para sustentação operacional")
                else:
                    st.error("🔴 Indicador abaixo do esperado, podendo comprometer desempenho e qualidade")

        st.caption(descricao)

        if acm:
            st.info(f"ACM: {acm:.2f}%")

    # ========================================================
    # 1️⃣ ABSENTEÍSMO
    # ========================================================
    grafico_iso(
        "📊 Índice de Absenteísmo (HHT)",
        "Mede a ausência de colaboradores em relação às horas trabalhadas.",
        get_lista("abs"),
        2.0,
        "max"
    )

    # ========================================================
    # 2️⃣ TREINAMENTO
    # ========================================================
    grafico_iso(
        "📊 Índice de Treinamento (HHT)",
        "Mede o volume de treinamento aplicado em relação às horas trabalhadas.",
        get_lista("trein"),
        1.5,
        "min"
    )

    # ========================================================
    # 3️⃣ FALTAS INJUSTIFICADAS
    # ========================================================
    grafico_iso(
        "📊 Índice de Faltas Injustificadas (HHT)",
        "Mede faltas sem justificativa em relação às horas trabalhadas.",
        get_lista("faltas"),
        1.5,
        "max"
    )

    # ========================================================
    # 4️⃣ HORAS EXTRAS
    # ========================================================
    grafico_iso(
        "📊 Índice de Horas Extras (HHT)",
        "Mede o uso de horas extras sobre o total de horas trabalhadas.",
        get_lista("extra"),
        10.0,
        "max"
    )

    # ========================================================
    # 📎 EVIDÊNCIA
    # ========================================================
    caminho = "data/Indicadores_RH/RH_MARÇO.docx"

    if os.path.exists(caminho):
        with open(caminho, "rb") as f:
            st.download_button("📎 Baixar evidência", f, file_name="RH_MARÇO.docx")