import html

import pandas as pd
import streamlit as st

from services.auth_service import restore_session, sign_in, sign_out, sign_up
from services.onboarding_service import (
    get_existing_data,
    has_completed_onboarding,
    save_preferences,
    save_profile,
)
from services.checkin_service import create_checkin
from services.task_service import complete_task, get_tasks
from services.analytics_service import (
    get_task_metrics,
    get_checkin_metrics,
    get_checkin_state_distribution,
    get_checkin_timeseries,
)

# --- Basic page configuration ---
st.set_page_config(
    page_title="Mody — Hoje",
    page_icon="🌿",
    layout="centered",
)


def load_css(path: str) -> None:
    """Reads the CSS file and injects it into the page."""
    with open(path, "r", encoding="utf-8") as f:
        css = f.read()
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


load_css("styles/style.css")


# =========================================================
# Portuguese (UI) <-> internal database value mappings
#
# Kept here (not in onboarding_service.py) because this is
# purely a presentation concern: the service only ever deals
# with the internal values already validated by the database
# constraints.
# =========================================================
SUPPORT_PROFILE_OPTIONS = {
    "TDAH": "adhd",
    "Ansiedade": "anxiety",
    "TDAH e ansiedade": "adhd_anxiety",
    "Nenhum desses": "none",
    "Prefiro não informar": "prefer_not_to_say",
}
SUPPORT_PROFILE_REVERSE = {
    v: k for k, v in SUPPORT_PROFILE_OPTIONS.items()
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
SUPPORT_NEEDS_REVERSE = {v: k for k, v in SUPPORT_NEEDS_OPTIONS.items()}


# =========================================================
# Auth state
#
# st.session_state.auth holds only what's needed to restore
# the session across Streamlit reruns: access_token,
# refresh_token, user_id and email. NEVER the password.
# =========================================================
if "auth" not in st.session_state:
    st.session_state.auth = None


def is_authenticated() -> bool:
    """
    Checks whether a session is stored and, if so, restores it
    on the session-specific Supabase client (needed on every
    rerun so that RLS policies can resolve auth.uid() correctly).

    If the token is invalid/expired, clears local auth state and
    treats the user as logged out.
    """
    auth = st.session_state.auth
    if auth is None:
        return False

    ok = restore_session(auth["access_token"], auth["refresh_token"])
    if not ok:
        st.session_state.auth = None
        return False

    return True


def start_session(session) -> None:
    """Stores the minimum session data needed after a successful
    sign-in or sign-up. Called only with a Supabase `session`
    object that already has a valid user (never with manually
    entered data)."""
    st.session_state.auth = {
        "access_token": session.access_token,
        "refresh_token": session.refresh_token,
        "user_id": session.user.id,
        "email": session.user.email,
    }


# =========================================================
# Screen: Login / Sign up
# =========================================================
def show_login() -> None:
    st.title("Mody")
    st.caption("Organização, gestão de tempo e autorregulação.")

    login_tab, signup_tab = st.tabs(["Entrar", "Criar conta"])

    with login_tab:
        with st.form("login_form"):
            email = st.text_input("E-mail", key="login_email")
            password = st.text_input("Senha", type="password", key="login_password")
            submitted = st.form_submit_button("Entrar", use_container_width=True)

        if submitted:
            if not email or not password:
                st.warning("Preencha e-mail e senha.")
            else:
                result = sign_in(email, password)
                if not result["success"]:
                    st.error(result["error"])
                else:
                    start_session(result["session"])
                    st.rerun()

    with signup_tab:
        with st.form("signup_form"):
            email = st.text_input("E-mail", key="signup_email")
            password = st.text_input("Senha", type="password", key="signup_password")
            submitted = st.form_submit_button("Criar conta", use_container_width=True)

        if submitted:
            if not email or not password:
                st.warning("Preencha e-mail e senha.")
            else:
                result = sign_up(email, password)
                if not result["success"]:
                    st.error(result["error"])
                elif result["needs_confirmation"]:
                    st.success(
                        "Conta criada. Verifique seu e-mail para confirmar "
                        "o cadastro antes de entrar."
                    )
                else:
                    # Project configured without requiring email
                    # confirmation: a session is already available.
                    start_session(result["session"])
                    st.rerun()


# =========================================================
# Screen: Onboarding
# =========================================================
def show_onboarding(user_id: str) -> None:
    st.title("Vamos te conhecer melhor")
    st.caption(
        "Só o essencial para o Mody começar a se adaptar a você. "
        "Tudo aqui pode ser ajustado depois."
    )

    existing_data = get_existing_data(user_id)
    existing_profile = existing_data["profile"] or {}
    existing_preferences = existing_data["preferences"] or {}

    st.divider()

    # ---- Section 1: Profile ----
    st.subheader("Como você gostaria de ser chamado(a)?")
    display_name = st.text_input(
        "Nome",
        value=existing_profile.get("display_name") or "",
        label_visibility="collapsed",
        placeholder="Seu nome ou apelido",
    )

    st.subheader("Qual é o seu fuso horário?")
    timezone = st.text_input(
        "Fuso horário",
        value=existing_profile.get("timezone") or "Europe/Lisbon",
        label_visibility="collapsed",
    )

    st.divider()

    # ---- Section 2: Personalization (optional) ----
    st.subheader(
        "Existe algo que você gostaria que o Mody levasse em "
        "consideração ao organizar seu dia?"
    )
    st.caption(
        "Essa informação é opcional e serve apenas para personalizar "
        "sua experiência. O Mody não realiza diagnósticos."
    )

    current_profile_value = existing_preferences.get("support_profile")
    profile_labels = list(SUPPORT_PROFILE_OPTIONS.keys())
    default_index = None
    if current_profile_value and current_profile_value in SUPPORT_PROFILE_REVERSE:
        default_index = profile_labels.index(
            SUPPORT_PROFILE_REVERSE[current_profile_value]
        )

    chosen_profile_label = st.radio(
        "Selecione uma opção",
        profile_labels,
        index=default_index,
        label_visibility="collapsed",
    )
    # None enquanto o usuário não clicar em nenhuma opção: ausência de
    # resposta não deve ser tratada como "adhd" (primeira opção da
    # lista) nem como qualquer outro valor. Só vira um valor real
    # quando o usuário escolhe ativamente uma opção — inclusive
    # "Prefiro não informar", que é uma resposta diferente de None.
    support_profile = (
        SUPPORT_PROFILE_OPTIONS[chosen_profile_label]
        if chosen_profile_label is not None
        else None
    )

    st.divider()

    # ---- Section 3: Support needs ----
    st.subheader("Com o que você mais gostaria de ajuda no dia a dia?")

    current_needs_values = existing_preferences.get("support_needs") or []
    default_needs_labels = [
        SUPPORT_NEEDS_REVERSE[v]
        for v in current_needs_values
        if v in SUPPORT_NEEDS_REVERSE
    ]

    chosen_needs_labels = st.multiselect(
        "Selecione quantas fizerem sentido",
        list(SUPPORT_NEEDS_OPTIONS.keys()),
        default=default_needs_labels,
        label_visibility="collapsed",
    )
    support_needs = [SUPPORT_NEEDS_OPTIONS[label] for label in chosen_needs_labels]

    st.divider()

    if st.session_state.get("onboarding_just_completed"):
        st.success("Tudo pronto! O Mody já pode começar a adaptar sua experiência.")
        if st.button("Ir para o Hoje →", use_container_width=True):
            st.session_state.onboarding_just_completed = False
            st.rerun()
        return

    if st.button("Concluir", type="primary", use_container_width=True):
        profile_result = save_profile(user_id, display_name, timezone)
        preferences_result = save_preferences(
            user_id, support_profile, support_needs
        )

        if not profile_result["success"]:
            st.error(profile_result["error"])
        elif not preferences_result["success"]:
            st.error(preferences_result["error"])
        else:
            st.session_state.onboarding_just_completed = True
            st.rerun()


# =========================================================
# Screen: Home
#
# The current task card now shows a real pending task from
# services/task_service.py. The "next appointment" card is
# still mock data — real calendar integration is a later phase.
# =========================================================
PRIORITY_LABELS_PT = {"low": "Baixa", "medium": "Média", "high": "Alta"}


def _render_current_task_card(task: dict | None) -> str:
    """Builds the HTML for the 'Tarefa atual' card: either the
    current pending task's details, or a friendly empty-state
    message when there are none. Uses inline styles for the
    secondary detail lines to avoid adding new classes to
    styles/style.css.

    Security: task fields (title, description, priority, due_date)
    come from the database and are ultimately user-controlled input
    (the person types the title/description themselves). Since this
    HTML is rendered with unsafe_allow_html=True, every such value
    MUST be escaped with html.escape() before interpolation, or a
    task title/description containing HTML/JS would be rendered as
    live markup instead of plain text (stored XSS).
    """
    if task is None:
        return (
            '<div class="card">'
            '<div class="card-label">Tarefa atual</div>'
            '<div class="card-value">Nenhuma tarefa pendente por enquanto.</div>'
            "</div>"
        )

    detail_style = "font-size:0.85rem;color:#6b7d76;margin-top:0.3rem;"
    details = []

    if task.get("description"):
        safe_description = html.escape(str(task["description"]))
        details.append(f'<div style="{detail_style}">{safe_description}</div>')
    if task.get("priority"):
        priority_label = PRIORITY_LABELS_PT.get(task["priority"], task["priority"])
        safe_priority_label = html.escape(str(priority_label))
        details.append(f'<div style="{detail_style}">Prioridade: {safe_priority_label}</div>')
    if task.get("estimated_minutes"):
        # estimated_minutes is a validated positive integer (see
        # task_service.py), not free text, but str() + escape kept
        # for consistency rather than trusting a raw interpolation.
        safe_minutes = html.escape(str(task["estimated_minutes"]))
        details.append(
            f'<div style="{detail_style}">Tempo estimado: {safe_minutes} min</div>'
        )
    if task.get("due_date"):
        safe_due_date = html.escape(str(task["due_date"]))
        details.append(f'<div style="{detail_style}">Vence em: {safe_due_date}</div>')

    safe_title = html.escape(str(task["title"]))

    return (
        '<div class="card">'
        '<div class="card-label">Tarefa atual</div>'
        f'<div class="card-value">{safe_title}</div>'
        + "".join(details)
        + "</div>"
    )


def show_home(user_id: str, display_name: str | None) -> None:
    col_title, col_logout = st.columns([4, 1])
    with col_title:
        st.title("Hoje")
    with col_logout:
        st.write("")
        if st.button("Sair", use_container_width=True):
            sign_out()
            st.session_state.clear()
            st.rerun()

    greeting_name = display_name or "você"
    st.caption(f"Olá, {greeting_name}")

    # --- Current task: real pending task from task_service.py ---
    tasks_result = get_tasks(user_id, status="pending")
    if not tasks_result["success"]:
        st.error(tasks_result["error"])
        current_task = None
    else:
        pending_tasks = tasks_result["data"]
        current_task = pending_tasks[0] if pending_tasks else None

    # --- Next appointment: still mock data (calendar is a later phase) ---
    next_appointment = "Consulta médica às 15h00"

    if "checkin_state" not in st.session_state:
        st.session_state.checkin_state = None
    if "checkin_just_saved" not in st.session_state:
        st.session_state.checkin_just_saved = False
    if "action_message" not in st.session_state:
        st.session_state.action_message = None
    if "task_just_completed" not in st.session_state:
        st.session_state.task_just_completed = False

    st.write("**Como você está agora?**")

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🟢 Bem", use_container_width=True):
            result = create_checkin(user_id=user_id, state="well")
            if result["success"]:
                st.session_state.checkin_state = "well"
                st.session_state.checkin_just_saved = True
            else:
                st.error(result["error"])
    with col2:
        if st.button("🟡 Sobrecarregada", use_container_width=True):
            result = create_checkin(user_id=user_id, state="overwhelmed")
            if result["success"]:
                st.session_state.checkin_state = "overwhelmed"
                st.session_state.checkin_just_saved = True
            else:
                st.error(result["error"])
    with col3:
        if st.button("🔴 Preciso me acalmar", use_container_width=True):
            result = create_checkin(user_id=user_id, state="calm_needed")
            if result["success"]:
                st.session_state.checkin_state = "calm_needed"
                st.session_state.checkin_just_saved = True
            else:
                st.error(result["error"])

    if st.session_state.checkin_just_saved:
        st.success("Check-in registrado.")
        st.session_state.checkin_just_saved = False

    if st.session_state.checkin_state == "well":
        st.markdown('<div class="resposta-suave">Que bom. Vamos seguir com o seu dia.</div>', unsafe_allow_html=True)
    elif st.session_state.checkin_state == "overwhelmed":
        st.markdown('<div class="resposta-suave">Entendido. Vamos manter a tela mais simples possível.</div>', unsafe_allow_html=True)
    elif st.session_state.checkin_state == "calm_needed":
        st.markdown('<div class="resposta-suave">Tudo bem. O Modo Acalmar ainda será construído — por enquanto, respire.</div>', unsafe_allow_html=True)

    st.write("")

    if st.session_state.task_just_completed:
        st.success("Tarefa concluída! 🎉")
        st.session_state.task_just_completed = False

    st.markdown(_render_current_task_card(current_task), unsafe_allow_html=True)

    if current_task is not None:
        if st.button("Concluir", key="complete_current_task"):
            result = complete_task(user_id, current_task["id"])
            if result["success"]:
                st.session_state.task_just_completed = True
                st.rerun()
            else:
                st.error(result["error"])

    st.markdown(
        f"""
        <div class="card">
            <div class="card-label">Próximo compromisso</div>
            <div class="card-value">{next_appointment}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        if st.button("▶️ Começar", use_container_width=True):
            st.session_state.action_message = "start"
    with col_b:
        if st.button("🚫 Não consigo começar", use_container_width=True):
            st.session_state.action_message = "cant_start"
    with col_c:
        if st.button("🌬️ Preciso me acalmar", use_container_width=True):
            st.session_state.action_message = "calm_mode"

    if st.session_state.action_message == "start":
        st.markdown('<div class="resposta-suave">Ótimo — a lógica de iniciar a tarefa será construída em uma próxima etapa.</div>', unsafe_allow_html=True)
    elif st.session_state.action_message == "cant_start":
        st.markdown('<div class="resposta-suave">Sem problema. O fluxo "Não consigo começar" ainda será construído.</div>', unsafe_allow_html=True)
    elif st.session_state.action_message == "calm_mode":
        st.markdown('<div class="resposta-suave">O Modo Acalmar ainda será construído nas próximas etapas.</div>', unsafe_allow_html=True)


# =========================================================
# Screen: Overview / Dashboard ("Visão geral")
#
# Read-only screen built entirely from services/analytics_service.py.
# app.py never computes metrics itself and never touches Supabase
# directly for analytics. Each section calls exactly one analytics
# function and checks its own "success" flag, so a single failing
# call only breaks its own section — the others still render.
#
# user_id is always the authenticated session's id (passed in by the
# router); this screen never lets it be edited.
# =========================================================
CHECKIN_STATE_LABELS_PT = {
    "well": "Bem",
    "overwhelmed": "Sobrecarregada",
    "calm_needed": "Preciso me acalmar",
}


def _format_average(value) -> str:
    """Check-in averages can be None when there is no numeric data.
    Show 'Sem dados' instead of a misleading 0, and never interpret
    the number (no "energia baixa" etc.) — descriptive only."""
    return "Sem dados" if value is None else str(value)


def show_overview(user_id: str, display_name: str | None) -> None:
    st.title("Visão geral")
    greeting_name = display_name or "você"
    st.caption(f"Um resumo do seu progresso, {greeting_name}.")

    # ---- Section 1: Task KPIs ----
    st.subheader("Tarefas")
    task_result = get_task_metrics(user_id)
    if not task_result["success"]:
        st.error(task_result["error"])
    else:
        task_data = task_result["data"]
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total de tarefas", task_data["total_tasks"])
        col2.metric("Pendentes", task_data["pending_tasks"])
        col3.metric("Concluídas", task_data["completed_tasks"])
        col4.metric("Taxa de conclusão", f"{task_data['completion_rate']}%")
        if task_data["total_tasks"] == 0:
            st.info("Ainda não há tarefas registradas.")

    st.divider()

    # ---- Section 2: Check-in KPIs ----
    st.subheader("Check-ins")
    checkin_result = get_checkin_metrics(user_id)
    if not checkin_result["success"]:
        st.error(checkin_result["error"])
    else:
        checkin_data = checkin_result["data"]
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total de check-ins", checkin_data["total_checkins"])
        col2.metric("Energia média", _format_average(checkin_data["average_energy"]))
        col3.metric("Ansiedade média", _format_average(checkin_data["average_anxiety"]))
        col4.metric("Foco médio", _format_average(checkin_data["average_focus"]))
        if checkin_data["total_checkins"] == 0:
            st.info("Ainda não há check-ins registrados.")

    st.divider()

    # ---- Section 3: Check-in distribution (bar chart) ----
    st.subheader("Distribuição dos check-ins")
    distribution_result = get_checkin_state_distribution(user_id)
    if not distribution_result["success"]:
        st.error(distribution_result["error"])
    else:
        distribution = distribution_result["data"]
        total_checkins = sum(item["count"] for item in distribution)
        if total_checkins == 0:
            st.info("Ainda não há check-ins registrados.")
        else:
            # pandas is used ONLY to shape data for the native chart, so the
            # x-axis shows Portuguese labels instead of internal state names.
            distribution_df = pd.DataFrame(
                {
                    "Estado": [
                        CHECKIN_STATE_LABELS_PT.get(item["state"], item["state"])
                        for item in distribution
                    ],
                    "Check-ins": [item["count"] for item in distribution],
                }
            )
            st.bar_chart(distribution_df, x="Estado", y="Check-ins")

    st.divider()

    # ---- Section 4: Recent check-in evolution (line chart) ----
    st.subheader("Evolução recente dos check-ins")
    timeseries_result = get_checkin_timeseries(user_id, limit=10)
    if not timeseries_result["success"]:
        st.error(timeseries_result["error"])
    else:
        timeseries = timeseries_result["data"]
        numeric_columns = ["energy_level", "anxiety_level", "focus_level"]

        # "Enough data" means at least one non-None numeric value across the
        # recent check-ins. None is never coerced to zero.
        has_numeric_data = any(
            row.get(column) is not None
            for row in timeseries
            for column in numeric_columns
        )

        if not timeseries or not has_numeric_data:
            st.info("Ainda não há dados suficientes para mostrar a evolução.")
        else:
            # pandas ONLY prepares chart data here — no analytics is computed.
            # Missing values become NaN (not 0), which st.line_chart renders
            # as gaps in the line rather than dropping the point to zero.
            evolution_df = pd.DataFrame(timeseries)
            evolution_df["created_at"] = pd.to_datetime(evolution_df["created_at"])
            evolution_df = evolution_df.rename(
                columns={
                    "energy_level": "Energia",
                    "anxiety_level": "Ansiedade",
                    "focus_level": "Foco",
                }
            )
            st.line_chart(
                evolution_df,
                x="created_at",
                y=["Energia", "Ansiedade", "Foco"],
            )


# =========================================================
# Routing
# =========================================================
if not is_authenticated():
    show_login()
else:
    auth = st.session_state.auth
    current_user_id = auth["user_id"]  # always from the authenticated session

    if not has_completed_onboarding(current_user_id):
        show_onboarding(current_user_id)
    else:
        profile = get_existing_data(current_user_id)["profile"] or {}
        display_name = profile.get("display_name")

        # Streamlit-native navigation between the two authenticated screens.
        # Login and onboarding intentionally have no sidebar nav.
        page = st.sidebar.radio("Navegação", ("Hoje", "Visão geral"))

        if page == "Hoje":
            show_home(current_user_id, display_name)
        else:
            show_overview(current_user_id, display_name)