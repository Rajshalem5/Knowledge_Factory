"""
Supabase Schema Migration - Complete Database Setup

This script creates all required tables for the Knowledge Factory platform:
- Core tables: users, jobs, applicant_status
- Assessment tables: questions, submissions, scores
- Phase 2 tables: assessments, job_questions, candidate_questions

Run this script to set up the complete database schema in Supabase.
"""

import psycopg2

DSN = "postgresql://postgres.nwlfflecgukgfgdcyihk:fRld9eJsOZ6WME0x@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres"

SCHEMA = """
create extension if not exists "uuid-ossp";

-- ── 1. USERS ──────────────────────────────────────────────────────
create table if not exists users (
    id            uuid primary key default uuid_generate_v4(),
    email         varchar(255) not null unique,
    password_hash text not null,
    full_name     varchar(150) not null,
    role          varchar(30)  not null
                      check (role in ('SUPERADMIN','ADMIN','HR','CANDIDATE')),
    status        varchar(20)  not null default 'ACTIVE'
                      check (status in ('ACTIVE','INACTIVE')),
    resume_url    text,
    college       varchar(255),
    branch        varchar(100),
    cgpa          numeric(4,2),
    phone         varchar(20),
    passed_out_year integer,
    created_by    uuid references users(id) on delete set null,
    created_at    timestamptz not null default now(),
    updated_at    timestamptz not null default now()
);

create unique index if not exists only_one_superadmin
    on users(role) where role = 'SUPERADMIN';
create index if not exists idx_users_email      on users(email);
create index if not exists idx_users_role       on users(role);
create index if not exists idx_users_created_by on users(created_by);

-- ── 2. JOBS ───────────────────────────────────────────────────────
create table if not exists jobs (
    id               uuid primary key default uuid_generate_v4(),
    job_id           varchar(50)  not null unique,
    title            varchar(255) not null,
    job_description  text not null,
    skillset         text[] not null,
    created_by       uuid not null references users(id) on delete restrict,
    status           varchar(20)  not null default 'DRAFT'
                         check (status in ('OPEN','CLOSED','DRAFT')),
    openings         int check (openings >= 0),
    experience_level varchar(50),
    location         varchar(150),
    created_at       timestamptz not null default now(),
    updated_at       timestamptz not null default now()
);

create index if not exists idx_jobs_created_by on jobs(created_by);
create index if not exists idx_jobs_status     on jobs(status);
create index if not exists idx_jobs_title      on jobs(title);

-- ── 3. APPLICANT_STATUS ───────────────────────────────────────────
create table if not exists applicant_status (
    id         uuid primary key default uuid_generate_v4(),
    user_id    uuid not null references users(id) on delete cascade,
    job_id     uuid not null references jobs(id)  on delete cascade,
    raw_text   text not null,
    score      numeric(5,2) not null,
    status     varchar(30)  not null
                   check (status in (
                       'APPLIED','SHORTLISTED','REJECTED',
                       'PHASE2_PENDING','PHASE2_STARTED','PHASE2_COMPLETED','SELECTED'
                   )),
    created_at timestamptz not null default now()
);

create unique index if not exists uq_applicant_status_user_job
    on applicant_status(user_id, job_id);
create index if not exists idx_applicant_status_user   on applicant_status(user_id);
create index if not exists idx_applicant_status_job    on applicant_status(job_id);
create index if not exists idx_applicant_status_status on applicant_status(status);

-- ── 4. QUESTIONS ──────────────────────────────────────────────────
create table if not exists questions (
    id                 uuid primary key default uuid_generate_v4(),
    qid                varchar(50)  not null unique,
    title              varchar(255) not null,
    description        text not null,
    difficulty         varchar(30)  not null
                           check (difficulty in ('EASY','MEDIUM','HARD')),
    topics             text[] not null,
    input_format       text not null,
    output_format      text not null,
    constraints        text not null,
    boilerplate        jsonb not null,
    public_test_cases  jsonb not null,
    private_test_cases jsonb not null,
    generated_by_ai    boolean not null default false,
    ai_model           varchar(100),
    ai_prompt          text,
    is_active          boolean not null default true,
    created_by         uuid not null references users(id) on delete restrict,
    created_at         timestamptz not null default now(),
    times_used         int not null default 0 check (times_used >= 0),
    avg_passrate       numeric(5,2) not null default 0
                           check (avg_passrate >= 0 and avg_passrate <= 100)
);

create index if not exists idx_questions_qid        on questions(qid);
create index if not exists idx_questions_difficulty on questions(difficulty);
create index if not exists idx_questions_created_by on questions(created_by);
create index if not exists idx_questions_is_active  on questions(is_active);

-- ── 5. SUBMISSIONS ────────────────────────────────────────────────
create table if not exists submissions (
    id            uuid primary key default uuid_generate_v4(),
    submission_id varchar(50) not null unique,
    qid           uuid not null references questions(id) on delete cascade,
    candidate_id  uuid not null references users(id)     on delete cascade,
    language      varchar(50) not null,
    code          text,
    mcq_answers   jsonb,
    time_spent    int not null check (time_spent >= 0),
    created_at    timestamptz not null default now(),
    updated_at    timestamptz not null default now()
);

create index if not exists idx_submissions_qid       on submissions(qid);
create index if not exists idx_submissions_candidate on submissions(candidate_id);
create index if not exists idx_submissions_language  on submissions(language);

-- ── 6. SCORES ─────────────────────────────────────────────────────
create table if not exists scores (
    id               uuid primary key default uuid_generate_v4(),
    score_id         varchar(50)  not null unique,
    candidate_id     uuid not null references users(id)        on delete cascade,
    submission_id    uuid not null references submissions(id)  on delete cascade,
    qid              uuid not null references questions(id)    on delete cascade,
    score_percentage numeric(5,2) not null
                         check (score_percentage >= 0 and score_percentage <= 100),
    marks_obtained   numeric(6,2) not null check (marks_obtained >= 0),
    total_marks      numeric(6,2) not null check (total_marks > 0),
    verdict          varchar(20)  not null check (verdict in ('PASS','FAIL')),
    created_at       timestamptz not null default now(),
    updated_at       timestamptz not null default now()
);

create index if not exists idx_scores_candidate  on scores(candidate_id);
create index if not exists idx_scores_submission on scores(submission_id);
create index if not exists idx_scores_qid        on scores(qid);
create index if not exists idx_scores_verdict    on scores(verdict);

-- ═══════════════════════════════════════════════════════════════════
-- PHASE 2 ASSESSMENT TABLES
-- ═══════════════════════════════════════════════════════════════════

-- ── 7. ASSESSMENTS ─────────────────────────────────────────────────
-- Tracks Phase 2 assessment sessions per candidate
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

-- ── 8. JOB_QUESTIONS ────────────────────────────────────────────────
-- HR/AI links questions to a job (question bank per job)
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

-- ── 9. CANDIDATE_QUESTIONS ──────────────────────────────────────────
-- AI assigns specific questions to candidate
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

-- ═══════════════════════════════════════════════════════════════════
-- ALTER EXISTING TABLES (for databases that already exist)
-- ═══════════════════════════════════════════════════════════════════

-- Add missing columns to users table if they don't exist
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='users' AND column_name='college') THEN
        ALTER TABLE users ADD COLUMN college VARCHAR(255);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='users' AND column_name='branch') THEN
        ALTER TABLE users ADD COLUMN branch VARCHAR(100);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='users' AND column_name='cgpa') THEN
        ALTER TABLE users ADD COLUMN cgpa NUMERIC(4,2);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='users' AND column_name='phone') THEN
        ALTER TABLE users ADD COLUMN phone VARCHAR(20);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='users' AND column_name='passed_out_year') THEN
        ALTER TABLE users ADD COLUMN passed_out_year INTEGER;
    END IF;
END $$;
"""

def run():
    print("Connecting to Supabase...")
    conn = psycopg2.connect(DSN)
    conn.autocommit = True
    cur = conn.cursor()

    print("Running migration...")
    cur.execute(SCHEMA)

    # Verify all required tables
    required_tables = [
        'users', 'jobs', 'applicant_status', 'questions', 
        'submissions', 'scores', 'assessments', 'job_questions', 
        'candidate_questions'
    ]
    
    print("\n[OK] Migration complete! Verifying tables...")
    cur.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename")
    all_tables = [r[0] for r in cur.fetchall()]
    
    print("\nRequired tables:")
    for table in required_tables:
        if table in all_tables:
            cur.execute(f"SELECT COUNT(*) FROM information_schema.columns WHERE table_name='{table}' AND table_schema='public'")
            col_count = cur.fetchone()[0]
            print(f"  [OK] {table} ({col_count} columns)")
        else:
            print(f"  [X] {table} - MISSING!")

    conn.close()
    print("\n[SUCCESS] Supabase schema migration complete!")

if __name__ == "__main__":
    run()
