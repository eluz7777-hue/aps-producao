import streamlit as st

# ===============================
# 🔐 BLOQUEIO DE ACESSO GLOBAL
# ===============================
if "logado" not in st.session_state or not st.session_state.logado:
    st.warning("🔒 Acesso não autorizado. Redirecionando para login...")
    st.switch_page("app.py")

import streamlit as st
import pandas as pd
import plotly.express as px
import os
import time
import holidays
import math

st.set_page_config(layout="wide")

# ===============================
# LOGO + TÍTULO
# ===============================
col1, col2 = st.columns([1, 6])

with col1:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=80)

with col2:
    st.title("📊 ELOHIM APS – Advanced Planning System")

# ===============================
# CONFIG
# ===============================
EFICIENCIA = 0.8
HORAS_DIA = 44 / 5  # 8.8 horas por dia útil
MAQUINAS = {
    "CORTE - SERRA": 2,          # Serra Fita + Serra Circular
    "CORTE-PLASMA": 1,
    "CORTE-LASER": 1,
    "CORTE-GUILHOTINA": 0,
    "TORNO CONVENCIONAL": 2,
    "TORNO CNC": 0,
    "CENTRO DE USINAGEM": 1,
    "FRESADORAS": 2,
    "PRENSA (AMASSAMENTO)": 1,
    "CALANDRA": 1,
    "DOBRADEIRA": 2,
    "ROSQUEADEIRA": 1,
    "METALEIRA": 1,
    "FURADEIRA DE BANCADA": 1,
    "SOLDAGEM": 4,
    "ACABAMENTO": 4,
    "JATEAMENTO": 1,
    "PINTURA": 1,
    "MONTAGEM": 1,
    "DIVERSOS": 1
}

# ===============================
# FERIADOS
# ===============================
br_holidays = holidays.Brazil()

def dias_uteis_periodo(inicio, fim):
    if pd.isna(inicio) or pd.isna(fim):
        return 0
    dias = pd.date_range(inicio, fim, freq="D")
    return sum(1 for d in dias if d.weekday() < 5 and d.date() not in br_holidays)

def dias_uteis_mes(ano, mes):
    inicio = pd.Timestamp(year=int(ano), month=int(mes), day=1)
    fim = inicio + pd.offsets.MonthEnd(1)
    return dias_uteis_periodo(inicio, fim)

def horas_uteis_mes(ano, mes):
    inicio = pd.Timestamp(year=int(ano), month=int(mes), day=1)
    fim = inicio + pd.offsets.MonthEnd(1)

    dias = pd.date_range(inicio, fim, freq="D")

    total_horas = 0

    for d in dias:
        if d.weekday() < 5 and d.date() not in br_holidays:
            if d.weekday() == 4:  # sexta
                total_horas += 8
            else:  # segunda a quinta
                total_horas += 9

    return total_horas

# ===============================
# CACHE DE LEITURA
# ===============================
@st.cache_data
def carregar_dados(base_path):
    df = pd.read_excel(os.path.join(base_path, "PV.xlsx"))
    return df

# ===============================
# ATUALIZAÇÃO
# ===============================
if st.button("🔄 Atualizar Dados"):
    st.cache_data.clear()
    st.rerun()

st.write("Última atualização:", time.strftime("%d/%m/%Y %H:%M:%S"))

# ===============================
# LEITURA
# ===============================
BASE_PATH = os.getcwd()

df_pv = carregar_dados(BASE_PATH)

# Normaliza cabeçalhos
df_pv.columns = [c.strip().upper() for c in df_pv.columns]

# Padroniza nomes da planilha única
df_pv = df_pv.rename(columns={
    "CÓDIGO": "CODIGO_PV",
    "CODIGO": "CODIGO_PV",
    "DATA DE ENTREGA": "ENTREGA",
    "QUANTIDADE": "QTD",
    "QTD": "QTD",
    "QTDE": "QTD",
    "QTD.": "QTD"
})

# ===============================
# VALIDAÇÃO DE COLUNAS OBRIGATÓRIAS
# ===============================
colunas_obrigatorias = ["PV", "CLIENTE", "CODIGO_PV", "ENTREGA", "QTD"]
faltantes = [c for c in colunas_obrigatorias if c not in df_pv.columns]

