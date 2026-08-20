# Mody — Project Overview

## 1. About Mody

**Mody** is an adaptive planning and self-regulation web application designed initially for the Brazilian market.

The project aims to help users who experience difficulties with:

- time management;
- starting tasks;
- organizing their day;
- remembering commitments;
- maintaining routines;
- estimating how long tasks will take;
- managing distractions;
- avoiding overload;
- adapting plans when their capacity changes.

Mody is especially designed with ADHD and anxiety-related needs in mind, but it is not a medical or diagnostic application.

The application does not diagnose or treat ADHD, anxiety, or any other health condition.

Its purpose is to provide practical tools for **organization, planning, time management and self-regulation**.

---

## 2. Core Idea

Traditional planners generally expect the user to adapt to the planning system.

Mody follows a different principle:

> **The user should not have to adapt to the planner.  
> The planner should adapt to the user.**

Instead of only showing everything that needs to be done, Mody aims to consider the user's current context before helping them plan their day.

The central idea is to combine:

```text
What needs to be done
        +
How much time is available
        +
What commitments already exist
        +
How the user is doing today
        +
What Mody has learned from past patterns
        ↓
A more realistic plan
```

---

## 3. Example

Imagine that a user has:

- 8 pending tasks;
- 2 calendar appointments;
- one important deadline;
- low energy;
- high perceived overload.

A traditional task manager might simply display all pending tasks.

Mody should eventually be able to recognize this context and suggest a more realistic plan.

For example:

### Today

- Attend mandatory appointments
- Complete 1 important task
- Complete 2 small tasks
- Move non-essential tasks to another day
- Include recovery/break periods

The objective is not to maximize the number of completed tasks.

The objective is to help the user create a **realistic and manageable day**.

---

## 4. Personalization

During onboarding, users may optionally tell Mody how they would like the experience to adapt to them.

Possible profiles:

- ADHD
- Anxiety
- ADHD + Anxiety
- None
- Prefer not to say

This information is optional and is used for personalization rather than diagnosis.

Users can also select areas where they would like support.

Examples:

- Starting tasks
- Organizing the day
- Remembering commitments
- Avoiding overload
- Reducing distractions
- Managing anxiety
- Building routines
- Estimating time

These preferences are stored in the user's personalization settings.

The objective is not to create a completely different application for each profile.

Instead, these preferences can influence how Mody presents information, suggestions and planning support.

---

## 5. Task Management

Mody will provide basic task management capabilities.

Tasks may contain information such as:

- title;
- description;
- status;
- priority;
- estimated duration;
- deadline;
- completion time;
- actual duration.

The goal is not only to store tasks.

Over time, these data can help the system understand patterns in how the user plans and completes activities.

For example:

> Tasks that you estimate at 30 minutes often take approximately 45 minutes.

This information could later help Mody improve planning suggestions.

Instead of repeatedly accepting an unrealistic estimate, Mody may eventually suggest a duration based on the user's own historical data.

---

## 6. Daily Check-ins

Mody will include lightweight check-ins.

The objective is to understand the user's current capacity without requiring a long questionnaire.

For example:

### How are you feeling right now?

- Good
- Low energy
- Overloaded

Future versions may consider additional dimensions when they provide useful information for planning, such as:

- energy;
- focus;
- perceived overload;
- perceived anxiety.

The goal is to keep check-ins short enough that users are willing to complete them regularly.

Check-ins can later be compared with task, calendar and planning data to identify patterns.

---

## 7. Adaptive Planning

Adaptive planning is one of the core ideas of Mody.

Eventually, the system should combine information such as:

```text
Tasks
   +
Priorities
   +
Available time
   +
Calendar
   +
Current capacity
   +
Historical patterns
   ↓
Adaptive daily plan
```

The objective is to create a plan that reflects both **what needs to be done** and **what is realistically manageable**.

For example, instead of filling every free period with tasks, Mody should consider whether the proposed workload is realistic for the user's current capacity.

A user may technically have four hours available but not necessarily have four hours of productive capacity.

Mody should attempt to distinguish between these concepts.

### Example

Suppose the user has:

```text
Available time: 4 hours
Energy: Low
Perceived overload: High
Tasks pending: 7
```

