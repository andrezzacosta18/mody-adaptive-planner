"""Validate the synthetic dataset produced by scripts/generate_synthetic_data.py.

This is a plain validation script (not a UI). Run it after generating the
data:

    python tests/test_synthetic_data.py

It reads the two CSV files under data/synthetic/ and asserts the structural
and logical guarantees the generator promises. Any failure raises an
AssertionError with a clear message; on success it prints a short report.

It is also import-safe for pytest: every check lives in a `test_*` function.
"""

import os
from datetime import date

import pandas as pd

# Resolve paths relative to the project root (parent of tests/), so the
# script works no matter where it is launched from.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data", "synthetic")
CHECKINS_PATH = os.path.join(DATA_DIR, "synthetic_checkins.csv")
TASKS_PATH = os.path.join(DATA_DIR, "synthetic_tasks.csv")

# The fixed 90-day observation window used by the generator. created_at for
# both check-ins and tasks must always fall inside this window. due_date is
# intentionally NOT bound by PERIOD_END — see test_tasks_due_date_* below.
PERIOD_START = date(2025, 1, 1)
PERIOD_END = date(2025, 3, 31)

VALID_STATES = {"well", "overwhelmed", "calm_needed"}
VALID_STATUSES = {"pending", "in_progress", "completed", "blocked"}
VALID_PRIORITIES = {"low", "medium", "high"}
VALID_LEVELS = {1, 2, 3, 4, 5}

CHECKIN_REQUIRED_COLUMNS = {
    "synthetic_checkin_id",
    "created_at",
    "state",
    "energy_level",
    "anxiety_level",
    "focus_level",
    "is_synthetic",
}
TASK_REQUIRED_COLUMNS = {
    "synthetic_task_id",
    "created_at",
    "completed_at",
    "status",
    "priority",
    "estimated_minutes",
    "due_date",
    "is_synthetic",
}

# Generous bounds: the dataset targets a fixed 90-day period. These ranges
# leave room for run-to-run tuning while still catching real breakage.
MIN_CHECKINS = 60
MIN_TASKS = 120
MIN_PERIOD_SPAN_DAYS = 80
MAX_PERIOD_SPAN_DAYS = 92


# ---------------------------------------------------------------------------
# Loading helpers
# ---------------------------------------------------------------------------
def _load_checkins() -> pd.DataFrame:
    assert os.path.exists(CHECKINS_PATH), (
        f"Check-ins file not found at {CHECKINS_PATH}. "
        "Run: python scripts/generate_synthetic_data.py"
    )
    return pd.read_csv(CHECKINS_PATH)


def _load_tasks() -> pd.DataFrame:
    assert os.path.exists(TASKS_PATH), (
        f"Tasks file not found at {TASKS_PATH}. "
        "Run: python scripts/generate_synthetic_data.py"
    )
    return pd.read_csv(TASKS_PATH)


def _all_true(series: pd.Series) -> bool:
    """True only if every value is boolean True.

    read_csv may parse an all-'True' column as bool dtype or (defensively)
    as the string 'True'; accept both, reject anything else."""
    normalized = series.map(lambda v: v is True or v == "True")
    return bool(normalized.all())


def _assert_levels_valid(series: pd.Series, name: str) -> None:
    """Non-missing level values must be integers in 1..5; missing is allowed."""
    present = series.dropna()
    for value in present:
        assert float(value).is_integer(), f"{name} has a non-integer value: {value!r}"
        assert int(value) in VALID_LEVELS, f"{name} out of range 1-5: {value!r}"


# ---------------------------------------------------------------------------
# Check-in validations
# ---------------------------------------------------------------------------
def test_checkins_file_and_columns() -> None:
    checkins = _load_checkins()
    missing = CHECKIN_REQUIRED_COLUMNS - set(checkins.columns)
    assert not missing, f"Check-ins missing required columns: {missing}"


def test_checkins_state_values_valid() -> None:
    checkins = _load_checkins()
    found = set(checkins["state"].unique())
    assert found <= VALID_STATES, f"Invalid check-in states found: {found - VALID_STATES}"


def test_checkins_levels_valid() -> None:
    checkins = _load_checkins()
    _assert_levels_valid(checkins["energy_level"], "energy_level")
    _assert_levels_valid(checkins["anxiety_level"], "anxiety_level")
    _assert_levels_valid(checkins["focus_level"], "focus_level")


