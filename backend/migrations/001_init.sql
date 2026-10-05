-- ResolvIQ initial schema
create extension if not exists vector;

-- ---------- helpers ----------
create or replace function set_updated_at() returns trigger
language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end $$;

-- ---------- agents ----------
create table agents (
  id           uuid primary key default gen_random_uuid(),
  name         text not null unique,
  team         text not null,
  current_load int  not null default 0 check (current_load >= 0),
  created_at   timestamptz not null default now()
);

-- ---------- tickets ----------
create table tickets (
  id                         uuid primary key default gen_random_uuid(),
  subject                    text not null,
  body                       text not null,
  customer_email             text not null,
  status                     text not null default 'new'
    check (status in ('new','classified','assigned','in_progress','resolved','closed')),
  category                   text
    check (category in ('billing','account','technical','shipping','integrations','general')),
  priority                   text check (priority in ('low','medium','high','urgent')),
  team                       text,
  assigned_agent_id          uuid references agents(id) on delete set null,
  classification_confidence  real check (classification_confidence between 0 and 1),
  needs_human_triage         boolean not null default false,
  extracted                  jsonb not null default '{}'::jsonb,  -- LLM structured extraction (order id, product, ...)
  queue_length_at_creation   int not null default 0,              -- SLA model feature
  agent_load_at_assignment   int,                                 -- SLA model feature
  reopen_count               int not null default 0,
  embedding                  vector(384),
  created_at                 timestamptz not null default now(),
  first_response_at          timestamptz,
  resolved_at                timestamptz,
  updated_at                 timestamptz not null default now()
);
create trigger trg_tickets_updated before update on tickets
  for each row execute function set_updated_at();

-- ---------- knowledge base ----------
create table kb_articles (
  id         uuid primary key default gen_random_uuid(),
  title      text not null unique,
  category   text not null,
  content    text not null,
  created_at timestamptz not null default now()
);

create table kb_chunks (
  id          uuid primary key default gen_random_uuid(),
  article_id  uuid not null references kb_articles(id) on delete cascade,
  chunk_index int  not null,
  content     text not null,
  embedding   vector(384),
  unique (article_id, chunk_index)
);

-- ---------- AI outputs ----------
create table replies (
  id             uuid primary key default gen_random_uuid(),
  ticket_id      uuid not null references tickets(id) on delete cascade,
  draft_text     text not null,
  sources        jsonb not null default '[]'::jsonb,
  model          text,
  top_similarity real,
  status         text not null default 'draft'
    check (status in ('draft','approved','sent','rejected')),
  created_at     timestamptz not null default now(),
  approved_at    timestamptz
);

create table sla_predictions (
  id                 uuid primary key default gen_random_uuid(),
  ticket_id          uuid not null references tickets(id) on delete cascade,
  breach_probability real not null check (breach_probability between 0 and 1),
  model_version      text,
  predicted_at       timestamptz not null default now()
);

create table clusters (
  id           uuid primary key default gen_random_uuid(),
  title        text,
  summary      text,
  size         int not null default 0,
  trend_score  real not null default 0,
  window_start timestamptz,
  window_end   timestamptz,
  created_at   timestamptz not null default now()
);

create table cluster_members (
  cluster_id uuid not null references clusters(id) on delete cascade,
  ticket_id  uuid not null references tickets(id)  on delete cascade,
  primary key (cluster_id, ticket_id)
);

-- ---------- indexes ----------
create index idx_tickets_embedding on tickets    using hnsw (embedding vector_cosine_ops);
create index idx_chunks_embedding  on kb_chunks  using hnsw (embedding vector_cosine_ops);
create index idx_tickets_status    on tickets (status);
create index idx_tickets_created   on tickets (created_at desc);
create index idx_tickets_team      on tickets (team);
create index idx_tickets_category  on tickets (category);
create index idx_tickets_agent     on tickets (assigned_agent_id);
create index idx_replies_ticket    on replies (ticket_id);
create index idx_sla_ticket_time   on sla_predictions (ticket_id, predicted_at desc);
create index idx_members_ticket    on cluster_members (ticket_id);

-- ---------- retrieval function ----------
create or replace function match_kb_chunks(
  query_embedding vector(384),
  match_count     int   default 5,
  min_similarity  float default 0.0
)
returns table (
  chunk_id uuid, article_id uuid, article_title text, content text, similarity float
)
language sql stable as $$
  select c.id, c.article_id, a.title, c.content,
         1 - (c.embedding <=> query_embedding) as similarity
  from kb_chunks c
  join kb_articles a on a.id = c.article_id
  where c.embedding is not null
    and 1 - (c.embedding <=> query_embedding) >= min_similarity
  order by c.embedding <=> query_embedding
  limit match_count;
$$;

-- ---------- security: deny-by-default ----------
-- Only the backend (postgres role, bypasses RLS) can touch data for now.
-- Per-role policies for the frontend come in the auth step.
alter table agents          enable row level security;
alter table tickets         enable row level security;
alter table kb_articles     enable row level security;
alter table kb_chunks       enable row level security;
alter table replies         enable row level security;
alter table sla_predictions enable row level security;
alter table clusters        enable row level security;
alter table cluster_members enable row level security;