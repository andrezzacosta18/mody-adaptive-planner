# Mody — Adaptive Planner

## Overview

Mody is a productivity and planning support application built with
Streamlit, Supabase/PostgreSQL, and pandas. People check in with how
they're feeling, manage tasks and appointments, and see both a real-time
overview of their own activity and a separate historical analytics dashboard
built on a reproducible synthetic dataset.

The interface is responsive and designed around a single guiding principle:
*one thing at a time*. The Portuguese tagline — *"Um jeito mais leve de
organizar o dia."* — captures the product's intention: a calmer, lower-friction
way to stay organised.

Mody is a productivity tool, not a diagnostic, medical, or psychological
application. It never produces medical, ADHD, anxiety, or psychological
conclusions about any user.

## Problem

Most planning and productivity tools treat every day identically: the same
task list, the same layout, regardless of how someone actually shows up
that day. Mody explores how a planning interface can adapt its suggestions
to a person's current, self-reported check-in state and pending workload —
and, where richer data is available, to energy and focus levels as well —
using simple, transparent, explainable rules rather than opaque scoring.

## Portfolio Objective

This project demonstrates practical, end-to-end skills across:

- **Data Analysis** — descriptive statistics, grouping, KPI design, grain-aware joins
- **SQL / PostgreSQL** — data modeling, RLS policies, scoped queries via Supabase
- **Python and pandas** — data preparation, aggregation, time-series handling
- **Product analytics thinking** — defining the right analytical questions before writing code
- **Data visualization** — Streamlit-native charts, lightweight KPI presentation
- **Data quality awareness** — handling missing values, never coercing nulls to zero
- **Streamlit** — multi-page app, session management, responsive layout
- **Supabase** — Auth, Postgres, Row Level Security, per-session client
- **Security-conscious data access** — auth.uid() boundary, no service_role in client code

## Core Features

- Authentication (Supabase Auth, email/password)
- Onboarding and personalization preferences
- Task management (create, complete, track status)
- Check-ins (self-reported state; the data model and service also support
  optional energy/anxiety/focus levels — see note below)
- Internal appointment calendar (create, view upcoming, and delete appointments)
- Next appointment displayed on the Today ("Hoje") page
- Real-user analytics overview ("Visão geral")
- Synthetic historical behavioral analytics ("Análise histórica")
- Deterministic, rule-based adaptive planning suggestions
- Custom Mody visual identity with responsive web interface designed for
  calm, low cognitive load across desktop and mobile layouts

> **Note on the adaptive suggestion:** the card labeled "✦ PARA AGORA"
> currently uses the user's **latest real check-in state** and **current
> pending task count**. The check-in data model and `checkin_service`
> support optional numeric energy/anxiety/focus levels, and
> `adaptive_service.get_adaptive_suggestion()` is already written to use
> them whenever they are present — but the current Home check-in UI only
> asks for a state (Estou bem / Estou sobrecarregada / Quero desacelerar),
> not numeric levels. In regular use today the suggestion is driven by
> state and pending task count. The energy/focus grouping shown on the
> historical dashboard comes entirely from the separate synthetic demo
> dataset, not from real check-ins.

> **Note on the appointment calendar:** the current MVP supports creating,
> listing, and deleting appointments. There is no update/edit operation in
> this version — to change an appointment, delete it and create a new one.

## Architecture

Two clearly separated data pathways feed two clearly separated UI areas.

**Real user data:**

```
Streamlit UI (app.py)
        ↓
Services layer (auth_service, task_service, checkin_service,
               appointment_service, analytics_service, adaptive_service)
        ↓
Supabase / PostgreSQL (RLS-protected, per-session client)
```

**Synthetic portfolio data:**

```
Synthetic CSV dataset (data/synthetic/*.csv)
        ↓
Synthetic analytics service (services/synthetic_analytics_service.py)
        ↓
Historical portfolio dashboard ("Análise histórica")
```

These two pathways never cross. The historical dashboard reads only the
synthetic CSV files and never touches Supabase; the real-user pages read
only Supabase (via the services layer) and never touch the synthetic
dataset. The current synthetic pipeline has no Supabase write path, so
synthetic demo data remains isolated from the real-user database.

## Data Model

- **profiles** — display name, timezone, one row per authenticated user.
- **personalization_preferences** — optional self-described support profile
  and support needs, used only to personalize the experience (never to
  diagnose).
- **tasks** — title, description, status (`pending`, `in_progress`,
  `completed`, `blocked`), priority, estimated duration, due date,
  completion timestamp.
