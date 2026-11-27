#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Handelsonderneming S.D. Broekhoven, trading as ITEagle Europe
# SPDX-License-Identifier: GPL-3.0-only
"""Repository consistency checks for SSTRE.

Runs locally and in CI, in the umbrella and (with ``--root``) in the sibling
repositories. Requires Python 3.10+ and, for schema checks, the ``jsonschema``
package (``pip install jsonschema``). Without it the schema check is reported
as an error unless ``--skip-schemas`` is given. No other dependencies.

Checks:
  1. schemas/*.json      - valid JSON, declares JSON Schema draft 2020-12,
                           passes the 2020-12 metaschema, and every entry in
                           the schema's own ``examples`` array (synthetic data)
                           validates against it. Cross-file ``$ref`` by ``$id``
                           is resolved against the other schemas in schemas/.
                           Every schema is handled generically; new schema
                           files need no change to this script.
     schemas/tests/<name>/valid/*.json, schemas/tests/<name>/invalid/*.json
                         - test documents for ``schemas/<name>.schema.json``.
                           Every ``valid`` document must validate and every
                           ``invalid`` document must be rejected (negative
                           tests). Test data is synthetic only.
  2. **/*.md             - relative links and images resolve to files or
                           directories inside the repository; fenced code
                           blocks are balanced. Missing heading anchors are
                           warnings (errors with --strict-anchors).
  3. tracked + untracked-not-ignored files
                         - no files with extensions that indicate original game
                           data, demos/savegames, extracted assets or model
                           weights; no binary files above --max-binary-mb; a
                           warning for any file above --max-file-mb.
                           Paths matching --forbidden-allowlist are exempt
                           (for preserved upstream history, e.g. SSTRE-Engine).

Exit code 0 = no errors, 1 = errors found, 2 = usage/environment problem.
Not a substitute for legal review: it only catches obvious mistakes.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote

DRAFT_2020_12 = "https://json-schema.org/draft/2020-12/schema"
SCHEMA_SUFFIX = ".schema.json"

# Extensions that indicate Serious Sam game data, demos/savegames, game audio,
# or ML model weights. Note: ``.tex`` collides with LaTeX; SSTRE does not use
# LaTeX.
FORBIDDEN_EXTENSIONS = {
    # Serious Engine 1 archives and asset formats
    ".gro", ".tex", ".mdl", ".wld", ".ani", ".bm", ".bs", ".ba", ".smc",
    ".fnt", ".tbn",
    # recorded demos and savegames (contain level/game state)
    ".dem", ".sav",
    # audio (game sound and music)
    ".ogg", ".wav", ".mp3",
    # model weights / checkpoints
    ".safetensors", ".ckpt", ".pth", ".pt", ".onnx", ".gguf",
}
FORBIDDEN_DIR_PARTS = {"extracted", "workspace"}
BINARY_SNIFF_BYTES = 8192

MD_INLINE_LINK = re.compile(r"!?\[(?:[^\[\]]|\[[^\[\]]*\])*\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)")
MD_REF_DEF = re.compile(r"^\s{0,3}\[[^\]]+\]:\s*<?(\S+?)>?(?:\s+.*)?$")
FENCE = re.compile(r"^\s{0,3}(`{3,}|~{3,})")
INLINE_CODE = re.compile(r"`+[^`]*`+")
HEADING = re.compile(r"^\s{0,3}#{1,6}\s+(.*?)\s*#*\s*$")
HTML_ANCHOR = re.compile(r"<a\s+(?:name|id)=\"([^\"]+)\"", re.IGNORECASE)
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__"}


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)


def iter_files(root: Path, suffix: str) -> list[Path]:
    out = []
    for p in root.rglob(f"*{suffix}"):
        if any(part in SKIP_DIRS for part in p.relative_to(root).parts):
            continue
        if p.is_file():
            out.append(p)
    return sorted(out)


def load_json(path: Path, root: Path, rep: Report) -> object | None:
    rel = path.relative_to(root).as_posix()
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        rep.error(f"{rel}: invalid JSON: {exc}")
        return None


def fmt_error(e) -> str:
    loc = "/".join(str(p) for p in e.absolute_path) or "<root>"
    return f"at {loc}: {e.message}"


# --------------------------------------------------------------------------
# 1. JSON Schemas
# --------------------------------------------------------------------------
def check_schemas(root: Path, rep: Report) -> int:
    schema_dir = root / "schemas"
    if not schema_dir.is_dir():
        print("schemas: no schemas/ directory, skipped")
        return 0
    # Schemas are the top-level *.json files; schemas/tests/ holds test data.
    files = sorted(p for p in schema_dir.glob("*.json") if p.is_file())
    if not files:
        print("schemas: no *.json files, skipped")
        return 0
    try:
        from jsonschema import Draft202012Validator
        from referencing import Registry, Resource
        from referencing.jsonschema import DRAFT202012
    except ImportError:
        rep.error("schemas: the 'jsonschema' package is not installed "
                  "(pip install jsonschema) - use --skip-schemas to bypass")
        return 0

    loaded: dict[Path, dict] = {}
    for f in files:
        rel = f.relative_to(root).as_posix()
        data = load_json(f, root, rep)
        if data is None:
            continue
        if not isinstance(data, dict):
            rep.error(f"{rel}: top level must be a JSON object")
            continue
        if data.get("$schema") != DRAFT_2020_12:
            rep.error(f"{rel}: $schema must be '{DRAFT_2020_12}', got {data.get('$schema')!r}")
            continue
        loaded[f] = data

    resources = []
    for f, data in loaded.items():
        if "$id" in data:
            resources.append((data["$id"], Resource.from_contents(data, default_specification=DRAFT202012)))
        else:
            rep.warn(f"{f.relative_to(root).as_posix()}: no $id; cannot be referenced by other schemas")
    registry = Registry().with_resources(resources)

    validators: dict[str, object] = {}
    nexamples = 0
    for f, data in loaded.items():
        rel = f.relative_to(root).as_posix()
        errs = sorted(Draft202012Validator(Draft202012Validator.META_SCHEMA).iter_errors(data),
                      key=lambda e: list(e.path))
        if errs:
            for e in errs:
                rep.error(f"{rel}: metaschema violation {fmt_error(e)}")
            continue
        examples = data.get("examples", [])
        if not examples:
            rep.warn(f"{rel}: no 'examples'; add synthetic example data so the schema is exercised")
        validator = Draft202012Validator(data, registry=registry)
        if f.name.endswith(SCHEMA_SUFFIX):
            validators[f.name[: -len(SCHEMA_SUFFIX)]] = validator
        for i, ex in enumerate(examples):
            nexamples += 1
            try:
                ex_errs = list(validator.iter_errors(ex))
            except Exception as exc:  # unresolvable $ref etc.
                rep.error(f"{rel}: examples[{i}] could not be validated: {exc}")
                continue
            for e in ex_errs:
                rep.error(f"{rel}: examples[{i}] invalid {fmt_error(e)}")
    print(f"schemas: checked {len(files)} schema(s), {nexamples} inline example(s)")
    check_schema_tests(root, schema_dir, validators, rep)
    return len(files)


def check_schema_tests(root: Path, schema_dir: Path, validators: dict[str, object], rep: Report) -> None:
    """Positive/negative test documents under schemas/tests/<name>/{valid,invalid}/."""
    tests_dir = schema_dir / "tests"
    counts = {"valid": 0, "invalid": 0}
    if tests_dir.is_dir():
        for sub in sorted(p for p in tests_dir.iterdir() if p.is_dir()):
            name = sub.name
            if name not in validators:
                rep.error(f"{sub.relative_to(root).as_posix()}: no valid schema "
                          f"schemas/{name}{SCHEMA_SUFFIX} for this test directory")
                continue
            validator = validators[name]
            for extra in sorted(p for p in sub.iterdir() if p.name not in ("valid", "invalid")):
                rep.error(f"{extra.relative_to(root).as_posix()}: unexpected entry; "
                          "use valid/ or invalid/")
            for kind in ("valid", "invalid"):
                for doc_path in sorted((sub / kind).glob("*.json")) if (sub / kind).is_dir() else []:
                    rel = doc_path.relative_to(root).as_posix()
                    doc = load_json(doc_path, root, rep)
                    if doc is None:
                        continue
                    counts[kind] += 1
                    try:
                        errs = sorted(validator.iter_errors(doc), key=lambda e: list(e.absolute_path))
                    except Exception as exc:
                        rep.error(f"{rel}: could not be validated: {exc}")
                        continue
                    if kind == "valid":
                        for e in errs:
                            rep.error(f"{rel}: expected valid, but invalid {fmt_error(e)}")
                    elif not errs:
                        rep.error(f"{rel}: expected to be rejected by schemas/{name}{SCHEMA_SUFFIX}, but it validates")
                    else:
                        print(f"schema-tests: {rel}: rejected as expected ({fmt_error(errs[0])})")
    untested = sorted(n for n in validators if not (tests_dir / n / "invalid").is_dir())
    print(f"schema-tests: {counts['valid']} valid and {counts['invalid']} invalid document(s) checked"
          + (f"; no negative tests yet for: {', '.join(untested)}" if untested else ""))


# --------------------------------------------------------------------------
# 2. Markdown links
# --------------------------------------------------------------------------
def github_slug(text: str) -> str:
    """Approximation of GitHub's heading anchor algorithm."""
    text = re.sub(r"<[^>]+>", "", text)                      # inline HTML
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)      # [text](url) -> text
    text = text.strip().lower()
    text = re.sub(r"[^\w\- ]", "", text, flags=re.UNICODE)
    return text.replace(" ", "-")


