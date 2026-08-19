-- =========================================================
-- Mody — schema v1
-- Tabelas: profiles, personalization_preferences, tasks, checkins
--
-- Pensado para rodar do zero no SQL Editor de um projeto
-- Supabase novo. Usa "if not exists" / "or replace" em tudo,
-- então também é seguro rodar de novo por cima do mesmo projeto
-- (não apaga nada existente).
-- =========================================================

create extension if not exists "pgcrypto";


-- =========================================================
-- Função reutilizável: atualiza updated_at automaticamente
-- em qualquer tabela que tenha essa coluna.
-- =========================================================
create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
    new.updated_at = now();
    return new;
end;
$$;


-- =========================================================
-- profiles
-- Dados básicos do usuário. 1 linha por conta autenticada.
-- =========================================================
create table if not exists public.profiles (
    user_id      uuid primary key references auth.users (id) on delete cascade,
    display_name text,
    timezone     text,
    created_at   timestamptz not null default now(),
    updated_at   timestamptz not null default now()
);

drop trigger if exists set_updated_at on public.profiles;
create trigger set_updated_at
    before update on public.profiles
    for each row execute function public.set_updated_at();


-- =========================================================
-- personalization_preferences
-- Preferências opcionais de personalização (onboarding).
-- Dados sensíveis (saúde mental) — minimização de dados:
-- só os dois campos abaixo. NUNCA usados para diagnóstico
-- ou decisão clínica, apenas para adaptar a interface.
-- =========================================================
create table if not exists public.personalization_preferences (
    user_id uuid primary key references auth.users (id) on delete cascade,

    -- NULL = ainda não respondeu. 'prefer_not_to_say' = respondeu
    -- e escolheu não informar. São sinais diferentes.
    support_profile text
        check (
            support_profile is null
            or support_profile in (
                'adhd',
                'anxiety',
                'adhd_anxiety',
                'none',
                'prefer_not_to_say'
            )
        ),

    -- Seleção múltipla opcional, validada contra a lista fechada.
    support_needs text[]
        check (
            support_needs is null
            or support_needs <@ array[
                'start_tasks',
                'organize_day',
                'remember_commitments',
                'avoid_overload',
                'reduce_distractions',
                'manage_anxiety',
                'build_routines',
                'estimate_time'
            ]::text[]
        ),

    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

drop trigger if exists set_updated_at on public.personalization_preferences;
create trigger set_updated_at
    before update on public.personalization_preferences
    for each row execute function public.set_updated_at();


-- =========================================================
-- tasks
-- Captura rápida: só "title" é obrigatório.
-- =========================================================
create table if not exists public.tasks (
    id                 uuid primary key default gen_random_uuid(),
    user_id            uuid not null references auth.users (id) on delete cascade,
    title              text not null
                         check (length(trim(title)) > 0),
    description        text,
    status             text not null default 'pending'
                         check (status in ('pending', 'in_progress', 'completed', 'blocked')),
    priority           text
                         check (priority is null or priority in ('low', 'medium', 'high')),
    estimated_minutes  integer
                         check (estimated_minutes is null or estimated_minutes > 0),
    due_date           date,
    created_at         timestamptz not null default now(),
    updated_at         timestamptz not null default now(),
    completed_at       timestamptz
);

-- Índice composto: cobre tanto consultas "todas as tarefas do usuário"
-- (Postgres usa o prefixo user_id da composta) quanto o caso mais comum,
-- "tarefas do usuário filtradas por status" (ex: pendentes de hoje).
create index if not exists tasks_user_status_idx on public.tasks (user_id, status);

drop trigger if exists set_updated_at on public.tasks;
create trigger set_updated_at
    before update on public.tasks
    for each row execute function public.set_updated_at();


-- =========================================================
-- checkins
-- Registro do estado do usuário. Sem updated_at: é um
-- evento pontual, não algo pensado para ser editado depois.
-- =========================================================
create table if not exists public.checkins (
    id             uuid primary key default gen_random_uuid(),
    user_id        uuid not null references auth.users (id) on delete cascade,
    state          text not null
                     check (state in ('well', 'overwhelmed', 'calm_needed')),
    energy_level   smallint check (energy_level between 1 and 5),
    anxiety_level  smallint check (anxiety_level between 1 and 5),
    focus_level    smallint check (focus_level between 1 and 5),
    created_at     timestamptz not null default now()
);

-- Índice composto: consulta típica é "check-ins do usuário, mais
-- recentes primeiro" (ex: histórico, último check-in do dia).
create index if not exists checkins_user_created_idx
    on public.checkins (user_id, created_at desc);


-- =========================================================
-- Row Level Security
-- Regra única em todas as tabelas: auth.uid() = user_id.
-- Policies escopadas ao role "authenticated" — usuários
-- anônimos (role "anon") não têm acesso a nenhuma linha.
-- =========================================================

alter table public.profiles                    enable row level security;
alter table public.personalization_preferences enable row level security;
alter table public.tasks                       enable row level security;
alter table public.checkins                    enable row level security;

-- ---- profiles ----
drop policy if exists "profiles_select_own" on public.profiles;
create policy "profiles_select_own" on public.profiles
    for select to authenticated
    using (auth.uid() = user_id);

drop policy if exists "profiles_insert_own" on public.profiles;
create policy "profiles_insert_own" on public.profiles
    for insert to authenticated
    with check (auth.uid() = user_id);

drop policy if exists "profiles_update_own" on public.profiles;
create policy "profiles_update_own" on public.profiles
    for update to authenticated
    using (auth.uid() = user_id)
    with check (auth.uid() = user_id);

drop policy if exists "profiles_delete_own" on public.profiles;
create policy "profiles_delete_own" on public.profiles
    for delete to authenticated
    using (auth.uid() = user_id);

-- ---- personalization_preferences ----
drop policy if exists "personalization_preferences_select_own" on public.personalization_preferences;
create policy "personalization_preferences_select_own" on public.personalization_preferences
    for select to authenticated
    using (auth.uid() = user_id);

drop policy if exists "personalization_preferences_insert_own" on public.personalization_preferences;
create policy "personalization_preferences_insert_own" on public.personalization_preferences
    for insert to authenticated
    with check (auth.uid() = user_id);

drop policy if exists "personalization_preferences_update_own" on public.personalization_preferences;
create policy "personalization_preferences_update_own" on public.personalization_preferences
    for update to authenticated
    using (auth.uid() = user_id)
    with check (auth.uid() = user_id);

drop policy if exists "personalization_preferences_delete_own" on public.personalization_preferences;
create policy "personalization_preferences_delete_own" on public.personalization_preferences
    for delete to authenticated
    using (auth.uid() = user_id);

-- ---- tasks ----
drop policy if exists "tasks_select_own" on public.tasks;
create policy "tasks_select_own" on public.tasks
    for select to authenticated
    using (auth.uid() = user_id);

drop policy if exists "tasks_insert_own" on public.tasks;
create policy "tasks_insert_own" on public.tasks
    for insert to authenticated
    with check (auth.uid() = user_id);

drop policy if exists "tasks_update_own" on public.tasks;
create policy "tasks_update_own" on public.tasks
    for update to authenticated
    using (auth.uid() = user_id)
    with check (auth.uid() = user_id);

drop policy if exists "tasks_delete_own" on public.tasks;
create policy "tasks_delete_own" on public.tasks
    for delete to authenticated
    using (auth.uid() = user_id);

-- ---- checkins ----
drop policy if exists "checkins_select_own" on public.checkins;
create policy "checkins_select_own" on public.checkins
    for select to authenticated
    using (auth.uid() = user_id);

drop policy if exists "checkins_insert_own" on public.checkins;
create policy "checkins_insert_own" on public.checkins
    for insert to authenticated
    with check (auth.uid() = user_id);

drop policy if exists "checkins_update_own" on public.checkins;
create policy "checkins_update_own" on public.checkins
    for update to authenticated
    using (auth.uid() = user_id)
    with check (auth.uid() = user_id);

drop policy if exists "checkins_delete_own" on public.checkins;
create policy "checkins_delete_own" on public.checkins
    for delete to authenticated
    using (auth.uid() = user_id);
