#!/usr/bin/env python3
"""Print the GitHub release notes for one version from README.md."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
README = (ROOT / "README.md").read_text(encoding="utf-8")

UPDATE_HELP = """\
설치한 방법에 따라 이렇게 업데이트합니다.

- Claude Code 플러그인: `/plugin marketplace update koreanizer`
- Skills CLI: `npx skills update koreanizer`
- Claude.ai와 Claude Desktop: 이 릴리스의 소스 ZIP을 받아 스킬로 다시 올립니다."""

if len(sys.argv) != 2:
    raise SystemExit("Usage: python3 scripts/release-notes.py <version>")

version = sys.argv[1].removeprefix("v")
note = re.search(rf"(?m)^- \*\*{re.escape(version)}\*\* - (.+)$", README)
if note is None:
    raise SystemExit(f"Add a README version entry for {version}")

print(f"{note.group(1)}\n\n{UPDATE_HELP}")
