import streamlit as st
import requests
import os
from dotenv import load_dotenv

load_dotenv()
API_URL = os.getenv("API_URL", "http://localhost:5000")  # fallback local


st.title("Entrevista RH - Candidato")

# 📧 Entrada do e-mail
email = st.text_input("Digite seu e-mail para iniciar a entrevista:")

if st.button("Iniciar entrevista") and email:
    response = requests.post(f"{API_URL}/iniciar-entrevista", json={"email": email})
    data = response.json()

    if response.status_code != 200:
        st.error(data.get("erro", "Erro ao iniciar entrevista"))
    elif data["status"] == "escolha_vaga":
        st.subheader(f"Olá, {data['nome']}! Escolha a vaga para entrevista:")
        vaga_opcao = st.selectbox("Vagas disponíveis", options=data["vagas"], format_func=lambda x: x["titulo_vaga"])
        if st.button("Selecionar vaga"):
            indice = vaga_opcao["indice"]
            response = requests.post(f"{API_URL}/gerar-perguntas", json={"email": email, "indice_vaga": indice})
            data = response.json()
    elif data["status"] == "ok":
        # Já tem uma vaga única
        pass  # segue abaixo

    if data["status"] == "ok":
        st.subheader(f"Entrevista para: {data['titulo_vaga']}")
        st.write(f"Objetivo da vaga: {data['objetivo_vaga']}")
        st.write(f"Competências esperadas: {data['competencias']}")
        st.write(f"Resumo da vaga: {data['resumo']}")

        respostas = []
        for i, pergunta in enumerate(data["perguntas"]):
            resposta = st.text_area(f"{i+1}. {pergunta}", key=f"resposta_{i}")
            respostas.append(resposta)

        if st.button("Enviar respostas"):
            payload = {
                "email": email,
                "indice_vaga": vaga_opcao["indice"] if data["status"] == "escolha_vaga" else 0,
                "perguntas": data["perguntas"],
                "respostas": respostas
            }
            response = requests.post(f"{API_URL}/avaliar-entrevista", json=payload)
            resultado = response.json()

            if response.status_code == 200:
                st.success(f"Resultado: {resultado['resultado']}")
                st.metric("Score compatibilidade", resultado["score_compatibilidade"])
                st.metric("Score detalhado", resultado["score_compatibilidade_detalhada"])
                st.write("✅ Requisitos mais compatíveis:")
                st.write(resultado["requisitos_mais_compatíveis"])
                st.write("⚠️ Requisitos menos compatíveis:")
                st.write(resultado["requisitos_menos_compatíveis"])
            else:
                st.error(resultado.get("erro", "Erro ao avaliar entrevista"))