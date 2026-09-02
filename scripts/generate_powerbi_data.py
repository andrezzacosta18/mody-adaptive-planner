"""Generate the final synthetic dataset for the Mody Power BI project.

All generated data is synthetic and does not represent real Mody users.

Final output:
    data/powerbi/dim_users.csv
    data/powerbi/dim_date.csv
    data/powerbi/fact_tasks.csv
    data/powerbi/fact_checkins.csv
"""

from pathlib import Path
import random

import numpy as np
import pandas as pd


# =========================================================
# CONFIGURATION
# =========================================================

RANDOM_SEED = 42

random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

NUM_USERS = 100

START_DATE = pd.Timestamp("2026-06-01")
NUM_DAYS = 90
END_DATE = START_DATE + pd.Timedelta(days=NUM_DAYS - 1)

TARGET_TASKS = 2500
TARGET_CHECKINS = 5000

OUTPUT_DIR = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "powerbi"
)


# =========================================================
# TASK GENERATION RULES
# =========================================================

TASK_PRIORITIES = [
    "low",
    "medium",
    "high",
]

TASK_PRIORITY_PROBABILITIES = [
    0.30,
    0.45,
    0.25,
]


TASK_DURATIONS = [
    15,
    30,
    45,
    60,
    90,
    120,
]

TASK_DURATION_PROBABILITIES = [
    0.15,
    0.30,
    0.20,
    0.20,
    0.10,
    0.05,
]


# =========================================================
# DUE DATE RULES
# =========================================================

DUE_DATE_PROBABILITY = 0.85
MAX_DUE_DATE_OFFSET_DAYS = 14


# =========================================================
# COMPLETION RULES
# =========================================================

BASE_COMPLETION_PROBABILITY = 0.72


# Priority effect
PRIORITY_COMPLETION_ADJUSTMENTS = {
    "low": -0.04,
    "medium": 0.00,
    "high": 0.06,
}


# Estimated duration effect
DURATION_COMPLETION_ADJUSTMENTS = {
    15: 0.04,
    30: 0.03,
    45: 0.01,
    60: 0.00,
    90: -0.04,
    120: -0.07,
}


# Check-in effect
#
# IMPORTANT:
# These values create a designed SYNTHETIC association.
# They do not represent a causal or medical relationship.
#
# The effect is intentionally strong enough to remain
# visible after random variation, priority differences,
# and task-duration differences.
CHECKIN_COMPLETION_ADJUSTMENTS = {
    "well": 0.08,
    "calm_needed": 0.00,
    "overwhelmed": -0.10,
}


MIN_COMPLETION_PROBABILITY = 0.45
MAX_COMPLETION_PROBABILITY = 0.90


# =========================================================
# CHECK-IN GENERATION RULES
# =========================================================

CHECKIN_STATES = [
    "well",
    "overwhelmed",
    "calm_needed",
]

CHECKIN_STATE_PROBABILITIES = [
    0.55,
    0.25,
    0.20,
]


USER_ACTIVITY_LEVELS = [
    "rare",
    "occasional",
    "frequent",
]

USER_ACTIVITY_PROBABILITIES = [
    0.20,
    0.50,
    0.30,
]


USER_ACTIVITY_WEIGHTS = {
    "rare": 0.35,
    "occasional": 1.00,
    "frequent": 1.80,
}


# =========================================================
# USERS
# =========================================================

def generate_users():
    """Generate synthetic users."""

    users = []

    for i in range(1, NUM_USERS + 1):

        activity_level = np.random.choice(
            USER_ACTIVITY_LEVELS,
            p=USER_ACTIVITY_PROBABILITIES,
        )

        users.append(
            {
                "user_id": f"USR_{i:03d}",
                "activity_level": activity_level,
            }
        )

    return pd.DataFrame(users)


# =========================================================
# CHECK-INS
# =========================================================

