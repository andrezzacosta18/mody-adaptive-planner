import html
import datetime

import pandas as pd
import streamlit as st

from services.auth_service import restore_session, sign_in, sign_out, sign_up
from services.onboarding_service import (
    get_existing_data,
    has_completed_onboarding,
    save_preferences,
    save_profile,
)
from services.checkin_service import create_checkin, get_checkins
from services.task_service import complete_task, get_tasks
from services.appointment_service import (
    create_appointment,
    delete_appointment,
    get_appointments,
    get_next_appointment,
)
from services.analytics_service import (
    get_task_metrics,
    get_checkin_metrics,
    get_checkin_state_distribution,
    get_checkin_timeseries,
)
from services.adaptive_service import get_adaptive_suggestion
from services.synthetic_analytics_service import (
    get_overall_task_metrics as get_synthetic_overall_task_metrics,
    get_completion_by_priority as get_synthetic_completion_by_priority,
    get_completion_by_weekday as get_synthetic_completion_by_weekday,
    get_checkin_state_distribution as get_synthetic_checkin_state_distribution,
    get_checkin_timeseries as get_synthetic_checkin_timeseries,
    get_completion_by_energy as get_synthetic_completion_by_energy,
    get_completion_by_focus as get_synthetic_completion_by_focus,
    get_completion_by_overwhelmed_state as get_synthetic_completion_by_overwhelmed_state,
    get_weekday_vs_weekend_metrics as get_synthetic_weekday_vs_weekend_metrics,
)

# =========================================================
# Page config
# =========================================================
st.set_page_config(
    page_title="Mody — Hoje",
    page_icon="assets/mody_icon.png",
    layout="wide",
)


def load_css(path: str) -> None:
    """Reads the CSS file and injects it into the page."""
    with open(path, "r", encoding="utf-8") as f:
        css = f.read()
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


load_css("styles/style.css")

# =========================================================
# Lookup tables
# =========================================================
SUPPORT_PROFILE_OPTIONS = {
    "TDAH": "adhd",
    "Ansiedade": "anxiety",
    "TDAH e ansiedade": "adhd_anxiety",
    "Nenhum desses": "none",
    "Prefiro não informar": "prefer_not_to_say",
}
SUPPORT_PROFILE_REVERSE = {v: k for k, v in SUPPORT_PROFILE_OPTIONS.items()}

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

PRIORITY_LABELS_PT = {"low": "Baixa", "medium": "Média", "high": "Alta"}

CHECKIN_STATE_LABELS_PT = {
    "well": "Bem",
    "overwhelmed": "Sobrecarregada",
    "calm_needed": "Preciso me acalmar",
}

SYNTHETIC_LEVEL_GROUP_LABELS_PT = {"Low": "Baixa", "Medium": "Média", "High": "Alta"}
SYNTHETIC_WEEKDAY_LABELS_PT = {
    "Monday": "Segunda", "Tuesday": "Terça", "Wednesday": "Quarta",
    "Thursday": "Quinta", "Friday": "Sexta", "Saturday": "Sábado", "Sunday": "Domingo",
}
SYNTHETIC_OVERWHELMED_LABELS_PT = {
    "Days with overwhelmed check-in": "Com check-in sobrecarregada",
    "Other check-in days": "Outros dias com check-in",
}
SYNTHETIC_WEEKDAY_VS_WEEKEND_LABELS_PT = {"Weekday": "Dia de semana", "Weekend": "Fim de semana"}

# =========================================================
# Auth state
#
# st.session_state.auth holds only what is needed to restore
# the session across reruns. NEVER stores the password.
# =========================================================
if "auth" not in st.session_state:
    st.session_state.auth = None


def is_authenticated() -> bool:
    """Restore the per-session Supabase client on every rerun so RLS
    can resolve auth.uid(). Clears state and returns False when the
    token is invalid or expired."""
    auth = st.session_state.auth
    if auth is None:
        return False
    ok = restore_session(auth["access_token"], auth["refresh_token"])
    if not ok:
        st.session_state.auth = None
        return False
    return True


