#!/usr/bin/env python3
"""Run every lint/style check for the site in one go.

    uv run tools/check.py               run all checks (uv supplies the pinned ruff)
    python3 tools/check.py              the same, if ruff is already on your PATH
    python3 tools/check.py ruff nojs    run only the named checks
    python3 tools/check.py --list       show the check names

Checks:
  ruff        ruff check + ruff format --check on the Python files (uses .ruff.toml)
  nojs        tools/build_nojs.py --check (is the generated nojs/ folder up to date?)
  eslint      ESLint on js/ and data/
  html        html-validate on the pages and the generated nojs/ pages

The two JavaScript-based checks need Node.  Their tools are installed once into
.cache/lint/ (git-ignored) and their settings live in this file, so nothing
extra is added to the repo.  Every selected check runs even if an earlier one
fails; the exit status is 1 if any of them failed.
"""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = ROOT / ".cache" / "lint"

# Pinned so a new release can't suddenly break the check.
NPM_PACKAGES = ["eslint@9", "@eslint/js@9", "globals@15", "html-validate@9"]

# The scripts are classic (ES5-style) browser scripts.  Empty catch blocks and
# unused `e` in catch are deliberate: localStorage can be blocked.
ESLINT_CONFIG = """\
import js from "@eslint/js";
import globals from "globals";
export default [
  js.configs.recommended,
  {
    files: ["**/*.js"],
    languageOptions: { sourceType: "script", ecmaVersion: 2022, globals: { ...globals.browser, ...globals.node } },
    rules: {
      "no-empty": ["error", { allowEmptyCatch: true }],
      "no-unused-vars": ["error", { caughtErrors: "none" }],
    },
  },
];
"""

# Lowercase <!doctype html> is valid HTML5, and a long <title> is only a style note.
HTML_VALIDATE_CONFIG = {
    "extends": ["html-validate:recommended"],
    "rules": {"doctype-style": "off", "long-title": "off"},
}


def say(text=""):
    print(text, flush=True)


def run(cmd, cwd=ROOT):
    """Run a command, streaming its output. True if it exited 0."""
    say("$ " + " ".join(str(c) for c in cmd))
    try:
        return subprocess.run(cmd, cwd=cwd, check=False).returncode == 0
    except FileNotFoundError as e:
        say(f"  could not run it: {e}")
        return False


def check_ruff():
    ruff = shutil.which("ruff")
    if not ruff:
        say("  ruff is not on PATH (activate the venv that has it).")
        return False
    lint = run([ruff, "check", "."])
    fmt = run([ruff, "format", "--check", "."])
    return lint and fmt


def check_nojs():
    return run([sys.executable, str(ROOT / "tools" / "build_nojs.py"), "--check"])


def js_tool(name):
    """Path to an installed npm tool, installing the pinned set on first use."""
    exe = TOOLS_DIR / "node_modules" / ".bin" / name
    npm = shutil.which("npm")
    if not exe.exists():
        if not npm:
            say("  Node/npm not found; install Node to run this check.")
            return None
        say("First run: installing the lint tools into .cache/lint/ ...")
        TOOLS_DIR.mkdir(parents=True, exist_ok=True)
        (TOOLS_DIR / "package.json").write_text('{"name": "lint-tools", "private": true}\n')
        if not run([npm, "install", "--no-audit", "--no-fund", "--silent", *NPM_PACKAGES], cwd=TOOLS_DIR):
            return None
    (TOOLS_DIR / "eslint.config.mjs").write_text(ESLINT_CONFIG)
    (TOOLS_DIR / "html-validate.json").write_text(json.dumps(HTML_VALIDATE_CONFIG, indent=2) + "\n")
    return exe


def check_eslint():
    exe = js_tool("eslint")
    return bool(exe) and run([exe, "-c", TOOLS_DIR / "eslint.config.mjs", "js", "data"])


def check_html():
    exe = js_tool("html-validate")
    if not exe:
        return False
    pages = sorted(p.name for p in ROOT.glob("*.html"))
    pages += sorted(f"nojs/{p.name}" for p in (ROOT / "nojs").glob("*.html"))
    return run([exe, "-c", TOOLS_DIR / "html-validate.json", *pages])


CHECKS = {"ruff": check_ruff, "nojs": check_nojs, "eslint": check_eslint, "html": check_html}


def main():
    ap = argparse.ArgumentParser(description="Run the site's lint and style checks.")
    ap.add_argument(
        "checks",
        nargs="*",
        choices=list(CHECKS),
        metavar="CHECK",
        help=f"which checks to run (default: all of {', '.join(CHECKS)})",
    )
    ap.add_argument("--list", action="store_true", help="list the available checks and exit")
    args = ap.parse_args()

    if args.list:
        say("\n".join(CHECKS))
        return 0

    selected = args.checks or list(CHECKS)
    results = {}
    for name in selected:
        say(f"\n=== {name} ===")
        results[name] = CHECKS[name]()

    say("\n=== summary ===")
    for name, ok in results.items():
        say(f"{'ok  ' if ok else 'FAIL'}  {name}")
    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
