"""Generate a synthetic historical dataset for Mody (portfolio/demo only).

============================================================================
SYNTHETIC DATA — READ THIS FIRST
============================================================================
- This script generates FICTIONAL data. It does NOT represent real users.
- It exists purely for development and portfolio demonstration, so Mody's
  analytics can be shown against ~90 days of history without waiting 90 days
  for real usage to accumulate.
- The data is written to local CSV files under data/synthetic/ and is NEVER
  inserted into Supabase. Real user metrics and this demo dataset stay fully
  separate.
- The relationships encoded below (e.g. "higher energy tends to go with
  higher focus") are SYNTHETIC GENERATION ASSUMPTIONS chosen so later
  analytics has something to find. They are NOT medical or psychological
  claims and must never be used to draw conclusions about ADHD, anxiety,
  mental health, or any real person's behavior.
- Every generated row carries is_synthetic = True so it can always be told
  apart from real data.

Reproducibility: a fixed random seed and a fixed 90-day period mean running
this script always produces the same dataset (and the same screenshots).

Usage:
    python scripts/generate_synthetic_data.py
============================================================================
"""

import os
import random
from collections import Counter
from datetime import date, datetime, time, timedelta

import pandas as pd

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
SEED = 42

# Fixed synthetic period. We anchor to fixed dates (not "today") so the
# dataset and any portfolio screenshots stay reproducible over time.
# 2025-01-01 .. 2025-03-31 inclusive == exactly 90 days.
PERIOD_START = date(2025, 1, 1)
PERIOD_DAYS = 90
PERIOD_END = PERIOD_START + timedelta(days=PERIOD_DAYS - 1)

# Latest allowed timestamp: end of the last day. completed_at is capped to
# this so no completion timestamp escapes the synthetic window.
# NOTE: this cap applies ONLY to completed_at. created_at must also stay
# inside the window, but due_date is intentionally NOT capped here — a task
# created near the end of the observation period may naturally be due after
# it (see the due_date generation comment below).
PERIOD_END_CAP = datetime.combine(PERIOD_END, time(23, 59, 59))

# Paths are resolved relative to the project root (the parent of scripts/),
# so the script works regardless of the current working directory.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "synthetic")
CHECKINS_PATH = os.path.join(OUTPUT_DIR, "synthetic_checkins.csv")
TASKS_PATH = os.path.join(OUTPUT_DIR, "synthetic_tasks.csv")

# Domain values, kept identical to the real application.
STATES = ("well", "overwhelmed", "calm_needed")
PRIORITIES = ("low", "medium", "high")
TASK_STATUSES = ("pending", "in_progress", "completed", "blocked")

# Fixed column order for the CSV files.
CHECKIN_COLUMNS = [
    "synthetic_checkin_id",
    "created_at",
    "state",
    "energy_level",
    "anxiety_level",
    "focus_level",
    "is_synthetic",
]
TASK_COLUMNS = [
    "synthetic_task_id",
    "created_at",
    "completed_at",
    "status",
    "priority",
    "estimated_minutes",
    "due_date",
    "is_synthetic",
]

# Probability that any individual numeric level is left missing (None).
MISSING_LEVEL_PROBABILITY = 0.08


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _clamp(value: float, low: float, high: float) -> float:
    """Keep a value within [low, high]."""
    return max(low, min(high, value))


def _random_datetime_on(day: date) -> datetime:
    """A random daytime timestamp (06:00-21:59) on the given day."""
    return datetime.combine(
        day,
        time(random.randint(6, 21), random.randint(0, 59), random.randint(0, 59)),
    )


def _maybe_missing(value: int) -> int | None:
    """Occasionally drop a numeric level so the data has realistic gaps.
    Missing means None (later written as an empty CSV cell) — never zero."""
    return None if random.random() < MISSING_LEVEL_PROBABILITY else value