def generate_checkins(dim_users):
    """Generate synthetic check-in events."""

    checkins = []

    user_ids = dim_users["user_id"].tolist()

    activity_weights = (
        dim_users["activity_level"]
        .map(USER_ACTIVITY_WEIGHTS)
        .astype(float)
        .to_numpy()
    )

    user_probabilities = (
        activity_weights
        / activity_weights.sum()
    )

    for i in range(1, TARGET_CHECKINS + 1):

        checkin_id = f"CHK_{i:06d}"

        user_id = np.random.choice(
            user_ids,
            p=user_probabilities,
        )

        day_offset = np.random.randint(
            0,
            NUM_DAYS,
        )

        checkin_date = (
            START_DATE
            + pd.Timedelta(
                days=int(day_offset)
            )
        )

        hour = np.random.randint(
            6,
            23,
        )

        minute = np.random.randint(
            0,
            60,
        )

        created_at = (
            checkin_date
            + pd.Timedelta(hours=int(hour))
            + pd.Timedelta(minutes=int(minute))
        )

        state = np.random.choice(
            CHECKIN_STATES,
            p=CHECKIN_STATE_PROBABILITIES,
        )

        checkins.append(
            {
                "checkin_id": checkin_id,
                "user_id": user_id,
                "state": state,
                "created_at": created_at,
            }
        )

    return pd.DataFrame(checkins)


# =========================================================
# DAILY CHECK-IN STATE
# =========================================================

def derive_daily_checkin_state(fact_checkins):
    """
    Derive one check-in state per user and date.

    If multiple check-ins exist on the same day,
    the latest check-in is selected.
    """

    daily_checkins = fact_checkins.copy()

    daily_checkins["date"] = (
        daily_checkins["created_at"]
        .dt.normalize()
    )

    daily_checkins = (
        daily_checkins
        .sort_values(
            [
                "user_id",
                "date",
                "created_at",
            ]
        )
    )

    daily_checkins = (
        daily_checkins
        .groupby(
            [
                "user_id",
                "date",
            ],
            as_index=False,
        )
        .tail(1)
    )

    daily_checkins = (
        daily_checkins[
            [
                "user_id",
                "date",
                "state",
                "created_at",
            ]
        ]
        .rename(
            columns={
                "state": "daily_checkin_state",
                "created_at": "daily_checkin_created_at",
            }
        )
        .reset_index(drop=True)
    )

    return daily_checkins


# =========================================================
# TASK STRUCTURE
# =========================================================

def generate_task_structure(dim_users):
    """
    Generate task attributes.

    Completion status is not generated here.
    It is generated only after the daily
    check-in state has been associated.
    """

    tasks = []

    user_ids = dim_users["user_id"].tolist()

    for i in range(1, TARGET_TASKS + 1):

        task_id = f"TSK_{i:06d}"

        user_id = np.random.choice(
            user_ids
        )

        # -------------------------------------------------
        # Creation date/time
        # -------------------------------------------------

        day_offset = np.random.randint(
            0,
            NUM_DAYS,
        )

        created_date = (
            START_DATE
            + pd.Timedelta(
                days=int(day_offset)
            )
        )

        hour = np.random.randint(
            7,
            23,
        )

        minute = np.random.randint(
            0,
            60,
        )

        created_at = (
            created_date
            + pd.Timedelta(hours=int(hour))
            + pd.Timedelta(minutes=int(minute))
        )

        # -------------------------------------------------
        # Priority
        # -------------------------------------------------

        priority = np.random.choice(
            TASK_PRIORITIES,
            p=TASK_PRIORITY_PROBABILITIES,
        )

        # -------------------------------------------------
        # Estimated duration
        # -------------------------------------------------

        estimated_minutes = int(
            np.random.choice(
                TASK_DURATIONS,
                p=TASK_DURATION_PROBABILITIES,
            )
        )

        # -------------------------------------------------
        # Due date
        # -------------------------------------------------

        has_due_date = (
            np.random.random()
            < DUE_DATE_PROBABILITY
        )

        if has_due_date:

            due_offset = np.random.randint(
                0,
                MAX_DUE_DATE_OFFSET_DAYS + 1,
            )

            due_date = (
                created_at.normalize()
                + pd.Timedelta(
                    days=int(due_offset)
                )
            )

        else:
            due_date = pd.NaT

        title = f"Synthetic Task {i:04d}"

        tasks.append(
            {
                "task_id": task_id,
                "user_id": user_id,
                "title": title,
                "priority": priority,
                "estimated_minutes": estimated_minutes,
                "due_date": due_date,
                "created_at": created_at,
            }
        )

    return pd.DataFrame(tasks)


