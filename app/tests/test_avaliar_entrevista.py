import pytest
from unittest.mock import patch, MagicMock
from app import app as flask_app

@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    return flask_app.test_client()

@patch("app.mlflow.start_run")
@patch("app.calcular_compatibilidade_emb")
@patch("app.montar_df_entrevista")
def test_avaliar_entrevista_ok(
    mock_montar_df,
    mock_calcular,
    mock_mlflow,
    client
):
    # Simula o DataFrame retornado
    mock_df = MagicMock()
    mock_df.iloc.__getitem__.return_value = {
        "informacoes_pessoais_nome": "João",
        "informacoes_basicas_titulo_vaga": "Dev Backend",
        "informacoes_basicas_objetivo_vaga": "Criar APIs",
        "perfil_vaga_competencia_tecnicas_e_comportamentais": "Python\nSQL",
        "perfil_vaga_habilidades_comportamentais_necessarias": "Comunicação\nTrabalho em equipe",
        "informacoes_profissionais_conhecimentos_tecnicos": "Python, Django",
        "cv_pt": "Experiência com APIs REST"
    }
    mock_montar_df.return_value = mock_df

    # Simula compatibilidade semântica
    mock_calcular.return_value = {
        "score": 75.0,
        "mais_compativeis": ["Python", "Comunicação"],
        "menos_compativeis": ["SQL"],
        "scores_individuais": []
    }

    # Simula mlflow
    mock_mlflow.return_value.__enter__.return_value = MagicMock()

    payload = {
        "email": "joao@email.com",
        "indice_vaga": 0,
        "perguntas": ["Qual sua experiência com Python?"],
        "respostas": ["Tenho 5 anos de experiência com Python."]
    }

    response = client.post("/avaliar-entrevista", json=payload)
    assert response.status_code == 200
    data = response.get_json()

    # Verificações
    assert data["status"] == "ok"
    assert data["nome"] == "João"
    assert data["titulo_vaga"] == "Dev Backend"
    assert data["resultado"] == "APTO"
    assert data["score_compatibilidade_semantica"] == 75.0