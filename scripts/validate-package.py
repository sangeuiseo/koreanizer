#!/usr/bin/env python3
"""Check Koreanizer's package files without external dependencies."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SKILL_PATH = ROOT / "SKILL.md"
SKILL = SKILL_PATH.read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")
AGENTS = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
PLUGIN = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))


def require_match(match: re.Match[str] | None, message: str) -> re.Match[str]:
    if match is None:
        raise SystemExit(message)
    return match


yaml_metadata = require_match(
    re.match(r"\A---\n(.*?)\n---\n", SKILL, re.DOTALL),
    "SKILL.md must begin with YAML metadata",
).group(1)

for unsupported_field in ("compatibility:", "allowed-tools:"):
    if re.search(rf"(?m)^{re.escape(unsupported_field)}", yaml_metadata):
        raise SystemExit(f"Remove unsupported YAML field: {unsupported_field[:-1]}")

skill_name = require_match(
    re.search(r"(?m)^name:\s*([a-z0-9-]+)\s*$", yaml_metadata),
    "Add a lowercase name to SKILL.md",
).group(1)
if skill_name != "koreanizer":
    raise SystemExit("Set SKILL.md name to koreanizer")
if PLUGIN.get("name") != "koreanizer":
    raise SystemExit("Set plugin.json name to koreanizer")

skill_version = require_match(
    re.search(r'(?m)^\s+version:\s*["\']([^"\']+)["\']\s*$', yaml_metadata),
    "Add metadata.version to SKILL.md",
).group(1)
readme_version = require_match(
    re.search(r"(?m)^- \*\*([0-9]+\.[0-9]+\.[0-9]+)\*\*", README),
    "Add a version entry to README.md",
).group(1)

package_versions = {skill_version, readme_version, str(PLUGIN.get("version", ""))}
if len(package_versions) != 1:
    raise SystemExit(
        f"Use one package version in all files: {sorted(package_versions)}"
    )

skill_files = {path.relative_to(ROOT) for path in ROOT.rglob("SKILL.md")}
if SKILL_PATH.is_symlink() or skill_files != {Path("SKILL.md")}:
    raise SystemExit("Keep one regular SKILL.md at the repo root")
if PLUGIN.get("skills") != ["./"]:
    raise SystemExit("Point the Claude plugin skill loader at the repo root")

plain_language_rules = (
    "## Writing style",
    "Lead with the main point.",
    "Use common words and active voice.",
    "Keep sentences and paragraphs short.",
    "Use `must` for requirements.",
    "Keep the full technical meaning.",
)
missing_plain_language_rules = [
    rule for rule in plain_language_rules if rule not in AGENTS
]
if missing_plain_language_rules:
    raise SystemExit(
        "Add the missing Plain Language rules to AGENTS.md: "
        + ", ".join(missing_plain_language_rules)
    )

if "fiction mode" not in SKILL.lower() and "소설 모드" not in SKILL:
    raise SystemExit("Keep a fiction mode section in SKILL.md")

pattern_numbers = [
    int(number)
    for number in re.findall(r"(?m)^### ([0-9]+)\. ", SKILL)
]
if pattern_numbers != list(range(1, 36)):
    raise SystemExit(f"Number SKILL.md patterns from 1 through 35: {pattern_numbers}")

readme_numbers = {
    int(number) for number in re.findall(r"(?m)^\| ([0-9]+) \|", README)
}
if readme_numbers != set(range(1, 36)):
    raise SystemExit("List patterns 1 through 35 in the README table")

snapshot_path = ROOT / "scripts" / "pattern-snapshot.json"


def skill_groups(text: str) -> dict[str, list[int]]:
    groups: dict[str, list[int]] = {}
    section = None
    for line in text.splitlines():
        if line.startswith("## "):
            section = line[3:].strip()
        heading = re.match(r"^### ([0-9]+)\. ", line)
        if heading and section:
            groups.setdefault(section, []).append(int(heading.group(1)))
    return groups


def readme_groups(text: str) -> dict[str, list[int]]:
    groups: dict[str, list[int]] = {}
    section = None
    for line in text.splitlines():
        heading = re.match(r"^### (.+)$", line)
        if heading:
            section = heading.group(1).strip()
            continue
        row = re.match(r"^\| ([0-9]+) \|", line)
        if row and section:
            groups.setdefault(section, []).append(int(row.group(1)))
    return groups


skill_sections = skill_groups(SKILL)
readme_sections = readme_groups(README)

if "--update-snapshot" in sys.argv:
    rebuilt = []
    for name, numbers in skill_sections.items():
        matches = [
            group for group, rows in readme_sections.items() if rows == numbers
        ]
        if len(matches) != 1:
            raise SystemExit(
                f"Match one README group to SKILL.md section {name} first"
            )
        rebuilt.append({"skill": name, "readme": matches[0], "numbers": numbers})
    snapshot_path.write_text(
        json.dumps(
            {
                "groups": rebuilt,
                "titles": {
                    number: title
                    for number, title in re.findall(
                        r"(?m)^### ([0-9]+)\. (.+)$", SKILL
                    )
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print("Updated scripts/pattern-snapshot.json")
    raise SystemExit(0)

snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
declared: list[int] = []
for group in snapshot["groups"]:
    numbers = group["numbers"]
    declared.extend(numbers)
    if skill_sections.get(group["skill"]) != numbers:
        raise SystemExit(
            f"SKILL.md section {group['skill']} must hold patterns {numbers}"
        )
    if readme_sections.get(group["readme"]) != numbers:
        raise SystemExit(
            f"README.md group {group['readme']} must hold patterns {numbers}"
        )
if sorted(declared) != list(range(1, 36)):
    raise SystemExit("Cover patterns 1 through 35 in scripts/pattern-snapshot.json")

for number, title in snapshot["titles"].items():
    if not re.search(rf"(?m)^### {re.escape(number)}\. {re.escape(title)}$", SKILL):
        raise SystemExit(f"Pattern {number} must keep the title: {title}")

out_of_range = sorted(
    {int(number) for number in re.findall(r"([0-9]+)절", SKILL)} - set(range(1, 36))
)
if out_of_range:
    raise SystemExit(f"SKILL.md refers to patterns that do not exist: {out_of_range}")

if len(SKILL.splitlines()) > 600:
    raise SystemExit("Keep SKILL.md at 600 lines or fewer")

print(f"Koreanizer package v{skill_version} is valid")