if faltantes:
    st.error(f"A planilha PV.xlsx está faltando as colunas obrigatórias: {', '.join(faltantes)}")
    st.stop()

def normalizar_codigo(x):
    if pd.isna(x):
        return ""
    x = str(x)
    x = x.replace("\xa0", "")
    x = x.replace(" ", "")
    x = x.replace(".0", "")
    x = x.strip()
    return x

# ===============================
# NORMALIZAÇÃO SEGURA
# ===============================
df_pv["CODIGO_PV"] = df_pv["CODIGO_PV"].apply(normalizar_codigo)

# Chave única
df_pv["CODIGO_KEY"] = df_pv["CODIGO_PV"].astype(str).str.strip()

# Campos principais
df_pv["CLIENTE"] = df_pv["CLIENTE"].fillna("SEM CLIENTE")
df_pv["PV"] = df_pv["PV"].astype(str).str.strip()

# 🔥 CORREÇÃO CRÍTICA: leitura correta de data brasileira
df_pv["ENTREGA"] = pd.to_datetime(df_pv["ENTREGA"], errors="coerce", dayfirst=True)

# Quantidade e tempos aceitam decimal
df_pv["QTD"] = pd.to_numeric(df_pv["QTD"], errors="coerce").fillna(0)

# Remove duplicidades exatas
df_pv = df_pv.drop_duplicates().copy()

# Remove apenas linhas sem código
df_pv = df_pv[df_pv["CODIGO_KEY"] != ""].copy()

