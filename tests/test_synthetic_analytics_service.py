"""Validation tests for services/synthetic_analytics_service.py.

These tests validate the ANALYTICS LAYER built on top of Mody's synthetic
90-day demo dataset (data/synthetic/*.csv). They check structural
correctness (columns, ranges, ordering, grain), not the specific numbers,
since the underlying dataset can be regenerated. All data referenced here
is SYNTHETIC / portfolio demo data — nothing here validates or implies
anything about real users.

Run with:
    python tests/test_synthetic_analytics_service.py
or:
    pytest tests/test_synthetic_analytics_service.py -v
"""

import math

import services.synthetic_analytics_service as svc

WEEKDAY_ORDER = svc.WEEKDAY_ORDER
CHECKIN_STATE_ORDER = svc.CHECKIN_STATE_ORDER
PRIORITY_ORDER = svc.PRIORITY_ORDER
ENERGY_GROUP_ORDER = svc.ENERGY_GROUP_ORDER
FOCUS_GROUP_ORDER = svc.FOCUS_GROUP_ORDER
OVERWHELMED_GROUP_ORDER = svc.OVERWHELMED_GROUP_ORDER
WEEKDAY_VS_WEEKEND_ORDER = svc.WEEKDAY_VS_WEEKEND_ORDER


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------
def test_checkins_load_successfully() -> None:
    checkins = svc.load_synthetic_checkins()
    assert len(checkins) > 0, "Expected at least one synthetic check-in row"


def test_tasks_load_successfully() -> None:
    tasks = svc.load_synthetic_tasks()
    assert len(tasks) > 0, "Expected at least one synthetic task row"


def test_checkins_are_synthetic_only() -> None:
    checkins = svc.load_synthetic_checkins()
    assert (checkins["is_synthetic"] == True).all(), (  # noqa: E712
        "load_synthetic_checkins() must only return is_synthetic rows"
    )


def test_tasks_are_synthetic_only() -> None:
    tasks = svc.load_synthetic_tasks()
    assert (tasks["is_synthetic"] == True).all(), (  # noqa: E712
        "load_synthetic_tasks() must only return is_synthetic rows"
    )


def test_checkins_expected_columns_present() -> None:
    checkins = svc.load_synthetic_checkins()
    required = {
        "created_at",
        "state",
        "energy_level",
        "anxiety_level",
        "focus_level",
        "is_synthetic",
        "date",
    }
    missing = required - set(checkins.columns)
    assert not missing, f"load_synthetic_checkins() missing columns: {missing}"


def test_tasks_expected_columns_present() -> None:
    tasks = svc.load_synthetic_tasks()
    required = {
        "created_at",
        "completed_at",
        "status",
        "priority",
        "estimated_minutes",
        "due_date",
        "is_synthetic",
        "date",
    }
    missing = required - set(tasks.columns)
    assert not missing, f"load_synthetic_tasks() missing columns: {missing}"


# ---------------------------------------------------------------------------
# Daily aggregation grain (the many-to-many safeguard)
# ---------------------------------------------------------------------------
def test_daily_checkin_metrics_one_row_per_date() -> None:
    daily = svc.get_daily_checkin_metrics()
    assert daily["date"].is_unique, (
        "get_daily_checkin_metrics() must return exactly one row per date"
    )
    expected_columns = {
        "date",
        "avg_energy",
        "avg_anxiety",
        "avg_focus",
        "checkin_count",
        "had_well",
        "had_overwhelmed",
        "had_calm_needed",
    }
    assert expected_columns <= set(daily.columns), (
        f"get_daily_checkin_metrics() missing columns: "
        f"{expected_columns - set(daily.columns)}"
    )


