from flask import Flask, jsonify, json, request, render_template
from pathlib import Path
from os.path import join, basename, splitext
import pandas as pd
import numpy as np
import joblib
import os
from datetime import timedelta
import zipfile
import sqlite3
import json
import ast
import re

app = Flask(__name__)

# Função para extrair múltiplos dicionários da string prospects
def parse_prospects_string(prospects_str):
    candidatos = []
    if not prospects_str or not isinstance(prospects_str, str):
        return candidatos

    # Regex para capturar cada dicionário individual
    pattern = r"\{[^{}]+\}"
    matches = re.findall(pattern, prospects_str)

    for match in matches:
        try:
            candidato = ast.literal_eval(match)
            if isinstance(candidato, dict):
                candidatos.append(candidato)
        except Exception as e:
            print(f"Erro ao interpretar bloco: {e}")
    return candidatos

# @app.route('/formulario')
# def formulario():
#     return render_template('formulario.html')

@app.route('/', methods=['GET'])
def home():
    return jsonify({'mensagem': 'API pronta para processar múltiplos ZIPs!'})

@app.route('/processar_todos_zips', methods=['POST'])
def processar_todos_zips():
    data = request.get_json()
    pasta_zips = data.get('pasta_zips')
    destino = data.get('destino')
    db_path = data.get('db_path', 'dados.db')

    if not pasta_zips or not os.path.isdir(pasta_zips):
        return jsonify({'erro': 'Pasta de ZIPs inválida ou inexistente.'}), 400

    if not destino:
        destino = os.path.join(pasta_zips, "extraidos")
    os.makedirs(destino, exist_ok=True)

    conn = sqlite3.connect(db_path)
    tabelas_criadas = []
    arquivos_processados = []

    for nome_arquivo in os.listdir(pasta_zips):
        if nome_arquivo.endswith(".zip"):
            zip_path = os.path.join(pasta_zips, nome_arquivo)
            try:
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(destino)
                    arquivos_extraidos = zip_ref.namelist()
                    arquivos_processados.append(nome_arquivo)
            except zipfile.BadZipFile:
                print(f"❌ ZIP inválido: {nome_arquivo}")
                continue

            for arquivo in arquivos_extraidos:
                if arquivo.endswith(".json"):
                    caminho_arquivo = os.path.join(destino, arquivo)
                    if os.path.isfile(caminho_arquivo):
                        with open(caminho_arquivo, encoding='utf-8') as f:
                            dados = json.load(f)

                        nome_tabela = splitext(basename(arquivo))[0]

                        df = None  # Inicializa o DataFrame

                        # Estrutura tabular: lista de dicts
                        if isinstance(dados, list) and all(isinstance(item, dict) for item in dados):
                            registros = []
                            for item in dados:
                                novo_registro = {}
                                for k, v in item.items():
                                    if k == "prospects":
                                        candidatos = parse_prospects_string(v)
                                        agrupado = {}
                                        for campo in ["nome", "codigo", "situacao_candidado", "data_candidatura", "ultima_atualizacao", "comentario", "recrutador"]:
                                            valores = [str(c.get(campo, "")).strip() for c in candidatos]
                                            agrupado[f"{campo}_applicant"] = ", ".join(valores)
                                        novo_registro.update(agrupado)

                                    elif isinstance(v, list):
                                        novo_registro[k] = ', '.join(map(str, v))
                                    else:
                                        novo_registro[k] = v
                                registros.append(novo_registro)
                            df = pd.DataFrame(registros)


                        # Estrutura tipo dict com subdicts
                        elif isinstance(dados, dict) and all(isinstance(v, dict) for v in dados.values()):
                            registros = []
                            for codigo, info in dados.items():
                                registro = {"codigo": codigo}
                                for categoria, campos in info.items():
                                    if isinstance(campos, dict):
                                        for chave, valor in campos.items():
                                            if isinstance(valor, list):
                                                valor = ', '.join(map(str, valor))
                                            registro[f"{categoria}_{chave}"] = valor
                                    else:
                                        if isinstance(campos, list):
                                            campos = ', '.join(map(str, campos))
                                        registro[categoria] = campos
                                registros.append(registro)
                            df = pd.DataFrame(registros)

                        # Estrutura tipo dict com lista interna
                        elif isinstance(dados, dict):
                            for chave, valor in dados.items():
                                if isinstance(valor, list) and all(isinstance(item, dict) for item in valor):
                                    registros = []
                                    for item in valor:
                                        novo_registro = {}
                                        for k, v in item.items():
                                            if k == "prospects":
                                                candidatos = parse_prospects_string(v)
                                                agrupado = {}
                                                for campo in ["nome", "codigo", "situacao_candidado", "data_candidatura", "ultima_atualizacao", "comentario", "recrutador"]:
                                                    valores = [str(c.get(campo, "")).strip() for c in candidatos]
                                                    agrupado[f"{campo}_applicant"] = ", ".join(valores)
                                                novo_registro.update(agrupado)

                                            elif isinstance(v, list):
                                                novo_registro[k] = ', '.join(map(str, v))
                                            else:
                                                novo_registro[k] = v
                                        registros.append(novo_registro)
                                    df = pd.DataFrame(registros)
                                    break

                        if df is not None:
                            df.to_sql(nome_tabela, conn, if_exists='replace', index=False)
                            tabelas_criadas.append(nome_tabela)
                            print(f"✅ Tabela '{nome_tabela}' salva com sucesso.")
                        else:
                            print(f"⚠️ Estrutura não reconhecida em '{arquivo}', tabela não criada.")
                    else:
                        print(f"Arquivo '{arquivo}' não encontrado.")

    conn.close()

    return jsonify({
        'mensagem': f'Todos os ZIPs foram processados.',
        'tabelas_salvas': tabelas_criadas,
        'banco': db_path,
        'zips_processados': arquivos_processados
    })

@app.route('/consultar/<tabela>', methods=['GET'])
def consultar_tabela(tabela):
    try:
        # Caminho absoluto baseado no local do script
        base_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(base_dir, 'data', 'extraidos', 'dados.db')

        conn = sqlite3.connect(db_path)
        df = pd.read_sql_query(f"SELECT * FROM {tabela} LIMIT 50", conn)
        conn.close()
        return jsonify(df.to_dict(orient='records'))
    except Exception as e:
        return jsonify({'erro': f'Erro ao consultar a tabela: {str(e)}'}), 400


if __name__ == '__main__':
    app.run(debug=True)