def test_checkins_is_synthetic_all_true() -> None:
    checkins = _load_checkins()
    assert _all_true(checkins["is_synthetic"]), "Some check-ins are not marked synthetic"


def test_checkins_timestamps_parse() -> None:
    checkins = _load_checkins()
    parsed = pd.to_datetime(checkins["created_at"], errors="coerce")
    assert parsed.notna().all(), "Some check-in created_at values could not be parsed"


def test_checkins_created_at_within_observation_window() -> None:
    """Every check-in must be created inside 2025-01-01..2025-03-31."""
    checkins = _load_checkins()
    created = pd.to_datetime(checkins["created_at"], errors="coerce")
    created_dates = created.dt.date
    out_of_range = created_dates[
        (created_dates < PERIOD_START) | (created_dates > PERIOD_END)
    ]
    assert out_of_range.empty, (
        f"Found check-in created_at values outside {PERIOD_START}..{PERIOD_END}: "
        f"{sorted(set(out_of_range))}"
    )


# ---------------------------------------------------------------------------
# Task validations
# ---------------------------------------------------------------------------
def test_tasks_file_and_columns() -> None:
    tasks = _load_tasks()
    missing = TASK_REQUIRED_COLUMNS - set(tasks.columns)
    assert not missing, f"Tasks missing required columns: {missing}"


def test_tasks_status_and_priority_valid() -> None:
    tasks = _load_tasks()
    found_status = set(tasks["status"].unique())
    assert found_status <= VALID_STATUSES, (
        f"Invalid task statuses found: {found_status - VALID_STATUSES}"
    )
    found_priority = set(tasks["priority"].unique())
    assert found_priority <= VALID_PRIORITIES, (
        f"Invalid task priorities found: {found_priority - VALID_PRIORITIES}"
    )


def test_tasks_estimated_minutes_positive() -> None:
    tasks = _load_tasks()
    assert (tasks["estimated_minutes"] > 0).all(), "estimated_minutes must be positive"


def test_tasks_is_synthetic_all_true() -> None:
    tasks = _load_tasks()
    assert _all_true(tasks["is_synthetic"]), "Some tasks are not marked synthetic"


def test_tasks_completion_consistency() -> None:
    tasks = _load_tasks()
    completed = tasks["status"] == "completed"
    has_completed_at = tasks["completed_at"].notna()

    assert (completed == has_completed_at).all(), (
        "completed_at must be present exactly for completed tasks "
        "(and absent for pending/in_progress/blocked)"
    )


def test_tasks_completed_at_after_created_at() -> None:
    tasks = _load_tasks()
    completed = tasks[tasks["status"] == "completed"].copy()
    created = pd.to_datetime(completed["created_at"], errors="coerce")
    finished = pd.to_datetime(completed["completed_at"], errors="coerce")
    assert created.notna().all(), "Some completed tasks have unparseable created_at"
    assert finished.notna().all(), "Some completed tasks have unparseable completed_at"
    assert (finished >= created).all(), "completed_at must be >= created_at"


def test_tasks_dates_parse() -> None:
    tasks = _load_tasks()
    assert pd.to_datetime(tasks["created_at"], errors="coerce").notna().all(), (
        "Some task created_at values could not be parsed"
    )
    # due_date may be missing; every present value must still parse.
    present_due = tasks["due_date"].dropna()
    assert pd.to_datetime(present_due, errors="coerce").notna().all(), (
        "Some task due_date values could not be parsed"
    )


def test_tasks_created_at_within_observation_window() -> None:
    """Every task must be created inside 2025-01-01..2025-03-31.

    Unlike due_date (see below), created_at is always bound by the fixed
    90-day observation window, since tasks are generated one day at a time
    within that range.
    """
    tasks = _load_tasks()
    created = pd.to_datetime(tasks["created_at"], errors="coerce")
    created_dates = created.dt.date
    out_of_range = created_dates[
        (created_dates < PERIOD_START) | (created_dates > PERIOD_END)
    ]
    assert out_of_range.empty, (
        f"Found task created_at values outside {PERIOD_START}..{PERIOD_END}: "
        f"{sorted(set(out_of_range))}"
    )