def start_session(session) -> None:
    """Store minimum session data after a successful sign-in or sign-up."""
    st.session_state.auth = {
        "access_token": session.access_token,
        "refresh_token": session.refresh_token,
        "user_id": session.user.id,
        "email": session.user.email,
    }


# =========================================================
# Shared rendering helpers
# =========================================================
def _render_page_header(title: str, description: str) -> None:
    """One consistent title + description block at the top of every page.
    Both values are html.escape()d before interpolation since description
    can carry a user-controlled display_name on some pages.
    """
    st.markdown(
        '<div class="page-header">'
        f'<h1 class="page-title">{html.escape(str(title))}</h1>'
        f'<p class="page-description">{html.escape(str(description))}</p>'
        "</div>",
        unsafe_allow_html=True,
    )


def _format_appointment_date(event_date) -> str:
    """ISO date → DD/MM/YYYY. Graceful fallback on parse failure."""
    try:
        parsed = datetime.date.fromisoformat(str(event_date))
        return parsed.strftime("%d/%m/%Y")
    except (ValueError, TypeError):
        return str(event_date)


def _format_appointment_date_short(event_date) -> str:
    """ISO date → 'DD MMM' in Portuguese for the agenda date anchor,
    e.g. '31 AGO'. Graceful fallback on parse failure."""
    _MONTHS_PT = {
        1: "JAN", 2: "FEV", 3: "MAR", 4: "ABR", 5: "MAI", 6: "JUN",
        7: "JUL", 8: "AGO", 9: "SET", 10: "OUT", 11: "NOV", 12: "DEZ",
    }
    try:
        parsed = datetime.date.fromisoformat(str(event_date))
        return f"{parsed.day} {_MONTHS_PT[parsed.month]}"
    except (ValueError, TypeError):
        return str(event_date)


def _format_appointment_time(event_time) -> str:
    """Stored TIME value → HH:MM. Graceful fallback."""
    try:
        raw = str(event_time)[:8]
        parsed = datetime.time.fromisoformat(raw)
        return parsed.strftime("%H:%M")
    except (ValueError, TypeError):
        return str(event_time)


def _compact_task_meta(task: dict) -> str:
    """Builds a single compact metadata string such as 'Alta · 45 min · vence 02/09'
    from the task's priority, estimated_minutes and due_date, omitting any
    field that is not present.  All interpolated values are from validated
    database columns (not free text) but are still passed through
    html.escape() for consistency with the rest of the HTML in this file."""
    parts = []
    if task.get("priority"):
        label = PRIORITY_LABELS_PT.get(task["priority"], task["priority"])
        parts.append(html.escape(str(label)))
    if task.get("estimated_minutes"):
        parts.append(html.escape(str(task["estimated_minutes"])) + " min")
    if task.get("due_date"):
        # Shorten YYYY-MM-DD to DD/MM for the compact line
        try:
            parsed = datetime.date.fromisoformat(str(task["due_date"]))
            parts.append("vence " + html.escape(parsed.strftime("%d/%m")))
        except (ValueError, TypeError):
            parts.append("vence " + html.escape(str(task["due_date"])))
    return " · ".join(parts) if parts else ""


# =========================================================
# Screen: Login / Sign up
# =========================================================
def show_login() -> None:
    # Center the auth area at ~460px so it does not stretch
    # across the full 1050px content column on wide layout.
    st.markdown('<div class="login-container">', unsafe_allow_html=True)

    # Mody logo — centered, ~220px wide, responsive on mobile.
    # st.image handles local file paths natively; no base64 embedding
    # is needed. The logo already contains the brand name so no
    # additional "Mody" heading is rendered beside it.
    col_l, col_logo, col_r = st.columns([1, 2, 1])
    with col_logo:
        st.image("assets/mody_logo.png", use_container_width=True)

    st.markdown(
        '<div class="login-tagline">Um jeito mais leve de organizar o dia.</div>',
        unsafe_allow_html=True,
    )

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
                    start_session(result["session"])
                    st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# Screen: Onboarding
