"""Add job_questions table to Supabase."""

import psycopg2

DSN = "postgresql://postgres.nwlfflecgukgfgdcyihk:fRld9eJsOZ6WME0x@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres"

SQL = """
create table if not exists job_questions (
    id          uuid primary key default uuid_generate_v4(),
    job_id      uuid not null references jobs(id) on delete cascade,
    question_id uuid not null references questions(id) on delete cascade,
    assigned_by uuid not null references users(id) on delete restrict,
    position    int  not null default 1 check (position >= 1),
    created_at  timestamptz not null default now(),
    unique (job_id, question_id)
);

create index if not exists idx_job_questions_job_id      on job_questions(job_id);
create index if not exists idx_job_questions_question_id on job_questions(question_id);
create index if not exists idx_job_questions_assigned_by on job_questions(assigned_by);

-- assessments table: tracks per-candidate Phase 2 session
create table if not exists assessments (
    id           uuid primary key default uuid_generate_v4(),
    candidate_id uuid not null references users(id) on delete cascade,
    job_id       uuid not null references jobs(id)  on delete cascade,
    status       varchar(30) not null default 'PENDING'
                     check (status in ('PENDING','IN_PROGRESS','COMPLETED','TERMINATED')),
    language     varchar(20) not null default 'python'
                     check (language in ('python','java','cpp','javascript')),
    link_token   varchar(64) not null unique,
    link_expiry  timestamptz not null,
    started_at   timestamptz,
    ended_at     timestamptz,
    time_limit_seconds int not null default 3600,
    created_at   timestamptz not null default now(),
    unique (candidate_id, job_id)
);

create index if not exists idx_assessments_candidate_id on assessments(candidate_id);
create index if not exists idx_assessments_job_id       on assessments(job_id);
create index if not exists idx_assessments_status       on assessments(status);
create index if not exists idx_assessments_link_token   on assessments(link_token);
"""

conn = psycopg2.connect(DSN)
conn.autocommit = True
cur = conn.cursor()
cur.execute(SQL)

cur.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename")
print("All tables:", [r[0] for r in cur.fetchall()])
conn.close()
print("Done.")