Instead of scheduling all seven tasks, Mody may suggest:

```text
TODAY

1 important task
        +
2 small tasks
        +
Existing commitments
        +
Breaks
```

The user remains in control and can accept, reject or modify the suggestion.

---

## 8. Calendar Integration

A future phase will integrate Mody with external calendars, initially Google Calendar.

The calendar will provide context about existing commitments.

Conceptually:

```text
Google Calendar
       ↓
Existing commitments
       ↓
      Mody
       ↓
Available periods
       +
Tasks
       +
Current capacity
       ↓
Suggested plan
```

Mody should not assume that every technically free hour represents productive capacity.

Calendar integration should help the system understand how much time is actually available before suggesting additional activities.

Future possibilities may include:

- reading existing calendar events;
- identifying available periods;
- detecting highly loaded days;
- suggesting focus blocks;
- optionally creating planning blocks;
- avoiding scheduling conflicts.

Calendar integration should remain separated from the core planning logic so that Mody does not depend on one specific calendar provider.

---

## 9. Calm Mode

Mody is planned to include a simplified experience called **Calm Mode**.

The purpose is to reduce cognitive load when a user feels overwhelmed or anxious.

Instead of presenting the normal productivity interface, Calm Mode may provide a simplified sequence involving:

- reducing immediate stimulation;
- grounding exercises;
- breathing guidance;
- simple next steps;
- predefined support resources.

The interface should intentionally contain fewer decisions and less information than the normal Mody interface.

For example:

```text
I'm overwhelmed
       ↓
Calm Mode
       ↓
One instruction at a time
       ↓
Grounding / breathing
       ↓
Small next step
```

This feature will be designed as a **support and self-regulation tool**.

It will not be presented as medical treatment, therapy, diagnosis, or emergency assistance.

Safety-sensitive flows should be structured and should not depend exclusively on unrestricted AI-generated responses.

---

## 10. Personal Analytics

One of Mody's goals is to help users understand their own patterns over time.

Rather than focusing only on daily productivity, Mody should eventually provide a **longitudinal view** of how the user's planning, workload, capacity and task behavior have changed.

Users may choose periods such as:

- Last 30 days
- Last 3 months
- Last 6 months
- Custom period

The objective is to help answer questions such as:

> How have my last three months been?

> Has my workload increased?

> Am I getting better at estimating how long tasks take?

> What types of tasks do I postpone most?

> When do I usually work best?

### 10.1 Data Sources

The analysis may combine information from different parts of Mody:

```text
Check-ins
    +
Tasks
    +
Estimated vs. actual time
    +
Calendar workload
    +
Routines
    +
Planning history
    ↓
Personal Analytics
```

Depending on which features are available and which data the user has chosen to record, Mody may analyze information such as:

- energy;
- perceived overload;
- focus;
- perceived anxiety;
- task completion;
- postponed tasks;
- estimated task duration;
- actual task duration;
- number of commitments;
- calendar workload;
- time of day;
- planning patterns.

---

### 10.2 Three- and Six-Month Review

Users should eventually be able to request a broader review of their recent history.

For example:

> How have I been doing over the last 3 months?

or:

> What patterns can you see in my last 6 months?

Mody should summarize the period using the user's own recorded data.

For example:

```text
MY LAST 6 MONTHS

Check-ins recorded:       74
Tasks completed:         183
Average task completion: 72%

Energy
→ relatively stable

Perceived overload
→ gradually increased

Task completion
→ improved

Time estimation
→ tasks usually took longer than estimated
```

The objective is to provide a useful overview without making medical or diagnostic conclusions.

---

### 10.3 Period Comparison

Mody may compare equivalent periods.

For example:

```text
Last 3 months
      VS
Previous 3 months
```

Example:

| Metric | Previous Period | Current Period | Change |
|---|---:|---:|---:|
| Average energy | 3.6 | 3.1 | ↓ |
| Average focus | 3.2 | 3.5 | ↑ |
| Average overload | 2.5 | 3.2 | ↑ |
| Task completion | 68% | 74% | ↑ |

This allows users to understand whether their recorded patterns are changing over time.

The system should also distinguish between percentages and percentage-point changes where appropriate.

---

### 10.4 Trends

