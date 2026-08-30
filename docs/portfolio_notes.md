# Mody — Portfolio Notes

## What this project is

Mody is a productivity and planning support application built with
Streamlit, Python, pandas, and Supabase/PostgreSQL. It combines real-user
functionality — authentication, task management, check-ins, an internal
appointment calendar, and a real-user analytics dashboard — with a
separate, clearly labeled historical dashboard built on a reproducible
synthetic dataset. It is a portfolio project built to demonstrate
end-to-end product and data-analysis skills, not a diagnostic, medical,
or psychological tool.

## What it demonstrates

- **Streamlit application development** — a multi-screen authenticated
  app (Hoje, Calendário, Visão geral, Análise histórica) with session
  state, forms, and a consistent services-layer pattern.
- **Python and pandas** — data shaping for charts and tables, kept
  strictly separate from business logic, which lives in the services
  layer.
- **Supabase/PostgreSQL** — schema design, Supabase Auth, and Row Level
  Security (RLS) as the actual database access-control boundary.
- **Authentication and RLS** — every real table, including appointments,
  is scoped to `auth.uid()`. RLS scoped to `auth.uid()` is the actual
  security boundary; application-side `user_id` filters may also be used
  for query clarity, but they are not relied on as the access-control
  boundary.
- **Task management** — create, complete, and track tasks with status and
  priority, backed by real Supabase persistence.
- **Persistent check-ins** — self-reported state, with an optional
  numeric energy/anxiety/focus schema already supported by the service
  layer for future use.
- **Internal appointment calendar** — Supabase-backed, persistent
  real-user appointments: create, list upcoming appointments in
  chronological order, and delete, with the next upcoming appointment
  displayed on "Hoje". RLS-protected using the same model as every other
  real table. No external calendar sync, no recurrence, no notifications
  — those are explicitly out of scope for this MVP.
- **Real-user dashboard** ("Visão geral") — task and check-in KPIs and
  charts computed directly from the authenticated user's own Supabase
  data.
- **Separate synthetic historical analytics** ("Análise histórica") — a
  reproducible, fictional 90-day dataset used to demonstrate a richer
  analytics layer without waiting on real usage to accumulate, clearly
  and repeatedly labeled as synthetic.
- **Deterministic adaptive rules** — a transparent, rules-based
  suggestion ("Modo sugerido para agora") driven by the user's latest
  real check-in state and pending task count, not a black-box model.

## The strongest Data Analyst decision in this project

Check-ins and tasks have different grains: a single day can have zero,
one, or several check-ins, and separately zero or several tasks. Joining
raw check-in rows directly to raw task rows on date would create a
many-to-many join and silently duplicate observations — for example, 3
check-ins and 4 tasks on the same day would produce 12 joined rows,
inflating every downstream count.

For the synthetic cross-domain analysis, each dataset is first aggregated
to exactly one row per day (`get_daily_checkin_metrics`,
`get_daily_task_metrics` in `services/synthetic_analytics_service.py`),
and only then are those two daily tables merged on `date`. This grain
mismatch, and the aggregate-then-merge fix, is one of the clearest
"know your grain before you join" examples in the project, and it's
unit-tested directly (summed daily counts equal the raw row counts, and
a merged daily dataset never produces more rows than either side).

Note: this cross-domain daily merge exists on the synthetic side only.
The real-user `services/analytics_service.py` computes its current
metrics separately and does not currently perform this same merge —
worth calling out honestly rather than implying parity between the two
paths.

## Real vs. synthetic data, kept honest

Two pathways feed two different parts of the UI, and they're kept
separate deliberately:

- **Real data**: Streamlit UI → services layer → Supabase/PostgreSQL,
  protected by Supabase Auth and RLS. Feeds "Hoje", "Calendário", and
  "Visão geral".
- **Synthetic data**: a fixed-seed, fixed-90-day-window CSV dataset →
  `synthetic_analytics_service.py` → "Análise histórica" only.

The current synthetic pipeline has no Supabase write path, so synthetic
demonstration data remains isolated from the real-user database. Every
synthetic figure shown in the app (e.g. the 56.7% overall synthetic
completion rate) is explicitly labeled as fictional and descriptive —
never a claim about real users, and never mixed into the real-user
dashboard.

## What would you build next?

- External calendar synchronization, such as Google Calendar.
- A richer task history / event model (tracking status changes over
  time, not just current status).
- Notifications.
- More real longitudinal analytics, once enough real usage accumulates
  to make that meaningful.
- An optional AI assistant layer — explicitly out of scope for this MVP.
- A mobile-optimized experience.

## Talking points for interviews

- Why check-ins and tasks needed to be aggregated to a daily grain before
  being joined, and what would have gone wrong (silently inflated counts)
  if they hadn't been.
- Why the adaptive suggestion is a small set of transparent, deterministic
  rules rather than a model — and what real signal (latest check-in state,
  pending task count) actually drives it in the app today, versus what the
  service layer already supports (energy/anxiety/focus) but the current
  Home UI doesn't yet collect.
- Why RLS, not application-side filtering, is the real security boundary
  in this project, and how that shows up consistently across every real
  table — tasks, check-ins, and now appointments.
- Why the synthetic dataset uses a fixed seed and a fixed historical
  window instead of "today", and why that reproducibility mattered for a
  portfolio piece.
- Why the calendar feature was scoped down deliberately (no recurrence,
  no external sync, no edit flow) to ship a complete, reliable MVP slice
  rather than a half-finished bigger feature.