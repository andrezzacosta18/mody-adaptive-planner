import streamlit as st
from supabase import create_client, Client


@st.cache_resource
def get_client() -> Client:
    """
    Cria (e reaproveita, via cache) o cliente Supabase.

    Usa a anon_key — é a chave pensada para rodar no lado do
    cliente. Ela pode ficar nos secrets do app com segurança
    DESDE QUE o Row Level Security esteja habilitado nas tabelas
    (ver sql/001_initial_schema.sql). É o RLS que impede um
    usuário de ler dados de outro, não o sigilo desta chave.

    A service_role key (que ignora RLS) NUNCA deve ser usada aqui
    nem colocada em nenhum secret acessível pelo app Streamlit.
    """
    url = st.secrets["supabase"]["url"]
    anon_key = st.secrets["supabase"]["anon_key"]
    return create_client(url, anon_key)