# =========================================================
# MATCH TASKS WITH DAILY CHECK-IN
# =========================================================

def match_tasks_with_daily_checkins(
    fact_tasks,
    daily_checkins,
):
    """
    Match each task with the user's daily state.

    Key:
        user_id + task creation date
    """

    tasks = fact_tasks.copy()

    tasks["created_date"] = (
        tasks["created_at"]
        .dt.normalize()
    )

    tasks = tasks.merge(
        daily_checkins[
            [
                "user_id",
                "date",
                "daily_checkin_state",
            ]
        ],
        left_on=[
            "user_id",
            "created_date",
        ],
        right_on=[
            "user_id",
            "date",
        ],
        how="left",
    )

    tasks = tasks.drop(
        columns=["date"]
    )

    return tasks


# =========================================================
# FINAL COMPLETION PROBABILITY
# =========================================================

def calculate_final_completion_probability(
    priority,
    estimated_minutes,
    daily_checkin_state,
):
    """
    Calculate final synthetic completion probability.

    Formula:

        baseline
        + priority adjustment
        + duration adjustment
        + check-in adjustment

    Missing check-in:
        no adjustment
    """

    probability = (
        BASE_COMPLETION_PROBABILITY
    )

    probability += (
        PRIORITY_COMPLETION_ADJUSTMENTS[
            priority
        ]
    )

    probability += (
        DURATION_COMPLETION_ADJUSTMENTS[
            estimated_minutes
        ]
    )

    if pd.notna(
        daily_checkin_state
    ):

        probability += (
            CHECKIN_COMPLETION_ADJUSTMENTS[
                daily_checkin_state
            ]
        )

    probability = max(
        MIN_COMPLETION_PROBABILITY,
        min(
            probability,
            MAX_COMPLETION_PROBABILITY,
        ),
    )

    return probability


# =========================================================
# COMPLETION TIMESTAMP
# =========================================================

def generate_completed_at(created_at):
    """Generate a valid completion timestamp."""

    completion_offset_days = (
        np.random.randint(
            0,
            8,
        )
    )

    completion_date = (
        created_at.normalize()
        + pd.Timedelta(
            days=int(completion_offset_days)
        )
    )

    hour = np.random.randint(
        7,
        23,
    )

    minute = np.random.randint(
        0,
        60,
    )

    completed_at = (
        completion_date
        + pd.Timedelta(hours=int(hour))
        + pd.Timedelta(minutes=int(minute))
    )

    # Completion must never occur before creation.
    if completed_at < created_at:

        completed_at = (
            created_at
            + pd.Timedelta(
                minutes=int(
                    np.random.randint(
                        15,
                        241,
                    )
                )
            )
        )

    return completed_at


# =========================================================
# FINALIZE TASKS
# =========================================================

