"""
Task service for Mody.

All database access for `tasks` goes through this module — the UI
must never call client.table("tasks") directly.

Nothing here bypasses RLS: every call uses the session-specific
Supabase client (services.supabase_service.get_client()), with the
session already restored via auth_service.restore_session() before
any of these functions run. auth.uid() in the RLS policies is what
actually grants/denies access — user_id is passed here only to build
readable queries and to stamp new rows, never to grant access on its
own.
"""

from datetime import datetime, timezone

from services.supabase_service import get_client

VALID_PRIORITIES = ("low", "medium", "high")

GENERIC_ERROR = "Não foi possível completar a operação agora. Tente novamente."

# Sentinel used by update_task() to distinguish "this parameter
# wasn't passed at all, don't touch the column" from "this parameter
# was explicitly passed as None, clear the column". A plain default
# of None can't express that distinction on its own.
_UNSET = object()


def _validate_title(title: str) -> str | None:
    """Returns a user-facing error message if the title is invalid,
    or None if it's fine."""
    if title is None or len(title.strip()) == 0:
        return "O título da tarefa não pode ficar vazio."
    return None


def _validate_estimated_minutes(estimated_minutes) -> str | None:
    """Returns a user-facing error message if estimated_minutes is
    invalid, or None if it's fine (including when it's None)."""
    if estimated_minutes is None:
        return None
    if not isinstance(estimated_minutes, int) or estimated_minutes <= 0:
        return "O tempo estimado deve ser um número de minutos maior que zero."
    return None


def _validate_priority(priority) -> str | None:
    """Returns a user-facing error message if priority is invalid,
    or None if it's fine (including when it's None)."""
    if priority is None:
        return None
    if priority not in VALID_PRIORITIES:
        return "Prioridade inválida."
    return None


def create_task(
    user_id: str,
    title: str,
    description: str | None = None,
    priority: str | None = None,
    estimated_minutes: int | None = None,
    due_date: str | None = None,
) -> dict:
    """
    Creates a task for the authenticated user. Status always starts
    as 'pending' — there's no reason for the caller to set it at
    creation time.

    due_date, when provided, should be an ISO date string
    ("YYYY-MM-DD") or a date/datetime object the Supabase client can
    serialize.
    """
    title_error = _validate_title(title)
    if title_error:
        return {"success": False, "error": title_error}

    minutes_error = _validate_estimated_minutes(estimated_minutes)
    if minutes_error:
        return {"success": False, "error": minutes_error}

    priority_error = _validate_priority(priority)
    if priority_error:
        return {"success": False, "error": priority_error}

    client = get_client()
    payload = {
        "user_id": user_id,
        "title": title.strip(),
        "description": description,
        "priority": priority,
        "estimated_minutes": estimated_minutes,
        "due_date": due_date,
    }

    try:
        response = client.table("tasks").insert(payload).execute()
        return {"success": True, "data": response.data[0] if response.data else None}
    except Exception:
        return {"success": False, "error": GENERIC_ERROR}


def get_tasks(user_id: str, status: str | None = None) -> dict:
    """
    Retrieves the authenticated user's tasks, optionally filtered by
    status. RLS is what actually restricts rows to this user — the
    .eq("user_id", ...) filter here is just for a clear, explicit
    query, not a substitute for RLS.

    Default order: due_date ascending (tasks without a due date
    sorted last, not hidden), then created_at ascending as a
    tiebreaker.
    """
    client = get_client()
    try:
        query = client.table("tasks").select("*").eq("user_id", user_id)
        if status is not None:
            query = query.eq("status", status)
        query = query.order("due_date", nullsfirst=False).order(
            "created_at", desc=False
        )
        response = query.execute()
        return {"success": True, "data": response.data}
    except Exception:
        return {"success": False, "error": GENERIC_ERROR}


def get_task_by_id(user_id: str, task_id: str) -> dict:
    """
    Retrieves a single task. Returns data=None (success=True) when
    the task doesn't exist or doesn't belong to this user — RLS
    already prevents reading another user's row, so an empty result
    here just means "not found from this user's point of view", not
    an error.
    """
    client = get_client()
    try:
        response = (
            client.table("tasks")
            .select("*")
            .eq("user_id", user_id)
            .eq("id", task_id)
            .execute()
        )
        data = response.data[0] if response.data else None
        return {"success": True, "data": data}
    except Exception:
        return {"success": False, "error": GENERIC_ERROR}


