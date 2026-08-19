import streamlit as st
from supabase import create_client, Client


@st.cache_resource
def get_client() -> Client:
    """
    Cria e reaproveita o cliente Supabase.

    Usa a publishable key do projeto.
    O acesso aos dados deve ser protegido por Row Level Security (RLS).

    Nunca use a secret key ou service_role key neste arquivo.
    """

    url = st.secrets["supabase"]["url"]
    publishable_key = st.secrets["supabase"]["publishable_key"]

    return create_client(url, publishable_key)