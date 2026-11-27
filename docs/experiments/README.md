# Experiment reports

Phase 1+ experiments that produce **measured** evidence. Research dossiers ([`../research/`](../research/)) summarize and interpret. Experiment reports record what was actually run.

## Evidence labels

Every claim carries one label:

| Label | Meaning | Required citation |
|---|---|---|
| **[DOC]** | Capability documented by an upstream project or vendor | URL or file path, with version |
| **[SRC]** | Finding from reading source code | repository, commit, `path:line` |
| **[EXP]** | Result of an experiment we ran | exact command, environment, date, output excerpt |
| **[ASM]** | Assumption or hypothesis, not yet verified | what would verify it |

A failed experiment is still a result, and it is recorded as such.

## Restrictions

- No game assets, extracted images, screenshots of restricted content or full proprietary file listings. Keep those in the local workspace.
- Game asset identifiers, paths and hashes may appear only in local copies until backlog GATE-05 is cleared.
- No engine binaries are published.

## Template

```markdown
# EXP-NNN: <title>

| Field | Value |
|---|---|
| Date | YYYY-MM-DD |
| Backlog items | POC-xx |
| Status | complete / partial / failed / blocked |
| Environment | OS, CPU, GPU + driver, toolchain versions, container digest |
| Inputs | upstream repo + commit, game edition (no hashes until GATE-05) |

## Goal and success criteria
## Procedure (exact, reproducible)
## Results ([EXP] unless labelled otherwise)
## Deviations, modifications and failures
## Interpretation ([SRC]/[DOC]/[ASM] clearly labelled)
## Impact on ADRs, dossiers and backlog
## Open questions
```