Mody should distinguish between a single difficult day and a longer-term pattern.

Instead of interpreting isolated values, the system may analyze weekly or monthly trends.

For example:

```text
Perceived overload

May       2.4
June      2.6
July      3.0
August    3.3

Trend
→ increasing
```

Mody could summarize this as:

> Your recorded overload has gradually increased during the last four months.

It should avoid conclusions such as:

> Your anxiety is getting worse.

The first statement describes the user's data.

The second would imply a clinical interpretation that the system is not designed to make.

---

### 10.5 Personal Patterns

With enough historical data, Mody may identify recurring patterns.

Examples:

```text
PERSONAL PATTERNS

Most productive period
→ 09:00–11:30

Tasks most frequently postponed
→ long administrative tasks

Estimated vs. actual duration
→ tasks usually take longer than estimated

High-calendar-load days
→ associated with fewer optional tasks completed
```

These patterns can later support adaptive planning.

For example, if the user consistently completes demanding tasks more successfully in the morning, Mody may take this pattern into account when suggesting future plans.

---

### 10.6 Relationships Between Variables

Mody may also explore relationships between different types of user data.

For example:

```text
Higher calendar workload
          ↓
Higher recorded overload?
```

```text
Low-energy check-in
          ↓
More postponed tasks?
```

```text
Tasks longer than 60 minutes
          ↓
Lower completion rate?
```

```text
High perceived overload
          ↓
Different task completion pattern?
```

These relationships should be presented carefully.

Mody should describe them as **associations observed in the user's data**, rather than assuming that one factor caused another.

Correlation or association should not automatically be presented as causation.

---

### 10.7 Estimated Time vs. Actual Time

Time estimation may become an important part of Mody's analytics.

For every task where enough information is available, Mody may compare:

```text
Estimated duration
        VS
Actual duration
```

For example:

```text
Estimated: 30 minutes
Actual:    48 minutes

Difference: +18 minutes
```

Across many tasks, the application may identify a recurring pattern.

For example:

> During the last 3 months, tasks took approximately 22% longer than you initially estimated.

This information may later improve adaptive planning.

---

### 10.8 Calendar Load

Calendar data may provide useful context for understanding workload.

For example, Mody may compare:

```text
Calendar commitments
        +
Task completion
        +
Check-ins
```

This may reveal patterns such as:

> Days with more than five hours of scheduled commitments were associated with fewer optional tasks completed.

or:

> Your recorded overload was usually higher during weeks with more calendar commitments.

These should remain descriptive observations rather than causal or clinical conclusions.

---

### 10.9 Data Context

Every insight should provide context about how much data was used.

For example:

> Based on 46 check-ins and 183 tasks recorded during the last 6 months.

When there is insufficient data, Mody should say so rather than presenting a weak pattern as a strong conclusion.

For example:

> There is not enough information yet to identify a consistent pattern.

As more data is collected, insights may become more useful.

The interface may eventually distinguish between:

```text
Limited data
→ preliminary observation

More historical data
→ recurring pattern

Consistent historical data
→ stronger personal pattern
```

These labels should not be presented as formal statistical confidence unless formal statistical methods are actually being used.

---

### 10.10 Analytics Levels

The analytics experience can be organized into three levels:

```text
1. OVERVIEW

How have my last months been?
        ↓

2. TRENDS

What has increased,
decreased or remained stable?
        ↓

3. PATTERNS

What tends to happen together
in my own data?
```

This allows users to start with a simple summary and explore deeper analysis only when they want to.

---

### 10.11 Connection With Adaptive Planning

Personal Analytics should not exist only as a dashboard.

Historical patterns may eventually improve Mody's planning suggestions.

Conceptually:

```text
Historical Data
      ↓
Personal Patterns
      ↓
Adaptive Planning
      ↓
Today's Context
      ↓
More realistic suggestion
```

For example:

> Tasks of this type usually take you around 45 minutes, although you normally estimate 30 minutes. Would you like me to reserve 45 minutes?

or:

> You usually complete demanding tasks more consistently in the morning. Would you like to schedule this one earlier?

The user should remain in control of whether to accept these suggestions.

---

### 10.12 AI and Historical Analysis