def test_daily_task_metrics_one_row_per_date() -> None:
    daily = svc.get_daily_task_metrics()
    assert daily["date"].is_unique, (
        "get_daily_task_metrics() must return exactly one row per date"
    )
    expected_columns = {
        "date",
        "task_count",
        "completed_tasks",
        "pending_tasks",
        "in_progress_tasks",
        "blocked_tasks",
        "completion_rate",
    }
    assert expected_columns <= set(daily.columns), (
        f"get_daily_task_metrics() missing columns: "
        f"{expected_columns - set(daily.columns)}"
    )


def test_daily_metrics_row_counts_match_raw_row_counts() -> None:
    """No many-to-many duplication: summing daily counts must reproduce the
    exact number of raw rows loaded, never more (which a bad join would
    produce) and never less."""
    checkins = svc.load_synthetic_checkins()
    daily_checkins = svc.get_daily_checkin_metrics()
    assert int(daily_checkins["checkin_count"].sum()) == len(checkins), (
        "Sum of daily checkin_count must equal the number of raw check-in rows"
    )

    tasks = svc.load_synthetic_tasks()
    daily_tasks = svc.get_daily_task_metrics()
    assert int(daily_tasks["task_count"].sum()) == len(tasks), (
        "Sum of daily task_count must equal the number of raw task rows"
    )


def test_merged_daily_dataset_does_not_duplicate_rows() -> None:
    """Merging the two daily-grain tables must not multiply row counts —
    each table already has one row per date, so an inner join on date can
    only produce at most one row per date (never a many-to-many blow-up)."""
    merged = svc._merge_daily_datasets()
    assert merged["date"].is_unique, (
        "Merged daily check-in/task dataset must have one row per date"
    )
    daily_checkins = svc.get_daily_checkin_metrics()
    assert len(merged) <= len(daily_checkins), (
        "Inner-joined daily dataset cannot have more rows than the "
        "check-in side of the join"
    )


# ---------------------------------------------------------------------------
# Q1 — overall completion rate
# ---------------------------------------------------------------------------
def test_overall_task_metrics_completion_rate_in_range() -> None:
    metrics = svc.get_overall_task_metrics()
    assert 0.0 <= metrics["completion_rate"] <= 100.0, (
        f"Overall completion_rate out of range: {metrics['completion_rate']}"
    )
    assert metrics["completed_tasks"] <= metrics["total_tasks"], (
        "completed_tasks cannot exceed total_tasks"
    )


def test_overall_task_metrics_status_counts_sum_to_total() -> None:
    metrics = svc.get_overall_task_metrics()
    status_sum = (
        metrics["completed_tasks"]
        + metrics["pending_tasks"]
        + metrics["in_progress_tasks"]
        + metrics["blocked_tasks"]
    )
    assert status_sum == metrics["total_tasks"], (
        "Sum of per-status task counts must equal total_tasks "
        f"({status_sum} != {metrics['total_tasks']})"
    )


# ---------------------------------------------------------------------------
# Q2 — completion by priority
# ---------------------------------------------------------------------------
def test_completion_by_priority_covers_all_priorities_in_order() -> None:
    results = svc.get_completion_by_priority()
    assert [r["priority"] for r in results] == PRIORITY_ORDER, (
        "get_completion_by_priority() must return low, medium, high in that order"
    )
    for row in results:
        assert 0.0 <= row["completion_rate"] <= 100.0, (
            f"completion_rate out of range for priority {row['priority']}: "
            f"{row['completion_rate']}"
        )


def test_completion_by_priority_totals_match_overall() -> None:
    results = svc.get_completion_by_priority()
    overall = svc.get_overall_task_metrics()
    assert sum(r["task_count"] for r in results) == overall["total_tasks"], (
        "Task counts across priorities must sum to the overall total_tasks"
    )
    assert sum(r["completed_tasks"] for r in results) == overall["completed_tasks"], (
        "Completed counts across priorities must sum to the overall completed_tasks"
    )


