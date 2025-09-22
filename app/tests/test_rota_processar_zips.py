import pytest
from unittest.mock import patch, MagicMock
from app import app

@pytest.fixture
def client():
    app.testing = True
    return app.test_client()

def test_processar_todos_zips_sucesso(client):
    payload = {
        "pasta_zips": "fake/zips",
        "destino": "fake/destino",
        "db_path": "fake.db"
    }

    # Mocks
    with patch("app.validar_pasta", return_value=True), \
         patch("app.os.makedirs"), \
         patch("app.sqlite3.connect") as mock_connect, \
         patch("app.os.listdir", return_value=["arquivo1.zip"]), \
         patch("app.extrair_zip", return_value=["dados.json"]), \
         patch("app.os.path.isfile", return_value=True), \
         patch("app.processar_json") as mock_processar_json:

        # Mock do DataFrame
        mock_df = MagicMock()
        mock_processar_json.return_value = mock_df

        response = client.post("/processar_todos_zips", json=payload)

        assert response.status_code == 200
        assert response.json["mensagem"] == "Todos os ZIPs foram processados."
        assert "arquivo1.zip" in response.json["zips_processados"]
        assert "dados" in response.json["tabelas_salvas"]
        assert response.json["banco"] == "fake.db"

def test_processar_todos_zips_pasta_invalida(client):
    payload = {
        "pasta_zips": "invalida",
        "destino": "qualquer",
        "db_path": "dados.db"
    }

    with patch("app.validar_pasta", return_value=False):
        response = client.post("/processar_todos_zips", json=payload)

        assert response.status_code == 400
        assert response.json["erro"] == "Pasta de ZIPs inválida ou inexistente."