In a later phase, the AI assistant may allow natural-language questions about the user's history.

For example:

> How have I been doing over the last 6 months?

> When do I usually work best?

> What types of tasks do I postpone most?

> Am I getting better at estimating my time?

The AI should receive structured or aggregated information generated from the user's authorized data rather than independently making clinical interpretations.

Conceptually:

```text
User question
      ↓
Mody Analytics
      ↓
Aggregated personal data
      ↓
AI explanation
      ↓
User-friendly answer
```

The underlying analytics should remain available even without the AI layer.

---

### 10.13 Analytics Principle

Mody should help the user move from:

```text
"I feel like I'm always behind."
```

toward something measurable:

```text
"What do my own data actually show?"
```

The purpose of Personal Analytics is **self-understanding and better planning**, not diagnosis.

Mody analyzes patterns in behavior recorded within the application and should clearly distinguish:

```text
Observed data
      ↓
Pattern
      ↓
Planning insight
```

from:

```text
Medical or psychological diagnosis
```

---

## 11. AI Assistant

Artificial Intelligence is planned as a later layer of Mody rather than the foundation of the application.

The core application should continue functioning even if the AI layer is unavailable.

Potential use cases include:

### Breaking Down Tasks

User:

> I need to prepare a presentation and don't know where to start.

Mody could suggest:

1. Define the objective
2. Create an outline
3. Gather information
4. Build the slides
5. Review the presentation

### Planning Assistance

The user might ask:

> What should I work on now?

With permission, the assistant could consider:

```text
Current tasks
      +
Calendar
      +
Priorities
      +
Available time
      +
Current check-in
      ↓
Suggested next step
```

### Historical Questions

The user may also ask:

> How have my last 6 months been?

In this case, the AI should explain results produced from the user's authorized historical data.

The AI should support the existing planning and analytics systems rather than replace the application's core business logic.

---

## 12. Initial Market

The initial target market is:

**Brazil**

Initial language:

**Portuguese (pt-BR)**

If monetization is introduced in the future, the initial currency would be:

**Brazilian Real (BRL / R$)**

However, monetization is not currently part of the MVP.

The first objective is to build and validate the product.

---

## 13. Current Technology

The MVP is currently being developed using:

- Python
- Streamlit
- Supabase
- PostgreSQL
- Supabase Auth
- Row Level Security (RLS)
- CSS
- Git
- GitHub

The current architecture prioritizes rapid MVP development and validation.

Conceptually:

```text
User
  ↓
Streamlit
  ↓
Python
  ↓
Services
  ↓
Supabase
  ├── Authentication
  └── PostgreSQL
          ↓
         RLS
```

Supabase is responsible for authentication, database access and security policies.

Python contains the application and business logic.

Streamlit provides the current user interface.

---

## 14. Data and User Isolation

Mody is being designed to support multiple users.

The initial data model includes:

```text
auth.users
     │
     ├── profiles
     │
     ├── personalization_preferences
     │
     ├── tasks
     │
     └── checkins
```

`auth.users` is managed by Supabase Auth.

Application tables associate their data with the authenticated user through `user_id`.

Row Level Security is used to isolate user data.

Conceptually:

```text
User
  ↓
Authentication
  ↓
JWT
  ↓
Supabase
  ↓
auth.uid()
  ↓
RLS Policy
  ↓
user_id
```

The intended result is:

```text
User A → User A data ✓
User A → User B data ✕

User B → User B data ✓
User B → User A data ✕
```

The application does not use the `service_role` key for normal client access.

---

## 15. Historical Data

Because Mody intends to analyze changes across periods such as three or six months, historical information is an important architectural requirement.

The database should preserve enough historical information to answer questions such as:

```text
What happened?
      ↓
When did it happen?
      ↓
What was the user's context?
      ↓
How has that changed over time?
```

It is not sufficient to store only the current state of an entity if previous states are important for future analysis.

For example, if a task changes from:

```text
Pending
   ↓
Postponed
   ↓
Rescheduled
   ↓
Completed
```

future analytics may benefit from knowing that history rather than seeing only:

```text
Completed
```

The detailed historical data strategy will be defined in:

`docs/DATABASE.md`

Possible approaches may include dedicated history tables or an event/activity log.

