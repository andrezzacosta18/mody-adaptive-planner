"""
Script único para validar a conexão com o Supabase.
Não faz parte do app principal (não é uma page).

Como rodar:
    streamlit run tests/test_connection.py
"""

import sys
import os

# permite importar services/ quando o script roda a partir de tests/
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
from services.supabase_service import get_client

st.title("Teste de conexão — Supabase")

try:
    client = get_client()
    st.success("Cliente Supabase criado com sucesso.")
except Exception as e:
    st.error(f"Erro ao criar o cliente: {e}")
    st.stop()

st.write("Tentando ler a tabela `tasks` (sem estar autenticado)...")

try:
    resposta = client.table("tasks").select("*").execute()
    st.write("Linhas retornadas:", resposta.data)
    st.info(
        "Se a lista veio vazia (mesmo que existam tarefas no banco), "
        "é um bom sinal: significa que o Row Level Security está "
        "bloqueando o acesso sem autenticação, como esperado."
    )
except Exception as e:
    st.error(f"Erro ao consultar a tabela: {e}")
