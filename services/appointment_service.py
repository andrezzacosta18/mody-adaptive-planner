"""Internal appointment calendar service.

Follows the same conventions as the other real-data services in this
project (task_service.py, checkin_service.py):

- Every public function returns the project's standard result shape:
  {"success": bool, "data": ..., "error": str | None}.
- Raw Supabase/PostgREST exceptions are never returned to the UI; they
  are caught and replaced with a short, user-facing Portuguese message
  (app.py just calls st.error(result["error"])).
- user_id is always supplied by the caller from the authenticated
  session (see app.py routing) — this module never reads or trusts a
  user_id from form input.
- Row Level Security (see sql/appointments.sql) is the actual access
  control boundary. The explicit .eq("user_id", user_id) filters below
  are kept for query clarity, not as the security mechanism itself.
- The per-session Supabase client comes from services.supabase_service,
  the same accessor task_service.py and checkin_service.py already use
  — this module does not introduce a separate client.

NOTE ON TIMEZONES:
Appointments are stored as plain PostgreSQL DATE/TIME values, with no
timezone attached. "Upcoming" is determined by comparing against the
server process's local date/time (datetime.now()), not the user's
profile timezone (onboarding_service.py stores one, e.g.
"Europe/Lisbon", but there is no timezone-conversion subsystem in this
codebase). This is a current MVP limitation, not full timezone-aware
calendar behavior — see _is_upcoming() below.
"""

from datetime import date, datetime, time

from services.supabase_service import get_client

GENERIC_LOAD_ERROR = "Não foi possível carregar os compromissos."
GENERIC_SAVE_ERROR = "Não foi possível salvar o compromisso. Tente novamente."
GENERIC_DELETE_ERROR = "Não foi possível excluir o compromisso. Tente novamente."


def _is_upcoming(appointment: dict) -> bool:
    """Determines whether an appointment's date/time has not passed yet.

    Simplification (documented, not a bug): compares the stored
    event_date/event_time against datetime.now() using naive
    datetimes — no timezone conversion. See the module docstring.
    Returns False (rather than raising) for malformed rows, since a
    single bad row should never break the whole list.
    """
    event_date_value = appointment.get("event_date")
    event_time_value = appointment.get("event_time")
    if not event_date_value or not event_time_value:
        return False

    try:
        parsed_date = date.fromisoformat(str(event_date_value))
        # PostgREST may return "10:00:00" or "10:00:00+00"; only the
        # first 8 characters ("HH:MM:SS") are needed here.
        parsed_time = time.fromisoformat(str(event_time_value)[:8])
    except (ValueError, TypeError):
        return False

    event_datetime = datetime.combine(parsed_date, parsed_time)
    return event_datetime >= datetime.now()


def create_appointment(
    user_id,
    title,
    event_date,
    event_time,
    notes=None,
):
    """Creates a new appointment for the authenticated user.

    Validates that user_id, title, event_date and event_time are all
    present, and that title is not blank after trimming. Trims title
    and notes before saving.
    """
    if not user_id:
        return {"success": False, "data": None, "error": "Usuário não autenticado."}

    if title is None or not str(title).strip():
        return {"success": False, "data": None, "error": "Título é obrigatório."}

    if not event_date:
        return {"success": False, "data": None, "error": "Data é obrigatória."}

    if not event_time:
        return {"success": False, "data": None, "error": "Hora é obrigatória."}

    clean_title = str(title).strip()
    clean_notes = str(notes).strip() if notes and str(notes).strip() else None

    payload = {
        "user_id": user_id,
        "title": clean_title,
        "event_date": event_date.isoformat() if isinstance(event_date, date) else str(event_date),
        "event_time": event_time.isoformat() if isinstance(event_time, time) else str(event_time),
        "notes": clean_notes,
    }

    try:
        response = get_client().table("appointments").insert(payload).execute()
        rows = response.data or []
        appointment = rows[0] if rows else None
        return {"success": True, "data": appointment, "error": None}
    except Exception:
        return {"success": False, "data": None, "error": GENERIC_SAVE_ERROR}


def get_appointments(user_id, upcoming_only=True):
    """Returns the authenticated user's appointments, ordered
    chronologically (event_date ascending, then event_time ascending).

    When upcoming_only is True, only appointments whose date/time has
    not passed are returned (see _is_upcoming). When False, all of the
    user's appointments are returned, still in chronological order.
    """
    if not user_id:
        return {"success": False, "data": None, "error": "Usuário não autenticado."}

    try:
        response = (
            get_client()
            .table("appointments")
            .select("*")
            .eq("user_id", user_id)
            .order("event_date", desc=False)
            .order("event_time", desc=False)
            .execute()
        )
        appointments = response.data or []
    except Exception:
        return {"success": False, "data": None, "error": GENERIC_LOAD_ERROR}

    if upcoming_only:
        appointments = [a for a in appointments if _is_upcoming(a)]

    return {"success": True, "data": appointments, "error": None}


def get_next_appointment(user_id):
    """Returns the single earliest upcoming appointment, or None if
    there isn't one. Reuses get_appointments() instead of duplicating
    the query/ordering logic.
    """
    result = get_appointments(user_id, upcoming_only=True)
    if not result["success"]:
        return result

    appointments = result["data"]
    next_appointment = appointments[0] if appointments else None
    return {"success": True, "data": next_appointment, "error": None}


def delete_appointment(user_id, appointment_id):
    """Deletes an appointment, scoped to both the appointment id and
    the authenticated user_id. RLS (see sql/appointments.sql) is the
    real security boundary; the .eq("user_id", ...) filter here is
    for query clarity / defense in depth.
    """
    if not user_id:
        return {"success": False, "data": None, "error": "Usuário não autenticado."}

    if not appointment_id:
        return {"success": False, "data": None, "error": "ID do compromisso é obrigatório."}

    try:
        response = (
            get_client()
            .table("appointments")
            .delete()
            .eq("id", appointment_id)
            .eq("user_id", user_id)
            .execute()
        )
        return {"success": True, "data": response.data, "error": None}
    except Exception:
        return {"success": False, "data": None, "error": GENERIC_DELETE_ERROR}