# =========================================================
def show_onboarding(user_id: str) -> None:
    _render_page_header(
        "Vamos te conhecer melhor",
        "Só o essencial para o Mody começar a se adaptar a você. "
        "Tudo aqui pode ser ajustado depois.",
    )

    existing_data = get_existing_data(user_id)
    existing_profile = existing_data["profile"] or {}
    existing_preferences = existing_data["preferences"] or {}

    st.divider()

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
    support_profile = (
        SUPPORT_PROFILE_OPTIONS[chosen_profile_label]
        if chosen_profile_label is not None
        else None
    )

    st.divider()

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
        preferences_result = save_preferences(user_id, support_profile, support_needs)
        if not profile_result["success"]:
            st.error(profile_result["error"])
        elif not preferences_result["success"]:
            st.error(preferences_result["error"])
        else:
            st.session_state.onboarding_just_completed = True
            st.rerun()


# =========================================================
# Screen: Today ("Hoje")
# =========================================================
def _get_latest_checkin_state_and_levels(user_id: str):
    """Latest real check-in state/levels for the adaptive suggestion.
    Returns (state, energy_level, focus_level), each None when absent.
    Always from real Supabase data via the per-session client; never
    from the synthetic dataset.
    """
    result = get_checkins(user_id, limit=1)
    if not result["success"] or not result["data"]:
        return None, None, None
    latest = result["data"][0]
    return latest.get("state"), latest.get("energy_level"), latest.get("focus_level")


def _render_appointment_snippet(appointment: dict | None) -> str:
    """Small inline appointment display for the 'Seu dia' left column.
    Uses _format_appointment_date_short() for a human-friendly '31 AGO'
    style date on the Today page. Escapes every user-controlled field (title).
    """
    if appointment is None:
        return (
            '<div class="day-col-label">Próximo compromisso</div>'
            '<div class="day-col-empty">Seu dia está livre por enquanto.</div>'
        )
    safe_title = html.escape(str(appointment.get("title", "")))
    fmt_date = _format_appointment_date_short(appointment.get("event_date", ""))
    fmt_time = _format_appointment_time(appointment.get("event_time", ""))
    return (
        '<div class="day-col-label">Próximo compromisso</div>'
        f'<div class="day-col-value">{safe_title}</div>'
        f'<div class="day-col-meta">{html.escape(fmt_date)} · {html.escape(fmt_time)}</div>'
    )


def _render_task_snippet(task: dict | None) -> str:
    """Small inline task display for the 'Seu dia' right column.
    Escapes every user-controlled field (title, description, due_date
    when used). Priority and estimated_minutes come from validated DB
    columns but are still escaped for consistency.
    """
    if task is None:
        return (
            '<div class="day-col-label">Tarefa atual</div>'
            '<div class="day-col-empty">Nenhuma tarefa pendente.</div>'
        )
    safe_title = html.escape(str(task.get("title", "")))
    meta = _compact_task_meta(task)
    desc_html = ""
    if task.get("description"):
        desc_html = f'<div class="day-col-desc">{html.escape(str(task["description"]))}</div>'
    meta_html = f'<div class="day-col-meta">{meta}</div>' if meta else ""
    return (
        '<div class="day-col-label">Tarefa atual</div>'
        f'<div class="day-col-value">{safe_title}</div>'
        f"{desc_html}"
        f"{meta_html}"
    )


