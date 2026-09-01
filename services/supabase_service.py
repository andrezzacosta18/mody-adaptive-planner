import streamlit as st
from supabase import create_client, Client
from supabase.client import ClientOptions


_SESSION_KEY = "_supabase_client"


def get_client() -> Client:
    """
    Retorna o cliente Supabase da sessão atual.

    O cliente é armazenado em st.session_state para que cada sessão
    de navegador tenha sua própria instância do Supabase.

    Isso evita compartilhar estado de autenticação entre usuários
    diferentes, algo que poderia acontecer se fosse usado
    st.cache_resource.

    O cliente utiliza somente a publishable key configurada em
    .streamlit/secrets.toml.

    A service_role key NUNCA deve ser usada neste app.

    O fluxo de autenticação é configurado como PKCE para permitir
    que links de recuperação de senha retornem ao Streamlit usando
    um código (?code=...), que depois poderá ser trocado por uma
    sessão válida através de exchange_code_for_session().
    """

    if _SESSION_KEY not in st.session_state:
        url = st.secrets["supabase"]["url"]
        publishable_key = st.secrets["supabase"]["publishable_key"]

        options = ClientOptions(
            flow_type="pkce",
            persist_session=True,
            auto_refresh_token=True,
        )

        st.session_state[_SESSION_KEY] = create_client(
            url,
            publishable_key,
            options=options,
        )

    return st.session_state[_SESSION_KEY]