def finalize_tasks(tasks_with_checkins):
    """
    Calculate final probability and generate
    task status exactly once.
    """

    tasks = tasks_with_checkins.copy()

    probabilities = []
    statuses = []
    completion_dates = []

    for _, row in tasks.iterrows():

        probability = (
            calculate_final_completion_probability(
                priority=row["priority"],
                estimated_minutes=row[
                    "estimated_minutes"
                ],
                daily_checkin_state=row[
                    "daily_checkin_state"
                ],
            )
        )

        probabilities.append(
            probability
        )

        is_completed = (
            np.random.random()
            < probability
        )

        if is_completed:

            status = "completed"

            completed_at = (
                generate_completed_at(
                    row["created_at"]
                )
            )

        else:

            status = "pending"
            completed_at = pd.NaT

        statuses.append(
            status
        )

        completion_dates.append(
            completed_at
        )

    tasks[
        "completion_probability"
    ] = probabilities

    tasks[
        "status"
    ] = statuses

    tasks[
        "completed_at"
    ] = pd.to_datetime(
        completion_dates
    )

    return tasks


# =========================================================
# DATE DIMENSION
# =========================================================

def generate_date_dimension(fact_tasks):
    """
    Generate the complete calendar dimension.

    It covers:
        created_at
        due_date
        completed_at
    """

    relevant_dates = [
        END_DATE
    ]

    if fact_tasks[
        "due_date"
    ].notna().any():

        relevant_dates.append(
            fact_tasks[
                "due_date"
            ].max()
        )

    if fact_tasks[
        "completed_at"
    ].notna().any():

        relevant_dates.append(
            fact_tasks[
                "completed_at"
            ]
            .max()
            .normalize()
        )

    calendar_end_date = max(
        relevant_dates
    )

    dates = pd.date_range(
        start=START_DATE,
        end=calendar_end_date,
        freq="D",
    )

    dim_date = pd.DataFrame(
        {
            "date": dates
        }
    )

    dim_date[
        "year"
    ] = dim_date["date"].dt.year

    dim_date[
        "month"
    ] = (
        dim_date["date"]
        .dt.to_period("M")
        .astype(str)
    )

    dim_date[
        "month_number"
    ] = dim_date["date"].dt.month

    dim_date[
        "month_name"
    ] = dim_date["date"].dt.month_name()

    dim_date[
        "weekday"
    ] = dim_date["date"].dt.day_name()

    dim_date[
        "weekday_number"
    ] = (
        dim_date["date"].dt.weekday
        + 1
    )

    dim_date[
        "weekday_name"
    ] = dim_date["date"].dt.day_name()

    dim_date[
        "is_weekend"
    ] = (
        dim_date["date"].dt.weekday
        >= 5
    )

    return dim_date


# =========================================================
# VALIDATION
# =========================================================

