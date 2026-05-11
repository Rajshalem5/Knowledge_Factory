"""
Phase 2 migration:
- Add candidate_questions table (AI assigns questions per candidate)
- Add job_questions table (question bank per job)
- Add assessments table (tracks phase 2 session per candidate)
"""

import psycopg2

DSN = "postgresql://postgres.nwlfflecgukgfgdcyihk:fRld9eJsOZ6WME0x@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres"

SCHEMA = """
-- ── job_questions: HR/AI links questions to a job ─────────────────
create table if not exists job_questions (
    id          uuid primary key default uuid_generate_v4(),
    job_id      uuid not null references jobs(id)      on delete cascade,
    question_id uuid not null references questions(id) on delete cascade,
    assigned_by uuid references users(id)              on delete set null,
    position    int  not null default 1 check (position >= 1),
    created_at  timestamptz not null default now(),
    unique (job_id, question_id)
);
create index if not exists idx_job_questions_job_id      on job_questions(job_id);
create index if not exists idx_job_questions_question_id on job_questions(question_id);

-- ── candidate_questions: AI assigns specific questions to candidate ─
-- One row per (candidate, question). Candidate ONLY sees rows where
-- their user_id matches. Private test cases never stored here.
create table if not exists candidate_questions (
    id              uuid primary key default uuid_generate_v4(),
    candidate_id    uuid not null references users(id)      on delete cascade,
    job_id          uuid not null references jobs(id)       on delete cascade,
    question_id     uuid not null references questions(id)  on delete cascade,
    -- snapshot of public test cases at assignment time
    public_snapshot jsonb not null default '[]',
    position        int  not null default 1,
    assigned_at     timestamptz not null default now(),
    unique (candidate_id, question_id)
);
create index if not exists idx_cq_candidate_id on candidate_questions(candidate_id);
create index if not exists idx_cq_job_id       on candidate_questions(job_id);
create index if not exists idx_cq_question_id  on candidate_questions(question_id);

-- ── assessments: tracks the phase 2 session per candidate ──────────
create table if not exists assessments (
    id              uuid primary key default uuid_generate_v4(),
    candidate_id    uuid not null references users(id) on delete cascade,
    job_id          uuid not null references jobs(id)  on delete cascade,
    status          varchar(20) not null default 'NOT_STARTED'
                        check (status in ('NOT_STARTED','IN_PROGRESS','COMPLETED','TERMINATED')),
    language        varchar(20) not null default 'python'
                        check (language in ('python','java','cpp','javascript')),
    time_limit_secs int not null default 3600,
    started_at      timestamptz,
    ended_at        timestamptz,
    created_at      timestamptz not null default now(),
    -- one active session per candidate per job
    unique (candidate_id, job_id)
);
create index if not exists idx_assessments_candidate_id on assessments(candidate_id);
create index if not exists idx_assessments_job_id       on assessments(job_id);
create index if not exists idx_assessments_status       on assessments(status);
"""

def run():
    print("Connecting to Supabase...")
    conn = psycopg2.connect(DSN)
    conn.autocommit = True
    cur = conn.cursor()

    print("Running Phase 2 migration...")
    cur.execute(SCHEMA)

    cur.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename")
    tables = [r[0] for r in cur.fetchall()]
    print("\nAll tables:")
    for t in tables:
        cur.execute(f"SELECT COUNT(*) FROM information_schema.columns WHERE table_name='{t}' AND table_schema='public'")
        print(f"  ✅ {t} ({cur.fetchone()[0]} columns)")

    conn.close()
    print("\nPhase 2 migration complete.")

if __name__ == "__main__":
    run()
