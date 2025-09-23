from utils.calcular_compatibilidade_emb import calcular_compatibilidade_emb

def test_estrutura_do_retorno():
    requisitos = "Python\nMachine Learning\nSQL"
    experiencia = "Tenho experiência com Python e Machine Learning."
    resultado = calcular_compatibilidade_emb(requisitos, experiencia)

    assert isinstance(resultado, dict)
    assert "score" in resultado
    assert "mais_compativeis" in resultado
    assert "menos_compativeis" in resultado

def test_requisitos_vazios():
    requisitos = ""
    experiencia = "Tenho experiência com Python."
    resultado = calcular_compatibilidade_emb(requisitos, experiencia)

    assert resultado["score"] == 0
    assert resultado["mais_compativeis"] == []
    assert resultado["menos_compativeis"] == []