def validate_dataset(
    dim_users,
    dim_date,
    fact_tasks,
    fact_checkins,
    daily_checkins,
):
    """Validate the final synthetic dataset."""

    print("\n" + "=" * 60)
    print("FINAL DATASET VALIDATION")
    print("=" * 60)

    # -----------------------------------------------------
    # Record counts
    # -----------------------------------------------------

    print("\nRecord counts:")

    print(
        f"Users: {len(dim_users)}"
    )

    print(
        f"Date rows: {len(dim_date)}"
    )

    print(
        f"Tasks: {len(fact_tasks)}"
    )

    print(
        f"Check-ins: {len(fact_checkins)}"
    )

    print(
        f"Daily check-in records: "
        f"{len(daily_checkins)}"
    )

    # -----------------------------------------------------
    # Check-in distribution
    # -----------------------------------------------------

    print(
        "\nCheck-in state distribution:"
    )

    print(
        fact_checkins[
            "state"
        ]
        .value_counts(
            normalize=True
        )
        .mul(100)
        .round(2)
    )

    # -----------------------------------------------------
    # Daily state
    # -----------------------------------------------------

    duplicate_daily_keys = (
        daily_checkins
        .duplicated(
            subset=[
                "user_id",
                "date",
            ]
        )
        .sum()
    )

    print(
        "\nDaily state validation:"
    )

    print(
        f"Duplicate User + Date keys: "
        f"{duplicate_daily_keys}"
    )

    # -----------------------------------------------------
    # Task/check-in matching
    # -----------------------------------------------------

    tasks_with_checkin = (
        fact_tasks[
            "daily_checkin_state"
        ]
        .notna()
        .sum()
    )

    match_rate = (
        tasks_with_checkin
        / len(fact_tasks)
        * 100
    )

    print(
        f"Tasks with daily check-in: "
        f"{tasks_with_checkin}"
    )

    print(
        f"Task/check-in match rate: "
        f"{match_rate:.2f}%"
    )

    # -----------------------------------------------------
    # Completion
    # -----------------------------------------------------

    completed_tasks = (
        fact_tasks[
            "status"
        ]
        .eq("completed")
        .sum()
    )

    pending_tasks = (
        fact_tasks[
            "status"
        ]
        .eq("pending")
        .sum()
    )

    completion_rate = (
        completed_tasks
        / len(fact_tasks)
        * 100
    )

    print(
        "\nTask completion:"
    )

    print(
        f"Completed tasks: "
        f"{completed_tasks}"
    )

    print(
        f"Pending tasks: "
        f"{pending_tasks}"
    )

    print(
        f"Overall completion rate: "
        f"{completion_rate:.2f}%"
    )

    # -----------------------------------------------------
    # Probability
    # -----------------------------------------------------

    print(
        "\nCompletion probability:"
    )

    print(
        f"Minimum: "
        f"{fact_tasks['completion_probability'].min():.2%}"
    )

    print(
        f"Maximum: "
        f"{fact_tasks['completion_probability'].max():.2%}"
    )

    # -----------------------------------------------------
    # Timestamp integrity
    # -----------------------------------------------------

    completed_rows = (
        fact_tasks[
            fact_tasks["status"]
            == "completed"
        ]
    )

    pending_rows = (
        fact_tasks[
            fact_tasks["status"]
            == "pending"
        ]
    )

    completed_before_creation = (
        completed_rows[
            completed_rows[
                "completed_at"
            ]
            < completed_rows[
                "created_at"
            ]
        ]
    )

    completed_without_date = (
        completed_rows[
            completed_rows[
                "completed_at"
            ]
            .isna()
        ]
    )

    pending_with_date = (
        pending_rows[
            pending_rows[
                "completed_at"
            ]
            .notna()
        ]
    )

    print(
        "\nTimestamp integrity:"
    )

    print(
        f"Completed before creation: "
        f"{len(completed_before_creation)}"
    )

    print(
        f"Completed without completed_at: "
        f"{len(completed_without_date)}"
    )

    print(
        f"Pending with completed_at: "
        f"{len(pending_with_date)}"
    )

    # -----------------------------------------------------
    # Due date validation
    # -----------------------------------------------------

    due_date_percentage = (
        fact_tasks[
            "due_date"
        ]
        .notna()
        .mean()
        * 100
    )

    invalid_due_dates = (
        fact_tasks[
            fact_tasks[
                "due_date"
            ].notna()
            & (
                fact_tasks[
                    "due_date"
                ]
                < fact_tasks[
                    "created_date"
                ]
            )
        ]
    )

    print(
        "\nDue date validation:"
    )

    print(
        f"Tasks with due date: "
        f"{due_date_percentage:.2f}%"
    )

    print(
        f"Invalid due dates: "
        f"{len(invalid_due_dates)}"
    )

    # -----------------------------------------------------
    # Completion by priority
    # -----------------------------------------------------

    print(
        "\nCompletion rate by priority:"
    )

    completion_by_priority = (
        fact_tasks
        .assign(
            completed=(
                fact_tasks["status"]
                == "completed"
            )
        )
        .groupby(
            "priority"
        )["completed"]
        .mean()
        .mul(100)
        .round(2)
    )

    print(
        completion_by_priority
    )

    # -----------------------------------------------------
    # Completion by duration
    # -----------------------------------------------------

    print(
        "\nCompletion rate by estimated duration:"
    )

    completion_by_duration = (
        fact_tasks
        .assign(
            completed=(
                fact_tasks["status"]
                == "completed"
            )
        )
        .groupby(
            "estimated_minutes"
        )["completed"]
        .mean()
        .mul(100)
        .round(2)
    )

    print(
        completion_by_duration
    )

    # -----------------------------------------------------
    # BQ8
    # -----------------------------------------------------

    print(
        "\nBQ8 - Completion rate by daily check-in state:"
    )

    matched_tasks = (
        fact_tasks[
            fact_tasks[
                "daily_checkin_state"
            ]
            .notna()
        ]
        .copy()
    )

    completion_by_state = (
        matched_tasks
        .assign(
            completed=(
                matched_tasks[
                    "status"
                ]
                == "completed"
            )
        )
        .groupby(
            "daily_checkin_state"
        )["completed"]
        .agg(
            [
                "count",
                "mean",
            ]
        )
    )

    completion_by_state[
        "completion_rate_pct"
    ] = (
        completion_by_state[
            "mean"
        ]
        * 100
    ).round(2)

    completion_by_state = (
        completion_by_state[
            [
                "count",
                "completion_rate_pct",
            ]
        ]
    )

    print(
        completion_by_state
    )

    # -----------------------------------------------------
    # No-check-in comparison
    # -----------------------------------------------------

    no_checkin_tasks = (
        fact_tasks[
            fact_tasks[
                "daily_checkin_state"
            ]
            .isna()
        ]
        .copy()
    )

    no_checkin_completion_rate = (
        no_checkin_tasks[
            "status"
        ]
        .eq("completed")
        .mean()
        * 100
    )

    print(
        "\nTasks without a same-day check-in:"
    )

    print(
        f"Tasks: "
        f"{len(no_checkin_tasks)}"
    )

    print(
        f"Completion rate: "
        f"{no_checkin_completion_rate:.2f}%"
    )

    # -----------------------------------------------------
    # User integrity
    # -----------------------------------------------------

    valid_users = set(
        dim_users["user_id"]
    )

    invalid_task_users = (
        ~fact_tasks[
            "user_id"
        ]
        .isin(valid_users)
    ).sum()

    invalid_checkin_users = (
        ~fact_checkins[
            "user_id"
        ]
        .isin(valid_users)
    ).sum()

    print(
        "\nUser integrity:"
    )

    print(
        f"Invalid task user IDs: "
        f"{invalid_task_users}"
    )

    print(
        f"Invalid check-in user IDs: "
        f"{invalid_checkin_users}"
    )

    # -----------------------------------------------------
    # Date coverage
    # -----------------------------------------------------

    max_dates = [
        fact_tasks[
            "created_at"
        ]
        .max()
        .normalize()
    ]

    if fact_tasks[
        "due_date"
    ].notna().any():

        max_dates.append(
            fact_tasks[
                "due_date"
            ].max()
        )

    if fact_tasks[
        "completed_at"
    ].notna().any():

        max_dates.append(
            fact_tasks[
                "completed_at"
            ]
            .max()
            .normalize()
        )

    max_fact_date = max(
        max_dates
    )

    print(
        "\nDate dimension:"
    )

    print(
        f"First date: "
        f"{dim_date['date'].min().date()}"
    )

    print(
        f"Last date: "
        f"{dim_date['date'].max().date()}"
    )

    print(
        f"Maximum fact date: "
        f"{max_fact_date.date()}"
    )

    print(
        f"Full date coverage: "
        f"{dim_date['date'].max() >= max_fact_date}"
    )


