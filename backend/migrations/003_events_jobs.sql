create table if not exists events (
  id         bigint generated always as identity primary key,
  type       text not null,
  ticket_id  uuid references tickets(id) on delete cascade,
  payload    jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);
create index if not exists idx_events_created on events (created_at);
alter table events enable row level security;

create table if not exists job_runs (
  id          uuid primary key default gen_random_uuid(),
  name        text not null,
  status      text not null check (status in ('running','ok','error','skipped')),
  detail      jsonb not null default '{}'::jsonb,
  started_at  timestamptz not null default now(),
  finished_at timestamptz
);
create index if not exists idx_job_runs_name_started on job_runs (name, started_at desc);
alter table job_runs enable row level security;