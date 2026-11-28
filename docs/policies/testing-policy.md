# Staged testing and test-resource policy

| Field | Value |
|---|---|
| Status | **Accepted** (owner directive, issue #26, 2026-11-28) |
| Applies to | all SSTRE tracks and repositories, M0.1 onwards |
| Related | [RD-008 testing and release](../research/RD-008-testing-release.md), [roadmap](../roadmap.md) exit criteria, [GitHub protocol](github-communication.md) |

This policy changes **testing cadence and duplication, not the quality bar.** Preview3, M1 and later exit criteria and the RD-008 gates stay exactly as they are. Exploratory evidence is kept apart from integration and release validation.

## 1. Four test stages

| Stage | Purpose | Default evidence | GPU/runtime use |
|---|---|---|---|
| **research** (feasibility) | answer a concrete open question | source inspection, earlier experiment results, logs, static analysis, synthetic CPU tests, small isolated proofs of concept | only when a concrete question cannot be answered otherwise; never a full matrix just to compare implementation options |
| **dev** (incremental) | show that a change does what it should | affected unit tests, compile checks, the smallest representative reproduction or smoke test | one renderer, one campaign, one asset configuration unless the impact analysis or an observed failure points further |
| **integration** | show that merged changes work together | targeted regression suites for the affected subsystems and their dependencies | compatible changes are batched into shared runtime sessions; agents coordinate instead of repeating identical runs |
| **release** (milestone / preview / release candidate) | gate acceptance | the complete applicable acceptance matrix on the integrated candidate: active gameplay, validation layers, both campaigns, all supported backends as the gates require | affected parts are rerun after changes; the complete matrix is repeated when broad or uncertain impact invalidates earlier evidence |

## 2. Before an expensive test

Write down, in the run's ledger entry or the track status file: the question, the affected code or asset scope, the configuration needed, the expected evidence, and why this is the cheapest test that answers it. If a broader test is requested, record why it is needed.

The lead approves unusually expensive exploratory matrices before they run. Ordinary justified targeted tests need no approval from the owner or the lead.

## 3. Evidence rules

- **Reuse** a result only if the source revision, configuration, dependencies, assets and relevant code paths still apply. Record the reused run id.
- Never present stale or unexecuted tests as current passes. Every report lists results as **executed**, **reused** (with run id), **skipped**, **deferred** or **invalidated**.
- Iterate with short, bounded smoke tests (the game watchdog stays mandatory); fail fast on clear errors; stop an exploratory run once the question is answered.
- Repeated, statistically controlled benchmark runs are reserved for real performance experiments and agreed integration or milestone baselines (quiet mode). Benchmark methodology and required regression coverage are never weakened to save resources.
- **Escalate to broader coverage** when impact cannot be bounded: shared rendering code, memory management, asset formats, platform abstractions, synchronization, and other high-risk cross-cutting code.
- GPU lock, quiet mode, CI, licensing and publication gates are unchanged. Mandatory automated CI checks are never skipped; only costly local runtime execution is optimized.

## 4. Shared test ledger

Every local runtime, GPU or benchmark run is recorded in a shared ledger on the reference machine: one JSON line per run with run id, UTC time, track, stage, question, revision, configuration, result (`pass`, `fail`, `inconclusive`, `skipped`, `deferred`, `reused`, `invalidated`), evidence location, reused run id and GPU minutes. Agents check it before reserving the GPU, to avoid duplicate reservations and redundant matrix runs. The ledger contains local paths and stays local (GATE-05). Public experiment reports summarise coverage from it in aggregate form.

## 5. Tracking coverage and savings

- Each experiment report (EXP) and each preview acceptance report has a coverage table: required item → executed / reused (run id) / skipped / deferred / invalidated, plus outstanding coverage.
- The lead reports per milestone: number of runs and GPU minutes per stage, runs avoided through reuse, and any duplicate runs found, all taken from the ledger and the GPU-lock log.
