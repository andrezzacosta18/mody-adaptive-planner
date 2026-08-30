"""Simple, transparent, deterministic adaptive suggestions for Mody.

This module provides productivity guidance, not mental-health treatment.

The rules are intentionally deterministic and explainable:
- No AI
- No machine learning
- No diagnostic conclusions
- No database access
- No synthetic-data access

All inputs are optional so the service can gracefully handle incomplete
check-in information.
"""

LEVEL_LOW_MAX = 2.5
LEVEL_HIGH_MIN = 4.0

PENDING_TASK_HIGH_THRESHOLD = 5

VALID_MODES = {"normal", "light", "focus", "pause"}


def _is_low(level: int | float | None) -> bool:
    """Return True when a numeric level belongs to the low range."""
    return level is not None and level < LEVEL_LOW_MAX


def _is_high(level: int | float | None) -> bool:
    """Return True when a numeric level belongs to the high range."""
    return level is not None and level >= LEVEL_HIGH_MIN


def _is_high_backlog(pending_task_count: int | None) -> bool:
    """Return True when the pending-task count reaches the backlog threshold."""
    return (
        pending_task_count is not None
        and pending_task_count >= PENDING_TASK_HIGH_THRESHOLD
    )


def _pause_suggestion() -> dict:
    return {
        "mode": "pause",
        "title": "Modo pausa",
        "message": (
            "Você indicou que precisa se acalmar agora. Está tudo bem "
            "pausar por um momento antes de continuar."
        ),
        "recommended_action": (
            "Considere respirar fundo e pausar por alguns minutos antes de "
            "voltar às tarefas."
        ),
    }


def _light_suggestion(reason: str) -> dict:
    messages = {
        "overwhelmed_checkin": (
            "Você registrou que está se sentindo sobrecarregada agora."
        ),
        "low_energy": (
            "Sua energia registrada está baixa no momento."
        ),
        "low_energy_and_focus": (
            "Sua energia e seu foco registrados estão baixos no momento."
        ),
    }

    return {
        "mode": "light",
        "title": "Modo leve",
        "message": messages[reason],
        "recommended_action": (
            "Considere escolher apenas uma tarefa pequena ou prioritária "
            "agora, e deixar o restante para depois."
        ),
    }


def _focus_suggestion(reason: str) -> dict:
    if reason == "low_focus":
        return {
            "mode": "focus",
            "title": "Modo foco",
            "message": "Seu foco registrado está baixo no momento.",
            "recommended_action": (
                "Escolha uma única tarefa por vez para reduzir a dispersão."
            ),
        }

    return {
        "mode": "focus",
        "title": "Modo foco",
        "message": (
            "Sua energia e seu foco registrados estão altos agora."
        ),
        "recommended_action": (
            "Esse pode ser um bom momento para avançar em uma tarefa "
            "prioritária ou mais desafiadora."
        ),
    }


def _normal_suggestion(checkin_state: str | None) -> dict:
    if checkin_state == "well":
        message = "Você registrou que está bem agora."
    else:
        message = (
            "Não há sinais fortes de sobrecarga, baixa energia ou baixo "
            "foco no momento."
        )

    return {
        "mode": "normal",
        "title": "Modo normal",
        "message": message,
        "recommended_action": (
            "Você pode seguir com sua rotina normalmente."
        ),
    }


def _with_backlog_note(suggestion: dict) -> dict:
    """Append a narrowing-priorities note without mutating the input."""
    updated = dict(suggestion)

    updated["message"] = (
        updated["message"]
        + " Você também tem várias tarefas pendentes."
    )

    updated["recommended_action"] = (
        updated["recommended_action"]
        + " Escolha 2 ou 3 prioridades para agora e deixe o restante para depois."
    )

    return updated


def get_adaptive_suggestion(
    checkin_state: str | None = None,
    energy_level: int | float | None = None,
    focus_level: int | float | None = None,
    pending_task_count: int | None = None,
) -> dict:
    """Return a simple and explainable productivity suggestion."""

    low_energy = _is_low(energy_level)
    high_energy = _is_high(energy_level)

    low_focus = _is_low(focus_level)
    high_focus = _is_high(focus_level)

    if checkin_state == "calm_needed":
        suggestion = _pause_suggestion()

    elif checkin_state == "overwhelmed":
        suggestion = _light_suggestion(
            reason="overwhelmed_checkin"
        )

    elif low_energy and low_focus:
        suggestion = _light_suggestion(
            reason="low_energy_and_focus"
        )

    elif low_energy:
        suggestion = _light_suggestion(
            reason="low_energy"
        )

    elif low_focus:
        suggestion = _focus_suggestion(
            reason="low_focus"
        )

    elif high_energy and high_focus:
        suggestion = _focus_suggestion(
            reason="high_energy_and_focus"
        )

    else:
        suggestion = _normal_suggestion(
            checkin_state
        )

    if (
        suggestion["mode"] != "pause"
        and _is_high_backlog(pending_task_count)
    ):
        suggestion = _with_backlog_note(
            suggestion
        )

    return suggestion