def md_anchors(path: Path, cache: dict[Path, set[str]]) -> set[str]:
    if path in cache:
        return cache[path]
    anchors: set[str] = set()
    counts: dict[str, int] = {}
    in_fence = None
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = FENCE.match(line)
        if m:
            tok = m.group(1)[0]
            in_fence = None if in_fence == tok else (in_fence or tok)
            continue
        if in_fence:
            continue
        anchors.update(HTML_ANCHOR.findall(line))
        h = HEADING.match(line)
        if h:
            slug = github_slug(h.group(1))
            n = counts.get(slug, 0)
            anchors.add(slug if n == 0 else f"{slug}-{n}")
            counts[slug] = n + 1
    cache[path] = anchors
    return anchors


def check_markdown(root: Path, rep: Report, strict_anchors: bool) -> int:
    files = iter_files(root, ".md")
    cache: dict[Path, set[str]] = {}
    nlinks = 0
    for f in files:
        rel = f.relative_to(root).as_posix()
        in_fence = None
        fence_line = 0
        for lineno, line in enumerate(f.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            m = FENCE.match(line)
            if m:
                tok = m.group(1)[0]
                if in_fence is None:
                    in_fence, fence_line = tok, lineno
                elif in_fence == tok:
                    in_fence = None
                continue
            if in_fence:
                continue
            stripped = INLINE_CODE.sub("", line)
            targets = MD_INLINE_LINK.findall(stripped)
            rd = MD_REF_DEF.match(stripped)
            if rd:
                targets.append(rd.group(1))
            for target in targets:
                if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", target):
                    continue  # absolute URL, mailto:, etc. (not checked offline)
                nlinks += 1
                path_part, _, anchor = target.partition("#")
                path_part = unquote(path_part)
                if path_part.startswith("/"):
                    dest = (root / path_part.lstrip("/")).resolve()
                elif path_part:
                    dest = (f.parent / path_part).resolve()
                else:
                    dest = f.resolve()
                try:
                    dest.relative_to(root.resolve())
                except ValueError:
                    rep.error(f"{rel}:{lineno}: link escapes repository: {target}")
                    continue
                if not dest.exists():
                    rep.error(f"{rel}:{lineno}: broken relative link: {target}")
                    continue
                if anchor and dest.is_file() and dest.suffix.lower() == ".md":
                    if anchor.lower() not in md_anchors(dest, cache):
                        msg = f"{rel}:{lineno}: anchor '#{anchor}' not found in {dest.relative_to(root.resolve()).as_posix()}"
                        (rep.error if strict_anchors else rep.warn)(msg)
        if in_fence:
            rep.error(f"{rel}:{fence_line}: unclosed fenced code block")
    print(f"markdown: checked {len(files)} file(s), {nlinks} relative link(s)")
    return len(files)


# --------------------------------------------------------------------------
# 3. Forbidden content
# --------------------------------------------------------------------------
def candidate_files(root: Path) -> list[str] | None:
    try:
        tracked = subprocess.run(["git", "-C", str(root), "ls-files", "-z"],
                                 capture_output=True, check=True).stdout
        untracked = subprocess.run(["git", "-C", str(root), "ls-files", "-z", "--others", "--exclude-standard"],
                                   capture_output=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return None
    names = {n for n in (tracked + untracked).decode("utf-8", "replace").split("\0") if n}
    return sorted(names)


def load_allowlist(path: Path | None, root: Path) -> list[str]:
    """Allowlist file: one repository-relative glob per line (fnmatch syntax,
    '/' separators, case-sensitive; '*' also matches '/'). '#' starts a
    comment. Intended only for preserved upstream files whose status is
    tracked by the licensing audit, never for new content."""
    if path is None:
        return []
    full = path if path.is_absolute() else root / path
    if not full.is_file():
        raise FileNotFoundError(f"forbidden allowlist {full} does not exist")
    patterns = []
    for line in full.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            patterns.append(line)
    return patterns


def is_binary(path: Path) -> bool:
    with path.open("rb") as fh:
        return b"\0" in fh.read(BINARY_SNIFF_BYTES)


def check_forbidden(root: Path, rep: Report, max_mb: float, max_binary_mb: float,
                    allowlist: list[str]) -> int:
    names = candidate_files(root)
    if names is None:
        rep.warn("forbidden-files: not a git work tree or git unavailable; scanning filesystem instead")
        names = [p.relative_to(root).as_posix() for p in root.rglob("*")
                 if p.is_file() and not any(part in SKIP_DIRS for part in p.relative_to(root).parts)]
    allowed = 0
    for name in names:
        if any(fnmatch.fnmatchcase(name, pat) for pat in allowlist):
            allowed += 1
            continue
        p = Path(name)
        if p.suffix.lower() in FORBIDDEN_EXTENSIONS:
            rep.error(f"{name}: forbidden extension '{p.suffix}' (game data, demos/savegames, game audio "
                      "or model weights must not be committed)")
        if FORBIDDEN_DIR_PARTS.intersection(part.lower() for part in p.parts[:-1]):
            rep.error(f"{name}: lives under a local-only directory ({'/'.join(sorted(FORBIDDEN_DIR_PARTS))})")
        full = root / name
        if not full.is_file():
            continue
        size = full.stat().st_size
        if size > max_binary_mb * 1024 * 1024 and is_binary(full):
            rep.error(f"{name}: binary file larger than {max_binary_mb:g} MB "
                      "(possible asset, archive or weights; binaries are not committed)")
        elif size > max_mb * 1024 * 1024:
            rep.warn(f"{name}: larger than {max_mb:g} MB; confirm it is not an asset or binary")
    print(f"forbidden-files: checked {len(names)} file(s)"
          + (f", {allowed} exempted by allowlist ({len(allowlist)} pattern(s))" if allowlist else ""))
    return len(names)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent,
                    help="repository root (default: parent of scripts/)")
    ap.add_argument("--skip-schemas", action="store_true", help="skip JSON Schema checks")
    ap.add_argument("--skip-forbidden", action="store_true",
                    help="skip the forbidden-file check entirely (prefer --forbidden-allowlist)")
    ap.add_argument("--forbidden-allowlist", type=Path, metavar="FILE",
                    help="file of repository-relative globs exempt from the forbidden-file check "
                         "(relative to --root unless absolute); for preserved upstream files only")
    ap.add_argument("--strict-anchors", action="store_true", help="treat missing heading anchors as errors")
    ap.add_argument("--max-file-mb", type=float, default=5.0, help="warn on files above this size")
    ap.add_argument("--max-binary-mb", type=float, default=1.0,
                    help="error on binary files (NUL byte in the first 8 KiB) above this size")
    args = ap.parse_args(argv)
    root = args.root.resolve()
    if not root.is_dir():
        print(f"error: root {root} is not a directory", file=sys.stderr)
        return 2
    try:
        allowlist = load_allowlist(args.forbidden_allowlist, root)
    except (OSError, UnicodeDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    rep = Report()
    if not args.skip_schemas:
        check_schemas(root, rep)
    check_markdown(root, rep, args.strict_anchors)
    if args.skip_forbidden:
        print("forbidden-files: skipped (--skip-forbidden)")
    else:
        check_forbidden(root, rep, args.max_file_mb, args.max_binary_mb, allowlist)

    for w in rep.warnings:
        print(f"WARNING: {w}")
    for e in rep.errors:
        print(f"ERROR: {e}")
    print(f"result: {len(rep.errors)} error(s), {len(rep.warnings)} warning(s)")
    return 1 if rep.errors else 0


if __name__ == "__main__":
    sys.exit(main())