- **checkins** — self-reported state (`well`, `overwhelmed`,
  `calm_needed`), with optional 1–5 energy/anxiety/focus levels.
- **appointments** — title, date, time, optional notes; RLS-protected per
  user. Supports create, list upcoming, and delete.

All real tables are protected by Row Level Security, scoped to
`auth.uid()`.

## Analytics Questions

The real-user overview ("Visão geral") and the synthetic historical
dashboard ("Análise histórica") are both built around concrete analytical
questions.

**Real-user overview:**

- How many tasks are pending, in progress, completed, or blocked, and what is the completion rate?
- How is the check-in state distribution, and how has it evolved recently?
- What are the average energy, anxiety, and focus levels among check-ins that recorded them?

**Synthetic historical dashboard** (using the fictional 90-day demo dataset,
which includes numeric energy, anxiety, and focus observations while
intentionally preserving some missing values):

- Does completion differ by task priority?
- Does completion differ across energy or focus groups (daily average, low/medium/high)?
- How does completion vary by weekday?
- What patterns appear on days that include an "overwhelmed" check-in, compared with other check-in days?
- How do weekdays compare with weekends, for both task completion and check-in levels?
- How do energy, anxiety, and focus evolve over the 90-day period?

## Synthetic Dataset

`data/synthetic/synthetic_checkins.csv` and
`data/synthetic/synthetic_tasks.csv` are generated by
`scripts/generate_synthetic_data.py` and are:

- **Reproducible** — a fixed random seed (`random.seed(42)`) produces
  byte-identical output on every run.
- **Fixed period** — a fixed 90-day window (2025-01-01 to 2025-03-31),
  chosen instead of "today" so screenshots and analysis stay reproducible
  over time.
- **Entirely fictional** — no real names, emails, user IDs, task titles,
  or check-ins. Every row is flagged `is_synthetic = True`.
- **Built for demonstration** — created so the analytics layer and
  dashboard could be shown without waiting 90 days for real usage to
  accumulate.
- **Intentionally patterned** — relationships such as "higher energy tends
  to go with higher focus" or "overwhelmed check-ins are somewhat more
  likely on low-energy days" were deliberately encoded during generation,
  as documented generation assumptions, so the analytics layer has
  something meaningful to find. These are not medical or psychological
  claims about real behavior.

## Example Insights

All figures below come from the current synthetic 90-day demo dataset
(103 check-ins, 210 tasks). They describe the fictional demo dataset only
and must never be read as findings about real users:

- Overall synthetic task completion: **56.7%**
- High-priority synthetic tasks: **70.6%** completion
- High-energy synthetic days: **67.1%** completion vs. low-energy synthetic days: **22.2%**
- Days with an overwhelmed synthetic check-in: **44.4%** completion vs. other synthetic check-in days: **61.0%**
- Synthetic weekend completion: **67.2%** vs. synthetic weekday completion: **52.3%**

Every association above is descriptive and observational within the
synthetic dataset — none of it implies causation, and none of it is a
finding about real people.

## Grain and Join Design

This is the most important Data Analyst decision in the project.

Check-ins and tasks have different grains: a single day can have zero, one,
or several check-ins, and separately zero or several tasks. Joining raw
check-in rows directly to raw task rows on date would create a
many-to-many join and silently duplicate observations — for example, 3
check-ins and 4 tasks on the same day would produce 12 joined rows,
inflating every downstream count.

To avoid this, `services/synthetic_analytics_service.py` first aggregates
each synthetic dataset to exactly one row per date (`get_daily_checkin_metrics`,
`get_daily_task_metrics`) and only then merges those two daily tables on
`date`. The real-user `services/analytics_service.py` computes its current
metrics separately and does not perform this cross-domain daily merge.
Analyses that only need one dataset (e.g. completion by priority, or
check-in metrics by weekday) work directly off the raw rows, since no
cross-grain join is required there. The synthetic-side aggregation decision
is unit-tested directly (e.g. confirming that summed daily counts equal the
raw row counts, and that a merged daily dataset never produces more rows
than either side).

## Security

- Authentication via Supabase Auth (email/password).
- Row Level Security (RLS) is the real access-control boundary: every
  table is scoped to `auth.uid()`, so a user can only ever see their own
  rows.
- The app uses a **per-Streamlit-session Supabase client**, restored from
  the stored access/refresh tokens on every rerun — never a single global
  or shared client.