# ---------------------------------------------------------------------------
# Q3 — completion by weekday
# ---------------------------------------------------------------------------
def test_completion_by_weekday_ordering_and_range() -> None:
    results = svc.get_completion_by_weekday()
    assert [r["weekday"] for r in results] == WEEKDAY_ORDER, (
        "get_completion_by_weekday() must follow Monday..Sunday order"
    )
    for row in results:
        assert 0.0 <= row["completion_rate"] <= 100.0, (
            f"completion_rate out of range for {row['weekday']}: {row['completion_rate']}"
        )


def test_completion_by_weekday_totals_match_overall() -> None:
    results = svc.get_completion_by_weekday()
    overall = svc.get_overall_task_metrics()
    assert sum(r["task_count"] for r in results) == overall["total_tasks"], (
        "Task counts across weekdays must sum to the overall total_tasks"
    )


# ---------------------------------------------------------------------------
# Q4 — check-in metrics by weekday
# ---------------------------------------------------------------------------
def test_checkin_metrics_by_weekday_ordering() -> None:
    results = svc.get_checkin_metrics_by_weekday()
    assert [r["weekday"] for r in results] == WEEKDAY_ORDER, (
        "get_checkin_metrics_by_weekday() must follow Monday..Sunday order"
    )


def test_checkin_metrics_by_weekday_missing_not_zero() -> None:
    """A weekday average must be None (not 0) when there is no numeric
    data to average — this directly checks the 'never treat missing as
    zero' rule at the weekday-grouping level."""
    results = svc.get_checkin_metrics_by_weekday()
    for row in results:
        if row["checkin_count"] == 0:
            assert row["avg_energy"] is None
            assert row["avg_anxiety"] is None
            assert row["avg_focus"] is None
        for key in ("avg_energy", "avg_anxiety", "avg_focus"):
            value = row[key]
            assert value is None or 1.0 <= value <= 5.0, (
                f"{key} for {row['weekday']} out of expected 1-5 range: {value}"
            )


def test_checkin_metrics_by_weekday_counts_match_total() -> None:
    results = svc.get_checkin_metrics_by_weekday()
    checkins = svc.load_synthetic_checkins()
    assert sum(r["checkin_count"] for r in results) == len(checkins), (
        "Check-in counts across weekdays must sum to the total number of check-ins"
    )


# ---------------------------------------------------------------------------
# Q5 — check-in state distribution
# ---------------------------------------------------------------------------
def test_checkin_state_distribution_covers_all_states_in_order() -> None:
    results = svc.get_checkin_state_distribution()
    assert [r["state"] for r in results] == CHECKIN_STATE_ORDER, (
        "get_checkin_state_distribution() must return well, overwhelmed, "
        "calm_needed in that order"
    )


def test_checkin_state_distribution_counts_sum_to_total() -> None:
    results = svc.get_checkin_state_distribution()
    checkins = svc.load_synthetic_checkins()
    assert sum(r["count"] for r in results) == len(checkins), (
        "State distribution counts must sum to the total number of check-ins"
    )


# ---------------------------------------------------------------------------
# Q6 — check-in time series
# ---------------------------------------------------------------------------
def test_checkin_timeseries_is_chronological() -> None:
    series = svc.get_checkin_timeseries()
    dates = [row["date"] for row in series]
    assert dates == sorted(dates), (
        "get_checkin_timeseries() must be sorted chronologically (oldest -> newest)"
    )


def test_checkin_timeseries_values_not_coerced_to_zero() -> None:
    series = svc.get_checkin_timeseries()
    for row in series:
        for key in ("avg_energy", "avg_anxiety", "avg_focus"):
            value = row[key]
            # Missing must surface as None; when present it must be a
            # plausible 1-5 average, never a fabricated 0.
            assert value is None or 1.0 <= value <= 5.0, (
                f"{key} on {row['date']} out of expected range: {value}"
            )
        assert row["checkin_count"] >= 1, (
            f"Timeseries row for {row['date']} should only exist when "
            "checkin_count >= 1"
        )


