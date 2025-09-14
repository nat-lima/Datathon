# Datathon: API de Entrevistas com Processamento de ZIPs, Geração de Perguntas e Avaliação via MLflow

Esta API em Flask processa arquivos ZIP contendo dados de candidatos e vagas, armazena-os em um banco SQLite, gera perguntas de entrevista usando **LangChain + OpenAI**, e avalia respostas registrando resultados no **MLflow**.

---

## 🚀 Funcionalidades

- **Processar múltiplos arquivos ZIP** contendo JSONs de candidatos, prospects e vagas.
- **Consultar tabelas** do banco SQLite.
- **Iniciar entrevista** a partir do e-mail do candidato.
- **Gerar perguntas** para uma vaga específica.
- **Avaliar entrevista** com cálculo de compatibilidade semântica e registro no MLflow.
- **Rodar via Docker Compose** com ambiente isolado e replicável.

---

## 📂 Estrutura de Pastas

DATATHON/
|    └── app
|        ├── data/
|        │   ├── extraidos
|        │   │   ├── applicants.json
|        │   │   ├── dados.db
|        │   │   ├── prospects.json
|        │   │   └── vagas.json
|        │   └── EDA dados db.ipynb
|        ├── utils/
|        │   ├── __init__.py
|        │   ├── calcular_compatibilidade_emb.py
|        │   ├── calcular_compatibilidade.py
|        │   ├── flatten_json.py
|        │   ├── gerar_perguntas_para_vaga.py
|        │   └── montar_df_entrevista.py
|        ├──.env
|        ├── app.py
|        ├── docker-compose.yml
|        ├── Docekrfile
|        ├── mlruns_analysis.ipynb
|        ├── requirements.txt
|
└── .env

---

## ⚙️ Pré-requisitos

- Python 3.9+
- Conta e chave de API da OpenAI
- MLflow instalado

---

## 🐳 Docker Compose

Para rodar o projeto com Docker:

### 1. `Dockerfile`

```Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt
EXPOSE 5000
CMD ["python", "app.py"]

### 2. `Docker=compose.yml`
Yaml

version: '3.10'

services:
  web:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - .:/app
    working_dir: /app
    env_file:
      - .env
    command: python app.py

### 3. `Rodar o projoto`

docker-compose up --build

---

## 📦 Instalação

1. **Clonar o repositório**:
   ```bash
   git clone https://seu-repositorio.git
   cd projeto

2. **Criar ambiente virtual**:
    ```bash
    python -m venv venv
    source venv/bin/activate   # Linux/Mac
    venv\Scripts\activate      # Windows

3. **Instalar dependências**:
    ```bash
    pip install -r requirements.txt

4. **Configurar variáveis de ambiente: Crie um arquivo .env na raiz com**:
  ```bash
    OPENAI_API_KEY=sua_chave_openai_aqui


📜 Endpoints
1️⃣ POST /processar_todos_zips
Processa todos os arquivos ZIP de uma pasta e salva no banco SQLite.
Body (JSON):
{
  "pasta_zips": "caminho/para/pasta",
  "destino": "caminho/para/destino",
  "db_path": "caminho/para/dados.db"
}


Resposta:
{
  "mensagem": "Todos os ZIPs foram processados.",
  "tabelas_salvas": ["applicants", "prospects", "vagas"],
  "banco": "dados.db",
  "zips_processados": ["arquivo1.zip", "arquivo2.zip"]
}


2️⃣ GET /consultar/<tabela>
Consulta até 50 registros de uma tabela.
Exemplo:
GET /consultar/applicants


3️⃣ POST /iniciar-entrevista
Inicia entrevista a partir do e-mail do candidato.
Body:
{
  "email": "candidato@exemplo.com"
}


Resposta:
- Se houver 1 vaga:
{
  "status": "ok",
  "nome": "Fulano",
  "titulo_vaga": "Analista de Sistemas",
  "objetivo_vaga": "...",
  "competencias": "...",
  "resumo": "...",
  "perguntas": ["Pergunta 1", "..."]
}


- Se houver mais de uma vaga:
{
  "status": "escolha_vaga",
  "nome": "Fulano",
  "vagas": [
    {"indice": 0, "titulo_vaga": "Vaga A"},
    {"indice": 1, "titulo_vaga": "Vaga B"}
  ]
}


4️⃣ POST /gerar-perguntas
Gera perguntas para uma vaga específica.
Body:
{
  "email": "candidato@exemplo.com",
  "indice_vaga": 0
}


Resposta:
{
  "status": "ok",
  "nome": "Fulano",
  "titulo_vaga": "Analista de Sistemas",
  "objetivo_vaga": "...",
  "competencias": "...",
  "resumo": "...",
  "perguntas": ["Pergunta 1", "..."]
}


5️⃣ POST /avaliar-entrevista
Avalia respostas e registra no MLflow.
Body:
{
  "email": "candidato@exemplo.com",
  "indice_vaga": 0,
  "perguntas": ["Pergunta 1", "..."],
  "respostas": ["Resposta 1", "..."]
}


Resposta:
{
  "status": "ok",
  "nome": "Fulano",
  "titulo_vaga": "Analista de Sistemas",
  "resultado": "APTO",
  "score_compatibilidade": 82.5,
  "requisitos_mais_compatíveis": ["comunicação eficaz", "trabalho em equipe"],
  "requisitos_menos_compatíveis": ["experiência com AWS"]
}

Compatibilidade semântica com embeddings
A função calcular_compatibilidade_detalhada usa sentence-transformers para comparar requisitos com:
- Experiência técnica
- Respostas às perguntas
- Resumo do currículo (cv_pt)
Ela retorna:
- ✅ Score médio de compatibilidade
- ✅ Lista de requisitos mais compatíveis
- ✅ Lista de requisitos menos compatíveis



🧪 Testando no Postman
Fluxo sugerido:
- /iniciar-entrevista → pega índice da vaga.
- /gerar-perguntas → obtém perguntas.
- /avaliar-entrevista → envia perguntas e respostas.
💡 Você pode usar Scripts Post‑response no Postman para salvar automaticamente as perguntas e reaproveitar na próxima requisição.

📊 Integração com MLflow
Cada avaliação cria um run no MLflow com:
- Parâmetros: nome, email, vaga, objetivo, resultado, competências.
- Métrica: compatibilidade técnica (%).
- Artefatos: perguntas e respostas em .txt.
Para visualizar:
mlflow ui


Acesse: http://127.0.0.1:5000

📄 Licença
Este projeto é de uso interno/educacional. Ajuste conforme necessário para produção.

---
