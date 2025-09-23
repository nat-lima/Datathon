import pytest
from unittest.mock import patch, MagicMock
from utils.db_path import get_db_path
from pathlib import Path

def test_get_db_path_sucesso():
    # Simula estrutura de diretório: /home/user/projetos/datathon
    fake_root = Path("/home/user/projetos/datathon")
    fake_db_path = fake_root / "app" / "data" / "extraidos" / "dados.db"

    with patch("utils.db_path.Path.cwd", return_value=fake_root / "subdir"):
        with patch("utils.db_path.Path.exists", return_value=True):
            caminho = get_db_path()
            assert caminho == str(fake_db_path)

def test_get_db_path_erro_arquivo_nao_encontrado():
    fake_root = Path("/home/user/datathon")

    with patch("utils.db_path.Path.cwd", return_value=fake_root):
        with patch("utils.db_path.Path.exists", return_value=False):
            with pytest.raises(FileNotFoundError) as exc:
                get_db_path()
            assert "Banco de dados não encontrado" in str(exc.value)