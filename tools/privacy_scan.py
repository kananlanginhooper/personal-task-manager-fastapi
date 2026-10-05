"""Block pushes that would publish personal content.

Reads a private denylist (one term per line) from $PRIVACY_DENYLIST or
~/.config/personal-task-manager/denylist.txt, then searches every tracked or staged file.
Short single words match as whole words; longer phrases match anywhere. Case-insensitive.
Fails closed: no denylist means no push.

    python tools/privacy_scan.py          # scan, exit 1 on any hit
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

DEFAULT = Path.home() / ".config" / "personal-task-manager" / "denylist.txt"


def load_terms() -> list[str]:
    path = Path(os.environ.get("PRIVACY_DENYLIST", DEFAULT))
    if not path.is_file():
        sys.exit(f"privacy scan: denylist not found at {path}. Refusing to continue.")
    return [t.strip() for t in path.read_text(encoding="utf-8").splitlines() if t.strip() and not t.startswith("#")]


def pattern(term: str) -> re.Pattern[str]:
    escaped = re.escape(term)
    if re.fullmatch(r"[\w'.-]{1,12}", term):
        return re.compile(rf"(?<![\w]){escaped}(?![\w])", re.IGNORECASE)
    return re.compile(escaped, re.IGNORECASE)


def files() -> list[str]:
    out = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"], capture_output=True, text=True, check=True).stdout
    return [f for f in out.splitlines() if f]


def main() -> int:
    pats = [(t, pattern(t)) for t in load_terms()]
    hits = 0
    for name in files():
        p = Path(name)
        if not p.is_file() or p.stat().st_size > 5_000_000:
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            for term, pat in pats:
                if pat.search(line):
                    hits += 1
                    print(f"  {name}:{lineno}: matches a private term ({term[:3]}..., {len(term)} chars)")
    if hits:
        print(f"privacy scan: {hits} hit(s). Nothing was pushed. Move that content to the database or the private seed.")
        return 1
    print(f"privacy scan: clean ({len(pats)} terms, {len(files())} files).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
