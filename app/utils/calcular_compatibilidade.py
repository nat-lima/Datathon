def calcular_compatibilidade(requisitos, experiencia):
    """Pontuação simples: % de itens de requisitos presentes no texto de experiência."""

    requisitos_lista = [r.strip().lower() for r in requisitos.split("\n") if r.strip()]
    experiencia_texto = experiencia.lower()
    acertos = sum(1 for r in requisitos_lista if r in experiencia_texto)
    total = len(requisitos_lista)
    return round((acertos / total) * 100, 2) if total > 0 else 0