# ---------------------------------------------------------------------------
# Check-in generation
# ---------------------------------------------------------------------------
def generate_checkins() -> tuple[list[dict], dict[date, dict]]:
    """Generate synthetic check-ins and a per-day summary.

    Synthetic assumptions (generation rules only, not medical claims):
      1. Focus generally tracks energy (focus ~ energy + small noise).
      2. Low energy nudges anxiety upward.
      3. Low energy makes 'overwhelmed'/'calm_needed' more likely.
      4. High anxiety makes 'overwhelmed'/'calm_needed' more likely.
      5. Weekends lean slightly higher-energy and slightly calmer.
      6. Roughly 0-2 check-ins per day; some days have none.
    Randomness is preserved throughout, so relationships are tendencies, not
    perfect rules.

    The per-day summary uses the TRUE generated levels (before missingness)
    and later biases task completion for that day.
    """
    checkins: list[dict] = []
    day_summaries: dict[date, dict] = {}

    for offset in range(PERIOD_DAYS):
        current_day = PERIOD_START + timedelta(days=offset)
        is_weekend = current_day.weekday() >= 5

        # How many check-ins today (some days: none).
        roll = random.random()
        if roll < 0.15:
            count = 0
        elif roll < 0.70:
            count = 1
        else:
            count = 2

        day_energies: list[int] = []
        day_focuses: list[int] = []
        day_states: list[str] = []

        for _ in range(count):
            # Energy: weekends skew a little higher.
            energy_weights = [1, 1, 3, 3, 3] if is_weekend else [1, 2, 3, 3, 2]
            energy = random.choices([1, 2, 3, 4, 5], weights=energy_weights)[0]

            # Focus generally follows energy, with noise (assumption 1).
            focus = int(_clamp(energy + random.choice([-1, 0, 0, 1]), 1, 5))

            # Anxiety: mostly low-to-mid, nudged up on low-energy days (2).
            anxiety = random.choices([1, 2, 3, 4, 5], weights=[3, 3, 3, 2, 1])[0]
            if energy <= 2:
                anxiety = int(_clamp(anxiety + 1, 1, 5))

            # State weights shaped by energy and anxiety (assumptions 3-5).
            weights = {"well": 6.0, "overwhelmed": 2.0, "calm_needed": 2.0}
            if energy <= 2:
                weights["overwhelmed"] += 3.0
                weights["calm_needed"] += 1.0
            if energy >= 4:
                weights["well"] += 3.0
            if anxiety >= 4:
                weights["overwhelmed"] += 2.0
                weights["calm_needed"] += 3.0
                weights["well"] = max(0.5, weights["well"] - 2.0)
            if anxiety <= 2:
                weights["well"] += 2.0
            if is_weekend:
                weights["well"] += 1.0

            state = random.choices(STATES, weights=[weights[s] for s in STATES])[0]

            day_energies.append(energy)
            day_focuses.append(focus)
            day_states.append(state)

            checkins.append(
                {
                    "created_at": _random_datetime_on(current_day).isoformat(),
                    "state": state,
                    # Missingness applied only to the stored values.
                    "energy_level": _maybe_missing(energy),
                    "anxiety_level": _maybe_missing(anxiety),
                    "focus_level": _maybe_missing(focus),
                    "is_synthetic": True,
                }
            )

        # Day summary from TRUE levels; neutral defaults when no check-in.
        day_summaries[current_day] = {
            "avg_energy": sum(day_energies) / len(day_energies) if day_energies else 3.0,
            "avg_focus": sum(day_focuses) / len(day_focuses) if day_focuses else 3.0,
            "had_overwhelmed": any(s == "overwhelmed" for s in day_states),
        }

    # Sort chronologically and assign stable sequential ids.
    checkins.sort(key=lambda row: row["created_at"])
    for index, row in enumerate(checkins, start=1):
        row["synthetic_checkin_id"] = index

    return checkins, day_summaries


