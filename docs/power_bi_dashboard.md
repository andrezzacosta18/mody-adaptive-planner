# Mody — Power BI Analytics Project

## 1. Business Understanding

### Business Scenario

Mody is a productivity application designed to help users organize tasks, appointments, and daily routines.

In addition to providing operational features such as task management and check-ins, the data generated through the application can be analyzed to better understand usage patterns and task completion behavior.

Since Mody is still under development and does not yet have enough real-user data for meaningful analysis, this project will use **synthetic data** to build and demonstrate the analytical pipeline.

The synthetic data is entirely fictional and does not represent real users.

### Main Business Question

> **How do users use Mody to organize and complete their tasks over time?**

### Analytical Objective

The objective of this project is to build a Power BI dashboard capable of:

- monitoring task volume;
- measuring task completion;
- identifying patterns over time;
- comparing completion patterns across task priorities;
- analyzing differences based on estimated task duration;
- analyzing the distribution of check-in states;
- exploring descriptive associations between check-ins and task completion.

The analyses are intended to be descriptive and exploratory.

Associations identified in the data should not be interpreted as causal relationships.


---

## 2. Business Questions

The dashboard should answer the following questions:

### BQ1 — How many tasks were created and how many were completed?

This helps monitor the overall volume of task activity in the application.

### BQ2 — What is the task completion rate?

This measures the proportion of registered tasks that were completed.

### BQ3 — Does the completion rate vary by task priority?

This allows comparison between tasks with:

- low priority;
- medium priority;
- high priority.

### BQ4 — On which days of the week do users complete the most tasks?

This helps identify weekly patterns in task completion.

### BQ5 — How does the volume of created and completed tasks change over time?

This helps identify:

- increases;
- decreases;
- stability;
- potential temporal patterns.

### BQ6 — Does task completion differ depending on estimated task duration?

This allows shorter and longer tasks to be compared to determine whether they show different completion patterns.

### BQ7 — Which states appear most frequently in check-ins?

The check-in states used by the application are:

```text
well
overwhelmed
calm_needed
```

### BQ8 — Is there a descriptive association between check-in state and task completion?

This analysis may compare task completion rates across periods associated with different check-in states.

This analysis is **descriptive only**.

An observed association does not mean that a particular check-in state caused an increase or decrease in task completion.


---

## 3. Metrics & KPIs

### KPI 1 — Total Tasks

Total number of registered tasks.

**Calculation:**

```text
COUNT(task_id)
```

### KPI 2 — Completed Tasks

Number of tasks that were completed.

**Rule:**

```text
status = completed
```

### KPI 3 — Pending Tasks

Number of tasks that are still pending.

**Rule:**

```text
status = pending
```

### KPI 4 — Completion Rate

Percentage of tasks completed relative to the total number of tasks.

**Formula:**

```text
Completed Tasks
─────────────── × 100
  Total Tasks
```


---

## 4. Supporting Metrics

In addition to the main KPIs, supporting metrics will be used to answer the business questions.

### Completion Rate by Priority

Task completion rate grouped by priority:

```text
low
medium
high
```

### Completed Tasks by Weekday

Number of completed tasks by day of the week.

### Tasks Created Over Time

Number of tasks created over time.

### Tasks Completed Over Time

Number of tasks completed over time.

### Completion Rate by Estimated Time

Task completion rate grouped by estimated task duration.

### Check-ins by State

Number of check-ins for each state:

```text
well
overwhelmed
calm_needed
```

### Completion Rate by Check-in State

Task completion rate compared with the check-in state recorded for the corresponding analytical period.


---

## 5. Metrics Mapping

| Business Question | Metric |
|---|---|
| BQ1 | Total Tasks |
| BQ1 | Completed Tasks |
| BQ1 | Pending Tasks |
| BQ2 | Completion Rate |
| BQ3 | Completion Rate by Priority |
| BQ4 | Completed Tasks by Weekday |
| BQ5 | Tasks Created Over Time |
| BQ5 | Tasks Completed Over Time |
| BQ6 | Completion Rate by Estimated Time |
| BQ7 | Check-ins by State |
| BQ8 | Completion Rate by Check-in State |


---

## 6. Data Requirements

To calculate the metrics defined above, data related to tasks, check-ins, users, and dates will be required.

### FactTasks

Main fact table of the analytical model.

Each row represents one task.

Required fields:

```text
task_id
user_id
title
status
priority
estimated_minutes
due_date
created_at
completed_at
```

#### Grain

> One row represents one task created by one user.

