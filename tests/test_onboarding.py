"""
Temporary onboarding test page for Mody.

Purpose:
Validate reads and writes to:

- profiles
- personalization_preferences

through `services/onboarding_service.py` before integrating
onboarding into the main application.

Run with:

python -m streamlit run tests/test_onboarding.py
"""

import os
import sys

# Allow imports from the project root.
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

from services.onboarding_service import (
    get_existing_data,
    has_completed_onboarding,
    save_preferences,
    save_profile,
)


st.set_page_config(
    page_title="Mody — Teste de Onboarding",
    page_icon="🧪",
)


# =========================================================
# AUTHENTICATION STATE
# =========================================================

if "auth" not in st.session_state:
    st.session_state.auth = None


def is_authenticated() -> bool:
    """
    Check whether a saved authentication session exists and restore
    it in the Supabase client.
    """
    auth = st.session_state.auth

    if auth is None:
        return False

    session_restored = restore_session(
        auth["access_token"],
        auth["refresh_token"],
    )

    if not session_restored:
        st.session_state.auth = None
        return False

    return True


# =========================================================
# LOGIN PAGE
# =========================================================

def show_login_page():
    """
    Display the temporary authentication interface used only for
    onboarding testing.
    """

    st.title("🧪 Teste de Onboarding — Login")

    st.caption(
        "Use uma conta já criada e confirmada ou crie uma nova conta."
    )

    login_tab, signup_tab = st.tabs(
        ["Entrar", "Criar conta"]
    )

    with login_tab:

        with st.form("test_login_form"):

            email = st.text_input(
                "E-mail",
                key="test_login_email",
            )

            password = st.text_input(
                "Senha",
                type="password",
                key="test_login_password",
            )

            submit_login = st.form_submit_button(
                "Entrar"
            )

        if submit_login:

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

        with st.form("test_signup_form"):

            email = st.text_input(
                "E-mail",
                key="test_signup_email",
            )

            password = st.text_input(
                "Senha",
                type="password",
                key="test_signup_password",
            )

            submit_signup = st.form_submit_button(
                "Criar conta"
            )

        if submit_signup:

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
                        "volte para fazer login nesta página."
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
# UI ↔ DATABASE VALUE MAPPINGS
# =========================================================

SUPPORT_PROFILE_OPTIONS = {
    "TDAH": "adhd",
    "Ansiedade": "anxiety",
    "TDAH e ansiedade": "adhd_anxiety",
    "Nenhum desses": "none",
    "Prefiro não informar": "prefer_not_to_say",
}


SUPPORT_PROFILE_OPTIONS_REVERSE = {
    database_value: ui_label
    for ui_label, database_value
    in SUPPORT_PROFILE_OPTIONS.items()
}


SUPPORT_NEEDS_OPTIONS = {
    "Começar tarefas": "start_tasks",
    "Organizar meu dia": "organize_day",
    "Lembrar compromissos": "remember_commitments",
    "Evitar sobrecarga": "avoid_overload",
    "Reduzir distrações": "reduce_distractions",
    "Gerenciar ansiedade": "manage_anxiety",
    "Criar rotinas": "build_routines",
    "Estimar melhor o tempo": "estimate_time",
}


SUPPORT_NEEDS_OPTIONS_REVERSE = {
    database_value: ui_label
    for ui_label, database_value
    in SUPPORT_NEEDS_OPTIONS.items()
}


# =========================================================
# ONBOARDING PAGE
# =========================================================