# ---------------------------------------------------------------------------
# Q7 / Q8 — completion by energy / focus group
# ---------------------------------------------------------------------------
def test_completion_by_energy_groups_valid() -> None:
    results = svc.get_completion_by_energy()
    assert [r["energy_group"] for r in results] == ENERGY_GROUP_ORDER, (
        "get_completion_by_energy() must return Low, Medium, High in that order"
    )
    for row in results:
        assert 0.0 <= row["completion_rate"] <= 100.0
        assert row["number_of_days"] >= 0
        assert row["completed_tasks"] <= row["task_count"]


def test_completion_by_focus_groups_valid() -> None:
    results = svc.get_completion_by_focus()
    assert [r["focus_group"] for r in results] == FOCUS_GROUP_ORDER, (
        "get_completion_by_focus() must return Low, Medium, High in that order"
    )
    for row in results:
        assert 0.0 <= row["completion_rate"] <= 100.0
        assert row["number_of_days"] >= 0
        assert row["completed_tasks"] <= row["task_count"]


def test_completion_by_energy_days_do_not_exceed_checkin_days() -> None:
    """Every day counted in the energy grouping must be a day that had a
    defined daily avg_energy (i.e. came from the merged daily dataset)."""
    results = svc.get_completion_by_energy()
    daily_checkins = svc.get_daily_checkin_metrics()
    days_with_energy = daily_checkins["avg_energy"].notna().sum()
    total_grouped_days = sum(r["number_of_days"] for r in results)
    assert total_grouped_days <= days_with_energy, (
        "Energy-grouped day count cannot exceed the number of days with a "
        "defined daily avg_energy"
    )


# ---------------------------------------------------------------------------
# Q9 — overwhelmed vs other check-in days
# ---------------------------------------------------------------------------
def test_completion_by_overwhelmed_state_groups_present() -> None:
    results = svc.get_completion_by_overwhelmed_state()
    assert [r["group"] for r in results] == OVERWHELMED_GROUP_ORDER, (
        "get_completion_by_overwhelmed_state() must return the two expected, "
        "neutrally-named groups in order"
    )
    for row in results:
        assert 0.0 <= row["completion_rate"] <= 100.0
        assert row["completed_tasks"] <= row["task_count"]


def test_completion_by_overwhelmed_state_days_match_checkin_days() -> None:
    results = svc.get_completion_by_overwhelmed_state()
    merged = svc._merge_daily_datasets()
    assert sum(r["number_of_days"] for r in results) == len(merged), (
        "Overwhelmed-vs-other day counts must sum to the number of days "
        "with matching check-in and task data"
    )


# ---------------------------------------------------------------------------
# Q10 — weekday vs weekend
# ---------------------------------------------------------------------------
def test_weekday_vs_weekend_groups_present() -> None:
    results = svc.get_weekday_vs_weekend_metrics()
    assert [r["group"] for r in results] == WEEKDAY_VS_WEEKEND_ORDER, (
        "get_weekday_vs_weekend_metrics() must return Weekday, Weekend in that order"
    )
    for row in results:
        assert 0.0 <= row["completion_rate"] <= 100.0
        assert row["completed_tasks"] <= row["task_count"]
        for key in ("avg_energy", "avg_anxiety", "avg_focus"):
            value = row[key]
            assert value is None or 1.0 <= value <= 5.0, (
                f"{key} for {row['group']} out of expected range: {value}"
            )


def test_weekday_vs_weekend_days_cover_full_period() -> None:
    results = svc.get_weekday_vs_weekend_metrics()
    daily_tasks = svc.get_daily_task_metrics()
    assert sum(r["number_of_days"] for r in results) == len(daily_tasks), (
        "Weekday + Weekend day counts must cover every task-observation day exactly once"
    )


def test_weekday_vs_weekend_task_totals_match_overall() -> None:
    results = svc.get_weekday_vs_weekend_metrics()
    overall = svc.get_overall_task_metrics()
    assert sum(r["task_count"] for r in results) == overall["total_tasks"], (
        "Weekday + Weekend task counts must sum to the overall total_tasks"
    )