This will be the main fact table because the primary business process analyzed by the dashboard is **task creation and completion**.


### FactCheckins

Secondary fact table.

Each row represents one check-in performed by a user.

Required fields:

```text
checkin_id
user_id
state
created_at
```

#### Grain

> One row represents one check-in performed by one user at a specific point in time.


### DimUser

Dimension used to identify events belonging to the same synthetic user.

Minimum required field:

```text
user_id
```

Only synthetic users will be used in this project.

No user represents a real person.


### DimDate

Calendar dimension used for time-based analysis.

Planned fields:

```text
date
year
month
month_number
month_name
weekday
weekday_number
weekday_name
is_weekend
```

This dimension will support analysis by:

- day;
- week;
- month;
- day of the week;
- weekdays versus weekends.


---

## 7. Data Model

Mody's operational database and analytical model serve different purposes.

### Operational Model — Supabase

The application's database supports Mody's operational functionality.

Its tables include:

```text
profiles
personalization_preferences
tasks
checkins
appointments
```

These tables store the data required for the application's features.

### Analytical Model — Power BI

For analytical purposes, the data will be organized into a dimensional model.

Initial structure:

```text
                       DimDate
                          │
                 ┌────────┴────────┐
                 │                 │
                 ▼                 ▼
            FactTasks        FactCheckins
                 │                 │
                 └────────┬────────┘
                          │
                          ▼
                       DimUser
```

The model contains multiple fact tables because tasks and check-ins represent different business events.

A direct relationship between `FactTasks` and `FactCheckins` will not be created.


---

## 8. Analytical Relationship Between Tasks and Check-ins

Special attention is required when analyzing tasks and check-ins together.

Connecting only:

```text
FactTasks.user_id
=
FactCheckins.user_id
```

would not be sufficient.

A single user may have multiple tasks and multiple check-ins.

A direct relationship could therefore create a many-to-many situation and lead to duplicated calculations.

For analyses involving both events, the time dimension will also be considered.

Conceptually:

```text
USER
 +
DATE
  │
  ├──── Check-in
  │
  └──── Tasks
```

This makes it possible to compare tasks and check-ins that belong to the same analytical context.

The exact association rule will be defined during the data transformation stage.


---

## 9. Synthetic Data Strategy

Since Mody does not yet have enough real-user data for meaningful analysis, a synthetic dataset will be created.

### Proposed Dataset

Initial target:

```text
Users:              100
Period:             90 days
Tasks:              ~2,000–3,000
Check-ins:          Volume to be defined
```

The final values will be determined during the development of the synthetic data generator.

### Important Principle

The data will not be generated randomly without defined rules.

Distributions and controlled behaviors will be established to create a dataset that is:

- coherent;
- reproducible;
- validatable;
- suitable for answering the defined business questions.

A fixed random seed should be used whenever possible to ensure reproducibility.


---

## 10. Data Privacy

The dashboard will use exclusively **synthetic data**.

The demonstration dataset:

- does not represent real users;
- does not contain real email addresses;
- does not contain real names;
- does not use real application check-ins;
- should not be interpreted as evidence of actual Mody user behavior.

The synthetic dataset will remain separate from the application's real operational data.


---

## 11. Project Workflow

The project will follow this analytical workflow:

```text
BUSINESS UNDERSTANDING
        ↓
BUSINESS QUESTIONS
        ↓
METRICS / KPIs
        ↓
DATA REQUIREMENTS
        ↓
SYNTHETIC DATA DESIGN
        ↓
DATA GENERATION
        ↓
DATA VALIDATION
        ↓
DATA TRANSFORMATION
        ↓
DATA MODEL
        ↓
DAX MEASURES
        ↓
POWER BI DASHBOARD
        ↓
INSIGHTS
        ↓
BUSINESS CONCLUSIONS
```


---

## 12. Dashboard — Initial Concept

The first dashboard page will focus on productivity.

### Page 1 — Productivity Overview

Main KPIs:

```text
Total Tasks
Completed Tasks
Pending Tasks
Completion Rate
```

Planned visualizations:

```text
Tasks Created vs Completed Over Time

Completion Rate by Priority

Completed Tasks by Weekday

Completion Rate by Estimated Time
```

Conceptual layout:

