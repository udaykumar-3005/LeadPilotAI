create table if not exists public.leads (
  id uuid primary key,
  created_at timestamptz not null default now(),
  lead jsonb not null,
  analysis jsonb not null,
  followup jsonb
);

alter table public.leads enable row level security;
revoke all on public.leads from anon, authenticated;
grant all on public.leads to service_role;
