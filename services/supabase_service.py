import streamlit as st
from supabase import create_client, Client

_SESSION_KEY = "_supabase_client"


def get_client() -> Client:
    """
    Retorna o cliente Supabase da sessão atual, criando-o na primeira
    chamada e reaproveitando-o nos reruns seguintes (via
    st.session_state).

    Por que não usar st.cache_resource: esse decorator cria UMA única
    instância compartilhada por todo o processo do servidor Streamlit,
    reaproveitada entre TODAS as sessões de navegador/usuários
    conectados — não apenas entre reruns da mesma sessão. Como o
    cliente Supabase guarda estado de autenticação internamente
    (client.auth.set_session(...) fica "gravado" na instância), um
    cliente compartilhado globalmente correria o risco de misturar
    sessões entre usuários diferentes em cenários concorrentes.

    Guardando o cliente em st.session_state, cada sessão de navegador
    recebe sua própria instância, isolada das demais. A autenticação
    de cada usuário fica de fato restrita à sua sessão.

    Usa a anon_key — é a chave pensada para rodar no lado do
    cliente. Ela pode ficar nos secrets do app com segurança
    DESDE QUE o Row Level Security esteja habilitado nas tabelas
    (ver database/001_schema.sql). É o RLS que impede um
    usuário de ler dados de outro, não o sigilo desta chave.

    A service_role key (que ignora RLS) NUNCA deve ser usada aqui
    nem colocada em nenhum secret acessível pelo app Streamlit.
    """
    if _SESSION_KEY not in st.session_state:
        url = st.secrets["supabase"]["url"]
        publishable_key = st.secrets["supabase"]["publishable_key"]
        st.session_state[_SESSION_KEY] = create_client(url, publishable_key)

    return st.session_state[_SESSION_KEY]
