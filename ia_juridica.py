import language_tool_python

_tool = language_tool_python.LanguageTool('pt-BR')

def melhorar_texto(texto: str) -> str:
    """
    Substituto da IA.
    Corrige ortografia e gramática offline.
    """
    return _tool.correct(texto)
