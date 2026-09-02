"""
Check-in service for Mody.

All database access for `checkins` goes through this module — the UI
must never call client.table("checkins") directly.

Nothing here bypasses RLS: every call uses the session-specific
Supabase client (services.supabase_service.get_client()), with the
session already restored via auth_service.restore_session() before
any of these functions run. auth.uid() in the RLS policies is what
actually grants/denies access.
"""

from services.supabase_service import get_client


VALID_STATES = ("well", "overwhelmed", "calm_needed")

GENERIC_ERROR = "Não foi possível completar a operação agora. Tente novamente."


def _validate_state(state: str) -> str | None:
    """
    Returns a user-facing error message if state is invalid,
    or None if it is valid.
    """
    if state not in VALID_STATES:
        return "Estado de check-in inválido."

    return None


def create_checkin(
    user_id: str,
    state: str,
) -> dict:
    """
    Creates a new check-in row for the authenticated user.

    The MVP stores only a simple productivity-oriented state.

    created_at is left out of the payload so the database
    default (now()) is used.
    """
    state_error = _validate_state(state)

    if state_error:
        return {
            "success": False,
            "error": state_error,
        }

    payload = {
        "user_id": user_id,
        "state": state,
    }

    try:
        client = get_client()

        response = (
            client.table("checkins")
            .insert(payload)
            .execute()
        )

        return {
            "success": True,
            "data": response.data[0] if response.data else None,
        }

    except Exception:
        return {
            "success": False,
            "error": GENERIC_ERROR,
        }


def get_checkins(
    user_id: str,
    limit: int | None = None,
) -> dict:
    """
    Retrieves the authenticated user's check-ins,
    newest first.

    RLS restricts rows to the authenticated user.
    """
    if limit is not None:
        if (
            isinstance(limit, bool)
            or not isinstance(limit, int)
            or limit <= 0
        ):
            return {
                "success": False,
                "error": "Limite inválido.",
            }

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

        return {
            "success": True,
            "data": response.data,
        }

    except Exception:
        return {
            "success": False,
            "error": GENERIC_ERROR,
        }


def get_latest_checkin(user_id: str) -> dict:
    """
    Retrieves the authenticated user's most recent check-in.

    Returns success=True, data=None when the user
    has no check-ins yet.
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

        return {
            "success": True,
            "data": data,
        }

    except Exception:
        return {
            "success": False,
            "error": GENERIC_ERROR,
        }


def get_checkin_by_id(
    user_id: str,
    checkin_id: str,
) -> dict:
    """
    Retrieves one check-in belonging to the authenticated user.

    If the row belongs to another user, RLS prevents access.
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

        return {
            "success": True,
            "data": data,
        }

    except Exception:
        return {
            "success": False,
            "error": GENERIC_ERROR,
        }