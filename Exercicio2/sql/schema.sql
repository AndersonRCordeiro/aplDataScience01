-- =============================================================
-- TechFix Informática — schema.sql
-- Banco: Supabase (PostgreSQL)
-- Executar no SQL Editor do Supabase
-- =============================================================

-- -------------------------------------------------------------
-- 1) TABELA DE CLIENTES
--    - id: chave primária auto-incremental
--    - email: único + validação de formato (CHECK com regex)
--    - celular_whatsapp: apenas dígitos, 10 a 13 caracteres
-- -------------------------------------------------------------
create table if not exists public.clientes (
    id                bigint generated always as identity primary key,
    nome              text        not null,
    endereco          text        not null,
    email             text        not null unique,
    celular_whatsapp  text        not null,
    data_cadastro     timestamptz not null default now(),

    -- Validação simples de formato de e-mail
    constraint chk_clientes_email
        check (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),

    -- Celular somente dígitos, entre 10 e 13 caracteres
    constraint chk_clientes_celular
        check (celular_whatsapp ~ '^[0-9]{10,13}$')
);

-- -------------------------------------------------------------
-- 2) TABELA DE ORDENS DE SERVIÇO
--    - cliente_id: FK → clientes(id)
--    - ON DELETE CASCADE: ao excluir cliente, suas OS são removidas
--    - status: restrito por CHECK aos valores permitidos
-- -------------------------------------------------------------
create table if not exists public.ordens_servico (
    id                 bigint generated always as identity primary key,
    cliente_id         bigint      not null
                         references public.clientes(id) on delete cascade,
    modelo_computador  text        not null,
    problema_relatado  text        not null,
    status             text        not null default 'Aberto',
    data_abertura      timestamptz not null default now(),
    data_atualizacao   timestamptz not null default now(),

    constraint chk_os_status
        check (status in ('Aberto', 'Em análise', 'Aguardando peça', 'Concluído', 'Entregue'))
);

-- -------------------------------------------------------------
-- 3) ÍNDICES auxiliares para consultas/filtros do painel
-- -------------------------------------------------------------
create index if not exists idx_os_cliente_id on public.ordens_servico(cliente_id);
create index if not exists idx_os_status     on public.ordens_servico(status);
create index if not exists idx_clientes_nome on public.clientes(nome);

-- -------------------------------------------------------------
-- 4) TRIGGER: atualiza data_atualizacao automaticamente a cada UPDATE
-- -------------------------------------------------------------
create or replace function public.set_data_atualizacao()
returns trigger
language plpgsql
as $$
begin
    new.data_atualizacao = now();
    return new;
end;
$$;

drop trigger if exists trg_os_data_atualizacao on public.ordens_servico;
create trigger trg_os_data_atualizacao
    before update on public.ordens_servico
    for each row
    execute function public.set_data_atualizacao();

-- -------------------------------------------------------------
-- 5) ROW LEVEL SECURITY (RLS)
--    ATENÇÃO DIDÁTICA: as políticas abaixo são PERMISSIVAS para
--    a chave "anon", pois é uma atividade de sala. Em produção,
--    restrinja por auth.uid() / roles específicas.
-- -------------------------------------------------------------
alter table public.clientes       enable row level security;
alter table public.ordens_servico enable row level security;

-- Clientes
create policy "clientes_select" on public.clientes
    for select to anon, authenticated using (true);
create policy "clientes_insert" on public.clientes
    for insert to anon, authenticated with check (true);
create policy "clientes_update" on public.clientes
    for update to anon, authenticated using (true) with check (true);
create policy "clientes_delete" on public.clientes
    for delete to anon, authenticated using (true);

-- Ordens de serviço
create policy "os_select" on public.ordens_servico
    for select to anon, authenticated using (true);
create policy "os_insert" on public.ordens_servico
    for insert to anon, authenticated with check (true);
create policy "os_update" on public.ordens_servico
    for update to anon, authenticated using (true) with check (true);
create policy "os_delete" on public.ordens_servico
    for delete to anon, authenticated using (true);