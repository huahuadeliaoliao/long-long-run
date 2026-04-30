# Hooks

Hooks are thin adapters over the runtime harness.

They should not invent extra business logic.

## `UserPromptSubmit`

Calls `context_for_user_prompt()`.

Behavior:

- no runtime state -> no-op
- broken state -> inject repair-required warning
- `inc` and not authorized -> remind the agent to keep working in `INC` using judgment, without treating the work as the committed mainline
- `inc` and authorized -> remind the agent it may activate
- `active` -> remind the agent to answer the user and then resume the mainline

## `Stop`

Calls `stop_decision(...)`.

Behavior:

- no runtime state -> allow
- broken state -> block with repair-required prompt
- `inc` -> allow
- `disabled` -> allow
- `active` -> block

`INC` intentionally has no stop wall.

That is by design:

- `INC` is a free dialogue mode
- it may stay live across long discovery, recovery, or project-forensics sessions
- implementation stop resistance belongs to `ACTIVE`, not to `INC`
