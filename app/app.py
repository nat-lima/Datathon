from flask import Flask, jsonify, request, render_template
from pathlib import Path
from os.path import join, basename, splitext
import pandas as pd
import os
from datetime import timedelta, datetime
import zipfile
import sqlite3
import json

import mlflow

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from dotenv import load_dotenv

from utils.montar_df_entrevista import montar_df_entrevista
from utils.calcular_compatibilidade import calcular_compatibilidade
from utils.calcular_compatibilidade_emb import calcular_compatibilidade_emb
from utils.gerar_perguntas_para_vaga import gerar_perguntas_para_vaga
from utils.flatten_json import flatten_json

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)

# @app.route('/formulario')
# def formulario():
#     return render_template('formulario.html')

@app.route('/', methods=['GET'])
def home():
    return jsonify({'mensagem': 'API pronta para processar diversos ZIPs!'})

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
                print(f"ZIP inválido: {nome_arquivo}")
                continue

            for arquivo in arquivos_extraidos:
                if arquivo.endswith(".json"):
                    caminho_arquivo = os.path.join(destino, arquivo)
                    if os.path.isfile(caminho_arquivo):
                        with open(caminho_arquivo, encoding='utf-8') as f:
                            dados = json.load(f)

                        nome_tabela = splitext(basename(arquivo))[0]
                        
                        df = None  # Inicializa o DataFrame

                        # Verificar se o arquivo existe
                        if nome_tabela =='prospects':
                            linhas = []

                            # Iterar sobre todas as vagas
                            for codigo_vaga, info_vaga in dados.items():
                                vaga_info = {k: v for k, v in info_vaga.items() if k != "prospects"}
                                vaga_info["codigo_vaga"] = codigo_vaga

                                for prospect in info_vaga.get("prospects", []):
                                    linha = vaga_info.copy()
                                    for chave, valor in prospect.items():
                                        if chave in ["data_candidatura", "ultima_atualizacao"]:
                                            valor = valor.replace("-", "/")
                                        linha[chave] = valor
                                    linhas.append(linha)

                            # Criar DataFrame
                            df = pd.DataFrame(linhas)

                            # Reordenar colunas (opcional)
                            colunas_ordenadas = sorted(df.columns, key=lambda x: (x != "codigo_vaga", x))
                            df = df[colunas_ordenadas]

                        else:
                            registros = []

                            # Se for dict com múltiplos registros
                            if isinstance(dados, dict):
                                for codigo, conteudo in dados.items():
                                    registro = flatten_json(conteudo)
                                    registro = {"codigo": codigo, **registro}  # <- Aqui garantimos que o código venha primeiro
                                    registros.append(registro)

                            # Criar DataFrame
                            df = pd.DataFrame(registros)
                             
                        if df is not None:
                            df.to_sql(nome_tabela, conn, if_exists='replace', index=False)
                            tabelas_criadas.append(nome_tabela)
                            print(f"Tabela '{nome_tabela}' salva com sucesso.")
                        else:
                            print(f"Estrutura não reconhecida em '{arquivo}', tabela não criada.")
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


@app.route("/iniciar-entrevista", methods=["POST"])
def iniciar_entrevista():
    email = (request.json.get("email") or "").strip().lower()
    df_merged = montar_df_entrevista(email)
    if df_merged is None:
        return jsonify({"erro": "Candidato não encontrado"}), 404

    nome = df_merged.iloc[0].get("informacoes_pessoais_nome", "")
    if len(df_merged) > 1:
        vagas = [{"indice": int(i), "titulo_vaga": row.get("informacoes_basicas_titulo_vaga", "")}
                 for i, row in df_merged.iterrows()]
        return jsonify({"status": "escolha_vaga", "nome": nome, "vagas": vagas})

    perguntas, resumo, competencias, titulo_vaga, objetivo_vaga = gerar_perguntas_para_vaga(df_merged.iloc[0])
    return jsonify({
        "status": "ok",
        "nome": nome,
        "titulo_vaga": titulo_vaga,
        "objetivo_vaga": objetivo_vaga,
        "competencias": competencias,
        "resumo": resumo,
        "perguntas": perguntas
    })

