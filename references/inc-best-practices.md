# INC Best Practices

INC is the agent's expert discovery and intent-noise-cancellation mode.

It is not passive analysis.
It is not a questionnaire.
It is not weaker than ACTIVE in tool use.
The difference is commitment: INC may explore, test, and clarify, but it must not treat the work as the authorized mainline.

INC should reduce ambiguity by doing expert work, not by transferring all uncertainty back to the user.

## Build Two Maps

In INC, build two maps in parallel:

- Domain map: how an expert would frame the task.
- Project map: what the current repository, files, runtime, data, and constraints actually show.

## Domain Map

Use domain expertise to identify:

- success criteria and quality bars
- common failure modes
- standard baselines or evaluation methods
- likely hidden constraints
- unacceptable tradeoffs
- what "done" should mean in this domain

When domain standards may have changed or are uncertain, search or inspect primary sources.

## Project Map

Ground the task in direct evidence:

- repository structure
- entrypoints and commands
- tests and validation paths
- configs and environment assumptions
- data inputs and generated outputs
- deployment or runtime behavior
- existing implementation boundaries
- current broken, missing, or ambiguous parts

Prefer reading files and running narrow probes over asking broad questions.

## Use Evidence Chain Thinking

INC should build a strong evidence chain from the user's request to the proposed mainline.

A useful evidence chain connects:

- user signals: what the user explicitly asked for, corrected, rejected, or emphasized
- domain inference: what an expert would infer from that request
- project evidence: what the repository, files, commands, data, and runtime behavior show
- inferred needs: likely hidden requirements, downstream uses, quality bars, or missing deliverables
- proposed contract: the objective, success criteria, guardrails, and next action that follow from the evidence
- confirmation gate: which inferred or extrapolated parts require user confirmation before becoming mainline work

INC should reduce ambiguity by strengthening this chain, not by collecting facts without deciding what they imply.

## Extrapolate, Then Confirm

In INC, the agent should use expert judgment to infer what the user may ultimately need, not only what the user literally asked for.

Reasonable extrapolation may include:

- likely final artifacts or deliverables
- missing acceptance criteria
- hidden quality requirements
- downstream workflows the output must support
- risks the user may not have named
- adjacent work that may be necessary for the stated goal to succeed

Treat extrapolated needs as hypotheses.

Surface them clearly as proposed additions, assumptions, or open decisions. Do not silently convert them into committed requirements. Extrapolated work must be confirmed by the user before it becomes part of the ACTIVE mainline.

## Label Knowledge

Record the difference between:

- expert_defaults: strong defaults inferred from professional practice
- verified_constraints: facts confirmed by files, commands, docs, or user statements
- assumptions: plausible beliefs that have not been verified
- risks: things likely to break the objective
- open_decisions: choices that need user judgment

## Surface the Synthesis

INC should make the current best understanding visible:

- objective
- why_now
- requirements
- success_criteria
- guardrails
- delivery_posture
- next_action
- remaining open decisions

The user should be able to accept, adjust, or reject the synthesis.

## Choose the Next INC Move

INC should not explore forever.

After each meaningful evidence-gathering step, decide which move is now appropriate:

- continue INC exploration because the evidence chain is still weak
- synthesize the current understanding because enough evidence has been gathered
- ask a targeted question because one user decision blocks the contract
- propose entering ACTIVE because the mainline is clear enough to authorize

Do not ask to enter ACTIVE just because some information has been gathered.

Do not keep exploring just because more information could be gathered.

The agent should explain its judgment: what is known, what remains uncertain, why the next move is exploration, synthesis, a targeted question, or an ACTIVE proposal.

When the next move is continued INC exploration, avoid saying only that more exploration is needed.

A useful continued-INC recommendation should make the next evidence-strengthening move visible. When the decision is non-obvious or the exploration could expand, include:

- evidence_gap: which part of the evidence chain is weak or missing
- next_probe: the concrete file, command, source, experiment, comparison, or user decision to inspect next
- expected_signal: what result would strengthen, weaken, or close the hypothesis
- stop_condition: when to stop this INC pass and re-evaluate whether to synthesize, ask a targeted question, or raise ACTIVE

For tiny or obvious next steps, keep this lightweight. Continued INC should be bounded by judgment, not by a rigid template. Do not continue exploration as a general posture; continue it as a specific evidence-strengthening move.

## Raise ACTIVE Only When It Means Commitment

Readiness is not authorization.

Raise ACTIVE when:

- the domain map is good enough to define quality
- the project map is good enough to choose a mainline
- defaults and constraints have been surfaced
- the next action is clear
- entering ACTIVE would represent real commitment, not just more exploration

Before raising ACTIVE, distinguish between confirmed requirements and extrapolated hypotheses. If the proposed mainline depends on extrapolated needs, ask the user to confirm or reject those needs before activation.

The user decides whether ACTIVE begins.
