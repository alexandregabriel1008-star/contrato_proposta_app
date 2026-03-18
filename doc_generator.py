from docx import Document
import os
import re


def _substituir_texto_completo(paragrafo, dados):
    """
    Reconstrói o texto completo do parágrafo,
    substitui variáveis {{VAR}}, e reaplica no primeiro run.
    Preserva formatação básica.
    """
    texto_completo = "".join(run.text for run in paragrafo.runs)

    for chave, valor in dados.items():
        padrao = r"\{\{\s*" + re.escape(chave) + r"\s*\}\}"
        texto_completo = re.sub(padrao, str(valor), texto_completo)

    if paragrafo.runs:
        paragrafo.runs[0].text = texto_completo
        for run in paragrafo.runs[1:]:
            run.text = ""


def _substituir_em_tabelas(doc, dados):
    """
    Substitui variáveis dentro de tabelas.
    """
    for tabela in doc.tables:
        for linha in tabela.rows:
            for celula in linha.cells:
                for p in celula.paragraphs:
                    _substituir_texto_completo(p, dados)


def gerar_documento(template_path, dados, tipo, nome_cliente):
    """
    Gera documento DOCX substituindo variáveis {{VAR}},
    preservando layout e estrutura do template.
    Retorna o caminho final do arquivo.
    """

    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template não encontrado: {template_path}")

    doc = Document(template_path)

    # Substituição em parágrafos
    for p in doc.paragraphs:
        _substituir_texto_completo(p, dados)

    # Substituição em tabelas
    _substituir_em_tabelas(doc, dados)

    nome_cliente_safe = nome_cliente.replace(" ", "_")
    nome_arquivo = f"{tipo}_{nome_cliente_safe}.docx"

    output_dir = "temp"
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, nome_arquivo)
    doc.save(output_path)

    return output_path
