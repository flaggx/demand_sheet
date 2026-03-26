-- Demand sheet schema derived from Excel template (Account + service fields + chemical columns)
-- Apply with: supabase db push   OR paste into SQL Editor in Supabase Dashboard

-- Chemical product catalog (per signed-in user)
create table if not exists public.chemicals (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  name text not null,
  sort_order int not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (user_id, name)
);

-- Customer / account row (per user)
create table if not exists public.customers (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  account_name text not null,
  service_day text,
  service_frequency text,
  service_tech text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (user_id, account_name)
);

-- Quantity per customer per chemical (null = blank cell in Excel)
create table if not exists public.customer_chemicals (
  customer_id uuid not null references public.customers (id) on delete cascade,
  chemical_id uuid not null references public.chemicals (id) on delete cascade,
  quantity numeric,
  primary key (customer_id, chemical_id)
);

create index if not exists idx_chemicals_user on public.chemicals (user_id);
create index if not exists idx_customers_user on public.customers (user_id);

alter table public.chemicals enable row level security;
alter table public.customers enable row level security;
alter table public.customer_chemicals enable row level security;

-- chemicals
create policy "chemicals_select_own" on public.chemicals
  for select using (auth.uid() = user_id);
create policy "chemicals_insert_own" on public.chemicals
  for insert with check (auth.uid() = user_id);
create policy "chemicals_update_own" on public.chemicals
  for update using (auth.uid() = user_id);
create policy "chemicals_delete_own" on public.chemicals
  for delete using (auth.uid() = user_id);

-- customers
create policy "customers_select_own" on public.customers
  for select using (auth.uid() = user_id);
create policy "customers_insert_own" on public.customers
  for insert with check (auth.uid() = user_id);
create policy "customers_update_own" on public.customers
  for update using (auth.uid() = user_id);
create policy "customers_delete_own" on public.customers
  for delete using (auth.uid() = user_id);

-- customer_chemicals (via parent customer)
create policy "cc_select_own" on public.customer_chemicals
  for select using (
    exists (
      select 1 from public.customers c
      where c.id = customer_chemicals.customer_id and c.user_id = auth.uid()
    )
  );
create policy "cc_insert_own" on public.customer_chemicals
  for insert with check (
    exists (
      select 1 from public.customers c
      where c.id = customer_chemicals.customer_id and c.user_id = auth.uid()
    )
    and exists (
      select 1 from public.chemicals ch
      where ch.id = customer_chemicals.chemical_id and ch.user_id = auth.uid()
    )
  );
create policy "cc_update_own" on public.customer_chemicals
  for update using (
    exists (
      select 1 from public.customers c
      where c.id = customer_chemicals.customer_id and c.user_id = auth.uid()
    )
  );
create policy "cc_delete_own" on public.customer_chemicals
  for delete using (
    exists (
      select 1 from public.customers c
      where c.id = customer_chemicals.customer_id and c.user_id = auth.uid()
    )
  );