# ===============================
# PROCESSOS
# ===============================
PROCESSOS_VALIDOS = [
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

processos = [p for p in PROCESSOS_VALIDOS if p in df_pv.columns]

# Converte todos os tempos para número (aceita decimal)
for proc in processos:
    df_pv[proc] = (
        df_pv[proc]
        .astype(str)
        .str.replace(",", ".", regex=False)
        .str.strip()
    )
    df_pv[proc] = pd.to_numeric(df_pv[proc], errors="coerce").fillna(0)


# ===============================
# EXPANSÃO CORRIGIDA (SEM ERRO)
# ===============================
pvs_totais_excel = df_pv["PV"].astype(str).str.strip().nunique()
pvs_excel_set = set(df_pv["PV"].astype(str).str.strip().unique())

linhas = []
pvs_excluidas = []
pvs_sem_carga = []
auditoria_pv = []

for _, row in df_pv.iterrows():

    pv_atual = str(row["PV"]).strip()
    cliente_atual = row.get("CLIENTE", "SEM CLIENTE")
    codigo_atual = row["CODIGO_PV"]

    # Validação de dados básicos
    if pd.isna(row["ENTREGA"]):
        registro = {
            "PV": pv_atual,
            "Cliente": cliente_atual,
            "CODIGO": codigo_atual,
            "Motivo": "Data de entrega inválida"
        }
        pvs_sem_carga.append(registro)
        pvs_excluidas.append(registro)

        linhas.append({
            "PV": pv_atual,
            "Cliente": cliente_atual,
            "Processo": "SEM DATA",
            "Data": pd.NaT,
            "Horas": 0
        })

        auditoria_pv.append({
            "PV": pv_atual,
            "Cliente": cliente_atual,
            "CODIGO": codigo_atual,
            "Status": "Sem data válida",
            "Qtd": row["QTD"],
            "Total Processos Válidos": 0,
            "Horas Totais": 0
        })
        continue

    if float(row["QTD"]) <= 0:
        registro = {
            "PV": pv_atual,
            "Cliente": cliente_atual,
            "CODIGO": codigo_atual,
            "Motivo": "Quantidade zero ou inválida"
        }
        pvs_sem_carga.append(registro)
        pvs_excluidas.append(registro)

        linhas.append({
            "PV": pv_atual,
            "Cliente": cliente_atual,
            "Processo": "SEM QTD",
            "Data": row["ENTREGA"],
            "Horas": 0
        })

        auditoria_pv.append({
            "PV": pv_atual,
            "Cliente": cliente_atual,
            "CODIGO": codigo_atual,
            "Status": "Quantidade inválida",
            "Qtd": row["QTD"],
            "Total Processos Válidos": 0,
            "Horas Totais": 0
        })
        continue

    roteiro = row
    teve_processo_valido = False
    qtde_processos_validos = 0
    horas_totais_pv = 0

    for proc in processos:
        tempo = pd.to_numeric(roteiro.get(proc), errors="coerce")

        if pd.notna(tempo) and tempo > 0 and tempo <= 2500:
            teve_processo_valido = True
            qtde_processos_validos += 1

            horas = (tempo * float(row["QTD"])) / 60
            horas_totais_pv += horas

            linhas.append({
                "PV": pv_atual,
                "Cliente": cliente_atual,
                "Processo": proc,
                "Data": row["ENTREGA"],
                "Horas": horas
            })

    if not teve_processo_valido:
        registro = {
            "PV": pv_atual,
            "Cliente": cliente_atual,
            "CODIGO": codigo_atual,
            "Motivo": "Sem processo válido com tempo > 0"
        }

        pvs_excluidas.append(registro)
        pvs_sem_carga.append(registro)

        linhas.append({
            "PV": pv_atual,
            "Cliente": cliente_atual,
            "Processo": "SEM PROCESSO",
            "Data": row["ENTREGA"],
            "Horas": 0
        })

        auditoria_pv.append({
            "PV": pv_atual,
            "Cliente": cliente_atual,
            "CODIGO": codigo_atual,
            "Status": "Sem processo válido",
            "Qtd": row["QTD"],
            "Total Processos Válidos": 0,
            "Horas Totais": 0
        })
    else:
        auditoria_pv.append({
            "PV": pv_atual,
            "Cliente": cliente_atual,
            "CODIGO": codigo_atual,
            "Status": "OK",
            "Qtd": row["QTD"],
            "Total Processos Válidos": qtde_processos_validos,
            "Horas Totais": horas_totais_pv
        })

df = pd.DataFrame(linhas)

# 🔥 GARANTE QUE NENHUMA PV SUMA
pvs_aps_set = set(df["PV"].astype(str).str.strip().unique()) if not df.empty else set()
pvs_excluidas_set = set([str(x["PV"]).strip() for x in pvs_excluidas])

pvs_faltantes_silenciosas = pvs_excel_set - pvs_aps_set

for pv_faltante in pvs_faltantes_silenciosas:
    linha_pv = df_pv[df_pv["PV"].astype(str).str.strip() == pv_faltante]

    if not linha_pv.empty:
        row = linha_pv.iloc[0]
        pvs_excluidas.append({
            "PV": row["PV"],
            "Cliente": row.get("CLIENTE", "SEM CLIENTE"),
            "CODIGO": row["CODIGO_PV"],
            "Motivo": "PV não carregada no APS"
        })

        linhas.append({
            "PV": str(row["PV"]).strip(),
            "Cliente": row.get("CLIENTE", "SEM CLIENTE"),
            "Processo": "PV NÃO CARREGADA",
            "Data": row["ENTREGA"],
            "Horas": 0
        })

df = pd.DataFrame(linhas)
df_excluidas = pd.DataFrame(pvs_excluidas)
df_sem_carga = pd.DataFrame(pvs_sem_carga)
df_auditoria_pv = pd.DataFrame(auditoria_pv)

if df.empty:
    st.warning("Nenhum dado válido foi encontrado para exibir no dashboard.")
    st.stop()
    
# ===============================
# FILTRO POR CLIENTE
# ===============================
df_excluidas = pd.DataFrame(pvs_excluidas)
df["Cliente"] = df["Cliente"].fillna("SEM CLIENTE").astype(str).str.strip()

clientes_disponiveis = sorted(df["Cliente"].dropna().unique().tolist())
cliente_sel = st.selectbox("Filtrar Cliente", ["Todos"] + clientes_disponiveis)

if cliente_sel != "Todos":
    df = df[df["Cliente"] == cliente_sel].copy()
    df_excluidas = df_excluidas[df_excluidas["Cliente"] == cliente_sel].copy() if not df_excluidas.empty else df_excluidas
    df_sem_carga = df_sem_carga[df_sem_carga["Cliente"] == cliente_sel].copy() if not df_sem_carga.empty else df_sem_carga
    df_auditoria_pv = df_auditoria_pv[df_auditoria_pv["Cliente"] == cliente_sel].copy() if not df_auditoria_pv.empty else df_auditoria_pv

if df.empty:
    st.warning("Nenhum dado encontrado para o filtro selecionado.")
    st.stop()

# ===============================
# DATAS
# ===============================
df["Semana"] = df["Data"].dt.isocalendar().week.astype(int)
df["Ano"] = df["Data"].dt.year
df["Mes"] = df["Data"].dt.month
mes_ref = int(df["Mes"].mode()[0])
ano_ref = int(df["Ano"].mode()[0])

horas_mes = horas_uteis_mes(ano_ref, mes_ref)
total_recursos = sum(MAQUINAS.values())

# ===============================
# FILA REAL POR PROCESSO
# ===============================
df = df.sort_values(by=["Processo", "Data", "PV"]).reset_index(drop=True)
df["Fila Acumulada (h)"] = df.groupby("Processo")["Horas"].cumsum()
df["Fila (dias)"] = df["Fila Acumulada (h)"] / HORAS_DIA

# ===============================
# CALENDÁRIO
# ===============================
cal = df[["Data", "Semana", "Ano"]].drop_duplicates().copy()

cal["Inicio"] = cal["Data"] - pd.to_timedelta(cal["Data"].dt.weekday, unit="d")
cal["Fim"] = cal["Inicio"] + pd.Timedelta(days=6)

cal = cal.groupby(["Semana", "Ano"]).agg({
    "Inicio": "min",
    "Fim": "max"
}).reset_index()

cal["Dias Úteis"] = cal.apply(
    lambda x: dias_uteis_periodo(x["Inicio"], x["Fim"]), axis=1
)

# ===============================
# VISÃO
# ===============================
tipo = st.radio("Visualização", ["Semanal", "Mensal"], horizontal=True)

if tipo == "Semanal":
    df["Periodo"] = "Sem " + df["Semana"].astype(str)

    dem = df.groupby(["Periodo", "Processo", "Semana", "Ano"], as_index=False)["Horas"].sum()
    dem = dem.merge(cal, on=["Semana", "Ano"], how="left")

    dem["Capacidade"] = dem.apply(
        lambda r: int(
            r["Dias Úteis"] *
            HORAS_DIA *
            MAQUINAS.get(r["Processo"], 1) *
            EFICIENCIA
        ),
        axis=1
    )

else:
    df["Periodo"] = "Mês " + df["Mes"].astype(str)

    dem = df.groupby(["Periodo", "Processo", "Mes", "Ano"], as_index=False)["Horas"].sum()

    dem["Dias Úteis"] = dem.apply(
        lambda r: dias_uteis_mes(r["Ano"], r["Mes"]),
        axis=1
    )

    dem["Capacidade"] = dem.apply(
        lambda r: int(
            r["Dias Úteis"] *
            HORAS_DIA *
            MAQUINAS.get(r["Processo"], 1) *
            EFICIENCIA
        ),
        axis=1
    )

# ===============================
# AGRUPAMENTO POR PROCESSO
# ===============================
dem_proc = df.groupby(["Processo"])["Horas"].sum().reset_index()

# ===============================
# MÉTRICAS
# ===============================
dem["Ocupação (%)"] = (dem["Horas"] / dem["Capacidade"]) * 100
dem["Ocupação (%)"] = dem["Ocupação (%)"].replace([float("inf"), -float("inf")], 0)
dem["Ocupação (%)"] = dem["Ocupação (%)"].fillna(0)
dem["Ocupação (%)"] = dem["Ocupação (%)"].round(0).astype(int)

def status(x):
    if x > 100:
        return "🔴"
    elif x > 80:
        return "🟡"
    else:
        return "🟢"

dem["Status"] = dem["Ocupação (%)"].apply(status)
dem["Saldo (h)"] = (dem["Capacidade"] - dem["Horas"]).round(1)

# ===============================
# CAPACIDADE POR PROCESSO
# ===============================
capacidade_proc = {
    proc: horas_mes * MAQUINAS.get(proc, 0) * EFICIENCIA
    for proc in processos
}

dem_proc["Capacidade Processo"] = dem_proc["Processo"].map(capacidade_proc)

dem_proc["Utilização (%)"] = (
    dem_proc["Horas"] / dem_proc["Capacidade Processo"] * 100
)

dem_proc["Utilização (%)"] = dem_proc["Utilização (%)"].replace([float("inf"), -float("inf")], 0)
dem_proc["Utilização (%)"] = dem_proc["Utilização (%)"].fillna(0)
dem_proc["Utilização (%)"] = dem_proc["Utilização (%)"].round(0).astype(int)

def faixa_utilizacao(x):
    if x > 100:
        return "Crítico"
    elif x > 80:
        return "Atenção"
    else:
        return "OK"

dem_proc["Faixa"] = dem_proc["Utilização (%)"].apply(faixa_utilizacao)

# ===============================
# ATRASO
# ===============================
pv_carga = df.groupby(["PV", "Cliente", "Data"], as_index=False)["Horas"].sum()

pv_carga["Dias Necessários"] = pv_carga["Horas"] / HORAS_DIA

hoje = pd.Timestamp.today().normalize()

pv_carga["Dias Disponíveis"] = pv_carga["Data"].apply(
    lambda x: dias_uteis_periodo(hoje, x)
)

pv_carga["Atraso (dias)"] = (
    pv_carga["Dias Necessários"] - pv_carga["Dias Disponíveis"]
).apply(lambda x: max(0, math.ceil(x)))

# ===============================
# PIZZA / ATRASOS
# ===============================
pvs_no_aps = len(pvs_aps_set)
atrasos = pv_carga[pv_carga["Atraso (dias)"] > 0].copy()

# ===============================
# RISCO
# ===============================
risco = pv_carga[
    (pv_carga["Atraso (dias)"] == 0) &
    (pv_carga["Dias Necessários"] > pv_carga["Dias Disponíveis"] * 0.8)
].copy()

# ===============================
# CAPACIDADE MENSAL FIXA (NOVO)
# ===============================
capacidade_mensal_total = int(
    horas_mes * total_recursos * EFICIENCIA
)

carga_total = df["Horas"].sum()

utilizacao_global = 0
if capacidade_mensal_total > 0:
    utilizacao_global = int((carga_total / capacidade_mensal_total) * 100)

# ============================================================
# ======================= VISÃO EXECUTIVA ====================
# ============================================================
st.markdown("## 📊 Visão Executiva")

# ===============================
# INDICADORES GERAIS
# ===============================
st.subheader("📊 Indicadores Gerais")

c1, c2, c3 = st.columns(3)

c1.metric("Carga Total (h)", int(carga_total))
c2.metric("Capacidade Mensal (h)", capacidade_mensal_total)
c3.metric("Utilização (%)", utilizacao_global)

# ===============================
# RESUMO
# ===============================
st.subheader("📊 Resumo Geral")

col1, col2, col3 = st.columns(3)

col1.metric("🔴 Atraso", len(atrasos))
col2.metric("🟡 Risco", len(risco))
col3.metric("🟢 OK", len(pv_carga) - len(atrasos) - len(risco))

c4, c5 = st.columns(2)

c4.metric("PVs no Excel", pvs_totais_excel)
c5.metric("PVs no APS", pvs_no_aps)

# ===============================
# ALERTA DE CAPACIDADE CRÍTICA
# ===============================
st.subheader("⚠️ Capacidade Crítica")

critico = dem[dem["Ocupação (%)"] > 95].copy()

if not critico.empty:
    st.error("Capacidade próxima ou acima do limite detectada.")
    st.dataframe(
        critico.sort_values(["Ocupação (%)", "Horas"], ascending=[False, False]).reset_index(drop=True)
    )
else:
    st.success("Capacidade sob controle.")

# ===============================
# GRÁFICO OCUPAÇÃO
# ===============================
st.subheader("📌 Ocupação por Processo (%)")

dem["Label"] = dem["Horas"].map(lambda x: f"{x:.1f}h")

fig = px.bar(
    dem,
    x="Periodo",
    y="Ocupação (%)",
    color="Processo",
    barmode="group",
    text="Label"
)

fig.add_hline(y=100, line_dash="dash")
fig.update_traces(textposition="outside")

st.plotly_chart(fig, use_container_width=True)

# ===============================
# VISÃO CAPACIDADE POR PROCESSO
# ===============================
st.subheader("📊 Utilização por Processo (%)")

fig_proc = px.bar(
    dem_proc.sort_values("Utilização (%)", ascending=False),
    x="Processo",
    y="Utilização (%)",
    text="Utilização (%)",
    color="Faixa",
    color_discrete_map={
        "OK": "green",
        "Atenção": "gold",
        "Crítico": "red"
    }
)

fig_proc.add_hline(y=100, line_dash="dash")
fig_proc.update_traces(texttemplate="%{text}")
fig_proc.update_yaxes(title="Utilização (%)")

st.plotly_chart(fig_proc, use_container_width=True)
st.subheader("🥧 Distribuição de Status dos Processos")

status_proc = dem_proc.groupby("Faixa", as_index=False)["Processo"].count()
status_proc = status_proc.rename(columns={"Processo": "Quantidade"})

fig_status = px.pie(
    status_proc,
    names="Faixa",
    values="Quantidade",
    color="Faixa",
    color_discrete_map={
        "OK": "green",
        "Atenção": "gold",
        "Crítico": "red"
    },
    title="Status dos Processos"
)

st.plotly_chart(fig_status, use_container_width=True)

# ===============================
# CURVA DE CARGA
# ===============================
st.subheader("📈 Evolução da Carga")

carga = df.groupby("Data", as_index=False)["Horas"].sum().sort_values("Data")
carga["Carga Acumulada (h)"] = carga["Horas"].cumsum()

fig_carga = px.line(
    carga,
    x="Data",
    y="Carga Acumulada (h)",
    title="Carga Acumulada no Tempo",
    markers=True
)

st.plotly_chart(fig_carga, use_container_width=True)

# ===============================
# PV CLIENTE
# ===============================
st.subheader("📌 PV por Cliente")

pv_cliente = df.groupby("Cliente", as_index=False)["PV"].nunique()
total = pv_cliente["PV"].sum()

pv_cliente = pd.concat(
    [pv_cliente, pd.DataFrame([{"Cliente": "TOTAL", "PV": total}])],
    ignore_index=True
)

fig_cliente = px.bar(pv_cliente, x="Cliente", y="PV", text="PV")
fig_cliente.update_traces(textposition="outside")

st.plotly_chart(fig_cliente, use_container_width=True)

# ===============================
# PIZZA
# ===============================
st.subheader("🥧 Distribuição de Atraso")

if not atrasos.empty:
    dist = atrasos.groupby("Atraso (dias)", as_index=False)["PV"].count()

    fig_pizza = px.pie(dist, names="Atraso (dias)", values="PV")
    st.plotly_chart(fig_pizza, use_container_width=True)

    atraso_select = st.selectbox(
        "Selecionar atraso",
        sorted(atrasos["Atraso (dias)"].unique())
    )

    detalhe = atrasos[atrasos["Atraso (dias)"] == atraso_select].copy()
    detalhe["Horas"] = detalhe["Horas"].round(1)
    detalhe["Dias Necessários"] = detalhe["Dias Necessários"].round(1)

    st.subheader("📋 Detalhamento")
    st.dataframe(detalhe)

else:
    st.success("Nenhum atraso 🎉")

# ============================================================
# ===================== ANÁLISE OPERACIONAL ==================
# ============================================================
st.markdown("## 🏭 Análise Operacional")

# ===============================
# GARGALO AUTOMÁTICO
# ===============================
st.subheader("🔥 Gargalos do Período")

gargalos = dem.sort_values(
    by=["Periodo", "Ocupação (%)", "Horas"],
    ascending=[True, False, False]
).copy()

top_gargalos = gargalos.groupby("Periodo").head(3).reset_index(drop=True)
top_gargalos["Semáforo"] = top_gargalos["Ocupação (%)"].apply(status)
st.dataframe(
    top_gargalos[["Periodo", "Semáforo", "Processo", "Horas", "Capacidade", "Ocupação (%)", "Saldo (h)"]]
)
st.subheader("🏭 Carga Real x Capacidade por Processo (h)")

fig_cap_proc = px.bar(
    dem_proc.sort_values("Capacidade Processo", ascending=False),
    x="Processo",
    y=["Horas", "Capacidade Processo"],
    barmode="group",
    text_auto=".0f",
    title="Carga Real x Capacidade por Processo (h)"
)

fig_cap_proc.update_layout(
    yaxis_title="Horas",
    xaxis_title="Processo"
)

st.plotly_chart(fig_cap_proc, use_container_width=True, key="grafico_capacidade_carga_processo")

# ===============================
# CAPACIDADE X CARGA POR PROCESSO
# ===============================
st.subheader("🏭 Capacidade x Carga por Processo")
st.dataframe(dem_proc)

# ============================================================
# ==================== TABELAS E AUDITORIA ===================
# ============================================================
st.markdown("## 📋 Tabelas e Auditoria")

# ===============================
# FILA POR PROCESSO
# ===============================
st.subheader("📦 Fila por Processo")

fila_exibicao = df[["PV", "Cliente", "Processo", "Data", "Horas", "Fila Acumulada (h)", "Fila (dias)"]].copy()
fila_exibicao["Horas"] = fila_exibicao["Horas"].round(1)
fila_exibicao["Fila Acumulada (h)"] = fila_exibicao["Fila Acumulada (h)"].round(1)
fila_exibicao["Fila (dias)"] = fila_exibicao["Fila (dias)"].round(1)

st.dataframe(fila_exibicao)

# ===============================
# AUDITORIA
# ===============================
st.subheader("📌 Auditoria de Capacidade")

auditoria = dem.copy()
auditoria["Horas"] = auditoria["Horas"].round(1)
auditoria["Semáforo"] = auditoria["Ocupação (%)"].apply(status)

st.dataframe(
    auditoria[["Periodo", "Semáforo", "Processo", "Horas", "Capacidade", "Ocupação (%)", "Saldo (h)"]]
)

# ===============================
# ATRASO
# ===============================
st.subheader("⏱️ Previsão de Atraso por PV")

pv_carga_exibicao = pv_carga.copy()
pv_carga_exibicao["Horas"] = pv_carga_exibicao["Horas"].round(1)
pv_carga_exibicao["Dias Necessários"] = pv_carga_exibicao["Dias Necessários"].round(1)

st.dataframe(pv_carga_exibicao)

# ===============================
# RISCO
# ===============================
st.subheader("⚠️ PVs em Risco")

risco_exibicao = risco.copy()
if not risco_exibicao.empty:
    risco_exibicao["Horas"] = risco_exibicao["Horas"].round(1)
    risco_exibicao["Dias Necessários"] = risco_exibicao["Dias Necessários"].round(1)

st.dataframe(risco_exibicao)

# ===============================
# CALENDÁRIO
# ===============================
st.subheader("📅 Calendário Industrial")
st.dataframe(cal)

# ===============================
# AUDITORIA DE PV
# ===============================
st.subheader("🧪 Auditoria de PV")

if not df_auditoria_pv.empty:
    resumo_auditoria = df_auditoria_pv["Status"].value_counts().reset_index()
    resumo_auditoria.columns = ["Status", "Qtde"]

    col1, col2, col3 = st.columns(3)
    col1.metric("PVs no Excel", pvs_totais_excel)
    col2.metric("PVs no APS", df["PV"].astype(str).str.strip().nunique())
    col3.metric("PVs Auditadas", df_auditoria_pv["PV"].astype(str).str.strip().nunique())

    st.dataframe(df_auditoria_pv.sort_values(["Status", "PV"]))
else:
    st.info("Nenhuma auditoria de PV disponível.")