The database design should be reviewed before advanced analytics are implemented.

---

## 16. Current Development Status

### Completed / Initially Configured

- Project structure
- Git repository
- Python virtual environment
- Streamlit
- Supabase project
- PostgreSQL database
- Initial database schema
- Row Level Security
- Streamlit → Supabase connection

### Currently in Development

**Authentication**

This phase includes:

- Sign up
- Sign in
- Session handling
- Sign out
- Authentication error handling
- Testing user isolation

### Next Phase

**Onboarding and personalization**

---

## 17. Development Roadmap

The planned development sequence is:

```text
Phase 1 — Foundation
          ✅
          ↓
Phase 2 — Authentication
          🚧
          ↓
Phase 3 — Onboarding
          ↓
Phase 4 — Task Management
          ↓
Phase 5 — Daily Check-ins
          ↓
Phase 6 — Adaptive Planning
          ↓
Phase 7 — Calendar Integration
          ↓
Phase 8 — Calm Mode
          ↓
Phase 9 — Personal Analytics
          ↓
Phase 10 — AI Assistant
          ↓
Phase 11 — Beta Testing
          ↓
Phase 12 — Productization
```

A detailed roadmap is maintained separately in:

`docs/ROADMAP.md`

---

## 18. MVP Strategy

Mody will be developed incrementally.

The objective is not to implement every planned feature before testing the product.

The development approach is:

```text
Build
  ↓
Test
  ↓
Collect feedback and data
  ↓
Learn
  ↓
Improve
```

The first versions should validate whether the core concept is useful before introducing more complex functionality.

Features such as advanced AI, sophisticated analytics and monetization should come after the fundamental experience has been validated.

---

## 19. Future Product Direction

If the MVP proves useful, later stages may include:

- improved responsive/mobile UX;
- production-grade frontend;
- additional calendar integrations;
- notifications;
- more advanced personal analytics;
- AI-assisted planning;
- deployment infrastructure;
- monitoring and observability;
- backups;
- privacy controls;
- LGPD compliance;
- terms of service;
- subscription management.

The current use of Streamlit is intended to accelerate MVP development.

As the product evolves, the frontend architecture can be reevaluated based on actual product requirements and usage.

---

## 20. Future Monetization

Monetization is intentionally outside the current MVP.

If the product is validated, a future model could include:

```text
Mody Free
    +
Mody Plus
```

Potential paid functionality could include more advanced features such as:

- advanced analytics;
- calendar automation;
- AI-assisted planning;
- extended history;
- additional personalization.

Because the initial market is Brazil, future payment options can be evaluated according to the needs of Brazilian users.

Payment infrastructure will only be designed after the core product has been validated.

---

## 21. Technical Questions Under Evaluation

As the project evolves, the following architectural decisions should be reviewed:

1. Is Streamlit + Python + Supabase/PostgreSQL appropriate for the entire MVP?

2. At what point would a dedicated frontend such as React or Next.js provide enough benefit to justify migration?

3. What is the best approach for authentication and session management in a multi-user Streamlit application?

4. Does the current database model provide enough flexibility for historical and behavioral analytics?

5. What historical events need to be stored now so that meaningful three- and six-month analyses are possible later?

6. Should task changes be stored through history tables, an event log, or another approach?

7. How should calendar integrations be isolated from the core planning logic?

8. How should the AI layer be designed so that the core product does not depend on an LLM?

9. What privacy and LGPD requirements should be addressed before beta testing with real users?

10. Which architectural decisions made during the MVP could become scalability problems if the application grows?

---

## 22. Vision

Mody is not intended to become simply another to-do list.

The long-term goal is to create a planning system that understands that:

> **Available time and available capacity are not always the same thing.**

Instead of asking only:

> What do you need to do today?

Mody should eventually also consider:

> What is realistically manageable for you today?

And over time:

> What can your own history teach you about how you plan, work and manage your time?

This creates a continuous cycle:

```text
Plan
  ↓
Act
  ↓
Record
  ↓
Analyze
  ↓
Learn
  ↓
Adapt
  ↓
Plan better
```

That principle guides the product:

> **The user should not have to adapt to the planner.  
> The planner should adapt to the user.**