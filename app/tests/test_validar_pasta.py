import os
import pytest
from app import validar_pasta

def test_validar_pasta_existente(tmp_path):
    pasta = tmp_path / "zips"
    pasta.mkdir()
    assert validar_pasta(str(pasta)) is True

def test_validar_pasta_inexistente():
    assert validar_pasta("caminho/falso") is False