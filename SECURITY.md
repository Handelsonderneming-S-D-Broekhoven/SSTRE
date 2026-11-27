# Security policy

## Status

SSTRE is in Phase 0 (bootstrap and research). No software has been released,
so there are no supported versions yet. This policy covers all five SSTRE
repositories:

- [SSTRE](https://github.com/Handelsonderneming-S-D-Broekhoven/SSTRE)
- [SSTRE-Engine](https://github.com/Handelsonderneming-S-D-Broekhoven/SSTRE-Engine)
- [SSTRE-AssetCompiler](https://github.com/Handelsonderneming-S-D-Broekhoven/SSTRE-AssetCompiler)
- [SSTRE-Manifests](https://github.com/Handelsonderneming-S-D-Broekhoven/SSTRE-Manifests)
- [Remaster-Toolkit](https://github.com/Handelsonderneming-S-D-Broekhoven/Remaster-Toolkit)

## Reporting a vulnerability

Report privately through GitHub Security Advisories:
open the affected repository, go to **Security → Advisories → Report a
vulnerability** (`https://github.com/Handelsonderneming-S-D-Broekhoven/<repo>/security/advisories/new`).

> Maintainer note: private vulnerability reporting must be enabled per
> repository (Settings → Code security). Until it is enabled the link above
> will not offer the form; this is tracked as an owner action.

Please do **not** open a public issue, pull request or discussion for a
suspected vulnerability, and do not include game files or extracted assets in
a report.

Include, where possible: affected repository and commit, a description of the
issue and its impact, and minimal reproduction steps using synthetic data.

## Scope

In scope, once code exists:

- Code execution or path traversal via crafted archives, manifests, recipes or
  workflow files processed by SSTRE-AssetCompiler or Remaster-Toolkit.
- Unsafe loading of model files or workflow nodes (for example pickle-based
  checkpoints, unreviewed custom nodes).
- Missing or bypassable hash verification for downloaded models and dependencies.
- Supply-chain issues in CI workflows (unpinned actions, excessive token permissions).
- Memory-safety issues in SSTRE-specific engine changes.

Issues that exist only in an upstream engine project should also be reported
to that upstream project.

## Response

This is a volunteer, pre-release project; there is no guaranteed response time.
Reports will be acknowledged through the advisory thread, fixed on a private
branch where needed, and disclosed through a published advisory once a fix or
mitigation exists.
