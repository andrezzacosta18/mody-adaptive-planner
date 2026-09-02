"""
Analytics service for Mody.

Descriptive analytics layer that prepares task and check-in data for the
Overview / Dashboard.

This module deliberately does NOT touch the database directly. It composes
the existing service layer:

    services.task_service.get_tasks()
    services.checkin_service.get_checkins()

Those services already run every query through the session-scoped Supabase
client, so RLS resolves auth.uid() and only the current user's rows are ever
returned.

Scope: descriptive analytics ONLY. This module never infers diagnoses,
never computes a mental-health or risk score, and never labels the user.
It only counts and organizes task and check-in data.
"""

from services.task_service import get_tasks
from services.checkin_service import get_checkins


GENERIC_ERROR = (
    "Não foi possível carregar os dados de análise agora. Tente novamente."
)

CHECKIN_STATES = ("well", "overwhelmed", "calm_needed")


def get_task_metrics(user_id: str) -> dict:
    """
    Return aggregate task counts and completion rate for the user.
    """
    try:
        result = get_tasks(user_id)

        if not result["success"]:
            return {
                "success": False,
                "error": result["error"],
            }

        tasks = result["data"]
        total = len(tasks)

        pending = sum(
            1 for task in tasks
            if task.get("status") == "pending"
        )

        in_progress = sum(
            1 for task in tasks
            if task.get("status") == "in_progress"
        )

        completed = sum(
            1 for task in tasks
            if task.get("status") == "completed"
        )

        blocked = sum(
            1 for task in tasks
            if task.get("status") == "blocked"
        )

        if total == 0:
            completion_rate = 0.0
        else:
            completion_rate = round(
                completed / total * 100,
                1,
            )

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
        return {
            "success": False,
            "error": GENERIC_ERROR,
        }


def get_checkin_metrics(user_id: str) -> dict:
    """
    Return check-in counts by state.

    The public MVP stores only the user's selected check-in state.
    No energy, anxiety or focus scores are collected from real users.
    """
    try:
        result = get_checkins(user_id)

        if not result["success"]:
            return {
                "success": False,
                "error": result["error"],
            }

        checkins = result["data"]
        total = len(checkins)

        well = sum(
            1 for checkin in checkins
            if checkin.get("state") == "well"
        )

        overwhelmed = sum(
            1 for checkin in checkins
            if checkin.get("state") == "overwhelmed"
        )

        calm_needed = sum(
            1 for checkin in checkins
            if checkin.get("state") == "calm_needed"
        )

        return {
            "success": True,
            "data": {
                "total_checkins": total,
                "well_count": well,
                "overwhelmed_count": overwhelmed,
                "calm_needed_count": calm_needed,
            },
        }

    except Exception:
        return {
            "success": False,
            "error": GENERIC_ERROR,
        }


def get_checkin_state_distribution(user_id: str) -> dict:
    """
    Return check-in counts per state.

    All three states are always returned in a fixed order,
    even when one of them has a count of zero.
    """
    try:
        result = get_checkins(user_id)

        if not result["success"]:
            return {
                "success": False,
                "error": result["error"],
            }

        checkins = result["data"]

        counts = {
            state: 0
            for state in CHECKIN_STATES
        }

        for checkin in checkins:
            state = checkin.get("state")

            if state in counts:
                counts[state] += 1

        distribution = [
            {
                "state": state,
                "count": counts[state],
            }
            for state in CHECKIN_STATES
        ]

        return {
            "success": True,
            "data": distribution,
        }

    except Exception:
        return {
            "success": False,
            "error": GENERIC_ERROR,
        }


def get_checkin_timeseries(
    user_id: str,
    limit: int | None = None,
) -> dict:
    """
    Return check-ins in chronological order.

    Only the timestamp and selected state are exposed because
    those are the only real check-in fields used by the MVP.
    """
    try:
        result = get_checkins(
            user_id,
            limit=limit,
        )

        if not result["success"]:
            return {
                "success": False,
                "error": result["error"],
            }

        chronological = list(
            reversed(result["data"])
        )

        data = [
            {
                "created_at": checkin.get("created_at"),
                "state": checkin.get("state"),
            }
            for checkin in chronological
        ]

        return {
            "success": True,
            "data": data,
        }

    except Exception:
        return {
            "success": False,
            "error": GENERIC_ERROR,
        }


def get_overview_metrics(user_id: str) -> dict:
    """
    Combine task metrics and check-in metrics.
    """
    try:
        task_result = get_task_metrics(user_id)

        if not task_result["success"]:
            return {
                "success": False,
                "error": task_result["error"],
            }

        checkin_result = get_checkin_metrics(user_id)

        if not checkin_result["success"]:
            return {
                "success": False,
                "error": checkin_result["error"],
            }

        return {
            "success": True,
            "data": {
                "tasks": task_result["data"],
                "checkins": checkin_result["data"],
            },
        }

    except Exception:
        return {
            "success": False,
            "error": GENERIC_ERROR,
        }