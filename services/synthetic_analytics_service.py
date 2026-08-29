"""Behavioral analytics over Mody's SYNTHETIC 90-day demo dataset.

============================================================================
SYNTHETIC DATA — READ THIS FIRST
============================================================================
- Every number produced by this module comes from FICTIONAL data generated
  by scripts/generate_synthetic_data.py (data/synthetic/*.csv). None of it
  describes real users.
- These are portfolio/demo analytics meant to showcase Data Analyst skills
  (aggregation, grouping, KPI calculation, time-based analysis, group
  comparisons) against a dataset large enough to be interesting.
- The behavioral relationships visible in this data (e.g. energy vs. task
  completion) were INTENTIONALLY introduced by the generator so there would
  be something to find. They are generation assumptions, not discoveries
  about real behavior.
- Every metric here is an ASSOCIATION observed in synthetic data, never a
  causal claim. Phrases like "X causes Y" or "X leads to Y" must not be
  attached to these numbers.
- Nothing in this module may be used to produce medical, psychological,
  ADHD, or anxiety conclusions, about anyone, real or synthetic.
============================================================================

Scope of this module:
- Reads ONLY data/synthetic/synthetic_checkins.csv and
  data/synthetic/synthetic_tasks.csv.
- NEVER touches Supabase, RLS, or the real-user analytics service
  (services/analytics_service.py). The two analytics layers are
  intentionally kept separate so synthetic and real metrics can never
  mix or be confused with each other.

============================================================================
DATA-GRAIN DECISION (important)
============================================================================
Check-ins and tasks have different grains: a single day can have zero, one,
or several check-ins, and separately zero or several tasks. Joining
individual check-in rows directly to individual task rows would create a
many-to-many join and silently duplicate observations (e.g. 3 check-ins x
4 tasks on the same day would produce 12 rows, inflating every count).

To avoid this, any analysis that needs BOTH check-ins and tasks first
aggregates each dataset to one row per DATE (get_daily_checkin_metrics,
get_daily_task_metrics), and only THEN merges those two daily tables on
`date`. Analyses that only need one dataset (e.g. completion by priority,
or check-in metrics by weekday) work directly off the raw rows, since no
cross-grain join is required for those.
"""

import os
from datetime import date as date_cls

import pandas as pd

# ---------------------------------------------------------------------------
# Paths (resolved relative to the project root, parent of services/)
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHECKINS_PATH = os.path.join(BASE_DIR, "data", "synthetic", "synthetic_checkins.csv")
TASKS_PATH = os.path.join(BASE_DIR, "data", "synthetic", "synthetic_tasks.csv")

# ---------------------------------------------------------------------------
# Fixed orderings / groupings, kept consistent with the rest of the project
# ---------------------------------------------------------------------------
CHECKIN_STATE_ORDER = ["well", "overwhelmed", "calm_needed"]
PRIORITY_ORDER = ["low", "medium", "high"]
WEEKDAY_ORDER = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]
ENERGY_GROUP_ORDER = ["Low", "Medium", "High"]
FOCUS_GROUP_ORDER = ["Low", "Medium", "High"]
OVERWHELMED_GROUP_ORDER = ["Days with overwhelmed check-in", "Other check-in days"]
WEEKDAY_VS_WEEKEND_ORDER = ["Weekday", "Weekend"]

# Group boundaries, as specified: Low < 2.5 <= Medium < 4.0 <= High.
LOW_MAX = 2.5
HIGH_MIN = 4.0


# ---------------------------------------------------------------------------
# Small numeric helpers
# ---------------------------------------------------------------------------
def _completion_rate(completed: int, total: int) -> float:
    """completed / total * 100, rounded to 1 decimal. 0.0 when total is 0."""
    if total == 0:
        return 0.0
    return round(completed / total * 100, 1)


def _round_or_none(value) -> float | None:
    """Round a numeric value to 1 decimal, or None when it is missing
    (NaN/None). Missing is NEVER turned into 0 — a group with no numeric
    observations reports 'no data' (None), not a zero average."""
    if value is None or pd.isna(value):
        return None
    return round(float(value), 1)


