# Mody — Adaptive Planner

Mody is an adaptive planning and self-regulation web application designed to help users organize their day according to both **available time and current capacity**.

> **The user should not have to adapt to the planner.  
> The planner should adapt to the user.**

The project is currently under active development as an MVP.

---

## About the Project

Traditional planners usually focus on:

```text
Tasks
  +
Deadlines
  +
Available time
```

Mody aims to go further by considering:

```text
Tasks
        +
Priorities
        +
Calendar
        +
Available time
        +
Current capacity
        +
Historical patterns
        ↓
Adaptive Planning
```

The objective is not simply to maximize productivity.

Mody aims to help users build plans that are **realistic, manageable and adaptable**.

---

## Core Features

### Adaptive Planning

Mody aims to create daily plans based on the user's tasks, priorities, available time, existing commitments and current capacity.

### Task Management

Users will be able to create and manage tasks with information such as:

- priority;
- deadline;
- estimated duration;
- actual duration;
- status.

### Daily Check-ins

Lightweight check-ins will allow users to record information such as energy, focus and perceived overload.

These data can later provide context for planning and personal analytics.

### Personalization

During onboarding, users may optionally select preferences related to areas where they would like additional support, such as:

- starting tasks;
- organizing the day;
- remembering commitments;
- avoiding overload;
- reducing distractions;
- managing anxiety;
- building routines;
- estimating time.

Mody is designed with ADHD and anxiety-related needs in mind, but it is **not a diagnostic or medical application**.

### Calendar Integration

Future versions will integrate with external calendars, initially Google Calendar, to understand existing commitments and available periods.

### Calm Mode

A simplified interface is planned for moments when the user feels overwhelmed.

The goal is to reduce cognitive load and provide structured self-regulation support without presenting the feature as medical treatment or emergency assistance.

### Personal Analytics

Mody will eventually allow users to explore their own historical patterns over periods such as:

```text
30 days
3 months
6 months
Custom period
```

Possible insights include:

- task completion trends;
- estimated vs. actual task duration;
- frequently postponed tasks;
- productive periods of the day;
- calendar workload;
- changes in recorded energy or overload;
- relationships between workload and task behavior.

For example:

> During the last 3 months, your tasks usually took longer than you initially estimated.

or:

> Your recorded overload tended to be higher during weeks with more calendar commitments.

These are intended to be **observations from the user's own data**, not medical or psychological conclusions.

Historical patterns may later help improve adaptive planning.

---

## How Mody Learns

The long-term product concept follows a continuous cycle:

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

Instead of only storing tasks, Mody aims to use historical information to help users better understand their own planning patterns.

---

## AI Assistant

Artificial Intelligence is planned as a later layer of the application.

Potential use cases include:

- breaking large tasks into smaller steps;
- helping identify the next task;
- explaining personal analytics;
- answering questions about historical patterns;
- supporting adaptive planning.

The core application should remain functional without AI.

---

## Technology Stack

Current MVP:

```text
Frontend / UI
Streamlit

Application Logic
Python

Backend Services
Supabase

Database
PostgreSQL

Authentication
Supabase Auth

Authorization
Row Level Security (RLS)

Version Control
Git + GitHub
```

---

## High-Level Architecture

```text
                User
                  ↓
              Streamlit
                  ↓
                Python
                  ↓
               Services
             ┌────┴────┐
             ↓         ↓
           Auth      Database
             ↓         ↓
             └── Supabase
                    ↓
                PostgreSQL
                    ↓
                   RLS
```

Future integrations may include:

```text
Google Calendar
Personal Analytics
AI Assistant
Notifications
```

---

## Data Privacy

Mody is being designed as a multi-user application.

Application data is associated with the authenticated user's `user_id`.

Supabase Row Level Security is used to ensure that users can access only their own data.

Conceptually:

```text
Authenticated User
        ↓
       JWT
        ↓
    auth.uid()
        ↓
   RLS Policies
        ↓
   User's Data
```

The application does not use the Supabase `service_role` key for normal client access.

Privacy and LGPD requirements will be reviewed before testing the application with external users.

---

## Current Status

### Completed

- [x] Initial project structure
- [x] Git repository
- [x] Python virtual environment
- [x] Streamlit setup
- [x] Supabase project
- [x] PostgreSQL initial schema
- [x] Row Level Security
- [x] Streamlit → Supabase connection

### In Progress

- [ ] Authentication
  - Sign up
  - Sign in
  - Session handling
  - Sign out
  - Error handling
  - User isolation testing

### Next

- [ ] Onboarding
- [ ] Personalization
- [ ] Task management
- [ ] Daily check-ins
- [ ] Adaptive planning
- [ ] Calendar integration
- [ ] Calm Mode
- [ ] Personal analytics
- [ ] AI assistant

---

## Roadmap

```text
Foundation                 ✅
     ↓
Authentication             🚧
     ↓
Onboarding
     ↓
Task Management
     ↓
Daily Check-ins
     ↓
Adaptive Planning
     ↓
Calendar Integration
     ↓
Calm Mode
     ↓
Personal Analytics
     ↓
AI Assistant
     ↓
Beta Testing
     ↓
Productization
```

---

## Documentation

Detailed project documentation is available in the `docs/` directory:

```text
docs/
├── PROJECT_OVERVIEW.md
├── DATABASE.md
├── ARCHITECTURE.md
└── ROADMAP.md
```

### Project Overview

`docs/PROJECT_OVERVIEW.md`

Contains the complete product concept, features, analytics strategy and long-term vision.

### Database

`docs/DATABASE.md`

Documents the database model, user data isolation and historical data strategy.

### Architecture

`docs/ARCHITECTURE.md`

Documents the application architecture and technical decisions.

### Roadmap

`docs/ROADMAP.md`

Contains the detailed development phases and milestones.

---

## Development Philosophy

Mody is being developed incrementally:

```text
Build
  ↓
Test
  ↓
Collect feedback
  ↓
Learn
  ↓
Improve
```

The current priority is validating the core product before introducing advanced AI, monetization or large-scale infrastructure.

---

## Initial Market

The first planned market is **Brazil**, with the application initially available in **Portuguese (pt-BR)**.

Monetization is intentionally outside the current MVP.

---

## Project Vision

Mody is not intended to become simply another to-do list.

The long-term goal is to create a planning system that recognizes an important distinction:

> **Available time and available capacity are not always the same thing.**

Mody should eventually help users answer not only:

> What do I need to do today?

but also:

> What is realistically manageable today?

and, over time:

> What can my own history teach me about how I plan and manage my time?