import streamlit as st

from services.auth_service import sign_up, sign_in, sign_out


st.title("Mody — Teste de autenticação")

tab_login, tab_cadastro = st.tabs(["Login", "Criar conta"])


# -------------------------
# LOGIN
# -------------------------

with tab_login:

    email_login = st.text_input(
        "E-mail",
        key="email_login"
    )

    password_login = st.text_input(
        "Senha",
        type="password",
        key="password_login"
    )

    if st.button("Entrar"):

        result = sign_in(
            email_login,
            password_login
        )

        if result["success"]:

            st.session_state["access_token"] = (
                result["session"].access_token
            )

            st.session_state["refresh_token"] = (
                result["session"].refresh_token
            )

            st.session_state["user_id"] = (
                result["user"].id
            )

            st.success("Login realizado com sucesso!")

        else:

            st.error(result["error"])


# -------------------------
# CADASTRO
# -------------------------

with tab_cadastro:

    email_signup = st.text_input(
        "E-mail",
        key="email_signup"
    )

    password_signup = st.text_input(
        "Senha",
        type="password",
        key="password_signup"
    )

    if st.button("Criar conta"):

        result = sign_up(
            email_signup,
            password_signup
        )

        if result["success"]:

            if result["needs_confirmation"]:

                st.success(
                    "Conta criada! Verifique seu e-mail para confirmar o cadastro."
                )

            else:

                st.success(
                    "Conta criada e autenticada com sucesso!"
                )

        else:

            st.error(result["error"])


# -------------------------
# SESSÃO
# -------------------------

st.divider()

if "user_id" in st.session_state:

    st.write("Usuário autenticado:")
    st.code(st.session_state["user_id"])

    if st.button("Sair"):

        sign_out()

        for key in [
            "access_token",
            "refresh_token",
            "user_id"
        ]:
            st.session_state.pop(key, None)

        st.rerun()