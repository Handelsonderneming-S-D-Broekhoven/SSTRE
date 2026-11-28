# Model allocation and token-efficiency policy

| Field | Value |
|---|---|
| Status | **Accepted** (owner directive, issue #29, 2026-11-28) |
| Applies to | the lead and every development agent, all SSTRE repositories |
| Related | [testing policy](testing-policy.md) (#26), [GitHub protocol](github-communication.md) |

Goal: the lowest total cost and time to a **validated** result. This is not a blanket downgrade. Quality, review, CI, licensing, publication and GPU-scheduling rules do not change with the model used.

## 1. Runtime facts (verified 2026-11-28)

- In this Claude Code environment, agents are started through the Agent tool. Its `model` parameter accepts `haiku`, `sonnet`, `opus` and `fable`. When `model` is omitted, the agent inherits the lead's model (Opus-class).
- The lead's own model cannot be changed by the lead.
- A running agent cannot switch models. A new allocation takes effect at the next assignment or handoff.
- `fable` is accepted by the runtime, but its tier relative to the others has not been established in this project. It is not used until a scoped trial shows where it fits.
- Telemetry available per agent run: the task notification's **token count, tool-use count and duration** (measured). **Not available** to the lead: per-model cost, cache-hit rates and price. Those are reported as *unavailable*, not estimated.

## 2. Allocation guidelines

These are defaults, not rigid classes. The lead chooses per assignment and records the choice.

| Tier | Agent tool `model` | Typical SSTRE work |
|---|---|---|
| None (script) | — | GitHub polling (`gh-poll.sh`), GATE-05 pre-push check (`gate05-check.sh`), test ledger, build/assemble/smoke scripts, CI watching, hash and leak scans. No LLM where a deterministic tool suffices |
| Light | `haiku` | bounded repository navigation, inventories and classification from clear rules, log extraction and summaries, repetitive structured edits, simple doc updates (index rows, links), routine status digests |
| Mid | `sonnet` | ordinary implementation and isolated bug fixes, test development, well-scoped source analysis, refactoring, integrating an established design, harness and packaging work, roadmap/backlog edits from a precise brief, benchmark execution and reporting |
| High | `opus` | renderer and RTGL1 design, difficult cross-subsystem debugging, high-risk integration, ambiguous research, security and licensing analysis, review of consequential changes |

## 3. Escalation and review

- Escalate one tier when an agent gets stuck, produces unreliable results, fails tests repeatedly or meets complexity beyond its brief. Do not allow repeated low-quality retries that cost more than a stronger model would have.
- Review stays risk-proportionate whatever model wrote the change. A cheaper implementation model is never a reason for less review or validation.

## 4. Context efficiency

- Briefs are narrow: goal, deliverable, relevant files and sections, constraints, acceptance criteria. Point to dossiers, ADRs, EXP reports and status files instead of copying them. Shared rules live in one brief file (for example `M01_LEAD_BRIEF.md`) that agents read once.
- No redundant repository-wide scans, no repeated research, and no parallel agents solving the same problem unless the goal is an independent review.
- Handoffs and status reports are short and evidence-based, but keep decisions, reproducibility details and mandatory documentation.
- Interplay with #26: reuse earlier results and ledger entries instead of re-deriving them.

## 5. Measurement

- The lead records each agent run in a local agent ledger: track, task, model, tokens, tool uses, duration, escalations and retries, outcome (merged / rework / abandoned), and whether each figure is measured or estimated.
- Per milestone the lead reports tokens per track and tier, escalations, and rework or regressions per tier. The allocation is then adjusted on the evidence.
