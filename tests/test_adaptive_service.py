"""Tests for services/adaptive_service.py.

Run from the project root with:

    python -m pytest tests/test_adaptive_service.py -v
"""

from services.adaptive_service import (
    PENDING_TASK_HIGH_THRESHOLD,
    VALID_MODES,
    get_adaptive_suggestion,
)


REQUIRED_KEYS = {
    "mode",
    "title",
    "message",
    "recommended_action",
}


def _assert_shape(result: dict) -> None:
    assert isinstance(result, dict)

    assert REQUIRED_KEYS <= set(result.keys())

    assert result["mode"] in VALID_MODES

    assert isinstance(result["title"], str)
    assert result["title"]

    assert isinstance(result["message"], str)
    assert result["message"]

    assert isinstance(
        result["recommended_action"],
        str,
    )
    assert result["recommended_action"]


def test_calm_needed_gives_pause_mode() -> None:
    result = get_adaptive_suggestion(
        checkin_state="calm_needed"
    )

    _assert_shape(result)

    assert result["mode"] == "pause"


def test_calm_needed_overrides_energy_and_focus() -> None:
    result = get_adaptive_suggestion(
        checkin_state="calm_needed",
        energy_level=5,
        focus_level=5,
    )

    _assert_shape(result)

    assert result["mode"] == "pause"


def test_overwhelmed_gives_light_mode() -> None:
    result = get_adaptive_suggestion(
        checkin_state="overwhelmed"
    )

    _assert_shape(result)

    assert result["mode"] == "light"


def test_overwhelmed_overrides_high_energy_and_focus() -> None:
    result = get_adaptive_suggestion(
        checkin_state="overwhelmed",
        energy_level=5,
        focus_level=5,
    )

    _assert_shape(result)

    assert result["mode"] == "light"


def test_low_energy_gives_light_mode() -> None:
    result = get_adaptive_suggestion(
        energy_level=1
    )

    _assert_shape(result)

    assert result["mode"] == "light"


def test_low_energy_and_low_focus_gives_light_mode() -> None:
    result = get_adaptive_suggestion(
        energy_level=2,
        focus_level=1,
    )

    _assert_shape(result)

    assert result["mode"] == "light"


def test_low_focus_alone_gives_focus_mode() -> None:
    result = get_adaptive_suggestion(
        energy_level=4,
        focus_level=1,
    )

    _assert_shape(result)

    assert result["mode"] == "focus"


def test_high_energy_and_focus_gives_focus_mode() -> None:
    result = get_adaptive_suggestion(
        energy_level=5,
        focus_level=5,
    )

    _assert_shape(result)

    assert result["mode"] == "focus"


def test_well_checkin_with_no_levels_gives_normal_mode() -> None:
    result = get_adaptive_suggestion(
        checkin_state="well"
    )

    _assert_shape(result)

    assert result["mode"] == "normal"


def test_medium_levels_give_normal_mode() -> None:
    result = get_adaptive_suggestion(
        energy_level=3,
        focus_level=3,
    )

    _assert_shape(result)

    assert result["mode"] == "normal"


def test_all_none_does_not_raise_and_returns_normal() -> None:
    result = get_adaptive_suggestion()

    _assert_shape(result)

    assert result["mode"] == "normal"


def test_all_none_explicit_arguments_does_not_raise() -> None:
    result = get_adaptive_suggestion(
        checkin_state=None,
        energy_level=None,
        focus_level=None,
        pending_task_count=None,
    )

    _assert_shape(result)


def test_partial_data_energy_only_does_not_raise() -> None:
    result = get_adaptive_suggestion(
        energy_level=1
    )

    _assert_shape(result)


def test_partial_data_focus_only_does_not_raise() -> None:
    result = get_adaptive_suggestion(
        focus_level=1
    )

    _assert_shape(result)


def test_unrecognized_checkin_state_falls_back_gracefully() -> None:
    result = get_adaptive_suggestion(
        checkin_state="something_unexpected"
    )

    _assert_shape(result)

    assert result["mode"] == "normal"


def test_high_pending_task_count_adds_narrowing_guidance() -> None:
    baseline = get_adaptive_suggestion(
        pending_task_count=0
    )

    overloaded = get_adaptive_suggestion(
        pending_task_count=PENDING_TASK_HIGH_THRESHOLD
    )

    _assert_shape(overloaded)

    assert overloaded["mode"] == "normal"

    assert (
        overloaded["message"]
        != baseline["message"]
    )

    assert (
        "priorid"
        in overloaded["recommended_action"].lower()
        or "priorid"
        in overloaded["message"].lower()
    )


def test_low_pending_task_count_does_not_add_backlog_note() -> None:
    below_threshold = get_adaptive_suggestion(
        pending_task_count=(
            PENDING_TASK_HIGH_THRESHOLD - 1
        )
    )

    baseline = get_adaptive_suggestion(
        pending_task_count=None
    )

    _assert_shape(below_threshold)

    assert (
        below_threshold["message"]
        == baseline["message"]
    )


def test_pending_task_overload_combined_with_light_mode() -> None:
    result = get_adaptive_suggestion(
        checkin_state="overwhelmed",
        pending_task_count=10,
    )

    _assert_shape(result)

    assert result["mode"] == "light"

    assert (
        "priorid"
        in result["recommended_action"].lower()
    )


def test_pending_task_overload_does_not_affect_pause_mode() -> None:
    with_backlog = get_adaptive_suggestion(
        checkin_state="calm_needed",
        pending_task_count=50,
    )

    without_backlog = get_adaptive_suggestion(
        checkin_state="calm_needed"
    )

    _assert_shape(with_backlog)

    assert with_backlog["mode"] == "pause"

    assert (
        with_backlog["message"]
        == without_backlog["message"]
    )

    assert (
        with_backlog["recommended_action"]
        == without_backlog["recommended_action"]
    )


def test_returns_expected_keys_for_various_inputs() -> None:
    cases = [
        {},
        {"checkin_state": "well"},
        {"checkin_state": "overwhelmed"},
        {"checkin_state": "calm_needed"},
        {
            "energy_level": 1,
            "focus_level": 1,
        },
        {
            "energy_level": 5,
            "focus_level": 5,
        },
        {
            "energy_level": 3,
            "focus_level": 3,
            "pending_task_count": 2,
        },
        {
            "pending_task_count": 20,
        },
    ]

    for kwargs in cases:
        result = get_adaptive_suggestion(
            **kwargs
        )

        _assert_shape(result)


def test_no_exception_for_none_inputs() -> None:
    get_adaptive_suggestion(
        None,
        None,
        None,
        None,
    )

    get_adaptive_suggestion(
        checkin_state=None
    )

    get_adaptive_suggestion(
        energy_level=None,
        focus_level=None,
    )

    get_adaptive_suggestion(
        pending_task_count=None
    )