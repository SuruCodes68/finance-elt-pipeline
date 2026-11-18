-- Schemas for the ELT pipeline: raw staging, then dbt-built marts.
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS marts;
