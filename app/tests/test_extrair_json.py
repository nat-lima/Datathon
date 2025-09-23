import json
import pandas as pd
import os
from utils.flatten_json import flatten_json

def test_flatten_json_simples():
    entrada = {"nome": "Viviana", "idade": 32}
    resultado = flatten_json(entrada)
    assert resultado == {"nome": "Viviana", "idade": 32}

def test_flatten_json_aninhado():
    entrada = {
        "usuario": {
            "nome": "Viviana",
            "endereco": {
                "cidade": "São Paulo",
                "cep": "01234-567"
            }
        },
        "ativo": True
    }
    resultado = flatten_json(entrada)
    esperado = {
        "usuario_nome": "Viviana",
        "usuario_endereco_cidade": "São Paulo",
        "usuario_endereco_cep": "01234-567",
        "ativo": True
    }
    assert resultado == esperado

def test_flatten_json_com_lista():
    entrada = {
        "nome": "Viviana",
        "habilidades": ["Python", "SQL"]
    }
    resultado = flatten_json(entrada)
    assert resultado == {
        "nome": "Viviana",
        "habilidades": ["Python", "SQL"]
    }

def test_flatten_json_vazio():
    entrada = {}
    resultado = flatten_json(entrada)
    assert resultado == {}

def test_flatten_json_custom_sep():
    entrada = {"a": {"b": {"c": 1}}}
    resultado = flatten_json(entrada, sep=".")
    assert resultado == {"a.b.c": 1}