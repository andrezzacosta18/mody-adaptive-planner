import streamlit as st

from services.auth_service import sign_in, sign_out
from services.supabase_service import get_client


st.title("Mody — Teste de RLS")

# LOGIN
email = st.text_input("E-mail")
password = st.text_input("Senha", type="password")

if st.button("Entrar"):
    result = sign_in(email, password)

    if result["success"]:
        st.session_state["user_id"] = result["user"].id
        st.session_state["access_token"] = result["session"].access_token
        st.session_state["refresh_token"] = result["session"].refresh_token

        st.success("Login realizado!")
        st.rerun()
    else:
        st.error(result["error"])


# USUÁRIO AUTENTICADO
if "user_id" in st.session_state:

    st.divider()

    st.write("Usuário:")
    st.code(st.session_state["user_id"])

    client = get_client()

    # CRIAR TAREFA
    st.subheader("Criar tarefa de teste")

    titulo = st.text_input("Título da tarefa")

    if st.button("Criar tarefa"):

        try:
            client.table("tasks").insert({
                "user_id": st.session_state["user_id"],
                "title": titulo
            }).execute()

            st.success("Tarefa criada!")

        except Exception as e:
            st.error(f"Erro: {e}")


    # LISTAR TAREFAS
    st.subheader("Tarefas que este usuário consegue ver")

    if st.button("Listar tarefas"):

        try:
            response = (
                client
                .table("tasks")
                .select("*")
                .execute()
            )

            st.write(response.data)

        except Exception as e:
            st.error(f"Erro: {e}")


    # LOGOUT
    if st.button("Sair"):

        sign_out()

        for key in [
            "user_id",
            "access_token",
            "refresh_token",
            "supabase_client"
        ]:
            st.session_state.pop(key, None)

        st.rerun()