import openai

def gerar_ata(transcricao, cliente, local, data):
    prompt = f"""
    Gere uma ATA DE REUNIÃO formal, clara e profissional,
    em português jurídico, com base na transcrição abaixo.

    Estrutura obrigatória:
    - Participantes
    - Pauta
    - Assuntos tratados
    - Decisões tomadas
    - Pendências
    - Próximos passos

    Dados:
    Cliente: {cliente}
    Local: {local}
    Data: {data}

    Transcrição:
    {transcricao}
    """

    resposta = openai.chat.completions.create(
        model="gpt-4.1",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    return resposta.choices[0].message.content
