import subprocess
import time
import os
from pathlib import Path

# =====================================================
# CONFIGURAÇÃO DO LIBREOFFICE
# =====================================================
LIBREOFFICE_PATH = r"C:\Program Files\LibreOffice\program\soffice.exe"


# =====================================================
# GERADOR DE PDF (COMPATÍVEL COM app.py)
# =====================================================
def gerar_pdf(
    caminho_docx: str,
    pasta_destino: str | None = None,
    cliente: str | None = None,
    tipo: str | None = None
) -> str:
    """
    Converte DOCX em PDF usando LibreOffice.
    O PDF é salvo na MESMA pasta do DOCX.
    Parâmetros extras existem apenas para compatibilidade.
    """

    caminho_docx = Path(caminho_docx)

    if not Path(LIBREOFFICE_PATH).exists():
        raise RuntimeError("LibreOffice não encontrado no caminho configurado.")

    if not caminho_docx.exists():
        raise RuntimeError(f"DOCX não encontrado: {caminho_docx}")

    pasta_saida = caminho_docx.parent
    pdf_esperado = pasta_saida / f"{caminho_docx.stem}.pdf"

    tentativas = 3
    ultimo_erro = None

    for tentativa in range(1, tentativas + 1):
        try:
            comando = [
                LIBREOFFICE_PATH,
                "--headless",
                "--nologo",
                "--nofirststartwizard",
                "--convert-to", "pdf",
                str(caminho_docx),
                "--outdir", str(pasta_saida)
            ]

            resultado = subprocess.run(
                comando,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=90
            )

            if resultado.returncode != 0:
                raise RuntimeError(
                    resultado.stderr.decode("utf-8", errors="ignore")
                )

            time.sleep(2)

            if not pdf_esperado.exists():
                raise RuntimeError("PDF não foi gerado pelo LibreOffice.")

            return str(pdf_esperado)

        except Exception as e:
            ultimo_erro = str(e)
            time.sleep(2)

    raise RuntimeError(
        f"Erro ao gerar PDF após {tentativas} tentativas: {ultimo_erro}"
    )