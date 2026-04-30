# Architecture Notes

`long-long-run` is a runtime harness, not a prompt checklist.

The design is intentionally small:

- `state.py` owns schema, normalization, load, and save
- `runtime.py` owns mode semantics, readiness, authorization, checkpointing, hook context, and stop logic
- `controller.py` is only a CLI facade

## Session identity

The runtime is session-bound.

Identity resolution order is:

1. hook-provided `session_id`
2. explicit CLI or API `session_id`
3. explicit state `path`
4. `CODEX_THREAD_ID`

## State philosophy

State stores only durable truth that affects runtime behavior.

It does not try to store every thought.

The persistent state is intentionally limited to:

- `runtime`
- `contract`
- `thinking`
- `activation`
- `progress`

Older schemas are not auto-migrated.

If a legacy state file is present, the runtime should reject it and force an explicit rebuild.

## Authorization model

The runtime separates:

- readiness
- authorization

The agent may be ready in `INC` and still remain in `INC`.

Readiness is a signal for agent judgment, not a forced transition rule.

The agent decides whether and when to raise `ACTIVE`.

The user decides whether `ACTIVE` is entered.

Only explicit user authorization may unlock `ACTIVE`.

## Checkpoint history

The runtime keeps a compact checkpoint trail:

- `progress.latest_checkpoint` is the current headline state
- `progress.checkpoint_history` is the short timeline of prior checkpoints

Use `checkpoint()` for frequent progress updates.
