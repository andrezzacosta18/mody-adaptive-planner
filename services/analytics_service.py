"""Analytics service for Mody.

Descriptive analytics layer that prepares task and check-in data for the
future Overview / Dashboard.

This module deliberately does NOT touch the database directly. It composes
the existing service layer:

    services.task_service.get_tasks()
    services.checkin_service.get_checkins()

Those services already run every query through the session-scoped Supabase
client, so RLS resolves auth.uid() and only the current user's rows are ever
returned. Because analytics reuses them, user isolation is preserved "for
free": there is no new Supabase client, no service_role, no raw SQL, and no
way for this layer to reach another user's data.

Scope: descriptive analytics ONLY. This module never infers diagnoses, never
computes a mental-health or risk score, and never labels the user (anxious,
unfocused, productive, etc.). It only counts, averages and orders data.
"""

from services.task_service import get_tasks
from services.checkin_service import get_checkins


# Generic, user-facing message for unexpected failures. We never surface raw
# Supabase errors, stack traces, auth tokens or database internals.
GENERIC_ERROR = (
    "Não foi possível carregar os dados de análise agora. Tente novamente."
)

# Fixed display order for check-in states, shared by the distribution output
# so the future UI does not have to hardcode it.
CHECKIN_STATES = ("well", "overwhelmed", "calm_needed")


def _average(values: list) -> float | None:
    """Average of the non-None numeric values, rounded to 1 decimal.

    Missing values are ignored, never treated as zero. Returns None when
    there is no valid numeric value at all, so the UI can distinguish
    "no data" from a genuine average of zero.
    """
    numbers = [value for value in values if value is not None]
    if not numbers:
        return None
    return round(sum(numbers) / len(numbers), 1)


def get_task_metrics(user_id: str) -> dict:
    """Return aggregate task counts and completion rate for the user.

    Reuses task_service.get_tasks() (called without a status filter to get
    every task). Deleted tasks are not counted because the current schema
    does not preserve them.
    """
    try:
        result = get_tasks(user_id)
        if not result["success"]:
            # Propagate the already-friendly message from the reused service.
            return {"success": False, "error": result["error"]}

        tasks = result["data"]
        total = len(tasks)

        pending = sum(1 for task in tasks if task.get("status") == "pending")
        in_progress = sum(1 for task in tasks if task.get("status") == "in_progress")
        completed = sum(1 for task in tasks if task.get("status") == "completed")
        blocked = sum(1 for task in tasks if task.get("status") == "blocked")

        if total == 0:
            completion_rate = 0.0
        else:
            completion_rate = round(completed / total * 100, 1)

        return {
            "success": True,
            "data": {
                "total_tasks": total,
                "pending_tasks": pending,
                "completed_tasks": completed,
                "in_progress_tasks": in_progress,
                "blocked_tasks": blocked,
                "completion_rate": completion_rate,
            },
        }
    except Exception:
        return {"success": False, "error": GENERIC_ERROR}


def get_checkin_metrics(user_id: str) -> dict:
    """Return check-in counts by state and average energy/anxiety/focus.

    Averages ignore None values and return None when a metric has no valid
    numeric values (see _average).
    """
    try:
        result = get_checkins(user_id)
        if not result["success"]:
            return {"success": False, "error": result["error"]}

        checkins = result["data"]
        total = len(checkins)

        well = sum(1 for c in checkins if c.get("state") == "well")
        overwhelmed = sum(1 for c in checkins if c.get("state") == "overwhelmed")
        calm_needed = sum(1 for c in checkins if c.get("state") == "calm_needed")

        average_energy = _average([c.get("energy_level") for c in checkins])
        average_anxiety = _average([c.get("anxiety_level") for c in checkins])
        average_focus = _average([c.get("focus_level") for c in checkins])

        return {
            "success": True,
            "data": {
                "total_checkins": total,
                "well_count": well,
                "overwhelmed_count": overwhelmed,
                "calm_needed_count": calm_needed,
                "average_energy": average_energy,
                "average_anxiety": average_anxiety,
                "average_focus": average_focus,
            },
        }
    except Exception:
        return {"success": False, "error": GENERIC_ERROR}


def get_checkin_state_distribution(user_id: str) -> dict:
    """Return check-in counts per state, ready for a future chart.

    Always returns all three states in the fixed CHECKIN_STATES order, even
    when a count is zero.
    """
    try:
        result = get_checkins(user_id)
        if not result["success"]:
            return {"success": False, "error": result["error"]}

        checkins = result["data"]
        counts = {state: 0 for state in CHECKIN_STATES}
        for checkin in checkins:
            state = checkin.get("state")
            if state in counts:
                counts[state] += 1

        distribution = [
            {"state": state, "count": counts[state]} for state in CHECKIN_STATES
        ]
        return {"success": True, "data": distribution}
    except Exception:
        return {"success": False, "error": GENERIC_ERROR}


def get_checkin_timeseries(user_id: str, limit: int | None = None) -> dict:
    """Return check-ins in chronological order (oldest -> newest).

    The limit is passed straight to get_checkins(), which already validates
    it and applies it at the database level (so invalid values can't bypass
    that validation and no unnecessary rows are fetched). get_checkins()
    returns the most recent `limit` check-ins newest first; this function
    only reverses them to chronological order (oldest -> newest). None
    values are preserved; no scores or diagnoses are computed.
    """
    try:
        result = get_checkins(user_id, limit=limit)
        if not result["success"]:
            return {"success": False, "error": result["error"]}

        # get_checkins() returns newest first -> reverse to chronological.
        chronological = list(reversed(result["data"]))

        data = [
            {
                "created_at": c.get("created_at"),
                "state": c.get("state"),
                "energy_level": c.get("energy_level"),
                "anxiety_level": c.get("anxiety_level"),
                "focus_level": c.get("focus_level"),
            }
            for c in chronological
        ]
        return {"success": True, "data": data}
    except Exception:
        return {"success": False, "error": GENERIC_ERROR}


def get_overview_metrics(user_id: str) -> dict:
    """Convenience aggregate combining task and check-in metrics.

    If either underlying metric call fails, the whole call fails and its
    friendly error is propagated. Partial metrics are never returned as if
    everything had succeeded.
    """
    try:
        task_result = get_task_metrics(user_id)
        if not task_result["success"]:
            return {"success": False, "error": task_result["error"]}

        checkin_result = get_checkin_metrics(user_id)
        if not checkin_result["success"]:
            return {"success": False, "error": checkin_result["error"]}

        return {
            "success": True,
            "data": {
                "tasks": task_result["data"],
                "checkins": checkin_result["data"],
            },
        }
    except Exception:
        return {"success": False, "error": GENERIC_ERROR}