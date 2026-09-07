-- Accounting Regulation Analysis & Standard-Setting Impact Measurement System
-- Core schema. SQLite dialect (portable to Postgres with minor type changes).

PRAGMA foreign_keys = ON;

-- Real FASB Accounting Standards Updates (ASUs): one row per issued standard.
CREATE TABLE IF NOT EXISTS asu_standards (
    asu_number              TEXT PRIMARY KEY,      -- e.g. '2016-02'
    topic_code              TEXT NOT NULL,          -- ASC topic, e.g. '842'
    title                   TEXT NOT NULL,
    issued_date             DATE NOT NULL,
    comment_deadline        DATE,                   -- exposure-draft comment period close; precedes issued_date
    effective_date_public   DATE NOT NULL,          -- effective date for public business entities
    effective_date_other    DATE,                   -- effective date for all other entities
    early_adoption_permitted INTEGER NOT NULL DEFAULT 0 CHECK (early_adoption_permitted IN (0,1))
);

-- Synthetic-but-structurally-realistic firm panel: which (firm, standard) pairs
-- adopted, and when, relative to the standard's public effective date.
-- Firm identifiers and adoption timing are simulated (see docs/DATA_SOURCES.md) --
-- real per-firm adoption/restatement data requires licensed sources (Audit Analytics,
-- Compustat/WRDS) not available in this environment.
CREATE TABLE IF NOT EXISTS firm_adoptions (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    firm_id             TEXT NOT NULL,
    sector              TEXT NOT NULL,
    asu_number          TEXT NOT NULL REFERENCES asu_standards(asu_number),
    adoption_date       DATE NOT NULL,
    restatement_filed   INTEGER NOT NULL DEFAULT 0 CHECK (restatement_filed IN (0,1)),
    audit_fee_usd       INTEGER,                    -- illustrative post-adoption audit fee
    UNIQUE(firm_id, asu_number)
);

CREATE INDEX IF NOT EXISTS idx_firm_adoptions_asu ON firm_adoptions(asu_number);
CREATE INDEX IF NOT EXISTS idx_firm_adoptions_firm ON firm_adoptions(firm_id);

-- Materialized-style summary table populated by the impact-metrics stage.
CREATE TABLE IF NOT EXISTS standard_impact_metrics (
    asu_number                 TEXT PRIMARY KEY REFERENCES asu_standards(asu_number),
    -- Days between the exposure draft's comment deadline (comment_deadline
    -- closes BEFORE a standard is finalized) and final issuance: how long
    -- FASB spent re-deliberating after the comment window closed.
    deliberation_lag_days      INTEGER,
    issuance_to_effective_days INTEGER,
    n_firms_tracked            INTEGER,
    n_early_adopters           INTEGER,
    n_on_time_adopters         INTEGER,
    n_late_adopters            INTEGER,
    restatement_rate           REAL,
    avg_audit_fee_usd          REAL,
    computed_at                TEXT NOT NULL
);
