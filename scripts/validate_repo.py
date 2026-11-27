#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Handelsonderneming S.D. Broekhoven, trading as ITEagle Europe
# SPDX-License-Identifier: GPL-3.0-only
"""Repository consistency checks for SSTRE Phase 0.

Runs locally and in CI. Requires Python 3.10+ and, for schema checks,
the ``jsonschema`` package (``pip install jsonschema``). Without it the
schema check is reported as an error unless ``--skip-schemas`` is given.

Checks:
  1. schemas/**/*.json   - valid JSON, declares JSON Schema draft 2020-12,
                           passes the 2020-12 metaschema, and every entry in
                           the schema's own ``examples`` array (synthetic data)
                           validates against it. Cross-file ``$ref`` by ``$id``
                           is resolved against the other schemas in schemas/.
  2. **/*.md             - relative links and images resolve to files or
                           directories inside the repository; fenced code
                           blocks are balanced. Missing heading anchors are
                           warnings (errors with --strict-anchors).
  3. tracked + untracked-not-ignored files
                         - no files with extensions that indicate original game
                           data, extracted assets or model weights, and a
                           warning for files larger than --max-file-mb.

Exit code 0 = no errors, 1 = errors found, 2 = usage/environment problem.
Not a substitute for legal review: it only catches obvious mistakes.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote

DRAFT_2020_12 = "https://json-schema.org/draft/2020-12/schema"

# Extensions that indicate Serious Sam game data, game audio, or ML model
# weights. Note: ``.tex`` collides with LaTeX; SSTRE does not use LaTeX.
FORBIDDEN_EXTENSIONS = {
    # Serious Engine 1 archives and asset formats
    ".gro", ".tex", ".mdl", ".wld", ".ani", ".bm", ".bs", ".ba", ".smc",
    ".fnt", ".tbn",
    # audio (game sound and music)
    ".ogg", ".wav", ".mp3",
    # model weights / checkpoints
    ".safetensors", ".ckpt", ".pth", ".pt", ".onnx", ".gguf",
}
FORBIDDEN_DIR_PARTS = {"extracted", "workspace"}

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


# --------------------------------------------------------------------------
# 1. JSON Schemas
# --------------------------------------------------------------------------
def check_schemas(root: Path, rep: Report) -> int:
    schema_dir = root / "schemas"
    if not schema_dir.is_dir():
        print("schemas: no schemas/ directory, skipped")
        return 0
    files = iter_files(schema_dir, ".json")
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
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            rep.error(f"{rel}: invalid JSON: {exc}")
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

    for f, data in loaded.items():
        rel = f.relative_to(root).as_posix()
        errs = sorted(Draft202012Validator(Draft202012Validator.META_SCHEMA).iter_errors(data),
                      key=lambda e: list(e.path))
        if errs:
            for e in errs:
                loc = "/".join(str(p) for p in e.path) or "<root>"
                rep.error(f"{rel}: metaschema violation at {loc}: {e.message}")
            continue
        examples = data.get("examples", [])
        if not examples:
            rep.warn(f"{rel}: no 'examples'; add synthetic example data so the schema is exercised")
        validator = Draft202012Validator(data, registry=registry)
        for i, ex in enumerate(examples):
            try:
                ex_errs = list(validator.iter_errors(ex))
            except Exception as exc:  # unresolvable $ref etc.
                rep.error(f"{rel}: examples[{i}] could not be validated: {exc}")
                continue
            for e in ex_errs:
                loc = "/".join(str(p) for p in e.path) or "<root>"
                rep.error(f"{rel}: examples[{i}] invalid at {loc}: {e.message}")
    print(f"schemas: checked {len(files)} file(s)")
    return len(files)


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


def check_forbidden(root: Path, rep: Report, max_mb: float) -> int:
    names = candidate_files(root)
    if names is None:
        rep.warn("forbidden-files: not a git work tree or git unavailable; scanning filesystem instead")
        names = [p.relative_to(root).as_posix() for p in root.rglob("*")
                 if p.is_file() and not any(part in SKIP_DIRS for part in p.relative_to(root).parts)]
    for name in names:
        p = Path(name)
        if p.suffix.lower() in FORBIDDEN_EXTENSIONS:
            rep.error(f"{name}: forbidden extension '{p.suffix}' (game data, game audio or model weights must not be committed)")
        if FORBIDDEN_DIR_PARTS.intersection(part.lower() for part in p.parts[:-1]):
            rep.error(f"{name}: lives under a local-only directory ({'/'.join(sorted(FORBIDDEN_DIR_PARTS))})")
        full = root / name
        if full.is_file() and full.stat().st_size > max_mb * 1024 * 1024:
            rep.warn(f"{name}: larger than {max_mb:g} MB; confirm it is not an asset or binary")
    print(f"forbidden-files: checked {len(names)} file(s)")
    return len(names)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent,
                    help="repository root (default: parent of scripts/)")
    ap.add_argument("--skip-schemas", action="store_true", help="skip JSON Schema checks")
    ap.add_argument("--strict-anchors", action="store_true", help="treat missing heading anchors as errors")
    ap.add_argument("--max-file-mb", type=float, default=5.0, help="warn on files above this size")
    args = ap.parse_args(argv)
    root = args.root.resolve()
    if not root.is_dir():
        print(f"error: root {root} is not a directory", file=sys.stderr)
        return 2

    rep = Report()
    if not args.skip_schemas:
        check_schemas(root, rep)
    check_markdown(root, rep, args.strict_anchors)
    check_forbidden(root, rep, args.max_file_mb)

    for w in rep.warnings:
        print(f"WARNING: {w}")
    for e in rep.errors:
        print(f"ERROR: {e}")
    print(f"result: {len(rep.errors)} error(s), {len(rep.warnings)} warning(s)")
    return 1 if rep.errors else 0


if __name__ == "__main__":
    sys.exit(main())
