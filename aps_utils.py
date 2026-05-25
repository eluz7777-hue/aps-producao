import pandas as pd


# ===============================
# FORMATAÇÃO BR (INALTERADO)
# ===============================
def fmt_br_num(valor, casas=1):
    try:
        valor = float(valor)
        texto = f"{valor:,.{casas}f}"
        texto = texto.replace(",", "X").replace(".", ",").replace("X", ".")
        return texto
    except:
        return "0"

def fmt_br_int(valor):
    try:
        valor = int(round(float(valor), 0))
        return f"{valor:,}".replace(",", ".")
    except:
        return "0"

def fmt_br_pct(valor, casas=1):
    try:
        valor = float(valor)
        texto = f"{valor:,.{casas}f}%"
        texto = texto.replace(",", "X").replace(".", ",").replace("X", ".")
        return texto
    except:
        return "0,0%"






# --------------------------------------------
# FUNÇÃO DE NORMALIZAÇÃO (CORRIGIDA)
# --------------------------------------------
def normalizar_chave_operacao(pv, processo, codigo):

    def limpar(valor):
        if pd.isna(valor):
            return ""

        return (
            str(valor)
            .strip()
            .upper()
            .replace("  ", " ")
            .replace(" - ", "-")
            .replace("- ", "-")
            .replace(" -", "-")
        )

    pv = limpar(pv)
    processo = limpar(processo)
    codigo = limpar(codigo)

    return f"{pv}||{processo}||{codigo}"




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
    "SOLDAGEM AÇO",
    "SOLDAGEM ALUMINIO",
    "ACABAMENTO",
    "JATEAMENTO",
    "PINTURA",
    "MONTAGEM",
    "DIVERSOS"
]


# ============================================================
# 🔥 NORMALIZAÇÃO GLOBAL DE PROCESSOS APS
# ============================================================

MAPEAMENTO_PROCESSOS = {

    # --------------------------------------------------------
    # CORTE - SERRA
    # --------------------------------------------------------
    "CORTE-SERRA": "CORTE - SERRA",
    "CORTE / SERRA": "CORTE - SERRA",
    "CORTE_SERRA": "CORTE - SERRA",
    "CORTE SERRA": "CORTE - SERRA",

    # --------------------------------------------------------
    # CORTE-LASER
    # --------------------------------------------------------
    "CORTE LASER": "CORTE-LASER",
    "LASER": "CORTE-LASER",

    # --------------------------------------------------------
    # CORTE-PLASMA
    # --------------------------------------------------------
    "CORTE PLASMA": "CORTE-PLASMA",
    "PLASMA": "CORTE-PLASMA",

    # --------------------------------------------------------
    # TORNO CONVENCIONAL
    # --------------------------------------------------------
    "TORNO": "TORNO CONVENCIONAL",

    # --------------------------------------------------------
    # FRESADORAS
    # --------------------------------------------------------
    "FRESA": "FRESADORAS",
    "FRESADORA": "FRESADORAS",

    # --------------------------------------------------------
    # SOLDAGEM
    # --------------------------------------------------------
    "SOLDA": "SOLDAGEM",

    # --------------------------------------------------------
    # CENTRO DE USINAGEM
    # --------------------------------------------------------
    "USINAGEM": "CENTRO DE USINAGEM",
    "CENTRO USINAGEM": "CENTRO DE USINAGEM",

    # --------------------------------------------------------
    # ACABAMENTO
    # --------------------------------------------------------
    "FINALIZACAO": "ACABAMENTO",
    "FINALIZAÇÃO": "ACABAMENTO"
}


# ============================================================
# 🔥 FUNÇÃO GLOBAL NORMALIZAÇÃO PROCESSOS
# ============================================================

def normalizar_processo(valor):

    if pd.isna(valor):
        return "DIVERSOS"

    valor = (

        str(valor)

        .strip()

        .upper()
    )

    valor = (
        MAPEAMENTO_PROCESSOS.get(
            valor,
            valor
        )
    )

    return valor