def _level_group(value: float | None, low_max: float, high_min: float) -> str | None:
    """Classify a daily average level into Low/Medium/High. None in, None
    out — a day with no numeric average cannot be grouped."""
    if value is None or pd.isna(value):
        return None
    if value < low_max:
        return "Low"
    if value >= high_min:
        return "High"
    return "Medium"


def _weekday_name(value: date_cls) -> str:
    """English weekday name (Monday..Sunday) for a date."""
    return value.strftime("%A")


def _is_weekend(value: date_cls) -> bool:
    """Saturday and Sunday are weekend; Monday-Friday are weekday."""
    return value.weekday() >= 5


# ---------------------------------------------------------------------------
# Loading (raw data, one row per check-in / task)
# ---------------------------------------------------------------------------
def _filter_synthetic(frame: pd.DataFrame) -> pd.DataFrame:
    """Keep only rows explicitly marked is_synthetic. Defensive: accepts
    either a real bool True or the string 'True', since CSV round-tripping
    can produce either depending on the pandas version reading the file."""
    mask = frame["is_synthetic"].map(lambda v: v is True or v == "True")
    return frame[mask].copy()


def load_synthetic_checkins() -> pd.DataFrame:
    """Load the raw synthetic check-in rows (one row per check-in).

    Adds a `date` column (Python date) derived from `created_at` for
    downstream daily aggregation. Numeric level columns keep NaN for
    missing values — they are never coerced to 0.
    """
    if not os.path.exists(CHECKINS_PATH):
        raise FileNotFoundError(
            f"Synthetic check-ins file not found at {CHECKINS_PATH}. "
            "Run: python scripts/generate_synthetic_data.py"
        )

    frame = pd.read_csv(CHECKINS_PATH)
    frame = _filter_synthetic(frame)
    frame["created_at"] = pd.to_datetime(frame["created_at"])
    frame["date"] = frame["created_at"].dt.date
    return frame


def load_synthetic_tasks() -> pd.DataFrame:
    """Load the raw synthetic task rows (one row per task).

    Adds a `date` column (Python date) derived from `created_at` for
    downstream daily aggregation. `completed_at` and `due_date` are parsed
    as datetimes but may legitimately be NaT (missing).
    """
    if not os.path.exists(TASKS_PATH):
        raise FileNotFoundError(
            f"Synthetic tasks file not found at {TASKS_PATH}. "
            "Run: python scripts/generate_synthetic_data.py"
        )

    frame = pd.read_csv(TASKS_PATH)
    frame = _filter_synthetic(frame)
    frame["created_at"] = pd.to_datetime(frame["created_at"])
    frame["completed_at"] = pd.to_datetime(frame["completed_at"])
    frame["due_date"] = pd.to_datetime(frame["due_date"])
    frame["date"] = frame["created_at"].dt.date
    return frame


# ---------------------------------------------------------------------------
# Daily aggregation (the grain used for any check-in + task merge)
# ---------------------------------------------------------------------------
def get_daily_checkin_metrics() -> pd.DataFrame:
    """Aggregate check-ins to one row per date.

    Columns: date, avg_energy, avg_anxiety, avg_focus, checkin_count,
    had_well, had_overwhelmed, had_calm_needed.

    Only dates that actually have at least one check-in appear here — a day
    with zero check-ins has nothing to average, so it is simply absent
    rather than represented with a fabricated value. Averages use pandas'
    default skipna behavior, so missing energy/anxiety/focus values are
    ignored rather than treated as 0; a date where every value for a given
    metric is missing reports NaN for that metric (surfaced as None by the
    public functions that consume this table).
    """
    checkins = load_synthetic_checkins()

    grouped = checkins.groupby("date")
    daily = grouped.agg(
        avg_energy=("energy_level", "mean"),
        avg_anxiety=("anxiety_level", "mean"),
        avg_focus=("focus_level", "mean"),
        checkin_count=("state", "count"),
    ).reset_index()

    had_well = grouped["state"].apply(lambda s: (s == "well").any())
    had_overwhelmed = grouped["state"].apply(lambda s: (s == "overwhelmed").any())
    had_calm_needed = grouped["state"].apply(lambda s: (s == "calm_needed").any())

    daily["had_well"] = daily["date"].map(had_well)
    daily["had_overwhelmed"] = daily["date"].map(had_overwhelmed)
    daily["had_calm_needed"] = daily["date"].map(had_calm_needed)

    return daily.sort_values("date").reset_index(drop=True)


