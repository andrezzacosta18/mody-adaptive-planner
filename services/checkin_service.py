"""
Check-in service for Mody.

All database access for `checkins` goes through this module — the UI
must never call client.table("checkins") directly.

Nothing here bypasses RLS: every call uses the session-specific
Supabase client (services.supabase_service.get_client()), with the
session already restored via auth_service.restore_session() before
any of these functions run. auth.uid() in the RLS policies is what
actually grants/denies access — user_id is passed here only to build
readable queries and to stamp new rows, never to grant access on its
own.
"""

from services.supabase_service import get_client

VALID_STATES = ("well", "overwhelmed", "calm_needed")

GENERIC_ERROR = "Não foi possível completar a operação agora. Tente novamente."


def _validate_state(state: str) -> str | None:
    """Returns a user-facing error message if state is invalid, or
    None if it's fine."""
    if state not in VALID_STATES:
        return "Estado de check-in inválido."
    return None


def _validate_level(level, label: str) -> str | None:
    """Returns a user-facing error message if an optional 1-5 level
    (energy/anxiety/focus) is invalid, or None if it's fine
    (including when it's None).

    bool is explicitly rejected even though Python treats bool as a
    subclass of int (isinstance(True, int) is True) — a level must
    be an actual integer 1-5, not True/False.
    """
    if level is None:
        return None
    if isinstance(level, bool) or not isinstance(level, int):
        return f"O nível de {label} deve estar entre 1 e 5."
    if not (1 <= level <= 5):
        return f"O nível de {label} deve estar entre 1 e 5."
    return None


def create_checkin(
    user_id: str,
    state: str,
    energy_level: int | None = None,
    anxiety_level: int | None = None,
    focus_level: int | None = None,
) -> dict:
    """
    Creates a new check-in row for the authenticated user.

    created_at is left out of the payload on purpose so the database
    default (now()) is used, rather than generating a timestamp here.
    """
    state_error = _validate_state(state)
    if state_error:
        return {"success": False, "error": state_error}

    energy_error = _validate_level(energy_level, "energia")
    if energy_error:
        return {"success": False, "error": energy_error}

    anxiety_error = _validate_level(anxiety_level, "ansiedade")
    if anxiety_error:
        return {"success": False, "error": anxiety_error}

    focus_error = _validate_level(focus_level, "foco")
    if focus_error:
        return {"success": False, "error": focus_error}

    payload = {
        "user_id": user_id,
        "state": state,
        "energy_level": energy_level,
        "anxiety_level": anxiety_level,
        "focus_level": focus_level,
    }

    try:
        client = get_client()
        response = client.table("checkins").insert(payload).execute()
        return {"success": True, "data": response.data[0] if response.data else None}
    except Exception:
        return {"success": False, "error": GENERIC_ERROR}


def get_checkins(user_id: str, limit: int | None = None) -> dict:
    """
    Retrieves the authenticated user's check-ins, newest first.

    RLS is what actually restricts rows to this user — the
    .eq("user_id", ...) filter here is just for a clear, explicit
    query, not a substitute for RLS.
    """
    if limit is not None:
        if isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0:
            return {"success": False, "error": "Limite inválido."}

    try:
        client = get_client()
        query = (
            client.table("checkins")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
        )
        if limit is not None:
            query = query.limit(limit)
        response = query.execute()
        return {"success": True, "data": response.data}
    except Exception:
        return {"success": False, "error": GENERIC_ERROR}


def get_latest_checkin(user_id: str) -> dict:
    """
    Retrieves the authenticated user's most recent check-in.

    Returns success=True, data=None when the user has no check-ins
    yet — that's an expected state, not an application error.
    """
    try:
        client = get_client()
        response = (
            client.table("checkins")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        data = response.data[0] if response.data else None
        return {"success": True, "data": data}
    except Exception:
        return {"success": False, "error": GENERIC_ERROR}


def get_checkin_by_id(user_id: str, checkin_id: str) -> dict:
    """
    Retrieves a single check-in, filtering by BOTH user_id and
    checkin_id, still backed by RLS.

    Used for the manual user-isolation test: if the row belongs to
    another user, this returns success=True, data=None — exactly the
    same shape as "not found" — so the caller can never tell whether
    a given id exists for someone else.
    """
    try:
        client = get_client()
        response = (
            client.table("checkins")
            .select("*")
            .eq("user_id", user_id)
            .eq("id", checkin_id)
            .execute()
        )
        data = response.data[0] if response.data else None
        return {"success": True, "data": data}
    except Exception:
        return {"success": False, "error": GENERIC_ERROR}