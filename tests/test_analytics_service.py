"""Manual test page for services/analytics_service.py.

Temporary Streamlit page to exercise the analytics service against real
data for the authenticated user. It follows the same authentication
pattern as tests/test_task_service.py and tests/test_checkin_service.py:

- the user signs in with e-mail and password
- the session is restored on every rerun so RLS can resolve auth.uid()
- user_id always comes from the session and is never editable in the UI
- auth tokens and passwords are never displayed

Run with:

    streamlit run tests/test_analytics_service.py
"""

import streamlit as st

from services.auth_service import restore_session, sign_in, sign_out
from services.analytics_service import (
    get_task_metrics,
    get_checkin_metrics,
    get_checkin_state_distribution,
    get_checkin_timeseries,
    get_overview_metrics,
)

st.set_page_config(page_title="Teste — Analytics Service", page_icon="🧪")


# =========================================================
# Auth state (same shape as app.py: only what's needed to
# restore the session; never the password)
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
    st.title("Teste — Analytics Service")
    st.caption("Entre para testar o serviço de análise com seus dados reais.")

    with st.form("login_form"):
        email = st.text_input("E-mail")
        password = st.text_input("Senha", type="password")
        submitted = st.form_submit_button("Entrar", use_container_width=True)

    if submitted:
        if not email or not password:
            st.warning("Preencha e-mail e senha.")
            return
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


def _format_average(value) -> str:
    """Show 'Sem dados' when an average is None, instead of a misleading 0."""
    return "Sem dados" if value is None else str(value)


def show_tests(user_id: str) -> None:
    col_title, col_logout = st.columns([4, 1])
    with col_title:
        st.title("Teste — Analytics Service")
    with col_logout:
        st.write("")
        if st.button("Sair", use_container_width=True):
            sign_out()
            st.session_state.clear()
            st.rerun()

    st.caption(f"Sessão ativa: {st.session_state.auth['email']}")

    st.divider()

    # ---------------------------------------------------------
    # A. Task metrics
    # ---------------------------------------------------------
    st.header("A. Métricas de tarefas")
    task_result = get_task_metrics(user_id)
    if not task_result["success"]:
        st.error(task_result["error"])
    else:
        data = task_result["data"]
        st.write(f"Total de tarefas: {data['total_tasks']}")
        st.write(f"Pendentes: {data['pending_tasks']}")
        st.write(f"Concluídas: {data['completed_tasks']}")
        st.write(f"Em andamento: {data['in_progress_tasks']}")
        st.write(f"Bloqueadas: {data['blocked_tasks']}")
        st.write(f"Taxa de conclusão: {data['completion_rate']}%")

    st.divider()

    # ---------------------------------------------------------
    # B. Check-in metrics
    # ---------------------------------------------------------
    st.header("B. Métricas de check-ins")
    checkin_result = get_checkin_metrics(user_id)
    if not checkin_result["success"]:
        st.error(checkin_result["error"])
    else:
        data = checkin_result["data"]
        st.write(f"Total de check-ins: {data['total_checkins']}")
        st.write(f"Bem: {data['well_count']}")
        st.write(f"Sobrecarregada: {data['overwhelmed_count']}")
        st.write(f"Preciso me acalmar: {data['calm_needed_count']}")
        st.write(f"Média de energia: {_format_average(data['average_energy'])}")
        st.write(f"Média de ansiedade: {_format_average(data['average_anxiety'])}")
        st.write(f"Média de foco: {_format_average(data['average_focus'])}")

    st.divider()

    # ---------------------------------------------------------
    # C. Check-in state distribution
    # ---------------------------------------------------------
    st.header("C. Distribuição por estado")
    dist_result = get_checkin_state_distribution(user_id)
    if not dist_result["success"]:
        st.error(dist_result["error"])
    else:
        st.table(dist_result["data"])

    st.divider()

    # ---------------------------------------------------------
    # D. Check-in time series (chronological)
    # ---------------------------------------------------------
    st.header("D. Série temporal (cronológica)")
    limit = st.slider(
        "Quantidade de check-ins mais recentes",
        min_value=1,
        max_value=50,
        value=10,
    )
    ts_result = get_checkin_timeseries(user_id, limit=limit)
    if not ts_result["success"]:
        st.error(ts_result["error"])
    else:
        rows = ts_result["data"]
        if not rows:
            st.info("Nenhum check-in registrado ainda.")
        else:
            st.table(rows)

    st.divider()

    # ---------------------------------------------------------
    # Overview (combined) — convenience aggregate
    # ---------------------------------------------------------
    st.header("Overview (combinado)")
    overview_result = get_overview_metrics(user_id)
    if not overview_result["success"]:
        st.error(overview_result["error"])
    else:
        st.json(overview_result["data"])


# =========================================================
# Routing
# =========================================================
if not is_authenticated():
    show_login()
else:
    current_user_id = st.session_state.auth["user_id"]  # always from the session
    show_tests(current_user_id)