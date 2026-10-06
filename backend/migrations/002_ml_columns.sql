alter table tickets
  add column if not exists priority_confidence real check (priority_confidence between 0 and 1),
  add column if not exists classified_by       text check (classified_by in ('model','llm','human')),
  add column if not exists sla_risk            real check (sla_risk between 0 and 1),
  add column if not exists sla_risk_updated_at timestamptz;

alter table replies
  add column if not exists warnings jsonb not null default '[]'::jsonb;

alter table clusters
  add column if not exists prev_size    int not null default 0,
  add column if not exists top_category text,
  add column if not exists is_trending  boolean not null default false;

create index if not exists idx_tickets_sla_risk on tickets (sla_risk desc) where sla_risk is not null;
create index if not exists idx_clusters_trend   on clusters (trend_score desc);