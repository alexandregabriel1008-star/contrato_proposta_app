import os
from datetime import datetime

from document_utils import gerar_documento
from pdf_utils import gerar_pdf
from database import salvar

from ata_generator import gerar_ata
from audio_utils import transcrever_audio_grande
from corretor import corrigir


TEMPLATES = {
    "PROPOSTA": "templates/propostas/proposta.docx",
    "CONTRATO": "templates/contratos/contrato.docx",
    "ATA_AUDIO": "templates/atas/ata_reuniao.docx",
}


def gerar_proposta(dados, usar_ia=False):
    texto = dados.get("CONTEUDO", "")

    if usar_ia:
        texto = corrigir(texto)

    dados["CONTEUDO"] = texto

    caminho = gerar_documento(
        template_path=TEMPLATES["PROPOSTA"],
        dados=dados,
        prefixo="PROPOSTA"
    )

    gerar_pdf(caminho)
    salvar("PROPOSTA", dados.get("CLIENTE"), caminho)
    return caminho


def gerar_contrato(dados, usar_ia=False):
    texto = dados.get("CONTEUDO", "")

    if usar_ia:
        texto = corrigir(texto)

    dados["CONTEUDO"] = texto

    caminho = gerar_documento(
        template_path=TEMPLATES["CONTRATO"],
        dados=dados,
        prefixo="CONTRATO"
    )

    gerar_pdf(caminho)
    salvar("CONTRATO", dados.get("CLIENTE"), caminho)
    return caminho


def gerar_ata_por_audio(
    caminho_audio,
    cliente,
    local,
    data,
    usar_correcao=True
):
    # 1️⃣ Transcrição sem limite
    transcricao = transcrever_audio_grande(caminho_audio)

    # 2️⃣ Geração da ata jurídica
    ata = gerar_ata(transcricao, cliente, local, data)

    # 3️⃣ Correção gramatical (opcional)
    if usar_correcao:
        ata = corrigir(ata)

    dados = {
        "CLIENTE": cliente,
        "LOCAL": local,
        "DATA": data,
        "CONTEUDO": ata
    }

    caminho = gerar_documento(
        template_path=TEMPLATES["ATA_AUDIO"],
        dados=dados,
        prefixo="ATA"
    )

    gerar_pdf(caminho)
    salvar("ATA", cliente, caminho)
    return caminho