# ---------------------------------------------------------------------------
# Task generation
# ---------------------------------------------------------------------------
def generate_tasks(day_summaries: dict[date, dict]) -> list[dict]:
    """Generate synthetic tasks with temporally consistent timestamps.

    Synthetic assumptions (generation rules only, not medical claims):
      - Higher-energy and higher-focus days complete tasks a bit more often.
      - Days that included an 'overwhelmed' check-in complete a bit less.
      - High-priority tasks complete a bit more often; low-priority a bit less.
      - Weekends complete slightly less often.
    Temporal rules enforced:
      - created_at always falls inside the 90-day observation window
        (PERIOD_START..PERIOD_END), since tasks are generated one day at
        a time within that range
      - completed tasks always have completed_at >= created_at, capped at
        PERIOD_END_CAP so completion never escapes the observation window
      - non-completed tasks have completed_at = None
      - due_date (when present) is on/after the creation day, but is
        intentionally NOT capped to PERIOD_END: a task created near the end
        of the observation window may naturally be due a few days later,
        so due_date may fall after 2025-03-31. This is expected, not a bug.
    """
    tasks: list[dict] = []

    for offset in range(PERIOD_DAYS):
        current_day = PERIOD_START + timedelta(days=offset)
        is_weekend = current_day.weekday() >= 5
        summary = day_summaries[current_day]

        num_tasks = random.choices([1, 2, 3, 4], weights=[2, 3, 3, 2])[0]

        for _ in range(num_tasks):
            priority = random.choices(PRIORITIES, weights=[3, 4, 3])[0]
            estimated_minutes = random.choice([15, 20, 30, 45, 60, 90, 120])
            created_at = _random_datetime_on(current_day)

            # Completion probability from the day's context + priority.
            probability = 0.5
            probability += (summary["avg_energy"] - 3.0) * 0.06
            probability += (summary["avg_focus"] - 3.0) * 0.06
            if summary["had_overwhelmed"]:
                probability -= 0.12
            if priority == "high":
                probability += 0.12
            elif priority == "low":
                probability -= 0.08
            if is_weekend:
                probability -= 0.05
            probability = _clamp(probability, 0.05, 0.95)

            if random.random() < probability:
                status = "completed"
            else:
                status = random.choices(
                    ["pending", "in_progress", "blocked"], weights=[5, 3, 2]
                )[0]

            # completed_at: only for completed tasks, always after creation,
            # capped inside the synthetic window.
            if status == "completed":
                completed_at = created_at + timedelta(hours=random.randint(1, 60))
                if completed_at > PERIOD_END_CAP:
                    completed_at = PERIOD_END_CAP
                completed_at_value = completed_at.isoformat()
            else:
                completed_at_value = None

            # due_date: most tasks have one, on/after the creation day.
            # Intentionally NOT clamped to PERIOD_END — a task created near
            # the end of the observation window may legitimately be due
            # after 2025-03-31.
            if random.random() < 0.8:
                due_date_value = (
                    current_day + timedelta(days=random.randint(0, 7))
                ).isoformat()
            else:
                due_date_value = None

            tasks.append(
                {
                    "created_at": created_at.isoformat(),
                    "completed_at": completed_at_value,
                    "status": status,
                    "priority": priority,
                    "estimated_minutes": estimated_minutes,
                    "due_date": due_date_value,
                    "is_synthetic": True,
                }
            )

    tasks.sort(key=lambda row: row["created_at"])
    for index, row in enumerate(tasks, start=1):
        row["synthetic_task_id"] = index

    return tasks


# ---------------------------------------------------------------------------
# CSV writing
# ---------------------------------------------------------------------------
def _write_csv(records: list[dict], columns: list[str], path: str,
               nullable_int_columns: tuple[str, ...] = ()) -> pd.DataFrame:
    """Write records to CSV with a fixed column order.

    nullable_int_columns use pandas' nullable 'Int64' dtype so integers stay
    integers ("4", not "4.0") while missing values become empty cells.
    """
    frame = pd.DataFrame(records, columns=columns)
    for column in nullable_int_columns:
        frame[column] = frame[column].astype("Int64")
    frame.to_csv(path, index=False)
    return frame


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    random.seed(SEED)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    checkins, day_summaries = generate_checkins()
    tasks = generate_tasks(day_summaries)

    _write_csv(
        checkins,
        CHECKIN_COLUMNS,
        CHECKINS_PATH,
        nullable_int_columns=("energy_level", "anxiety_level", "focus_level"),
    )
    _write_csv(tasks, TASK_COLUMNS, TASKS_PATH)

    # Short, purely descriptive summary (no behavioral analysis here).
    state_counts = Counter(row["state"] for row in checkins)
    status_counts = Counter(row["status"] for row in tasks)

    print("Synthetic dataset generated successfully.")
    print(f"Check-ins: {len(checkins)}")
    print(f"Tasks: {len(tasks)}")
    print(f"Period: {PERIOD_START.isoformat()} to {PERIOD_END.isoformat()}")
    print(f"Check-in states: {dict(state_counts)}")
    print(f"Task statuses: {dict(status_counts)}")
    print(f"Files: {CHECKINS_PATH}")
    print(f"       {TASKS_PATH}")


if __name__ == "__main__":
    main()