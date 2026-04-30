# Worked Examples

For shell examples below:

```bash
export CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
export LLR_PY="$CODEX_HOME/skills/long-long-run/scripts"
export LLR_CTL="$CODEX_HOME/skills/long-long-run/scripts/controller.py"
```

## Example 1: INC exploration with Python

```bash
python3 - <<'PY'
import os
import sys

sys.path.insert(0, os.environ["LLR_PY"])
from runtime import current_runtime

rt = current_runtime()
print(rt.bind(auto_create=True, project_root="/tmp/project"))

print(
    rt.update_contract(
        {
            "objective": "Map the legacy service and define the implementation path.",
            "why_now": "The user needs a trustworthy takeover before implementation begins.",
            "requirements": ["Base conclusions on direct evidence."],
            "success_criteria": ["Produce a coherent project map and an agreed execution path."],
            "guardrails": ["Do not start implementation before authorization."],
            "confirmed": True,
        }
    )
)

print(
    rt.update_thinking(
        {
            "inferred_intent": "Stay in INC while reconstructing the project from repo artifacts and logs.",
            "expert_defaults": ["Inspect structure, docs, configs, and real run entrypoints first."],
            "verified_constraints": ["Use the deployment docs as the source of truth for environment paths."],
            "open_decisions": ["Whether to start implementation after the mapping is complete."],
        }
    )
)

print(
    rt.checkpoint(
        summary="Finished the first project scan.",
        next_action="Read the backend entrypoints and dependency manifests.",
    )
)
PY
```

## Example 2: Authorization and activation

```bash
python3 "$LLR_CTL" authorize-active \
  --evidence "The user explicitly said: start implementation now."

python3 "$LLR_CTL" activate
```

## Example 3: Return from ACTIVE to INC

```bash
python3 "$LLR_CTL" return-to-inc \
  --reason "The validation target changed, so the contract must be resynthesized." \
  --next-action "Clarify the new success criteria with the user."
```

## Example 4: Close the runtime

```bash
python3 "$LLR_CTL" close \
  --reason complete \
  --summary "Completed the authorized mainline and captured the final report."
```