def test_weekday_vs_weekend_checkin_averages_match_raw_observations() -> None:
    """avg_energy/avg_anxiety/avg_focus in get_weekday_vs_weekend_metrics()
    must equal the mean of the INDIVIDUAL raw check-in observations for
    that group (each check-in weighted equally), NOT the mean of each
    day's own daily average. This directly reproduces the required
    calculation independently, using the raw check-in rows and the same
    weekday/weekend classification and 1-decimal rounding convention."""
    results = {row["group"]: row for row in svc.get_weekday_vs_weekend_metrics()}

    checkins = svc.load_synthetic_checkins().copy()
    checkins["group"] = checkins["date"].map(
        lambda d: "Weekend" if svc._is_weekend(d) else "Weekday"
    )

    for group_label in WEEKDAY_VS_WEEKEND_ORDER:
        subset = checkins[checkins["group"] == group_label]

        expected_energy = svc._round_or_none(subset["energy_level"].mean())
        expected_anxiety = svc._round_or_none(subset["anxiety_level"].mean())
        expected_focus = svc._round_or_none(subset["focus_level"].mean())

        actual = results[group_label]

        assert actual["avg_energy"] == expected_energy, (
            f"{group_label} avg_energy mismatch: expected {expected_energy} "
            f"(from raw check-ins), got {actual['avg_energy']}"
        )
        assert actual["avg_anxiety"] == expected_anxiety, (
            f"{group_label} avg_anxiety mismatch: expected {expected_anxiety} "
            f"(from raw check-ins), got {actual['avg_anxiety']}"
        )
        assert actual["avg_focus"] == expected_focus, (
            f"{group_label} avg_focus mismatch: expected {expected_focus} "
            f"(from raw check-ins), got {actual['avg_focus']}"
        )


# ---------------------------------------------------------------------------
# Runner (so the file also works as a plain script, not just via pytest)
# ---------------------------------------------------------------------------
def run_all() -> None:
    checks = [
        test_checkins_load_successfully,
        test_tasks_load_successfully,
        test_checkins_are_synthetic_only,
        test_tasks_are_synthetic_only,
        test_checkins_expected_columns_present,
        test_tasks_expected_columns_present,
        test_daily_checkin_metrics_one_row_per_date,
        test_daily_task_metrics_one_row_per_date,
        test_daily_metrics_row_counts_match_raw_row_counts,
        test_merged_daily_dataset_does_not_duplicate_rows,
        test_overall_task_metrics_completion_rate_in_range,
        test_overall_task_metrics_status_counts_sum_to_total,
        test_completion_by_priority_covers_all_priorities_in_order,
        test_completion_by_priority_totals_match_overall,
        test_completion_by_weekday_ordering_and_range,
        test_completion_by_weekday_totals_match_overall,
        test_checkin_metrics_by_weekday_ordering,
        test_checkin_metrics_by_weekday_missing_not_zero,
        test_checkin_metrics_by_weekday_counts_match_total,
        test_checkin_state_distribution_covers_all_states_in_order,
        test_checkin_state_distribution_counts_sum_to_total,
        test_checkin_timeseries_is_chronological,
        test_checkin_timeseries_values_not_coerced_to_zero,
        test_completion_by_energy_groups_valid,
        test_completion_by_focus_groups_valid,
        test_completion_by_energy_days_do_not_exceed_checkin_days,
        test_completion_by_overwhelmed_state_groups_present,
        test_completion_by_overwhelmed_state_days_match_checkin_days,
        test_weekday_vs_weekend_groups_present,
        test_weekday_vs_weekend_days_cover_full_period,
        test_weekday_vs_weekend_task_totals_match_overall,
        test_weekday_vs_weekend_checkin_averages_match_raw_observations,
    ]

    for check in checks:
        check()
        print(f"PASS  {check.__name__}")

    print(f"\nAll {len(checks)} checks passed.")


if __name__ == "__main__":
    run_all()