```text
┌────────────────────────────────────────────────────────────┐
│              MODY — PRODUCTIVITY OVERVIEW                  │
├──────────────┬──────────────┬──────────────┬────────────────┤
│ Total Tasks  │ Completed    │ Pending      │ Completion     │
│              │ Tasks        │ Tasks        │ Rate           │
├─────────────────────────────┬──────────────────────────────┤
│                             │                              │
│ Created vs Completed        │ Completion by Priority       │
│ Over Time                   │                              │
│                             │                              │
├─────────────────────────────┼──────────────────────────────┤
│                             │                              │
│ Completed Tasks             │ Completion by               │
│ by Weekday                  │ Estimated Time               │
│                             │                              │
└─────────────────────────────┴──────────────────────────────┘
```

A second dashboard page may later explore synthetic check-in data and its descriptive associations with task completion.

## 13. Synthetic Data Design

The synthetic data generation rules will be defined before generating the dataset.

The objective is to create realistic variation while avoiding purely random or deterministic patterns.

All behavioral patterns introduced into the dataset are simulated and must not be interpreted as evidence of real Mody user behavior.

### 13.1 Task Volume

The dataset will contain approximately 2,500 tasks created by 100 synthetic users over a 90-day period.

The number of tasks will vary between users to simulate different levels of application usage.

The target average is approximately 25 tasks per user, but individual users may create more or fewer tasks.

Task creation dates will be distributed throughout the 90-day period to support time-based analysis.

This variation is intentionally simulated and does not represent real Mody user behavior.

### 13.2 Task Priority

Each task will be assigned one of three priority levels:

- Low: approximately 30%
- Medium: approximately 45%
- High: approximately 25%

These percentages will be used as generation probabilities rather than fixed quotas. Therefore, the final distribution may vary slightly.

Medium-priority tasks will be the most common, while high-priority tasks will be less frequent.

This distribution is intentionally defined for the synthetic dataset and does not represent actual Mody user behavior.

### 13.3 Estimated Task Duration

Each task will be assigned an estimated duration using the following probabilities:

- 15 minutes: approximately 15%
- 30 minutes: approximately 30%
- 45 minutes: approximately 20%
- 60 minutes: approximately 20%
- 90 minutes: approximately 10%
- 120 minutes: approximately 5%

Short and medium-length tasks will therefore be more common than long tasks.

These values will be used as generation probabilities rather than fixed quotas, so the final distribution may vary slightly.

The variation in estimated duration will support the analysis of task completion patterns across different task lengths.

This distribution is intentionally defined for the synthetic dataset and does not represent actual Mody user behavior.

### 13.4 Task Completion

Each task will have one of two statuses:

- Completed
- Pending

The synthetic dataset will use a baseline task completion probability of approximately 72%.

This percentage will not be applied as a fixed quota. Instead, it will serve as the starting probability used by the data generator.

Small adjustments to the completion probability will later be introduced based on selected task characteristics, such as priority and estimated duration.

Random variation will remain part of the generation process so that these relationships are not deterministic.

For completed tasks, a `completed_at` timestamp will be generated. Pending tasks will have a null `completed_at` value.

The expected overall completion rate is approximately 70–75%, although the final value may vary slightly.

Any completion patterns observed in this dataset are intentionally simulated and must not be interpreted as evidence of real Mody user behavior.

### 13.5 Priority and Completion Probability

Task priority will introduce a small adjustment to the baseline completion probability.

The baseline completion probability is 72%.

The following adjustments will be applied:

- Low priority: -4 percentage points
- Medium priority: no adjustment
- High priority: +6 percentage points

This results in the following probabilities before other adjustments are applied:

- Low priority: approximately 68%
- Medium priority: approximately 72%
- High priority: approximately 78%

Priority does not determine whether a task will be completed. It only changes the probability used during synthetic data generation.

Random variation will remain part of the process, meaning that high-priority tasks may remain pending and low-priority tasks may be completed.

This relationship is intentionally simulated for analytical purposes and does not represent actual Mody user behavior.

### 13.6 Estimated Duration and Completion Probability

Estimated task duration will also introduce a small adjustment to the baseline completion probability.

The following adjustments will be applied:

- 15 minutes: +4 percentage points
- 30 minutes: +3 percentage points
- 45 minutes: +1 percentage point
- 60 minutes: no adjustment
- 90 minutes: -4 percentage points
- 120 minutes: -7 percentage points

These adjustments will be combined with the priority adjustment when calculating the final completion probability for each task.

For example, a high-priority 30-minute task would have:

- Baseline probability: 72%
- Priority adjustment: +6 percentage points
- Duration adjustment: +3 percentage points
- Final completion probability: 81%

The resulting probability determines the likelihood of completion rather than the final status directly. Random variation will therefore remain present in the dataset.

This creates a controlled but non-deterministic pattern that can later be explored through the `Completion Rate by Estimated Time` metric.

