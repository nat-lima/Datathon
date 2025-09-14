import re

def calcular_compatibilidade(requisitos, experiencia):
    """
    Calcula a compatibilidade entre requisitos e experiência/respostas do candidato.
    A pontuação é baseada na proporção de requisitos encontrados no texto.
    """

    # Pré-processamento dos textos
    requisitos_lista = [r.strip().lower() for r in requisitos.split("\n") if r.strip()]
    experiencia_texto = experiencia.lower()

    # Normaliza o texto da experiência (remove pontuação, etc.)
    experiencia_texto = re.sub(r"[^\w\s]", " ", experiencia_texto)

    # Conta quantos requisitos estão presentes no texto
    acertos = sum(1 for r in requisitos_lista if r in experiencia_texto)
    total = len(requisitos_lista)

    # Retorna a porcentagem de compatibilidade
    return round((acertos / total) * 100, 2) if total > 0 else 0