def show_home(user_id: str, display_name: str | None) -> None:
    greeting_name = display_name or "você"

    # Spec item 10: specific greeting copy for Today page.
    st.markdown(
        '<div class="page-header">'
        f'<h1 class="page-title">Hoje</h1>'
        f'<p class="page-greeting">Olá, {html.escape(str(greeting_name))}.</p>'
        '<p class="page-description">Vamos cuidar do que importa, uma coisa de cada vez.</p>'
        "</div>",
        unsafe_allow_html=True,
    )

    # --- Load real task data ---
    tasks_result = get_tasks(user_id, status="pending")
    if not tasks_result["success"]:
        st.error(tasks_result["error"])
        current_task = None
        pending_task_count = None
    else:
        pending_tasks = tasks_result["data"]
        current_task = pending_tasks[0] if pending_tasks else None
        pending_task_count = len(pending_tasks)

    # --- Session state ---
    if "checkin_state" not in st.session_state:
        st.session_state.checkin_state = None
    if "checkin_just_saved" not in st.session_state:
        st.session_state.checkin_just_saved = False
    if "task_just_completed" not in st.session_state:
        st.session_state.task_just_completed = False

    # --- Check-in ---
    st.markdown('<p class="section-question">Como você está agora?</p>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🙂 Estou bem", use_container_width=True):
            result = create_checkin(user_id=user_id, state="well")
            if result["success"]:
                st.session_state.checkin_state = "well"
                st.session_state.checkin_just_saved = True
            else:
                st.error(result["error"])
    with col2:
        if st.button("😮‍💨 Estou sobrecarregada", use_container_width=True):
            result = create_checkin(user_id=user_id, state="overwhelmed")
            if result["success"]:
                st.session_state.checkin_state = "overwhelmed"
                st.session_state.checkin_just_saved = True
            else:
                st.error(result["error"])
    with col3:
        if st.button("🌿 Quero desacelerar", use_container_width=True):
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
        st.markdown(
            '<div class="resposta-suave">Que bom. Vamos seguir com o seu dia.</div>',
            unsafe_allow_html=True,
        )
    elif st.session_state.checkin_state == "overwhelmed":
        st.markdown(
            '<div class="resposta-suave">Entendido. Vamos manter a tela mais simples possível.</div>',
            unsafe_allow_html=True,
        )
    elif st.session_state.checkin_state == "calm_needed":
        st.markdown(
            '<div class="resposta-suave">Entendido. Considere reduzir o ritmo e escolher o próximo passo com calma.</div>',
            unsafe_allow_html=True,
        )

    st.markdown('<div class="checkin-to-suggestion-gap"></div>', unsafe_allow_html=True)

    # --- Adaptive suggestion ("✦ PARA AGORA" label) ---
    latest_state, latest_energy, latest_focus = _get_latest_checkin_state_and_levels(user_id)
    suggestion = get_adaptive_suggestion(
        checkin_state=latest_state,
        energy_level=latest_energy,
        focus_level=latest_focus,
        pending_task_count=pending_task_count,
    )
    safe_suggestion_title = html.escape(str(suggestion["title"]))
    safe_suggestion_message = html.escape(str(suggestion["message"]))
    safe_suggestion_action = html.escape(str(suggestion["recommended_action"]))
    st.markdown(
        '<div class="para-agora">'
        '<div class="para-agora-label">✦ PARA AGORA</div>'
        f'<div class="para-agora-title">{safe_suggestion_title}</div>'
        f'<div class="para-agora-message">{safe_suggestion_message}</div>'
        f'<div class="para-agora-action">{safe_suggestion_action}</div>'
        "</div>",
        unsafe_allow_html=True,
    )

    st.write("")

    # --- "Seu dia" two-column layout (spec item 1) ---
    # Load real appointment data. Never the synthetic dataset.
    next_appointment_result = get_next_appointment(user_id)
    if not next_appointment_result["success"]:
        st.error(next_appointment_result["error"])
        next_appointment = None
    else:
        next_appointment = next_appointment_result["data"]

    st.markdown('<div class="seu-dia-heading">Seu dia</div>', unsafe_allow_html=True)

    left_col, right_col = st.columns(2)

    with left_col:
        # Left: next appointment card
        appt_inner_html = _render_appointment_snippet(next_appointment)
        st.markdown(
            f'<div class="day-col-card">{appt_inner_html}</div>',
            unsafe_allow_html=True,
        )

    with right_col:
        # Right: current task card + complete button
        task_inner_html = _render_task_snippet(current_task)
        st.markdown(
            f'<div class="day-col-card">{task_inner_html}</div>',
            unsafe_allow_html=True,
        )
        if st.session_state.task_just_completed:
            st.success("Tarefa concluída! 🎉")
            st.session_state.task_just_completed = False
        if current_task is not None:
            if st.button("Concluir", key="complete_current_task", type="primary"):
                result = complete_task(user_id, current_task["id"])
                if result["success"]:
                    st.session_state.task_just_completed = True
                    st.rerun()
                else:
                    st.error(result["error"])


# =========================================================
# Screen: Calendar ("Calendário")
# =========================================================
def show_calendar(user_id: str, display_name: str | None) -> None:
    # Spec item 3: changed description copy
    _render_page_header(
        "Calendário",
        "Um espaço tranquilo para organizar o que vem pela frente.",
    )

    if "appointment_just_saved" not in st.session_state:
        st.session_state.appointment_just_saved = False
    if "appointment_just_deleted" not in st.session_state:
        st.session_state.appointment_just_deleted = False

    if st.session_state.appointment_just_saved:
        st.success("Compromisso adicionado.")
        st.session_state.appointment_just_saved = False
    if st.session_state.appointment_just_deleted:
        st.success("Compromisso excluído.")
        st.session_state.appointment_just_deleted = False

    # Spec item 3: form inside an expander — not permanently open.
    with st.expander("＋ Novo compromisso"):
        with st.form("new_appointment_form", clear_on_submit=True):
            title = st.text_input("Título")
            date_col, time_col = st.columns(2)
            with date_col:
                event_date = st.date_input("Data")
            with time_col:
                event_time = st.time_input("Hora")
            notes = st.text_area("Observação", value="")
            submitted = st.form_submit_button(
                "Adicionar compromisso", use_container_width=True, type="primary"
            )

    if submitted:
        result = create_appointment(
            user_id=user_id,
            title=title,
            event_date=event_date,
            event_time=event_time,
            notes=notes or None,
        )
        if not result["success"]:
            st.error(result["error"])
        else:
            st.session_state.appointment_just_saved = True
            st.rerun()

    st.write("")

    # --- Upcoming appointments as a calm agenda/timeline (spec item 4) ---
    appointments_result = get_appointments(user_id, upcoming_only=True)
    if not appointments_result["success"]:
        st.error(appointments_result["error"])
        return

    appointments = appointments_result["data"]
    if not appointments:
        st.markdown(
            '<div class="agenda-empty">Nenhum compromisso futuro.</div>',
            unsafe_allow_html=True,
        )
        return

    # Render each appointment as a lightweight agenda timeline entry.
    # The date anchor is the visual anchor; time and title follow on
    # the same line. The delete action stays visually secondary in a
    # narrow right column.  Every user-controlled field is escaped.
    for appointment in appointments:
        short_date = _format_appointment_date_short(appointment.get("event_date", ""))
        fmt_time = _format_appointment_time(appointment.get("event_time", ""))
        safe_title = html.escape(str(appointment.get("title", "")))
        note_html = ""
        if appointment.get("notes"):
            safe_notes = html.escape(str(appointment["notes"]))
            note_html = f'<div class="agenda-entry-note">{safe_notes}</div>'

        content_col, delete_col = st.columns([8, 1])
        with content_col:
            st.markdown(
                '<div class="agenda-timeline">'
                f'<div class="agenda-date-anchor">{html.escape(short_date)}</div>'
                '<div class="agenda-time-title-row">'
                f'<span class="agenda-time">{html.escape(fmt_time)}</span>'
                f'<span class="agenda-entry-title">{safe_title}</span>'
                "</div>"
                f"{note_html}"
                "</div>",
                unsafe_allow_html=True,
            )
        with delete_col:
            if st.button(
                "✕",
                key=f"delete_appointment_{appointment['id']}",
                help="Excluir compromisso",
            ):
                delete_result = delete_appointment(user_id, appointment["id"])
                if not delete_result["success"]:
                    st.error(delete_result["error"])
                else:
                    st.session_state.appointment_just_deleted = True
                    st.rerun()

        st.markdown('<hr class="agenda-divider" />', unsafe_allow_html=True)


# =========================================================
# Screen: Overview ("Visão geral")
# =========================================================
def _format_average(value) -> str:
    """None → 'Sem dados'. Never coerces missing check-in levels to 0."""
    return "Sem dados" if value is None else str(value)


def _render_metric_row(metrics: list[tuple[str, str]]) -> None:
    """Render a lightweight numeric-stat row without st.metric's card
    appearance. metrics is a list of (value, label) tuples.
    Values and labels are static strings (not user-controlled) so
    no escaping is needed here, but we escape them anyway for
    consistent discipline.
    """
    items_html = "".join(
        f'<div class="metric-item">'
        f'<div class="metric-value">{html.escape(str(v))}</div>'
        f'<div class="metric-label">{html.escape(str(l))}</div>'
        f"</div>"
        for v, l in metrics
    )
    st.markdown(
        f'<div class="metric-row">{items_html}</div>',
        unsafe_allow_html=True,
    )


def show_overview(user_id: str, display_name: str | None) -> None:
    greeting_name = display_name or "você"
    _render_page_header("Visão geral", f"Um resumo leve do seu progresso, {greeting_name}.")

    # ---- Task KPIs (spec item 6: lightweight, no card boxes) ----
    st.subheader("Tarefas")
    task_result = get_task_metrics(user_id)
    if not task_result["success"]:
        st.error(task_result["error"])
    else:
        d = task_result["data"]
        _render_metric_row([
            (d["total_tasks"], "Tarefas"),
            (d["pending_tasks"], "Pendentes"),
            (d["completed_tasks"], "Concluídas"),
            (f"{d['completion_rate']}%", "Conclusão"),
        ])
        if d["total_tasks"] == 0:
            st.info("Ainda não há tarefas registradas.")

    st.divider()

    # ---- Check-in KPIs ----
    st.subheader("Check-ins")
    checkin_result = get_checkin_metrics(user_id)
    if not checkin_result["success"]:
        st.error(checkin_result["error"])
    else:
        d = checkin_result["data"]
        _render_metric_row([
            (d["total_checkins"], "Total"),
            (_format_average(d["average_energy"]), "Energia média"),
            (_format_average(d["average_anxiety"]), "Ansiedade média"),
            (_format_average(d["average_focus"]), "Foco médio"),
        ])
        if d["total_checkins"] == 0:
            st.info("Ainda não há check-ins registrados.")

    st.divider()

    # ---- Distribution chart ----
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
            distribution_df = pd.DataFrame({
                "Estado": [
                    CHECKIN_STATE_LABELS_PT.get(item["state"], item["state"])
                    for item in distribution
                ],
                "Check-ins": [item["count"] for item in distribution],
            })
            st.bar_chart(distribution_df, x="Estado", y="Check-ins")

    st.divider()

    # ---- Evolution chart ----
    st.subheader("Evolução recente dos check-ins")
    timeseries_result = get_checkin_timeseries(user_id, limit=10)
    if not timeseries_result["success"]:
        st.error(timeseries_result["error"])
    else:
        timeseries = timeseries_result["data"]
        numeric_columns = ["energy_level", "anxiety_level", "focus_level"]
        has_numeric_data = any(
            row.get(col) is not None for row in timeseries for col in numeric_columns
        )
        if not timeseries or not has_numeric_data:
            st.info("Ainda não há dados suficientes para mostrar a evolução.")
        else:
            # pandas ONLY for chart shaping; None becomes NaN (never 0),
            # which st.line_chart renders as line gaps.
            evolution_df = pd.DataFrame(timeseries)
            evolution_df["created_at"] = pd.to_datetime(evolution_df["created_at"])
            evolution_df = evolution_df.rename(columns={
                "energy_level": "Energia",
                "anxiety_level": "Ansiedade",
                "focus_level": "Foco",
            })
            st.line_chart(evolution_df, x="created_at", y=["Energia", "Ansiedade", "Foco"])


# =========================================================
# Screen: Historical Analysis ("Análise histórica")
# =========================================================
def _completion_rate_bar_chart(labels: list[str], rates: list[float], label_column: str) -> None:
    """Shared helper: draws a completion-rate bar chart."""
    chart_df = pd.DataFrame({label_column: labels, "Taxa de conclusão (%)": rates})
    st.bar_chart(chart_df, x=label_column, y="Taxa de conclusão (%)")


def show_historical_analysis(user_id: str, display_name: str | None) -> None:
    _render_page_header(
        "Análise histórica",
        "Demonstração do pipeline analítico do Mody.",
    )

    # Required synthetic-data disclosure — calm info-panel, not st.warning().
    # Static text, but escaped for consistent discipline.
    safe_title = html.escape("🧪 Dados de demonstração")
    safe_body = html.escape(
        "Esta análise utiliza dados fictícios gerados para demonstrar o "
        "fluxo analítico do Mody. Os resultados não representam usuários reais."
    )
    st.markdown(
        '<div class="info-panel">'
        f'<div class="info-panel-title">{safe_title}</div>'
        f'<p class="info-panel-text">{safe_body}</p>'
        "</div>",
        unsafe_allow_html=True,
    )

    st.divider()

    # ---- Summary KPIs ----
    st.subheader("Resumo (dados sintéticos)")
    overall = get_synthetic_overall_task_metrics()
    state_distribution = get_synthetic_checkin_state_distribution()
    total_checkins = sum(item["count"] for item in state_distribution)
    _render_metric_row([
        (overall["total_tasks"], "Tarefas"),
        (f"{overall['completion_rate']}%", "Conclusão"),
        (overall["completed_tasks"], "Concluídas"),
        (total_checkins, "Check-ins"),
    ])

    st.divider()

    # ---- Energy ----
    st.subheader("Conclusão por nível de energia")
    energy_results = get_synthetic_completion_by_energy()
    _completion_rate_bar_chart(
        labels=[SYNTHETIC_LEVEL_GROUP_LABELS_PT[r["energy_group"]] for r in energy_results],
        rates=[r["completion_rate"] for r in energy_results],
        label_column="Energia",
    )
    eg = {r["energy_group"]: r["completion_rate"] for r in energy_results}
    st.caption(
        f"Neste conjunto sintético, dias com energia alta apresentaram taxa de conclusão de "
        f"{eg['High']}%, enquanto dias com energia baixa apresentaram {eg['Low']}%. "
        "Associação observada nos dados de demonstração, não uma relação de causa e efeito."
    )

    st.divider()

    # ---- Focus ----
    st.subheader("Conclusão por nível de foco")
    focus_results = get_synthetic_completion_by_focus()
    _completion_rate_bar_chart(
        labels=[SYNTHETIC_LEVEL_GROUP_LABELS_PT[r["focus_group"]] for r in focus_results],
        rates=[r["completion_rate"] for r in focus_results],
        label_column="Foco",
    )
    fg = {r["focus_group"]: r["completion_rate"] for r in focus_results}
    st.caption(
        f"Nos dados sintéticos, dias com foco alto apresentaram taxa de conclusão de "
        f"{fg['High']}%, contra {fg['Low']}% em dias com foco baixo. "
        "Associação observada apenas neste conjunto de demonstração."
    )

    st.divider()

    # ---- Priority ----
    st.subheader("Conclusão por prioridade")
    priority_results = get_synthetic_completion_by_priority()
    _completion_rate_bar_chart(
        labels=[PRIORITY_LABELS_PT[r["priority"]] for r in priority_results],
        rates=[r["completion_rate"] for r in priority_results],
        label_column="Prioridade",
    )
    st.caption(
        "Neste conjunto de demonstração, tarefas de prioridade alta "
        "apresentaram a maior taxa de conclusão entre os três níveis."
    )

    st.divider()

    # ---- Weekday ----
    st.subheader("Conclusão por dia da semana")
    weekday_results = get_synthetic_completion_by_weekday()
    _completion_rate_bar_chart(
        labels=[SYNTHETIC_WEEKDAY_LABELS_PT[r["weekday"]] for r in weekday_results],
        rates=[r["completion_rate"] for r in weekday_results],
        label_column="Dia",
    )
    st.caption(
        "Nos dados sintéticos, a taxa de conclusão variou ao longo dos dias da semana, "
        "sem representar um padrão real de comportamento."
    )

    st.divider()

    # ---- Overwhelmed comparison ----
    st.subheader("Dias com check-in de sobrecarga")
    overwhelmed_results = get_synthetic_completion_by_overwhelmed_state()
    _completion_rate_bar_chart(
        labels=[SYNTHETIC_OVERWHELMED_LABELS_PT[r["group"]] for r in overwhelmed_results],
        rates=[r["completion_rate"] for r in overwhelmed_results],
        label_column="Grupo",
    )
    owg = {r["group"]: r["completion_rate"] for r in overwhelmed_results}
    st.caption(
        f"Nos dados de demonstração, dias com check-in de sobrecarga apresentaram "
        f"taxa de conclusão de {owg['Days with overwhelmed check-in']}%, contra "
        f"{owg['Other check-in days']}% nos demais. Associação observada apenas neste "
        "conjunto sintético, sem relação de causa e efeito implícita."
    )

    st.divider()

    # ---- Weekday vs weekend ----
    st.subheader("Dias de semana vs. fim de semana")
    wvw_results = get_synthetic_weekday_vs_weekend_metrics()
    summary_table = pd.DataFrame([
        {
            "Grupo": SYNTHETIC_WEEKDAY_VS_WEEKEND_LABELS_PT[r["group"]],
            "Taxa de conclusão (%)": r["completion_rate"],
            "Energia média": r["avg_energy"] if r["avg_energy"] is not None else "Sem dados",
            "Foco médio": r["avg_focus"] if r["avg_focus"] is not None else "Sem dados",
            "Ansiedade média": r["avg_anxiety"] if r["avg_anxiety"] is not None else "Sem dados",
        }
        for r in wvw_results
    ])
    st.table(summary_table)
    _completion_rate_bar_chart(
        labels=[SYNTHETIC_WEEKDAY_VS_WEEKEND_LABELS_PT[r["group"]] for r in wvw_results],
        rates=[r["completion_rate"] for r in wvw_results],
        label_column="Grupo",
    )
    st.caption(
        "Neste conjunto sintético, o fim de semana apresentou taxa de conclusão "
        "diferente da observada nos dias de semana. Padrão descritivo do conjunto "
        "de demonstração, não uma conclusão sobre hábitos reais."
    )

    st.divider()

    # ---- 90-day evolution ----
    st.subheader("Evolução dos check-ins (90 dias, dados sintéticos)")
    synthetic_timeseries = get_synthetic_checkin_timeseries()
    has_numeric_data = any(
        row.get(col) is not None
        for row in synthetic_timeseries
        for col in ("avg_energy", "avg_anxiety", "avg_focus")
    )
    if not synthetic_timeseries or not has_numeric_data:
        st.info("Ainda não há dados suficientes para mostrar a evolução.")
    else:
        synthetic_df = pd.DataFrame(synthetic_timeseries)
        synthetic_df["date"] = pd.to_datetime(synthetic_df["date"])
        synthetic_df = synthetic_df.rename(columns={
            "avg_energy": "Energia", "avg_anxiety": "Ansiedade", "avg_focus": "Foco",
        })
        st.line_chart(synthetic_df, x="date", y=["Energia", "Ansiedade", "Foco"])
    st.caption(
        "Linha do tempo com base no conjunto sintético de 90 dias. "
        "Valores ausentes são exibidos como lacunas no gráfico, nunca como zero."
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

        # Sidebar brand block — icon image + text, no routing logic.
        # st.sidebar.image renders the icon natively; the text identity
        # (name + subtitle) follows as a styled markdown block.
        st.sidebar.image("assets/mody_icon.png", width=90)
        st.sidebar.markdown(
            '<div class="sidebar-brand">'
            '<div class="sidebar-brand-name">Mody</div>'
            '<div class="sidebar-brand-subtitle">Adaptive Planner</div>'
            "</div>",
            unsafe_allow_html=True,
        )

        page = st.sidebar.radio(
            "Navegação",
            ("Hoje", "Calendário", "Visão geral", "Análise histórica"),
            label_visibility="collapsed",
        )

        st.sidebar.divider()
        if st.sidebar.button("Sair", use_container_width=True):
            sign_out()
            st.session_state.clear()
            st.rerun()

        if page == "Hoje":
            show_home(current_user_id, display_name)
        elif page == "Calendário":
            show_calendar(current_user_id, display_name)
        elif page == "Visão geral":
            show_overview(current_user_id, display_name)
        else:
            show_historical_analysis(current_user_id, display_name)