# =========================================================
# EXPORT
# =========================================================

def export_dataset(
    dim_users,
    dim_date,
    fact_tasks,
    fact_checkins,
):
    """Export final CSV files for Power BI."""

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # -----------------------------------------------------
    # DimUser
    # -----------------------------------------------------

    # activity_level was used only during generation.
    # It is not required in the final analytical model.
    dim_users_export = (
        dim_users[
            [
                "user_id",
            ]
        ]
        .copy()
    )

    # -----------------------------------------------------
    # FactTasks
    # -----------------------------------------------------

    # completion_probability is intentionally excluded.
    #
    # It is part of the synthetic generation mechanism,
    # not a business field that should appear in Power BI.
    fact_tasks_export = (
        fact_tasks[
            [
                "task_id",
                "user_id",
                "title",
                "status",
                "priority",
                "estimated_minutes",
                "due_date",
                "created_at",
                "completed_at",
                "daily_checkin_state",
            ]
        ]
        .copy()
    )

    # -----------------------------------------------------
    # FactCheckins
    # -----------------------------------------------------

    fact_checkins_export = (
        fact_checkins[
            [
                "checkin_id",
                "user_id",
                "state",
                "created_at",
            ]
        ]
        .copy()
    )

    # -----------------------------------------------------
    # Export
    # -----------------------------------------------------

    dim_users_export.to_csv(
        OUTPUT_DIR
        / "dim_users.csv",
        index=False,
    )

    dim_date.to_csv(
        OUTPUT_DIR
        / "dim_date.csv",
        index=False,
        date_format="%Y-%m-%d",
    )

    fact_tasks_export.to_csv(
        OUTPUT_DIR
        / "fact_tasks.csv",
        index=False,
        date_format="%Y-%m-%d %H:%M:%S",
    )

    fact_checkins_export.to_csv(
        OUTPUT_DIR
        / "fact_checkins.csv",
        index=False,
        date_format="%Y-%m-%d %H:%M:%S",
    )

    print(
        "\n"
        + "=" * 60
    )

    print(
        "FILES CREATED"
    )

    print(
        "=" * 60
    )

    print(
        OUTPUT_DIR
        / "dim_users.csv"
    )

    print(
        OUTPUT_DIR
        / "dim_date.csv"
    )

    print(
        OUTPUT_DIR
        / "fact_tasks.csv"
    )

    print(
        OUTPUT_DIR
        / "fact_checkins.csv"
    )