def get_daily_task_metrics() -> pd.DataFrame:
    """Aggregate tasks to one row per creation date.

    Columns: date, task_count, completed_tasks, pending_tasks,
    in_progress_tasks, blocked_tasks, completion_rate.

    The generator creates at least one task every day of the 90-day window,
    so every observation date is expected to appear here.
    """
    tasks = load_synthetic_tasks()

    def _count_status(frame: pd.DataFrame, status: str) -> int:
        return int((frame["status"] == status).sum())

    rows = []
    for day, group in tasks.groupby("date"):
        task_count = len(group)
        completed = _count_status(group, "completed")
        rows.append(
            {
                "date": day,
                "task_count": task_count,
                "completed_tasks": completed,
                "pending_tasks": _count_status(group, "pending"),
                "in_progress_tasks": _count_status(group, "in_progress"),
                "blocked_tasks": _count_status(group, "blocked"),
                "completion_rate": _completion_rate(completed, task_count),
            }
        )

    daily = pd.DataFrame(rows)
    return daily.sort_values("date").reset_index(drop=True)


# ---------------------------------------------------------------------------
# Q1 — overall task completion rate
# ---------------------------------------------------------------------------
def get_overall_task_metrics() -> dict:
    """Overall task counts and completion rate across the full dataset."""
    tasks = load_synthetic_tasks()
    total = len(tasks)
    completed = int((tasks["status"] == "completed").sum())

    return {
        "total_tasks": total,
        "completed_tasks": completed,
        "pending_tasks": int((tasks["status"] == "pending").sum()),
        "in_progress_tasks": int((tasks["status"] == "in_progress").sum()),
        "blocked_tasks": int((tasks["status"] == "blocked").sum()),
        "completion_rate": _completion_rate(completed, total),
    }


# ---------------------------------------------------------------------------
# Q2 — completion rate by priority
# ---------------------------------------------------------------------------
def get_completion_by_priority() -> list[dict]:
    """Task completion rate grouped by priority, in low/medium/high order."""
    tasks = load_synthetic_tasks()

    results = []
    for priority in PRIORITY_ORDER:
        group = tasks[tasks["priority"] == priority]
        total = len(group)
        completed = int((group["status"] == "completed").sum())
        results.append(
            {
                "priority": priority,
                "task_count": total,
                "completed_tasks": completed,
                "completion_rate": _completion_rate(completed, total),
            }
        )
    return results


# ---------------------------------------------------------------------------
# Q3 — completion rate by weekday (tasks only, no check-in merge needed)
# ---------------------------------------------------------------------------
def get_completion_by_weekday() -> list[dict]:
    """Task completion rate grouped by weekday (Monday..Sunday order)."""
    tasks = load_synthetic_tasks()
    tasks = tasks.copy()
    tasks["weekday"] = tasks["date"].map(_weekday_name)

    results = []
    for weekday in WEEKDAY_ORDER:
        group = tasks[tasks["weekday"] == weekday]
        total = len(group)
        completed = int((group["status"] == "completed").sum())
        results.append(
            {
                "weekday": weekday,
                "task_count": total,
                "completed_tasks": completed,
                "completion_rate": _completion_rate(completed, total),
            }
        )
    return results


# ---------------------------------------------------------------------------
# Q4 — average energy/anxiety/focus by weekday (check-ins only)
# ---------------------------------------------------------------------------
def get_checkin_metrics_by_weekday() -> list[dict]:
    """Average energy/anxiety/focus grouped by weekday (Monday..Sunday).

    This uses the raw check-in rows directly (not the daily-aggregated
    table): since no task data is involved, there is no cross-grain merge
    to protect against, so individual check-ins can be averaged directly
    per weekday.
    """
    checkins = load_synthetic_checkins()
    checkins = checkins.copy()
    checkins["weekday"] = checkins["date"].map(_weekday_name)

    results = []
    for weekday in WEEKDAY_ORDER:
        group = checkins[checkins["weekday"] == weekday]
        results.append(
            {
                "weekday": weekday,
                "checkin_count": len(group),
                "avg_energy": _round_or_none(group["energy_level"].mean()),
                "avg_anxiety": _round_or_none(group["anxiety_level"].mean()),
                "avg_focus": _round_or_none(group["focus_level"].mean()),
            }
        )
    return results