This relationship is intentionally simulated for analytical purposes and does not represent actual Mody user behavior.

### 13.7 Task Dates

Task dates will follow logical chronological rules to ensure data consistency.

#### Creation Date

Each task will receive a `created_at` timestamp within the 90-day synthetic data period.

Task creation will be distributed throughout the period rather than concentrated on specific dates.

#### Due Date

Most tasks will receive a due date.

Approximately 85% of tasks will have a `due_date`, while approximately 15% will have no defined deadline.

For tasks with a due date:

- `due_date` will be between 0 and 14 days after the task creation date.

Therefore:

created_at <= due_date

#### Completion Date

Only tasks with `status = completed` will receive a `completed_at` timestamp.

Pending tasks will have:

completed_at = null

For completed tasks:

completed_at >= created_at

A completed task may be finished:

- before its due date;
- on its due date;
- after its due date.

This allows the dataset to support future analyses of early, on-time, and overdue task completion.

Tasks created near the end of the 90-day period may have due dates or completion dates that extend slightly beyond the analytical period.

All generated timestamps must respect chronological consistency. A task can never be completed before it was created.

### 13.8 Check-in Generation

Check-ins will be generated for the same 100 synthetic users over the 90-day analytical period.

Users will not perform a check-in every day.

The frequency of check-ins will vary between users to simulate different levels of application engagement.

Some users will check in frequently, while others will use the feature occasionally or rarely.

The target dataset will contain approximately 5,000 check-ins.

This corresponds to an average of approximately 50 check-ins per user over the 90-day period, although the actual number will vary considerably between users.

A user may have:

- no check-in on a given day;
- one check-in on a given day;
- occasionally more than one check-in on the same day.

Each check-in will contain:

- `checkin_id`
- `user_id`
- `state`
- `created_at`

All check-in IDs and user IDs will be synthetic.

Check-in timestamps will be distributed throughout the 90-day analytical period.

The variation in check-in frequency is intentionally simulated and does not represent actual Mody user behavior.

### 13.9 Check-in State Distribution

Each check-in will contain one of the three states currently supported by Mody:

- `well`
- `overwhelmed`
- `calm_needed`

The following baseline probabilities will be used:

- Well: approximately 55%
- Overwhelmed: approximately 25%
- Calm needed: approximately 20%

These percentages will be used as generation probabilities rather than fixed quotas. Therefore, the final distribution may vary slightly.

The purpose of this distribution is to ensure that all three states have enough observations to support meaningful comparisons in the Power BI dashboard.

No energy, anxiety, focus, diagnostic, or medical variables will be included in this Power BI synthetic dataset.

The check-in states represent simple self-reported states within the productivity application.

This distribution is intentionally simulated and does not represent actual Mody user behavior.

### 13.10 Linking Check-ins and Tasks

Tasks and check-ins represent different business events and will remain stored in separate fact tables.

No direct relationship will be created between `FactTasks` and `FactCheckins`.

For analyses involving both datasets, the common analytical context will be:

User + Date

Conceptually:

User
  +
Date
  │
  ├── Check-in State
  │
  └── Task Activity

This allows task activity to be compared with the check-in state recorded by the same synthetic user on the same day.

If a user has no check-in on a particular day, tasks from that day will not be assigned an artificial check-in state.

If multiple check-ins exist for the same user on the same day, a transformation rule will be applied later to derive one daily check-in state before combining the information analytically.

The Power BI model will continue to use shared dimensions such as `DimUser` and `DimDate` rather than creating a direct many-to-many relationship between the two fact tables.

This approach helps prevent duplicated task counts and incorrect KPI calculations.

### 13.11 Check-in State and Task Completion

A small simulated association between check-in state and task completion will be introduced to support BQ8.

When a valid daily check-in state is available for the same synthetic user and analytical date, the following adjustments may be applied to the task completion probability:

- `well`: +4 percentage points
- `calm_needed`: no adjustment
- `overwhelmed`: -5 percentage points

If no check-in is available for that user on the relevant date, no check-in-based adjustment will be applied.

The check-in adjustment will be combined with the previously defined baseline, priority, and estimated-duration adjustments.

For example:

Baseline completion probability: 72%
High-priority adjustment:        +6 pp
30-minute duration adjustment:   +3 pp
Well check-in adjustment:        +4 pp

Final completion probability:    85%

The resulting probability will still be evaluated through random generation. Therefore, a task associated with a `well` check-in may remain pending, while a task associated with an `overwhelmed` check-in may be completed.

This relationship is deliberately introduced into the synthetic dataset for analytical demonstration purposes.

