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
# 💰 COMERCIAL (INDICADOR + EVIDÊNCIA ISO)
# ============================================================

with tab1:

    import os
    import pandas as pd
    import streamlit as st

    st.subheader("💰 Indicador Comercial (Orçamentos → Pedidos)")
    st.caption("Meta: ≥ 25%")

    # ========================================================
    # 📊 BASE (CONTROLADA PELO SISTEMA)
    # ========================================================
    indicador_comercial = {
        "Jan/26": {
            "valor": 0.1463,
            "arquivo": "INDC. COMERCIAL - JANEIRO.docx"
        },
        "Fev/26": {
            "valor": 0.1282,
            "arquivo": "INDI. COMERCIAL - FEVEREIRO.docx"
        },
        "Mar/26": {
            "valor": 0.1875,
            "arquivo": "INDC. COMERCIAL - MARÇO.docx"
        },
    }

    META = 0.25

    meses = list(indicador_comercial.keys())

    # ========================================================
    # 🎯 SELECTOR DE MÊS
    # ========================================================
    mes_sel = st.selectbox(
        "Selecionar mês",
        meses,
        index=len(meses) - 1
    )

    dados_mes = indicador_comercial[mes_sel]
    valor = dados_mes["valor"]
    arquivo = dados_mes["arquivo"]

    # ========================================================
    # 📊 KPI + GAP
    # ========================================================
    gap = valor - META

    if valor >= META:
        status = "🟢 Dentro da meta"
    else:
        status = "🔴 Fora da meta"

    c1, c2, c3 = st.columns(3)

    c1.metric("Resultado", f"{valor*100:.2f}%")
    c2.metric("Meta", f"{META*100:.0f}%")
    c3.metric("Desvio", f"{gap*100:.2f}%", delta_color="inverse")

    st.write(f"Status: {status}")

    st.divider()

    # ========================================================
    # 📈 HISTÓRICO
    # ========================================================
    df_hist = pd.DataFrame({
        "Mês": meses,
        "Valor": [v["valor"] for v in indicador_comercial.values()]
    })

    df_hist["Meta"] = META

    st.line_chart(df_hist.set_index("Mês"))

    # ========================================================
    # 📎 EVIDÊNCIA ISO (DOWNLOAD DO .DOCX)
    # ========================================================
    caminho_base = "data/Indicadores Comerciais"
    caminho_arquivo = os.path.join(caminho_base, arquivo)

    if os.path.exists(caminho_arquivo):
        with open(caminho_arquivo, "rb") as file:
            st.download_button(
                label="📎 Baixar evidência do indicador",
                data=file,
                file_name=arquivo
            )
    else:
        st.warning("Arquivo de evidência não encontrado na pasta.")

    # ========================================================
    # 🚨 REGRA ISO (3 MESES FORA DA META)
    # ========================================================
    valores = [v["valor"] for v in indicador_comercial.values()]

    if len(valores) >= 3:
        ultimos_3 = valores[-3:]

        if all(v < META for v in ultimos_3):
            st.error("🚨 3 meses consecutivos fora da meta — AÇÃO OBRIGATÓRIA (abrir plano de ação)")
        else:
            st.success("Indicador sob controle no período recente")



# ============================================================
# 🧪 QUALIDADE
# ============================================================

with tab2:
    st.subheader("🧪 Indicadores de Qualidade")

    st.info("➡️ Aqui entra: NC interna, externa, refugo, retrabalho")

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