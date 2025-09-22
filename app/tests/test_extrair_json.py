import json
from app import processar_json

def test_processar_json_valido(tmp_path):
    dados = {"nome": "Viviana", "idade": 32}
    caminho = tmp_path / "dados.json"
    with open(caminho, "w") as f:
        json.dump(dados, f)

    df = processar_json(str(caminho), "funcionarios")
    assert df is not None
    assert "nome" in df.columns
    assert df.iloc[0]["nome"] == "Viviana"

def test_processar_json_invalido(tmp_path):
    caminho = tmp_path / "dados.json"
    caminho.write_text("isso não é JSON válido")

    df = processar_json(str(caminho), "funcionarios")
    assert df is None