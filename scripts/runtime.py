#!/usr/bin/env python3
from pathlib import Path
from typing import Any, Optional

from state import (
    ACTIVATION_SCOPE_VALUES,
    CHECKPOINT_HISTORY_LIMIT,
    MODE_VALUES,
    SessionIdentity,
    clean_list,
    clean_string,
    default_project_root,
    default_state,
    load_state_with_error,
    normalize_state,
    now_iso,
    resolve_identity,
    save_state,
)


def _deep_merge(base: Any, patch: Any) -> Any:
    if isinstance(base, dict) and isinstance(patch, dict):
        merged = dict(base)
        for key, value in patch.items():
            if key in merged:
                merged[key] = _deep_merge(merged[key], value)
            else:
                merged[key] = value
        return merged
    return patch


def _sanitize_update_patch(patch: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    allowed_top_level = {"contract", "thinking", "progress"}
    sanitized: dict[str, Any] = {}
    ignored: list[str] = []
    for key, value in patch.items():
        if key in allowed_top_level and isinstance(value, dict):
            sanitized[key] = value
        else:
            ignored.append(key)
    return sanitized, ignored


def _append_list_summary(parts: list[str], label: str, values: object, max_items: int = 2) -> None:
    if not isinstance(values, list):
        return
    cleaned = [clean_string(value) for value in values if clean_string(value)]
    if not cleaned:
        return
    summary = ", ".join(cleaned[:max_items])
    if len(cleaned) > max_items:
        summary += ", ..."
    parts.append(f"{label}={summary}")


def render_brief_context(state: dict[str, Any]) -> str:
    parts: list[str] = []
    runtime = state["runtime"]
    contract = state["contract"]
    thinking = state["thinking"]
    activation = state["activation"]
    progress = state["progress"]

    objective = clean_string(contract.get("objective", ""))
    if objective:
        parts.append("objective=" + objective)
    else:
        inferred_intent = clean_string(thinking.get("inferred_intent", ""))
        if inferred_intent:
            parts.append("inferred_intent=" + inferred_intent)

    parts.append("mode=" + clean_string(runtime.get("mode", "disabled")))

    project_root = clean_string(runtime.get("project_root", ""))
    if project_root:
        parts.append("project_root=" + project_root)

    contract_confirmed = "yes" if contract.get("confirmed") else "no"
    parts.append("contract_confirmed=" + contract_confirmed)

    delivery_posture = clean_string(contract.get("delivery_posture", ""))
    if delivery_posture:
        parts.append("delivery_posture=" + delivery_posture)

    activation_status = clean_string(activation.get("status", ""))
    if activation_status:
        parts.append("activation=" + activation_status)

    _append_list_summary(parts, "requirements", contract.get("requirements"))
    _append_list_summary(parts, "success", contract.get("success_criteria"))
    _append_list_summary(parts, "guardrails", contract.get("guardrails"))
    _append_list_summary(parts, "expert_defaults", thinking.get("expert_defaults"))
    _append_list_summary(parts, "verified_constraints", thinking.get("verified_constraints"))
    _append_list_summary(parts, "open_decisions", thinking.get("open_decisions"))

    latest_checkpoint = clean_string(progress.get("latest_checkpoint", ""))
    if latest_checkpoint:
        parts.append("latest_checkpoint=" + latest_checkpoint)

    next_action = clean_string(progress.get("next_action", ""))
    if next_action:
        parts.append("next_action=" + next_action)

    checkpoint_history = progress.get("checkpoint_history")
    if isinstance(checkpoint_history, list) and checkpoint_history:
        parts.append("checkpoint_count=" + str(len(checkpoint_history)))

    blocker = progress.get("blocker", {})
    if isinstance(blocker, dict):
        kind = clean_string(blocker.get("kind", ""))
        summary = clean_string(blocker.get("summary", ""))
        if kind and kind != "none":
            text = "blocker=" + kind
            if summary:
                text += f" ({summary})"
            parts.append(text)

    return " | ".join(parts)


def _append_sentence(prefix: str, sentence: str) -> str:
    prefix = clean_string(prefix)
    sentence = clean_string(sentence)
    if not prefix:
        return sentence
    if not sentence:
        return prefix
    if prefix.endswith((".", "!", "?")):
        return prefix + " " + sentence
    return prefix + ". " + sentence


def build_readiness(state: dict[str, Any]) -> dict[str, Any]:
    missing: list[str] = []
    warnings: list[str] = []

    runtime = state["runtime"]
    contract = state["contract"]
    thinking = state["thinking"]
    progress = state["progress"]

    project_root = clean_string(runtime.get("project_root", ""))
    objective = clean_string(contract.get("objective", ""))
    why_now = clean_string(contract.get("why_now", ""))
    next_action = clean_string(progress.get("next_action", ""))
    confirmed = bool(contract.get("confirmed"))

    has_success_basis = bool(
        clean_list(contract.get("success_criteria"))
        or clean_list(thinking.get("expert_defaults"))
        or clean_list(thinking.get("verified_constraints"))
    )
    has_guardrails = bool(clean_list(contract.get("guardrails")))

    score = 0
    if project_root:
        score += 20
    else:
        missing.append("runtime.project_root")

    if objective:
        score += 20
    else:
        missing.append("contract.objective")

    if confirmed:
        score += 20
    else:
        missing.append("contract.confirmed")

    if has_success_basis:
        score += 20
    else:
        warnings.append(
            "No success criteria, expert defaults, or verified constraints are captured yet."
        )

    if next_action:
        score += 20
    else:
        missing.append("progress.next_action")

    if not has_guardrails:
        warnings.append("No guardrails are captured yet.")

    if clean_string(runtime.get("mode", "")) == "inc":
        if not clean_string(thinking.get("inferred_intent", "")):
            warnings.append("thinking.inferred_intent is still empty.")
        if not why_now:
            warnings.append("contract.why_now is still empty.")

    open_decisions = clean_list(thinking.get("open_decisions"))
    if open_decisions:
        warnings.append(f"{len(open_decisions)} open decision(s) remain in the current contract.")

    blocker = progress.get("blocker", {})
    blocker_active = False
    if isinstance(blocker, dict):
        kind = clean_string(blocker.get("kind", "")).lower()
        summary = clean_string(blocker.get("summary", ""))
        if kind and kind != "none":
            blocker_active = True
            message = f"blocker active: {kind}"
            if summary:
                message += f" ({summary})"
            warnings.append(message)

    if clean_string(runtime.get("mode", "")) == "active" and (missing or blocker_active):
        warnings.append("The session is active but missing normal activation prerequisites.")

    return {
        "ok": not missing and not blocker_active,
        "missing": missing,
        "warnings": warnings,
        "score": score,
        "needs_authorization": clean_string(state["activation"].get("status", "")) != "authorized",
    }


def broken_state_message(path: Path, error: str) -> str:
    return (
        "This session has a long-long-run state file at "
        + str(path)
        + ", but it could not be loaded ("
        + error
        + "). Do not treat this as disabled. Repair or recreate a valid state before continuing. "
        + "If the long-running objective is already finished or intentionally stopped, close it explicitly instead of ignoring the broken file."
    )


def stop_repair_message(path: Path, error: str) -> str:
    return (
        "Stop checkpoint. This session has a long-long-run state file at "
        + str(path)
        + ", but it could not be loaded ("
        + error
        + "). Do not stop or assume the runtime is disabled. Repair or recreate a valid state now. "
        + "If the objective is truly complete, the user explicitly asked to stop, or the session should be abandoned, close it explicitly before ending the turn. "
        + "Do not mention this checkpoint or the gate file to the user."
    )


def build_stop_prompt(path: Path, state: dict[str, Any], had_assistant_text: bool) -> str:
    context = render_brief_context(state)
    if had_assistant_text:
        prompt = _append_sentence(
            "Stop checkpoint. This session is in long-long-run ACTIVE mode. " + context,
            "Do not stop because of the checkpoint. Continue with the next action now unless blocked by user input, permissions, or unavailable external resources.",
        )
    else:
        prompt = _append_sentence(
            "Stop checkpoint. This session is in long-long-run ACTIVE mode, and your latest completion attempt produced no user-visible assistant text. "
            + context,
            "Continue with the next action now unless the objective is truly complete or genuinely blocked.",
        )
    prompt += (
        " If the objective is truly complete, the user explicitly asked to stop, or the work is genuinely blocked, "
        + "close the runtime state at "
        + str(path)
        + " before ending the turn. Do not mention this checkpoint or the gate file to the user."
    )
    return prompt


def _append_checkpoint_history(
    state: dict[str, Any],
    *,
    summary: str,
    next_action: str = "",
    mode: str = "",
) -> bool:
    summary = clean_string(summary)
    if not summary:
        return False

    progress = state["progress"]
    history = progress.get("checkpoint_history")
    if not isinstance(history, list):
        history = []

    entry = {
        "timestamp": now_iso(),
        "mode": mode or clean_string(state["runtime"].get("mode", "")),
        "summary": summary,
        "next_action": clean_string(next_action),
    }

    if history:
        last = history[-1]
        if (
            isinstance(last, dict)
            and clean_string(last.get("summary", "")) == entry["summary"]
            and clean_string(last.get("next_action", "")) == entry["next_action"]
            and clean_string(last.get("mode", "")) == entry["mode"]
        ):
            return False

    history.append(entry)
    progress["checkpoint_history"] = history[-CHECKPOINT_HISTORY_LIMIT:]
    return True


def _maybe_rebind_project_root(state: dict[str, Any], project_root: Optional[str]) -> bool:
    if project_root is None:
        return False
    resolved = default_project_root(project_root)
    if clean_string(state["runtime"].get("project_root", "")) == resolved:
        return False
    state["runtime"]["project_root"] = resolved
    return True


class LongLongRunRuntime:
    def __init__(self, identity: SessionIdentity):
        self.identity = identity

    def _state_exists(self) -> bool:
        return self.identity.path.is_file()

    def _load(self, project_root_hint: str = "") -> tuple[dict[str, Any], Optional[str]]:
        return load_state_with_error(
            self.identity.path,
            session_id_hint=self.identity.session_id,
            project_root_hint=project_root_hint,
        )

    def _bootstrap_state(self, project_root: Optional[str] = None) -> dict[str, Any]:
        state = default_state(
            session_id=self.identity.session_id,
            project_root=default_project_root(project_root),
        )
        state["runtime"]["mode"] = "inc"
        return save_state(self.identity.path, state, transition="bootstrap")

    def _status_payload(
        self,
        *,
        exists: bool,
        state: Optional[dict[str, Any]] = None,
        error: Optional[str] = None,
        warnings: Optional[list[str]] = None,
        created: bool = False,
        action: str = "",
        include_state: bool = False,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "ok": error is None,
            "skill": "long-long-run",
            "session_id": self.identity.session_id,
            "path": str(self.identity.path),
            "exists": exists,
            "created": created,
            "identity_source": self.identity.source,
            "warnings": list(self.identity.warnings),
            "action": action,
        }
        if warnings:
            payload["warnings"].extend(warnings)
        if error:
            payload["health"] = "broken"
            payload["error"] = error
            return payload
        if not state:
            payload["health"] = "missing"
            payload["mode"] = "disabled"
            return payload

        readiness = build_readiness(state)
        runtime = state["runtime"]
        payload.update(
            {
                "health": "ok",
                "mode": clean_string(runtime.get("mode", "disabled")),
                "project_root": clean_string(runtime.get("project_root", "")),
                "brief_context": render_brief_context(state),
                "readiness": readiness,
                "objective": clean_string(state["contract"].get("objective", "")),
                "close_reason": clean_string(runtime.get("close_reason", "")),
                "authorized": clean_string(state["activation"].get("status", "")) == "authorized",
            }
        )
        if include_state:
            payload["state"] = state
        payload["warnings"].extend(readiness["warnings"])
        return payload

    def bind(self, *, auto_create: bool = False, project_root: Optional[str] = None) -> dict[str, Any]:
        if not self._state_exists():
            if not auto_create:
                return self._status_payload(exists=False, action="noop")
            state = self._bootstrap_state(project_root=project_root)
            return self._status_payload(
                exists=True,
                state=state,
                created=True,
                action="bootstrap",
            )

        state, error = self._load()
        if error:
            return self._status_payload(exists=True, error=error, action="repair_required")
        rebound = _maybe_rebind_project_root(state, project_root)
        if rebound:
            state = save_state(self.identity.path, state, transition="rebind")
        return self._status_payload(
            exists=True,
            state=state,
            warnings=["Rebound project_root to the explicit path."] if rebound else None,
            action="rebind" if rebound else "ready",
        )

    def show(self) -> dict[str, Any]:
        if not self._state_exists():
            return self._status_payload(exists=False, action="noop")
        state, error = self._load()
        if error:
            return self._status_payload(exists=True, error=error, action="repair_required")
        return self._status_payload(exists=True, state=state, action="show", include_state=True)

    def update(
        self,
        patch: dict[str, Any],
        *,
        auto_create: bool = True,
        project_root: Optional[str] = None,
    ) -> dict[str, Any]:
        exists = self._state_exists()
        if not exists:
            if not auto_create:
                return self._status_payload(
                    exists=False,
                    warnings=["No session state exists yet; use current --auto-create first."],
                    action="noop",
                )
            state = self._bootstrap_state(project_root=project_root)
        else:
            state, error = self._load()
            if error:
                return self._status_payload(exists=True, error=error, action="repair_required")

        patch, ignored_keys = _sanitize_update_patch(patch)
        if not patch:
            warnings = ["update only accepts contract, thinking, and progress patches."]
            if ignored_keys:
                warnings.append("Ignored keys: " + ", ".join(sorted(ignored_keys)))
            return self._status_payload(
                exists=True,
                state=state,
                warnings=warnings,
                action="noop",
            )

        merged = normalize_state(
            _deep_merge(state, patch),
            session_id_hint=self.identity.session_id,
        )
        rebound = _maybe_rebind_project_root(merged, project_root)
        previous_checkpoint = clean_string(state["progress"].get("latest_checkpoint", ""))
        current_checkpoint = clean_string(merged["progress"].get("latest_checkpoint", ""))
        if current_checkpoint and current_checkpoint != previous_checkpoint:
            _append_checkpoint_history(
                merged,
                summary=current_checkpoint,
                next_action=clean_string(merged["progress"].get("next_action", "")),
            )
        saved = save_state(self.identity.path, merged, transition="update")
        warnings: list[str] = []
        if rebound:
            warnings.append("Rebound project_root to the explicit path.")
        if ignored_keys:
            warnings.append("Ignored keys: " + ", ".join(sorted(ignored_keys)))
        return self._status_payload(
            exists=True,
            state=saved,
            warnings=warnings or None,
            action="update",
        )

    def update_contract(
        self,
        patch: dict[str, Any],
        *,
        auto_create: bool = True,
        project_root: Optional[str] = None,
    ) -> dict[str, Any]:
        return self.update(
            {"contract": patch},
            auto_create=auto_create,
            project_root=project_root,
        )

    def update_thinking(
        self,
        patch: dict[str, Any],
        *,
        auto_create: bool = True,
        project_root: Optional[str] = None,
    ) -> dict[str, Any]:
        return self.update(
            {"thinking": patch},
            auto_create=auto_create,
            project_root=project_root,
        )

    def checkpoint(
        self,
        *,
        summary: str,
        next_action: str = "",
        auto_create: bool = True,
        project_root: Optional[str] = None,
    ) -> dict[str, Any]:
        exists = self._state_exists()
        if not exists:
            if not auto_create:
                return self._status_payload(
                    exists=False,
                    warnings=["No session state exists yet; use current --auto-create first."],
                    action="noop",
                )
            state = self._bootstrap_state(project_root=project_root)
        else:
            state, error = self._load()
            if error:
                return self._status_payload(exists=True, error=error, action="repair_required")

        summary = clean_string(summary)
        if not summary:
            return self._status_payload(
                exists=exists,
                state=state,
                warnings=["checkpoint requires a non-empty summary."],
                action="noop",
            )

        rebound = _maybe_rebind_project_root(state, project_root)
        state["progress"]["latest_checkpoint"] = summary
        if next_action:
            state["progress"]["next_action"] = clean_string(next_action)
        _append_checkpoint_history(
            state,
            summary=summary,
            next_action=clean_string(state["progress"].get("next_action", "")),
        )
        saved = save_state(self.identity.path, state, transition="checkpoint")
        return self._status_payload(
            exists=True,
            state=saved,
            warnings=["Rebound project_root to the explicit path."] if rebound else None,
            action="checkpoint",
        )

    def authorize_active(
        self,
        *,
        evidence: str,
        scope: str = "single",
    ) -> dict[str, Any]:
        if not self._state_exists():
            return self._status_payload(
                exists=False,
                warnings=["No session state exists yet; bootstrap the runtime first."],
                action="noop",
            )

        state, error = self._load()
        if error:
            return self._status_payload(exists=True, error=error, action="repair_required")

        evidence = clean_string(evidence)
        if not evidence:
            return self._status_payload(
                exists=True,
                state=state,
                warnings=["authorize-active requires non-empty user authorization evidence."],
                action="noop",
            )

        scope = clean_string(scope).lower()
        if scope not in ACTIVATION_SCOPE_VALUES:
            scope = "single"

        state["activation"] = {
            "status": "authorized",
            "scope": scope,
            "evidence": evidence,
            "updated_at": now_iso(),
        }
        saved = save_state(self.identity.path, state, transition="authorize_active")
        return self._status_payload(exists=True, state=saved, action="authorize_active")

    def activate(self) -> dict[str, Any]:
        if not self._state_exists():
            return self._status_payload(
                exists=False,
                warnings=["No session state exists yet; bootstrap the runtime first."],
                action="noop",
            )

        state, error = self._load()
        if error:
            return self._status_payload(exists=True, error=error, action="repair_required")

        readiness = build_readiness(state)
        authorized = clean_string(state["activation"].get("status", "")) == "authorized"
        if not readiness["ok"] or not authorized:
            payload = self._status_payload(exists=True, state=state, action="activate_blocked")
            payload["ok"] = False
            payload["needs_authorization"] = not authorized
            return payload

        state["runtime"]["mode"] = "active"
        saved = save_state(self.identity.path, state, transition="activate")
        payload = self._status_payload(exists=True, state=saved, action="activate")
        payload["activated"] = True
        return payload

    def return_to_inc(self, *, reason: str, next_action: str = "") -> dict[str, Any]:
        if not self._state_exists():
            return self._status_payload(
                exists=False,
                warnings=["No session state exists yet; nothing to return."],
                action="noop",
            )

        state, error = self._load()
        if error:
            return self._status_payload(exists=True, error=error, action="repair_required")

        reason = clean_string(reason)
        if reason:
            state["progress"]["latest_checkpoint"] = reason
            _append_checkpoint_history(
                state,
                summary=reason,
                next_action=clean_string(next_action) or clean_string(state["progress"].get("next_action", "")),
                mode="inc",
            )
        if next_action:
            state["progress"]["next_action"] = clean_string(next_action)
        state["runtime"]["mode"] = "inc"
        state["activation"] = {
            "status": "idle",
            "scope": "single",
            "evidence": "",
            "updated_at": now_iso(),
        }
        saved = save_state(self.identity.path, state, transition="return_to_inc")
        return self._status_payload(exists=True, state=saved, action="return_to_inc")

    def close(self, *, reason: str, summary: str = "") -> dict[str, Any]:
        if not self._state_exists():
            return self._status_payload(
                exists=False,
                warnings=["No session state exists yet; nothing to close."],
                action="noop",
            )

        state, error = self._load()
        if error:
            return self._status_payload(exists=True, error=error, action="repair_required")

        summary = clean_string(summary)
        if summary:
            state["progress"]["latest_checkpoint"] = summary
            _append_checkpoint_history(
                state,
                summary=summary,
                next_action=clean_string(state["progress"].get("next_action", "")),
                mode=clean_string(state["runtime"].get("mode", "")),
            )
        state["runtime"]["mode"] = "disabled"
        state["runtime"]["close_reason"] = clean_string(reason)
        state["activation"] = {
            "status": "idle",
            "scope": "single",
            "evidence": "",
            "updated_at": now_iso(),
        }
        saved = save_state(self.identity.path, state, transition="close")
        return self._status_payload(exists=True, state=saved, action="close")

    def context_for_user_prompt(self) -> dict[str, Any]:
        if not self._state_exists():
            return {
                "ok": True,
                "action": "noop",
                "session_id": self.identity.session_id,
                "path": str(self.identity.path),
                "identity_source": self.identity.source,
                "warnings": list(self.identity.warnings),
                "message": "",
            }

        state, error = self._load()
        if error:
            return {
                "ok": False,
                "action": "repair_required",
                "session_id": self.identity.session_id,
                "path": str(self.identity.path),
                "identity_source": self.identity.source,
                "warnings": list(self.identity.warnings),
                "message": broken_state_message(self.identity.path, error),
            }

        mode = clean_string(state["runtime"].get("mode", "disabled"))
        context = render_brief_context(state)
        readiness = build_readiness(state)
        authorized = clean_string(state["activation"].get("status", "")) == "authorized"

        message = ""
        action = "noop"
        if mode == "active":
            action = "inject_context"
            message = _append_sentence(
                "This session has an active long-long-run objective. " + context,
                "First address the user's latest message. Then resume the active mainline automatically.",
            )
        elif mode == "inc":
            action = "inject_context"
            if authorized:
                message = _append_sentence(
                    "This session is in long-long-run INC mode, and the user has already authorized ACTIVE. "
                    + context,
                    "First address the user's latest message. Then activate when you judge that the work should now be carried as the authorized mainline.",
                )
            else:
                message = _append_sentence(
                    "This session is in long-long-run INC mode (Intent Noise Cancellation). "
                    + context,
                    "First address the user's latest message. Then continue using judgment to reduce uncertainty, clarify the contract, and make the work more legible. "
                    + "INC is not limited to passive analysis, but it does not grant implicit authorization to treat the work as the committed mainline. "
                    + "Surface expert defaults and verified constraints clearly so the user can adjust them. "
                    + "Whether and when to raise a transition to ACTIVE is a matter of agent judgment; entering ACTIVE still requires explicit user authorization.",
                )

        return {
            "ok": True,
            "action": action,
            "session_id": self.identity.session_id,
            "path": str(self.identity.path),
            "identity_source": self.identity.source,
            "warnings": list(self.identity.warnings),
            "mode": mode,
            "brief_context": context,
            "message": message,
            "readiness": readiness,
        }

    def stop_decision(self, *, last_assistant_message: str = "") -> dict[str, Any]:
        if not self._state_exists():
            return {
                "ok": True,
                "decision": "allow",
                "session_id": self.identity.session_id,
                "path": str(self.identity.path),
                "identity_source": self.identity.source,
                "warnings": list(self.identity.warnings),
            }

        state, error = self._load()
        if error:
            return {
                "ok": False,
                "decision": "block",
                "session_id": self.identity.session_id,
                "path": str(self.identity.path),
                "identity_source": self.identity.source,
                "warnings": list(self.identity.warnings),
                "reason": stop_repair_message(self.identity.path, error),
            }

        if clean_string(state["runtime"].get("mode", "disabled")) != "active":
            return {
                "ok": True,
                "decision": "allow",
                "session_id": self.identity.session_id,
                "path": str(self.identity.path),
                "identity_source": self.identity.source,
                "warnings": list(self.identity.warnings),
            }

        reason = build_stop_prompt(
            self.identity.path,
            state,
            bool(clean_string(last_assistant_message)),
        )
        return {
            "ok": False,
            "decision": "block",
            "session_id": self.identity.session_id,
            "path": str(self.identity.path),
            "identity_source": self.identity.source,
            "warnings": list(self.identity.warnings),
            "reason": reason,
        }


def current_runtime(
    *,
    session_id: Optional[str] = None,
    path: Optional[str] = None,
) -> LongLongRunRuntime:
    return LongLongRunRuntime(resolve_identity(session_id=session_id, path=path))
