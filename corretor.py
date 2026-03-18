import language_tool_python
import re

from blacklist import BLACKLIST
from dicionario_contabil import DICIONARIO_CONTABIL

tool = language_tool_python.LanguageTool(
    "pt-BR",
    motherTongue="pt-BR"
)

def dividir_texto(texto, limite=3500):
    if not texto:
        return []

    partes = []
    texto = texto.strip()

    while len(texto) > limite:
        corte = texto.rfind(" ", 0, limite)
        if corte == -1:
            corte = limite
        partes.append(texto[:corte].strip())
        texto = texto[corte:].strip()

    if texto:
        partes.append(texto)

    return partes


def aplicar_blacklist(texto):
    """
    Aplica correções forçadas (acentuação e erros comuns)
    """
    palavras = texto.split()
    resultado = []

    for palavra in palavras:
        limpa = re.sub(r"[^\wÀ-ÿ]", "", palavra).lower()
        if limpa in BLACKLIST:
            palavra_corrigida = re.sub(
                limpa,
                BLACKLIST[limpa],
                palavra,
                flags=re.IGNORECASE
            )
            resultado.append(palavra_corrigida)
        else:
            resultado.append(palavra)

    return " ".join(resultado)


def proteger_termos_contabeis(texto):
    """
    Evita que o LanguageTool altere termos técnicos
    """
    for termo in DICIONARIO_CONTABIL:
        texto = texto.replace(termo, f"@@{termo}@@")
    return texto


def restaurar_termos_contabeis(texto):
    for termo in DICIONARIO_CONTABIL:
        texto = texto.replace(f"@@{termo}@@", termo)
    return texto


def corrigir(texto, tipo="GERAL", ativo=True):
    if not ativo or not texto:
        return texto

    # 1️⃣ Blacklist (forçado)
    texto = aplicar_blacklist(texto)

    # 2️⃣ Protege termos técnicos
    texto = proteger_termos_contabeis(texto)

    partes = dividir_texto(texto)
    texto_corrigido = []

    for parte in partes:
        frases = re.split(r'(?<=[.!?])\s+', parte)
        frases_corrigidas = []

        for frase in frases:
            matches = tool.check(frase)
            corrigido = language_tool_python.utils.correct(frase, matches)
            frases_corrigidas.append(corrigido)

        texto_corrigido.append(" ".join(frases_corrigidas))

    texto_final = "\n\n".join(texto_corrigido)

    # 3️⃣ Restaura termos técnicos
    texto_final = restaurar_termos_contabeis(texto_final)

    return texto_final