# ---------------------------------------------------------------------------
# Q5 — check-in state distribution
# ---------------------------------------------------------------------------
def get_checkin_state_distribution() -> list[dict]:
    """Check-in counts per state, in the fixed well/overwhelmed/calm_needed
    order. All three states are always returned, even if a count is 0."""
    checkins = load_synthetic_checkins()
    counts = checkins["state"].value_counts()

    return [
        {"state": state, "count": int(counts.get(state, 0))}
        for state in CHECKIN_STATE_ORDER
    ]


# ---------------------------------------------------------------------------
# Q6 — check-in evolution over the 90-day period
# ---------------------------------------------------------------------------
def get_checkin_timeseries() -> list[dict]:
    """Chronological daily check-in metrics: date, avg_energy, avg_anxiety,
    avg_focus, checkin_count. One row per date that has at least one
    check-in; missing numeric averages are reported as None, never 0."""
    daily = get_daily_checkin_metrics()

    return [
        {
            "date": row.date.isoformat(),
            "avg_energy": _round_or_none(row.avg_energy),
            "avg_anxiety": _round_or_none(row.avg_anxiety),
            "avg_focus": _round_or_none(row.avg_focus),
            "checkin_count": int(row.checkin_count),
        }
        for row in daily.itertuples()
    ]


# ---------------------------------------------------------------------------
# Shared helper for the daily-merge group comparisons (Q7, Q8, Q9)
# ---------------------------------------------------------------------------
def _merge_daily_datasets() -> pd.DataFrame:
    """Merge the two daily-grain tables on `date` (inner join).

    Only dates with at least one check-in are kept, since check-in metrics
    (energy/focus/overwhelmed) are undefined on days without a check-in.
    This is the single, reusable point where check-ins and tasks are joined
    at matching grain, per the data-grain decision documented at the top of
    this module — it must never be replaced with a raw row-level join.
    """
    daily_checkins = get_daily_checkin_metrics()
    daily_tasks = get_daily_task_metrics()
    return daily_checkins.merge(daily_tasks, on="date", how="inner")


def _aggregate_by_group(
    merged: pd.DataFrame, group_labels: pd.Series, group_order: list[str]
) -> list[dict]:
    """Sum task_count/completed_tasks per group and compute completion_rate.

    group_order guarantees every listed group appears in the output, with
    zeros when a group happens to have no matching days. Rows whose group
    label is None (e.g. a day that couldn't be classified) are excluded.
    """
    working = merged.copy()
    working["_group"] = group_labels

    results = []
    for label in group_order:
        subset = working[working["_group"] == label]
        task_count = int(subset["task_count"].sum())
        completed = int(subset["completed_tasks"].sum())
        results.append(
            {
                "group": label,
                "number_of_days": len(subset),
                "task_count": task_count,
                "completed_tasks": completed,
                "completion_rate": _completion_rate(completed, task_count),
            }
        )
    return results


# ---------------------------------------------------------------------------
# Q7 — completion rate by daily energy level
# ---------------------------------------------------------------------------
def get_completion_by_energy() -> list[dict]:
    """Task completion rate grouped by daily average energy (Low/Medium/
    High, per the 2.5 / 4.0 thresholds). Only dates with a defined daily
    avg_energy are included. Descriptive association only — this does not
    claim energy causes task completion."""
    merged = _merge_daily_datasets()
    merged = merged[merged["avg_energy"].notna()]
    groups = merged["avg_energy"].apply(lambda v: _level_group(v, LOW_MAX, HIGH_MIN))

    results = _aggregate_by_group(merged, groups, ENERGY_GROUP_ORDER)
    for row in results:
        row["energy_group"] = row.pop("group")
    return results