@app.route("/gerar-perguntas", methods=["POST"])
def gerar_perguntas_vaga():
    dados = request.get_json()
    email = (dados.get("email") or "").strip().lower()
    indice_vaga = dados.get("indice_vaga")

    if email == "" or indice_vaga is None:
        return jsonify({"erro": "email e indice_vaga são obrigatórios"}), 400

    df_merged = montar_df_entrevista(email)
    if df_merged is None or df_merged.empty:
        return jsonify({"erro": "Candidato não encontrado"}), 404

    try:
        linha = df_merged.iloc[int(indice_vaga)]
    except Exception:
        return jsonify({"erro": "indice_vaga inválido"}), 400

    perguntas, resumo, competencias, titulo_vaga, objetivo_vaga = gerar_perguntas_para_vaga(linha)

    return jsonify({
        "status": "ok",
        "nome": linha.get("informacoes_pessoais_nome", ""),
        "titulo_vaga": titulo_vaga,
        "objetivo_vaga": objetivo_vaga,
        "competencias": competencias,
        "resumo": resumo,
        "perguntas": perguntas
    })

@app.route("/avaliar-entrevista", methods=["POST"])
def avaliar_entrevista():
    dados = request.json
    email = (dados.get("email") or "").strip().lower()
    indice_vaga = dados.get("indice_vaga", 0)
    perguntas = dados.get("perguntas", [])
    respostas = dados.get("respostas", [])

    df_merged = montar_df_entrevista(email)
    if df_merged is None:
        return jsonify({"erro": "Candidato não encontrado"}), 404

    linha = df_merged.iloc[int(indice_vaga)]
    nome = linha.get("informacoes_pessoais_nome", "")
    titulo_vaga = linha.get("informacoes_basicas_titulo_vaga", "")
    objetivo_vaga = linha.get("informacoes_basicas_objetivo_vaga", "")
    requisitos = linha.get("perfil_vaga_competencia_tecnicas_e_comportamentais", "")
    comp_comp = linha.get("perfil_vaga_habilidades_comportamentais_necessarias", "")
    competencias_full = f"{requisitos}\n{comp_comp}".strip()
    experiencia = linha.get("informacoes_profissionais_conhecimentos_tecnicos", "")
    respostas_texto = "\n".join(respostas)
    cv_resumo = linha.get("cv_pt", "")
    experiencia_completa = f"{experiencia}\n{cv_resumo}\n{respostas_texto}".strip()

    score = calcular_compatibilidade(requisitos, experiencia_completa)

    resultado_detalhado = calcular_compatibilidade_emb(requisitos, experiencia_completa)
    score_emb = resultado_detalhado["score"]
    mais_compativeis = resultado_detalhado["mais_compativeis"]
    menos_compativeis = resultado_detalhado["menos_compativeis"]

    resultado = "APTO" if score > 50 and score_emb > 50 else "NÃO APTO"

    with mlflow.start_run(run_name=f"Entrevista_{nome}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"):
        mlflow.log_param("nome", nome)
        mlflow.log_param("email", email)
        mlflow.log_param("vaga", titulo_vaga)
        mlflow.log_param("objetivo_vaga", objetivo_vaga)
        mlflow.log_param("resultado", resultado)
        mlflow.log_param("competencias", competencias_full)
        mlflow.log_metric("compatibilidade_tecnica", score)
        mlflow.log_metric("compatibilidade_tecnica_emb", score_emb)
        mlflow.log_text("\n".join(perguntas), "perguntas_geradas.txt")
        mlflow.log_text("\n".join([f"Q: {q}\nA: {r}" for q, r in zip(perguntas, respostas)]), "respostas_candidato.txt")
        mlflow.log_text(respostas_texto, "respostas_processadas.txt")
        mlflow.log_text(cv_resumo, "cv_resumo.txt")

    return jsonify({
        "status": "ok",
        "nome": nome,
        "titulo_vaga": titulo_vaga,
        "resultado": resultado,
        "score_compatibilidade": score,
        "score_compatibilidade_detalhada": score_emb,
        "requisitos_mais_compatíveis": mais_compativeis,
        "requisitos_menos_compatíveis": menos_compativeis
    })


if __name__ == '__main__':
    app.run(debug=True)