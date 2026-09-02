"""
Temporary manual test page for services/checkin_service.py.

Goal:
Test create/list/latest operations for the simplified Mody check-in.

Real check-ins store only:

- state
- created_at

Run with:

    streamlit run tests/test_checkin_service.py
"""

import os
import sys

sys.path.append(
    os.path.join(
        os.path.dirname(__file__),
        "..",
    )
)

import streamlit as st

from services.auth_service import (
    restore_session,
    sign_in,
    sign_out,
    sign_up,
)

from services.checkin_service import (
    create_checkin,
    get_checkin_by_id,
    get_checkins,
    get_latest_checkin,
)


st.set_page_config(
    page_title="Mody — Teste de Check-ins",
    page_icon="🧪",
)


# =========================================================
# AUTHENTICATION
# =========================================================

if "auth" not in st.session_state:
    st.session_state.auth = None


def is_authenticated() -> bool:
    auth = st.session_state.auth

    if auth is None:
        return False

    ok = restore_session(
        auth["access_token"],
        auth["refresh_token"],
    )

    if not ok:
        st.session_state.auth = None
        return False

    return True


def show_login() -> None:
    st.title("🧪 Teste de Check-ins — login")

    st.caption(
        "Use uma conta de teste já existente "
        "ou crie uma nova."
    )

    login_tab, signup_tab = st.tabs(
        ["Entrar", "Criar conta"]
    )

    with login_tab:

        with st.form("login_form_checkins"):

            email = st.text_input(
                "E-mail",
                key="login_email_checkins",
            )

            password = st.text_input(
                "Senha",
                type="password",
                key="login_password_checkins",
            )

            submitted = st.form_submit_button(
                "Entrar"
            )

        if submitted:

            if not email or not password:

                st.warning(
                    "Preencha e-mail e senha."
                )

            else:

                result = sign_in(
                    email,
                    password,
                )

                if not result["success"]:

                    st.error(
                        result["error"]
                    )

                else:

                    session = result["session"]

                    st.session_state.auth = {
                        "access_token": session.access_token,
                        "refresh_token": session.refresh_token,
                        "user_id": session.user.id,
                        "email": session.user.email,
                    }

                    st.rerun()

    with signup_tab:

        with st.form("signup_form_checkins"):

            email = st.text_input(
                "E-mail",
                key="signup_email_checkins",
            )

            password = st.text_input(
                "Senha",
                type="password",
                key="signup_password_checkins",
            )

            submitted = st.form_submit_button(
                "Criar conta"
            )

        if submitted:

            if not email or not password:

                st.warning(
                    "Preencha e-mail e senha."
                )

            else:

                result = sign_up(
                    email,
                    password,
                )

                if not result["success"]:

                    st.error(
                        result["error"]
                    )

                elif result["needs_confirmation"]:

                    st.success(
                        "Conta criada. Confirme o e-mail e depois "
                        "volte para fazer login."
                    )

                else:

                    session = result["session"]

                    st.session_state.auth = {
                        "access_token": session.access_token,
                        "refresh_token": session.refresh_token,
                        "user_id": session.user.id,
                        "email": session.user.email,
                    }

                    st.rerun()


# =========================================================
# CHECK-IN OPTIONS
# =========================================================

STATE_OPTIONS_PT = {
    "Bem": "well",
    "Sobrecarregada": "overwhelmed",
    "Quero desacelerar": "calm_needed",
}


STATE_LABELS_REVERSE = {
    value: label
    for label, value
    in STATE_OPTIONS_PT.items()
}


def _render_checkin_row(checkin: dict) -> None:
    """
    Render the fields stored by the current check-in model.
    """

    state = checkin.get("state")

    state_label = STATE_LABELS_REVERSE.get(
        state,
        state,
    )

    st.write(
        f"**Estado:** {state_label}"
    )

    st.write(
        f"**Criado em:** {checkin.get('created_at')}"
    )

    st.write(
        f"**id:** `{checkin.get('id')}`"
    )


# =========================================================
# CHECK-IN TEST PAGE
# =========================================================

def show_checkin_tests() -> None:

    auth = st.session_state.auth
    user_id = auth["user_id"]

    col_title, col_logout = st.columns(
        [4, 1]
    )

    with col_title:

        st.title(
            "🧪 Teste de Check-ins"
        )

    with col_logout:

        st.write("")

        if st.button("Sair"):

            sign_out()

            st.session_state.clear()

            st.rerun()

    st.caption(
        f"Conectado como {auth['email']}"
    )

    st.divider()

    # =====================================================
    # CREATE CHECK-IN
    # =====================================================

    st.subheader(
        "Criar check-in"
    )

    with st.form(
        "create_checkin_form"
    ):

        state_label = st.radio(
            "Como você está agora?",
            list(
                STATE_OPTIONS_PT.keys()
            ),
        )

        submitted = st.form_submit_button(
            "Registrar check-in",
            type="primary",
        )

    if submitted:

        result = create_checkin(
            user_id=user_id,
            state=STATE_OPTIONS_PT[state_label],
        )

        if result["success"]:

            st.success(
                "Check-in registrado."
            )

        else:

            st.error(
                result["error"]
            )

    st.divider()

    # =====================================================
    # LATEST CHECK-IN
    # =====================================================

    st.subheader(
        "Último check-in"
    )

    result = get_latest_checkin(
        user_id
    )

    if not result["success"]:

        st.error(
            result["error"]
        )

    elif result["data"] is None:

        st.info(
            "Nenhum check-in registrado ainda."
        )

    else:

        _render_checkin_row(
            result["data"]
        )

    st.divider()

    # =====================================================
    # RECENT CHECK-INS
    # =====================================================

    st.subheader(
        "Check-ins recentes"
    )

    recent_limit = st.number_input(
        "Quantos mostrar",
        min_value=1,
        max_value=50,
        value=10,
        step=1,
    )

    result = get_checkins(
        user_id,
        limit=int(recent_limit),
    )

    if not result["success"]:

        st.error(
            result["error"]
        )

    else:

        checkins = result["data"]

        if not checkins:

            st.info(
                "Nenhum check-in encontrado."
            )

        for checkin in checkins:

            state = checkin.get("state")

            label = STATE_LABELS_REVERSE.get(
                state,
                state,
            )

            with st.expander(
                f"{label} — {checkin.get('created_at')}"
            ):

                _render_checkin_row(
                    checkin
                )


# =========================================================
# ROUTING
# =========================================================

if is_authenticated():

    show_checkin_tests()

else:

    show_login()