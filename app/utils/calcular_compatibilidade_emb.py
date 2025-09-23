from sentence_transformers import SentenceTransformer, util

# Carrega o modelo de embeddings
model = SentenceTransformer('paraphrase-MiniLM-L6-v2')

def calcular_compatibilidade_emb(requisitos, experiencia_completa, limiar_alto=0.6, limiar_baixo=0.3, modo_teste=False):
    """
    Avalia compatibilidade semântica entre requisitos e perfil do candidato.
    
    Parâmetros:
    - requisitos: string com requisitos separados por quebra de linha
    - experiencia_completa: string com a descrição da experiência do candidato
    - limiar_alto: limite para considerar um requisito como compatível
    - limiar_baixo: limite para considerar um requisito como pouco compatível
    - modo_teste: se True, simula os scores com base em presença literal (para testes unitários)

    Retorna:
    - dict com score médio, lista de requisitos mais compatíveis e menos compatíveis
    """
    requisitos_lista = [r.strip() for r in requisitos.split("\n") if r.strip()]
    resultados = []

    if modo_teste:
        experiencia_lower = experiencia_completa.lower()
        for requisito in requisitos_lista:
            if requisito.lower() in experiencia_lower:
                resultados.append((requisito, 0.9))  # compatível
            else:
                resultados.append((requisito, 0.1))  # não compatível
    else:
        emb_experiencia = model.encode(experiencia_completa, convert_to_tensor=True)
        for requisito in requisitos_lista:
            emb_requisito = model.encode(requisito, convert_to_tensor=True)
            score = util.cos_sim(emb_requisito, emb_experiencia).item()
            resultados.append((requisito, score))

    media_score = sum(score for _, score in resultados) / len(resultados) if resultados else 0
    compatibilidade = round(media_score * 100, 2)

    mais_compativeis = [r for r, s in resultados if s >= limiar_alto]
    menos_compativeis = [r for r, s in resultados if s < limiar_baixo]

    return {
        "score": compatibilidade,
        "mais_compativeis": mais_compativeis,
        "menos_compativeis": menos_compativeis,
        "scores_individuais": resultados  # útil para depuração
    }