def test_tasks_due_date_on_or_after_created_at() -> None:
    """due_date, when present, must be on/after the task's creation date.

    due_date is intentionally allowed to fall AFTER the observation window
    (a task created near 2025-03-31 may naturally be due a few days later)
    — that is expected and is validated separately below, not rejected here.
    """
    tasks = _load_tasks()
    with_due = tasks[tasks["due_date"].notna()].copy()
    created_dates = pd.to_datetime(with_due["created_at"], errors="coerce").dt.date
    due_dates = pd.to_datetime(with_due["due_date"], errors="coerce").dt.date

    assert created_dates.notna().all(), "Some due_date rows have unparseable created_at"
    assert due_dates.notna().all(), "Some due_date values could not be parsed"
    assert (due_dates >= created_dates).all(), (
        "Found due_date values earlier than the task's created_at date"
    )


def test_tasks_due_date_may_extend_beyond_observation_window() -> None:
    """Confirms due_date is NOT clamped to PERIOD_END.

    This is not a strict requirement (a dataset with due dates that all
    happen to land inside the window would still be valid), but it
    documents and checks the intended behavior: due dates near the end of
    the observation period are allowed to extend past 2025-03-31, and the
    generator must not artificially cap them.
    """
    tasks = _load_tasks()
    due_dates = pd.to_datetime(tasks["due_date"].dropna(), errors="coerce").dt.date
    beyond_window = due_dates[due_dates > PERIOD_END]
    assert len(beyond_window) > 0, (
        "Expected at least one due_date beyond the observation window "
        f"({PERIOD_END}); found none. due_date should not be clamped to "
        "PERIOD_END."
    )


# ---------------------------------------------------------------------------
# Dataset-level validations
# ---------------------------------------------------------------------------
def test_dataset_covers_about_90_days() -> None:
    checkins = _load_checkins()
    created = pd.to_datetime(checkins["created_at"], errors="coerce")
    span_days = (created.max().normalize() - created.min().normalize()).days + 1
    assert MIN_PERIOD_SPAN_DAYS <= span_days <= MAX_PERIOD_SPAN_DAYS, (
        f"Dataset span is {span_days} days; expected ~90 "
        f"({MIN_PERIOD_SPAN_DAYS}-{MAX_PERIOD_SPAN_DAYS})"
    )


def test_dataset_has_variety() -> None:
    checkins = _load_checkins()
    tasks = _load_tasks()
    assert checkins["state"].nunique() > 1, "Expected more than one check-in state"
    assert tasks["status"].nunique() > 1, "Expected more than one task status"


def test_dataset_large_enough() -> None:
    checkins = _load_checkins()
    tasks = _load_tasks()
    assert len(checkins) >= MIN_CHECKINS, (
        f"Only {len(checkins)} check-ins; expected at least {MIN_CHECKINS}"
    )
    assert len(tasks) >= MIN_TASKS, (
        f"Only {len(tasks)} tasks; expected at least {MIN_TASKS}"
    )


# ---------------------------------------------------------------------------
# Runner (so the file works as a plain script too)
# ---------------------------------------------------------------------------
def run_all() -> None:
    checks = [
        test_checkins_file_and_columns,
        test_checkins_state_values_valid,
        test_checkins_levels_valid,
        test_checkins_is_synthetic_all_true,
        test_checkins_timestamps_parse,
        test_checkins_created_at_within_observation_window,
        test_tasks_file_and_columns,
        test_tasks_status_and_priority_valid,
        test_tasks_estimated_minutes_positive,
        test_tasks_is_synthetic_all_true,
        test_tasks_completion_consistency,
        test_tasks_completed_at_after_created_at,
        test_tasks_dates_parse,
        test_tasks_created_at_within_observation_window,
        test_tasks_due_date_on_or_after_created_at,
        test_tasks_due_date_may_extend_beyond_observation_window,
        test_dataset_covers_about_90_days,
        test_dataset_has_variety,
        test_dataset_large_enough,
    ]
    for check in checks:
        check()
        print(f"PASS  {check.__name__}")

    checkins = _load_checkins()
    tasks = _load_tasks()
    print("\nAll checks passed.")
    print(f"Check-ins: {len(checkins)}  |  Tasks: {len(tasks)}")


if __name__ == "__main__":
    run_all()