def update_task(
    user_id: str,
    task_id: str,
    title=_UNSET,
    description=_UNSET,
    priority=_UNSET,
    estimated_minutes=_UNSET,
    due_date=_UNSET,
) -> dict:
    """
    Updates only the fields actually provided. id, user_id and
    created_at are never editable through this function — they're
    simply not accepted as parameters.

    Each optional field defaults to the private _UNSET sentinel
    instead of None, so the function can tell apart two different
    caller intents:

    - _UNSET (parameter omitted)  -> field not touched at all.
    - None (parameter passed as None) -> field explicitly cleared
      (column set to NULL), e.g. removing a due date or priority.

    title is the one exception: it can be omitted (_UNSET), but it
    can't be explicitly cleared to None — a task always needs a
    title, so passing title=None is treated as invalid input, not as
    "clear the title".
    """
    fields = {}

    if title is not _UNSET:
        title_error = _validate_title(title)
        if title_error:
            return {"success": False, "error": title_error}
        fields["title"] = title.strip()

    if description is not _UNSET:
        # Free-form optional text: None clears it, any string
        # (including "") sets it. No validation needed either way.
        fields["description"] = description

    if priority is not _UNSET:
        # _validate_priority already treats None as valid (nothing
        # to validate when clearing), and only checks the allowed
        # values when priority is an actual value.
        priority_error = _validate_priority(priority)
        if priority_error:
            return {"success": False, "error": priority_error}
        fields["priority"] = priority

    if estimated_minutes is not _UNSET:
        # Same idea: _validate_estimated_minutes accepts None
        # (clearing) and only checks "> 0" for an actual value.
        minutes_error = _validate_estimated_minutes(estimated_minutes)
        if minutes_error:
            return {"success": False, "error": minutes_error}
        fields["estimated_minutes"] = estimated_minutes

    if due_date is not _UNSET:
        # None clears the deadline, any other value sets it. No
        # format validation here — the caller is expected to pass an
        # ISO date string or a value the Supabase client can
        # serialize, same as in create_task.
        fields["due_date"] = due_date

    if not fields:
        return {"success": False, "error": "Nenhuma alteração foi enviada."}

    client = get_client()
    try:
        response = (
            client.table("tasks")
            .update(fields)
            .eq("user_id", user_id)
            .eq("id", task_id)
            .execute()
        )
        data = response.data[0] if response.data else None
        return {"success": True, "data": data}
    except Exception:
        return {"success": False, "error": GENERIC_ERROR}


def complete_task(user_id: str, task_id: str) -> dict:
    """Marks a task as completed, stamping completed_at with the
    current timezone-aware timestamp."""
    client = get_client()
    fields = {
        "status": "completed",
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        response = (
            client.table("tasks")
            .update(fields)
            .eq("user_id", user_id)
            .eq("id", task_id)
            .execute()
        )
        data = response.data[0] if response.data else None
        return {"success": True, "data": data}
    except Exception:
        return {"success": False, "error": GENERIC_ERROR}


def reopen_task(user_id: str, task_id: str) -> dict:
    """Moves a completed task back to pending, clearing
    completed_at."""
    client = get_client()
    fields = {"status": "pending", "completed_at": None}
    try:
        response = (
            client.table("tasks")
            .update(fields)
            .eq("user_id", user_id)
            .eq("id", task_id)
            .execute()
        )
        data = response.data[0] if response.data else None
        return {"success": True, "data": data}
    except Exception:
        return {"success": False, "error": GENERIC_ERROR}


def delete_task(user_id: str, task_id: str) -> dict:
    """Deletes a task belonging to the authenticated user."""
    client = get_client()
    try:
        client.table("tasks").delete().eq("user_id", user_id).eq(
            "id", task_id
        ).execute()
        return {"success": True}
    except Exception:
        return {"success": False, "error": GENERIC_ERROR}