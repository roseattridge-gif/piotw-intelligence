# PIOTW company intelligence read model v1

## Purpose

This read model turns stored evidence into a company-facing factual view without pretending that PIOTW has a validated score or predictor. The machine-readable contract is [company_intelligence_snapshot_v1.schema.json](../config/company_intelligence_snapshot_v1.schema.json); the implementation is `piotw_read_model/company_intelligence.py`.

## Contract

Each snapshot contains:

- company ID, display name and observation time;
- all eight approved ontology dimensions;
- factual observations and accepted events per dimension;
- deterministic state, change, velocity, novelty and persistence where history permits;
- exact source URL, source hash, observation/effective time and collector version;
- source freshness, collection health and coverage;
- explicit `NOT_YET_VALIDATED` placeholders for dimension score, prediction, overall score, benchmark, Pressure and Expansion.

Facts are canonical. One event may link to several dimensions, but the source fact is not copied into several competing records.

## Current real-evidence fixture

[affirm.json](../data/derived/company_intelligence_v1/affirm.json) is generated from the real careers collection database. It shows two snapshots, the current open-vacancy state, observed change and source-level provenance. Procurement is deliberately shown as unresolved because no supplier-to-company match has been approved.

The small internal API boundary is `load_company_snapshot(snapshot_directory, company_id)`. It returns the versioned JSON payload suitable for a later `piotw-web` company profile. No web UI integration is made in this phase.

## What the model does not say

A vacancy increase is not labelled growth; a vacancy decrease is not labelled distress. Procurement notices are not attached to companies through fuzzy guesses. Missing dimensions display insufficient source coverage. This makes uncertainty visible instead of converting sparse evidence into a score.

