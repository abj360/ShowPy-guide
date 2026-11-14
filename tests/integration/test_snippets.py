#!/usr/bin/env python3

"""
test_snippets.py --- runs every chapter's >>> snippets and checks them against the stored text

Contains:
    test_chapter_snippets_match(): runs one chapter's snippets through the guide build
"""

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CHAPTERS = sorted((ROOT / "chapters").glob("*.md"))
SNIPPETS_ONLY = ("--skip-examples", "--skip-figures", "--skip-exercises", "--no-pdf")
TIMEOUT_S = 300


@pytest.mark.parametrize("chapter", CHAPTERS, ids=lambda path: path.stem)
def test_chapter_snippets_match(chapter: Path) -> None:
    """Runs one chapter's snippets and checks every output equals the stored one."""
    done = subprocess.run(
        [sys.executable, str(ROOT / "build_guide.py"), *SNIPPETS_ONLY, "--only", chapter.name],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=TIMEOUT_S,
        check=False,
    )
    assert done.returncode == 0, done.stdout + done.stderr
    assert f"Ran {chapter.name}" in done.stdout