# ---------------------------------------------------------------------------
# Q8 — completion rate by daily focus level
# ---------------------------------------------------------------------------
def get_completion_by_focus() -> list[dict]:
    """Task completion rate grouped by daily average focus (Low/Medium/
    High, per the 2.5 / 4.0 thresholds). Only dates with a defined daily
    avg_focus are included. Descriptive association only — this does not
    claim focus causes task completion."""
    merged = _merge_daily_datasets()
    merged = merged[merged["avg_focus"].notna()]
    groups = merged["avg_focus"].apply(lambda v: _level_group(v, LOW_MAX, HIGH_MIN))

    results = _aggregate_by_group(merged, groups, FOCUS_GROUP_ORDER)
    for row in results:
        row["focus_group"] = row.pop("group")
    return results


# ---------------------------------------------------------------------------
# Q9 — completion rate on overwhelmed vs. other check-in days
# ---------------------------------------------------------------------------
def get_completion_by_overwhelmed_state() -> list[dict]:
    """Compares task completion on days that included an 'overwhelmed'
    check-in against other check-in days. Only dates with check-in data are
    included (had_overwhelmed is only meaningful when a check-in exists).

    Neutral naming is used deliberately: this reports an observed
    association in synthetic data, NOT a claim that the overwhelmed state
    causes lower (or higher) task completion.
    """
    merged = _merge_daily_datasets()
    labels = merged["had_overwhelmed"].map(
        {True: "Days with overwhelmed check-in", False: "Other check-in days"}
    )
    return _aggregate_by_group(merged, labels, OVERWHELMED_GROUP_ORDER)


# ---------------------------------------------------------------------------
# Q10 — weekday vs. weekend
# ---------------------------------------------------------------------------
def get_weekday_vs_weekend_metrics() -> list[dict]:
    """Compares Weekday vs. Weekend across both tasks and check-ins.

    Task metrics (number_of_days, task_count, completed_tasks,
    completion_rate) are computed from the daily task table
    (get_daily_task_metrics): each day is classified as Weekday or Weekend
    and the per-day counts are summed within each group.

    Check-in averages (avg_energy, avg_anxiety, avg_focus) are computed
    directly from the RAW individual check-in observations, not from an
    average of daily averages: each check-in row is classified as Weekday
    or Weekend by its own date, and the mean is taken across all matching
    check-ins. This gives every check-in equal weight regardless of how
    many check-ins occurred on its day — e.g. a day with a single energy=5
    check-in and a day with two energy=2 check-ins average to (5+2+2)/3,
    not (5+2)/2. Missing numeric values are skipped, never treated as 0.

    Task counts and check-in averages are computed independently, each at
    its own natural grain, and combined only as final per-group scalars in
    the returned dict — this function never joins raw check-in rows to raw
    task rows, so the many-to-many protection is preserved.
    """
    daily_tasks = get_daily_task_metrics().copy()
    daily_tasks["group"] = daily_tasks["date"].map(
        lambda d: "Weekend" if _is_weekend(d) else "Weekday"
    )

    checkins = load_synthetic_checkins().copy()
    checkins["group"] = checkins["date"].map(
        lambda d: "Weekend" if _is_weekend(d) else "Weekday"
    )

    results = []
    for label in WEEKDAY_VS_WEEKEND_ORDER:
        task_subset = daily_tasks[daily_tasks["group"] == label]
        task_count = int(task_subset["task_count"].sum())
        completed = int(task_subset["completed_tasks"].sum())

        checkin_subset = checkins[checkins["group"] == label]

        results.append(
            {
                "group": label,
                "number_of_days": len(task_subset),
                "task_count": task_count,
                "completed_tasks": completed,
                "completion_rate": _completion_rate(completed, task_count),
                "avg_energy": _round_or_none(checkin_subset["energy_level"].mean()),
                "avg_anxiety": _round_or_none(checkin_subset["anxiety_level"].mean()),
                "avg_focus": _round_or_none(checkin_subset["focus_level"].mean()),
            }
        )
    return results