- No `service_role` key is used anywhere in the client application.
- Auth tokens and passwords are never displayed or logged by the UI.
- The synthetic dataset never touches Supabase, so it can never leak into
  or be confused with real user data.

## Tech Stack

- Python
- Streamlit
- Supabase (Auth + PostgreSQL)
- pandas
- pytest
- Git / GitHub

## Project Structure

```
mody-adaptive-planner/
├── app.py                              # Streamlit UI and routing
├── styles/
│   └── style.css                       # Mody design system and responsive CSS
├── assets/
│   ├── mody_logo.png                   # Horizontal brand logo (login screen)
│   └── mody_icon.png                   # Brand icon (favicon, sidebar)
├── services/
│   ├── auth_service.py                 # Supabase Auth (sign in/up/out, session restore)
│   ├── onboarding_service.py           # Profile + personalization preferences
│   ├── task_service.py                 # Real-user tasks
│   ├── checkin_service.py              # Real-user check-ins
│   ├── appointment_service.py          # Real-user appointments (internal calendar)
│   ├── analytics_service.py            # Real-user analytics (Supabase-backed)
│   ├── synthetic_analytics_service.py  # Synthetic/demo analytics (CSV-backed)
│   └── adaptive_service.py             # Deterministic adaptive suggestion rules
├── scripts/
│   └── generate_synthetic_data.py      # Reproducible synthetic dataset generator
├── data/
│   └── synthetic/
│       ├── synthetic_checkins.csv
│       └── synthetic_tasks.csv
├── tests/
│   ├── test_synthetic_data.py
│   ├── test_synthetic_analytics_service.py
│   ├── test_adaptive_service.py
│   └── test_appointment_service.py
└── docs/
    └── portfolio_notes.md
```

## Running Locally

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt

python -m streamlit run app.py
```

Streamlit secrets (`.streamlit/secrets.toml`, not committed) should contain
your Supabase project URL and **publishable/anon** key only — never a
`service_role` key. No real secret values are included in this repository
or in this README.

## Tests

```bash
python -m pytest -v
```

## Current MVP vs. Future Development

### Current MVP

The following features are implemented and working:

- Supabase Auth (sign in, sign up, session restore, logout)
- User onboarding and personalization preferences
- Task management (create, complete, track status)
- Check-ins (self-reported state)
- **Internal appointment calendar** — create, view upcoming, and delete appointments; next appointment displayed on the Today page
- Real-user analytics overview (task KPIs, check-in distribution, recent evolution)
- Synthetic historical behavioral analytics (90-day demo dataset)
- Deterministic, rule-based adaptive planning suggestions
- Responsive web interface (desktop, tablet, and narrow mobile layouts)
- Custom Mody visual identity (branding, favicon, calm design system)

### Future Development

The following are intentionally outside the current MVP scope:

#### External Calendar Synchronization

Future integration with external calendar services (e.g. Google Calendar)
to synchronize appointments bidirectionally. The current internal calendar
is independent and self-contained.

#### WhatsApp Companion

A future low-friction interaction layer via WhatsApp could allow users to:

- complete a quick daily check-in
- ask what is planned for today
- check the next upcoming appointment
- quickly create a task or appointment
- receive planning or reminder prompts

Conceptually, this would route through a webhook to the same Supabase
user data, making Mody accessible without opening a browser. **Not
implemented in the current MVP.**

#### Notifications and Reminders

Future push or scheduled reminders for upcoming appointments and pending
tasks. Not currently implemented.

#### Natural Language Input

Future ability to create tasks or appointments through conversational text
(e.g. "add a meeting tomorrow at 10am"). Not currently implemented.

#### Longitudinal Analytics

As real usage accumulates, the real-user analytics layer can be extended
with longitudinal behavioral analysis. Current historical analytics remain
synthetic/demo only.

#### Optional AI Assistance

A future optional AI layer could provide richer planning suggestions. The
current adaptive suggestions are entirely deterministic and rule-based —
no AI or machine learning is involved.

#### Mobile / PWA Experience

The current interface is a responsive web application usable on mobile
browsers. A future evolution could package this as a Progressive Web App
or native-wrapper experience for a more app-like feel on mobile devices.

## Disclaimer

Mody is a productivity and planning support tool. It is **not** a
diagnostic tool, medical application, psychological assessment, or
treatment tool. The historical analytics dashboard is built entirely from
a **fictional, synthetic** 90-day dataset created for portfolio
demonstration; it does not represent real users, and any association
described in that dashboard (e.g. between energy and task completion) is
descriptive only — never a causal or medical claim.