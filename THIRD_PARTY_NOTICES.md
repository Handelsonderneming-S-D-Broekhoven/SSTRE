# Third-party notices

**Status (2026-11-27):** this repository contains no vendored or redistributed third-party code, data, fonts, images or model weights.

Third-party software is *used* but not distributed:

| Component | Used by | How | License (per upstream) |
|---|---|---|---|
| [jsonschema](https://pypi.org/project/jsonschema/) 4.26.0 | `scripts/validate_repo.py` | installed by the developer or CI from PyPI; not vendored | MIT |
| [actions/checkout](https://github.com/actions/checkout), [actions/setup-python](https://github.com/actions/setup-python) | `.github/workflows/` | referenced by pinned commit SHA; executed by GitHub; not vendored | MIT |

The GNU GPL v3 text in [`LICENSE`](LICENSE) is the unmodified text published by the Free Software Foundation. The SPDX identifier for this repository awaits owner confirmation ([ADR-0006](docs/adr/0006-licensing-boundaries.md)).

Serious Sam, Croteam and Devolver Digital names and marks belong to their respective owners. This project is unofficial and is not affiliated with or endorsed by them.

Maintenance follows the draft [notices policy](docs/policies/notices-policy.md): any change that vendors, bundles or redistributes third-party material must update this file in the same pull request.
