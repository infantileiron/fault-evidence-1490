-- Incremental upgrade for databases created before soft (weighted) evidence.
-- Fresh databases are created by SQLAlchemy metadata; existing databases need this reviewable migration.
-- Historical runs/reports are not rewritten: old snapshots keep their original fields and CSV layout.
ALTER TABLE cases ADD COLUMN weights JSON NULL;
ALTER TABLE runs ADD COLUMN log_normalizer DOUBLE NULL;
ALTER TABLE runs ADD COLUMN normalizer_probability DOUBLE NULL;
ALTER TABLE runs ADD COLUMN normalizer_underflow BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE runs ADD COLUMN weights JSON NULL;
ALTER TABLE branch_metrics ADD COLUMN log_normalizer DOUBLE NULL;
ALTER TABLE branch_metrics ADD COLUMN log_evidence_probability DOUBLE NULL;