# =========================================================
# MAIN
# =========================================================

def main():
    """Generate, validate and export the dataset."""

    print(
        "Mody Power BI Synthetic Data Generator"
    )

    print(
        f"Seed: {RANDOM_SEED}"
    )

    print(
        f"Users: {NUM_USERS}"
    )

    print(
        f"Analytical period: "
        f"{START_DATE.date()} "
        f"to "
        f"{END_DATE.date()}"
    )

    print(
        f"Target tasks: "
        f"{TARGET_TASKS}"
    )

    print(
        f"Target check-ins: "
        f"{TARGET_CHECKINS}"
    )

    print(
        f"Output directory: "
        f"{OUTPUT_DIR}"
    )

    # 1. Generate users.
    dim_users = (
        generate_users()
    )

    # 2. Generate check-ins.
    fact_checkins = (
        generate_checkins(
            dim_users
        )
    )

    # 3. Derive one daily state.
    daily_checkins = (
        derive_daily_checkin_state(
            fact_checkins
        )
    )

    # 4. Generate task structure.
    task_structure = (
        generate_task_structure(
            dim_users
        )
    )

    # 5. Associate task with same-day check-in.
    tasks_with_checkins = (
        match_tasks_with_daily_checkins(
            task_structure,
            daily_checkins,
        )
    )

    # 6. Calculate final outcome once.
    fact_tasks = (
        finalize_tasks(
            tasks_with_checkins
        )
    )

    # 7. Generate complete calendar.
    dim_date = (
        generate_date_dimension(
            fact_tasks
        )
    )

    # 8. Validate.
    validate_dataset(
        dim_users=dim_users,
        dim_date=dim_date,
        fact_tasks=fact_tasks,
        fact_checkins=fact_checkins,
        daily_checkins=daily_checkins,
    )

    # 9. Export final Power BI files.
    export_dataset(
        dim_users=dim_users,
        dim_date=dim_date,
        fact_tasks=fact_tasks,
        fact_checkins=fact_checkins,
    )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    main()