def show_onboarding_page():
    """
    Display the temporary onboarding interface.
    """

    auth = st.session_state.auth

    # The user ID always comes from the authenticated session.
    user_id = auth["user_id"]

    # -----------------------------------------------------
    # HEADER
    # -----------------------------------------------------

    title_column, logout_column = st.columns(
        [4, 1]
    )

    with title_column:
        st.title(
            "🧪 Teste de Onboarding"
        )

    with logout_column:

        st.write("")

        if st.button("Sair"):

            sign_out()

            st.session_state.auth = None

            st.rerun()

    st.caption(
        f"Conectado como {auth['email']}"
    )

    # -----------------------------------------------------
    # LOAD EXISTING DATA
    # -----------------------------------------------------

    existing_data = get_existing_data(
        user_id
    )

    existing_profile = (
        existing_data["profile"] or {}
    )

    existing_preferences = (
        existing_data["preferences"] or {}
    )

    if has_completed_onboarding(user_id):

        st.info(
            "Este usuário já possui dados de onboarding. "
            "Os campos foram preenchidos com os valores existentes."
        )

    st.divider()

    # =====================================================
    # SECTION 1 — USER PROFILE
    # =====================================================

    st.subheader(
        "Sobre você"
    )

    display_name = st.text_input(
        "Como podemos te chamar?",
        value=existing_profile.get(
            "display_name"
        )
        or "",
    )

    timezone = st.text_input(
        "Fuso horário",
        value=existing_profile.get(
            "timezone"
        )
        or "Europe/Lisbon",
    )

    st.divider()

    # =====================================================
    # SECTION 2 — PERSONALIZATION
    # =====================================================

    st.subheader(
        "Personalização"
    )

    st.write(
        "Existe algo que você gostaria que o Mody "
        "levasse em consideração ao organizar seu dia?"
    )

    st.caption(
        "Essa informação é opcional e serve apenas para "
        "personalizar sua experiência. "
        "O Mody não realiza diagnósticos."
    )

    current_support_profile = (
        existing_preferences.get(
            "support_profile"
        )
    )

    profile_options = list(
        SUPPORT_PROFILE_OPTIONS.keys()
    )

    # No option selected by default.
    default_profile_index = None

    if (
        current_support_profile
        and current_support_profile
        in SUPPORT_PROFILE_OPTIONS_REVERSE
    ):

        current_ui_value = (
            SUPPORT_PROFILE_OPTIONS_REVERSE[
                current_support_profile
            ]
        )

        default_profile_index = (
            profile_options.index(
                current_ui_value
            )
        )

    selected_profile_label = st.radio(
        "Selecione uma opção:",
        profile_options,
        index=default_profile_index,
        label_visibility="collapsed",
    )

    if selected_profile_label:

        support_profile = (
            SUPPORT_PROFILE_OPTIONS[
                selected_profile_label
            ]
        )

    else:

        support_profile = None

    st.divider()

    # =====================================================
    # SECTION 3 — SUPPORT NEEDS
    # =====================================================

    st.subheader(
        "Com o que você mais gostaria de ajuda no dia a dia?"
    )

    current_support_needs = (
        existing_preferences.get(
            "support_needs"
        )
        or []
    )

    default_support_needs = [
        SUPPORT_NEEDS_OPTIONS_REVERSE[value]
        for value in current_support_needs
        if value in SUPPORT_NEEDS_OPTIONS_REVERSE
    ]

    selected_support_labels = st.multiselect(
        "Selecione quantas fizerem sentido:",
        list(
            SUPPORT_NEEDS_OPTIONS.keys()
        ),
        default=default_support_needs,
        label_visibility="collapsed",
    )

    support_needs = [
        SUPPORT_NEEDS_OPTIONS[label]
        for label in selected_support_labels
    ]

    st.divider()

    # =====================================================
    # SAVE ONBOARDING
    # =====================================================

    if st.button(
        "Concluir",
        type="primary",
    ):

        profile_result = save_profile(
            user_id,
            display_name,
            timezone,
        )

        preferences_result = save_preferences(
            user_id,
            support_profile,
            support_needs,
        )

        if not profile_result["success"]:

            st.error(
                profile_result["error"]
            )

        elif not preferences_result["success"]:

            st.error(
                preferences_result["error"]
            )

        else:

            st.success(
                "Tudo pronto! O Mody já pode começar "
                "a adaptar sua experiência."
            )

    # =====================================================
    # DEVELOPMENT-ONLY DATABASE CHECK
    # =====================================================

    with st.expander(
        "🔧 Dev only — dados salvos no Supabase"
    ):

        updated_data = get_existing_data(
            user_id
        )

        st.write(
            "**profiles**"
        )

        st.json(
            updated_data["profile"]
            or {}
        )

        st.write(
            "**personalization_preferences**"
        )

        st.json(
            updated_data["preferences"]
            or {}
        )

        st.caption(
            "Tokens e senhas não são exibidos."
        )


# =========================================================
# ROUTING
# =========================================================

if is_authenticated():

    show_onboarding_page()

else:

    show_login_page()