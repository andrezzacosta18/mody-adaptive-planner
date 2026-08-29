"""
Temporary manual test page for services/checkin_service.py.

Goal: exercise create/list/latest and the user-isolation (RLS) check
via get_checkin_by_id, without touching app.py yet.

How to run:
    streamlit run tests/test_checkin_service.py
"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st

from services.auth_service import restore_session, sign_in, sign_out, sign_up
from services.checkin_service import (
    create_checkin,
    get_checkin_by_id,
    get_checkins,
    get_latest_checkin,
)

st.set_page_config(page_title="Mody — Teste de Check-ins", page_icon="🧪")


# =========================================================
# Authentication (minimal copy, same pattern as
# tests/test_task_service.py, just so this page can run in
# isolation)
# =========================================================
if "auth" not in st.session_state:
    st.session_state.auth = None


def is_authenticated() -> bool:
    auth = st.session_state.auth
    if auth is None:
        return False
    ok = restore_session(auth["access_token"], auth["refresh_token"])
    if not ok:
        st.session_state.auth = None
        return False
    return True


def show_login() -> None:
    st.title("🧪 Teste de Check-ins — login")
    st.caption(
        "Use uma conta já existente, ou crie duas para testar o "
        "isolamento entre usuários (A e B)."
    )

    login_tab, signup_tab = st.tabs(["Entrar", "Criar conta"])

    with login_tab:
        with st.form("login_form_checkins"):
            email = st.text_input("E-mail", key="login_email_checkins")
            password = st.text_input(
                "Senha", type="password", key="login_password_checkins"
            )
            submitted = st.form_submit_button("Entrar")

        if submitted:
            if not email or not password:
                st.warning("Preencha e-mail e senha.")
            else:
                result = sign_in(email, password)
                if not result["success"]:
                    st.error(result["error"])
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
            email = st.text_input("E-mail", key="signup_email_checkins")
            password = st.text_input(
                "Senha", type="password", key="signup_password_checkins"
            )
            submitted = st.form_submit_button("Criar conta")

        if submitted:
            if not email or not password:
                st.warning("Preencha e-mail e senha.")
            else:
                result = sign_up(email, password)
                if not result["success"]:
                    st.error(result["error"])
                elif result["needs_confirmation"]:
                    st.success(
                        "Conta criada. Confirme o e-mail e depois volte "
                        "para fazer login."
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


STATE_OPTIONS_PT = {
    "Bem": "well",
    "Sobrecarregada": "overwhelmed",
    "Preciso me acalmar": "calm_needed",
}
STATE_LABELS_REVERSE = {v: k for k, v in STATE_OPTIONS_PT.items()}

# Descriptive labels so the user understands each number without
# needing an external explanation. The leading digit is what gets
# parsed back into the integer sent to create_checkin() — see
# _level_from_label() below.
ENERGY_LEVEL_OPTIONS = [
    "",
    "1 — Muito baixa",
    "2 — Baixa",
    "3 — Média",
    "4 — Alta",
    "5 — Muito alta",
]
ENERGY_LEVEL_HELP = "Indica quanta disposição e energia você sente neste momento."

ANXIETY_LEVEL_OPTIONS = [
    "",
    "1 — Muito baixa",
    "2 — Baixa",
    "3 — Moderada",
    "4 — Alta",
    "5 — Muito alta",
]
ANXIETY_LEVEL_HELP = "Indica o nível de ansiedade ou tensão que você sente neste momento."

FOCUS_LEVEL_OPTIONS = [
    "",
    "1 — Muito baixo",
    "2 — Baixo",
    "3 — Médio",
    "4 — Alto",
    "5 — Muito alto",
]
FOCUS_LEVEL_HELP = "Indica o quanto você consegue se concentrar neste momento."


def _level_from_label(label: str) -> int | None:
    """Converts a descriptive option like '4 — Alta' into the
    integer 4 for create_checkin(). Empty string (no answer) maps to
    None. Reading just the first character is safe here because the
    scale is fixed at 1-5, so the leading digit is always a single
    character."""
    return int(label[0]) if label else None


def _render_checkin_row(checkin: dict) -> None:
    """Renders one check-in's fields as plain text (st.write escapes
    automatically, no manual HTML involved here)."""
    state_label = STATE_LABELS_REVERSE.get(checkin.get("state"), checkin.get("state"))
    st.write(f"**Estado:** {state_label}")
    st.write(f"**Energia:** {checkin.get('energy_level') or '—'}")
    st.write(f"**Ansiedade:** {checkin.get('anxiety_level') or '—'}")
    st.write(f"**Foco:** {checkin.get('focus_level') or '—'}")
    st.write(f"**Criado em:** {checkin.get('created_at')}")
    st.write(f"**id:** `{checkin.get('id')}`")


def show_checkin_tests() -> None:
    auth = st.session_state.auth
    user_id = auth["user_id"]  # always from the authenticated session

    col_title, col_logout = st.columns([4, 1])
    with col_title:
        st.title("🧪 Teste de Check-ins")
    with col_logout:
        st.write("")
        if st.button("Sair"):
            sign_out()
            st.session_state.clear()
            st.rerun()

    st.caption(f"Conectado como {auth['email']} · user_id: {user_id}")

    st.divider()

    # ---- B. Create a check-in ----
    st.subheader("Criar check-in")
    with st.form("create_checkin_form"):
        state_label = st.radio("Como você está agora?", list(STATE_OPTIONS_PT.keys()))

        col1, col2, col3 = st.columns(3)
        with col1:
            energy_label = st.selectbox(
                "Energia (opcional)",
                ENERGY_LEVEL_OPTIONS,
                key="energy_select",
                help=ENERGY_LEVEL_HELP,
            )
        with col2:
            anxiety_label = st.selectbox(
                "Ansiedade (opcional)",
                ANXIETY_LEVEL_OPTIONS,
                key="anxiety_select",
                help=ANXIETY_LEVEL_HELP,
            )
        with col3:
            focus_label = st.selectbox(
                "Foco (opcional)",
                FOCUS_LEVEL_OPTIONS,
                key="focus_select",
                help=FOCUS_LEVEL_HELP,
            )

        submitted = st.form_submit_button("Registrar check-in", type="primary")

    if submitted:
        result = create_checkin(
            user_id=user_id,
            state=STATE_OPTIONS_PT[state_label],
            energy_level=_level_from_label(energy_label),
            anxiety_level=_level_from_label(anxiety_label),
            focus_level=_level_from_label(focus_label),
        )
        if result["success"]:
            st.success("Check-in registrado.")
        else:
            st.error(result["error"])

    st.divider()

    # ---- C. Latest check-in ----
    st.subheader("Último check-in")
    result = get_latest_checkin(user_id)
    if not result["success"]:
        st.error(result["error"])
    elif result["data"] is None:
        st.info("Nenhum check-in registrado ainda.")
    else:
        _render_checkin_row(result["data"])

    st.divider()

    # ---- D. Recent check-ins ----
    st.subheader("Check-ins recentes")
    recent_limit = st.number_input(
        "Quantos mostrar", min_value=1, max_value=50, value=10, step=1
    )
    result = get_checkins(user_id, limit=int(recent_limit))
    if not result["success"]:
        st.error(result["error"])
    else:
        checkins = result["data"]
        if not checkins:
            st.info("Nenhum check-in encontrado.")
        for checkin in checkins:
            with st.expander(
                f"{STATE_LABELS_REVERSE.get(checkin['state'], checkin['state'])} "
                f"— {checkin.get('created_at')}"
            ):
                _render_checkin_row(checkin)

    st.divider()

    # ---- E. RLS / user isolation test ----
    st.subheader("Buscar check-in de outro usuário (teste de isolamento)")
    st.caption(
        "Copie o id de um check-in criado pelo Usuário A, faça login "
        "como Usuário B, e cole esse id aqui — o resultado deve ser "
        '"Check-in não encontrado.", nunca os dados de A.'
    )
    checkin_id_input = st.text_input("Check-in id")
    if st.button("Buscar"):
        if not checkin_id_input:
            st.warning("Informe um id.")
        else:
            result = get_checkin_by_id(user_id, checkin_id_input)
            if not result["success"]:
                st.error(result["error"])
            elif result["data"] is None:
                st.info("Check-in não encontrado.")
            else:
                _render_checkin_row(result["data"])


# =========================================================
# Routing
# =========================================================
if is_authenticated():
    show_checkin_tests()
else:
    show_login()