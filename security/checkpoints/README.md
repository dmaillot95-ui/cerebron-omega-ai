# GUARDIAN Ω — VALIDATED CHECKPOINT LEDGER

This directory is the append-only logical ledger for validated rollback checkpoints.

Rules:
- one immutable record per approved checkpoint;
- records are chained with previous_checkpoint_id and previous_record_hash;
- each record carries its own SHA-256 record_hash;
- corrections create a new record; existing records are never silently rewritten;
- only checkpoints satisfying LAST_VALIDATED_STATE_PROTOCOL may enter the ledger;
- AFAH approval is mandatory;
- AI-generated approval is invalid;
- deletion/rewrite attempt => GUARDIAN BLOCK + QUARANTINE candidate.

The Git history is an additional audit trail, not a substitute for external human approval.