It represents a simulated association only and must not be interpreted as evidence that a check-in state causes changes in productivity or task completion.

### 13.12 Completion Probability Limits

The final task completion probability will be calculated by combining the baseline probability with the applicable synthetic adjustments.

The general calculation will be:

Final Probability =
Baseline Probability
+ Priority Adjustment
+ Estimated Duration Adjustment
+ Check-in Adjustment (when applicable)

To prevent unrealistic probabilities, the final value will be constrained to the following range:

- Minimum completion probability: 45%
- Maximum completion probability: 90%

Therefore:

- values below 45% will be set to 45%;
- values above 90% will be set to 90%;
- values within the range will remain unchanged.

After the final probability is calculated, a random outcome will determine whether the task is marked as `completed` or `pending`.

These limits ensure that no combination of synthetic characteristics guarantees completion or makes completion virtually impossible.

The probability model is designed exclusively for synthetic data generation and does not represent or predict real user behavior.

### 13.13 Reproducibility and Synthetic IDs

The synthetic dataset will be generated using a fixed random seed.

The initial seed will be:

42

Using a fixed seed ensures that the same generation rules produce the same dataset whenever the generation script is executed.

This improves:

- reproducibility;
- testing;
- validation;
- debugging;
- consistency between the Python-generated data and the Power BI analysis.

All users, tasks, and check-ins will receive synthetic identifiers.

The identifiers will follow these formats:

Synthetic users:

USR_001
USR_002
...
USR_100

Synthetic tasks:

TSK_000001
TSK_000002
...

Synthetic check-ins:

CHK_000001
CHK_000002
...

These identifiers exist exclusively within the synthetic analytical dataset and are not linked to Supabase Auth IDs or any real Mody user.

The synthetic dataset will remain physically and logically separate from the application's operational user data.

### 13.14 Synthetic Dataset Output Structure

The synthetic data generator will produce four CSV files for the Power BI analytical model.

The files will be stored separately from Mody's operational data.

Proposed structure:

data/
└── powerbi/
    ├── dim_users.csv
    ├── dim_date.csv
    ├── fact_tasks.csv
    └── fact_checkins.csv


#### dim_users.csv

One row represents one synthetic user.

Fields:

- `user_id`

Expected number of rows:

100


#### dim_date.csv

One row represents one calendar date.

Fields:

- `date`
- `year`
- `month`
- `month_number`
- `month_name`
- `weekday`
- `weekday_number`
- `weekday_name`
- `is_weekend`

The date dimension will cover the full analytical period and any additional dates required by task due dates or completion dates.


#### fact_tasks.csv

One row represents one synthetic task.

Fields:

- `task_id`
- `user_id`
- `title`
- `status`
- `priority`
- `estimated_minutes`
- `due_date`
- `created_at`
- `completed_at`

Expected number of rows:

Approximately 2,500


#### fact_checkins.csv

One row represents one synthetic check-in.

Fields:

- `checkin_id`
- `user_id`
- `state`
- `created_at`

Expected number of rows:

Approximately 5,000


### Data Separation

The Power BI synthetic dataset will not be inserted into the production Supabase database.

The CSV files will be generated locally and imported directly into Power BI.

This separation prevents synthetic analytical records from being mixed with real application data.


### Expected Analytical Model

The generated files will support the following dimensional model:

                       DimDate
                          |
                 -----------------
                 |               |
                 |               |
             FactTasks      FactCheckins
                 |               |
                 ------ DimUser --

`DimUser` and `DimDate` will act as shared dimensions between the two fact tables.

No direct relationship will be created between `FactTasks` and `FactCheckins`.

### 13.15 Daily Check-in State

For analyses that combine task activity and check-in data, one daily check-in state will be derived for each synthetic user.

The analytical key will be:

`user_id + date`

If a user performs only one check-in on a given day, that check-in will represent the user's daily state.

If multiple check-ins are recorded by the same user on the same day, the most recent check-in of that day will be selected.

Example:

| User | Date | Time | State |
|---|---|---|---|
| USR_025 | 2026-07-10 | 08:00 | well |
| USR_025 | 2026-07-10 | 15:00 | overwhelmed |

The derived daily state will be:

`overwhelmed`

because it is the most recent check-in recorded on that date.

If a user has no check-in on a given day, no daily state will be assigned.

No state will be inferred or imputed for missing check-in days.

The derived daily state will be used only for analytical purposes when evaluating the descriptive association between check-in state and task completion.

The original `FactCheckins` table will remain unchanged and will continue to contain every individual check-in.