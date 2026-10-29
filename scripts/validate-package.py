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
MARKETPLACE = json.loads(
    (ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8")
)

# Each check adds its message here, so one run reports every problem.
errors: list[str] = []


def check(ok: bool, message: str) -> None:
    if not ok:
        errors.append(message)


def first_group(pattern: str, text: str, message: str, flags: int = 0) -> str | None:
    match = re.search(pattern, text, flags)
    check(match is not None, message)
    return match.group(1) if match else None


def exit_on_errors() -> None:
    if errors:
        print(f"Fix {len(errors)} problem(s) in the package files:", file=sys.stderr)
        for message in errors:
            print(f"- {message}", file=sys.stderr)
        raise SystemExit(1)


yaml_metadata = (
    first_group(
        r"\A---\n(.*?)\n---\n",
        SKILL,
        "SKILL.md must begin with YAML metadata",
        re.DOTALL,
    )
    or ""
)

for unsupported_field in ("compatibility:", "allowed-tools:"):
    check(
        not re.search(rf"(?m)^{re.escape(unsupported_field)}", yaml_metadata),
        f"Remove unsupported YAML field: {unsupported_field[:-1]}",
    )

skill_name = first_group(
    r"(?m)^name:\s*([a-z0-9-]+)\s*$", yaml_metadata, "Add a lowercase name to SKILL.md"
)
if skill_name is not None:
    check(skill_name == "koreanizer", "Set SKILL.md name to koreanizer")
check(PLUGIN.get("name") == "koreanizer", "Set plugin.json name to koreanizer")
marketplace_entries = [
    entry for entry in MARKETPLACE.get("plugins", []) if entry.get("name") == "koreanizer"
]
check(
    len(marketplace_entries) == 1
    and marketplace_entries[0].get("description") == PLUGIN.get("description"),
    "Use the plugin.json description for the koreanizer entry in marketplace.json",
)

skill_version = first_group(
    r'(?m)^\s+version:\s*["\']([^"\']+)["\']\s*$',
    yaml_metadata,
    "Add metadata.version to SKILL.md",
)
readme_version = first_group(
    r"(?m)^- \*\*([0-9]+\.[0-9]+\.[0-9]+)\*\*",
    README,
    "Add a version entry to README.md",
)

package_versions = {
    version
    for version in (skill_version, readme_version, str(PLUGIN.get("version", "")))
    if version is not None
}
check(
    len(package_versions) == 1,
    f"Use one package version in all files: {sorted(package_versions)}",
)

skill_files = {path.relative_to(ROOT) for path in ROOT.rglob("SKILL.md")}
check(
    not SKILL_PATH.is_symlink() and skill_files == {Path("SKILL.md")},
    "Keep one regular SKILL.md at the repo root",
)
check(
    PLUGIN.get("skills") == ["./"],
    "Point the Claude plugin skill loader at the repo root",
)

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
check(
    not missing_plain_language_rules,
    "Add the missing Plain Language rules to AGENTS.md: "
    + ", ".join(missing_plain_language_rules),
)

# SKILL.md routes each situation to one of these files. An agent reads a file
# only when SKILL.md links it, so every file must exist and be linked.
REFERENCE_NAMES = ("technical", "translation", "fiction")
REFERENCES: dict[str, str] = {}
for name in REFERENCE_NAMES:
    path = ROOT / "references" / f"{name}.md"
    check(path.is_file(), f"Add references/{name}.md")
    check(
        f"](references/{name}.md)" in SKILL,
        f"Link references/{name}.md from SKILL.md",
    )
    if path.is_file():
        REFERENCES[name] = path.read_text(encoding="utf-8")
PROMPT_TEXTS = [SKILL, *REFERENCES.values()]

check(
    "소설 모드" in SKILL and "소설 모드" in REFERENCES.get("fiction", ""),
    "Keep fiction mode in references/fiction.md and name it in SKILL.md",
)

pattern_numbers = [
    int(number)
    for number in re.findall(r"(?m)^### ([0-9]+)\. ", SKILL)
]
check(
    pattern_numbers == list(range(1, 36)),
    f"Number SKILL.md patterns from 1 through 35: {pattern_numbers}",
)

readme_numbers = {
    int(number) for number in re.findall(r"(?m)^\| ([0-9]+) \|", README)
}
check(
    readme_numbers == set(range(1, 36)),
    "List patterns 1 through 35 in the README table",
)

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
    exit_on_errors()
    rebuilt = []
    for name, numbers in skill_sections.items():
        matches = [
            group for group, rows in readme_sections.items() if rows == numbers
        ]
        check(
            len(matches) == 1,
            f"Match one README group to SKILL.md section {name} first",
        )
        if len(matches) == 1:
            rebuilt.append({"skill": name, "readme": matches[0], "numbers": numbers})
    exit_on_errors()
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
    check(
        skill_sections.get(group["skill"]) == numbers,
        f"SKILL.md section {group['skill']} must hold patterns {numbers}",
    )
    check(
        readme_sections.get(group["readme"]) == numbers,
        f"README.md group {group['readme']} must hold patterns {numbers}",
    )
check(
    sorted(declared) == list(range(1, 36)),
    "Cover patterns 1 through 35 in scripts/pattern-snapshot.json",
)

for number, title in snapshot["titles"].items():
    check(
        bool(re.search(rf"(?m)^### {re.escape(number)}\. {re.escape(title)}$", SKILL)),
        f"Pattern {number} must keep the title: {title}",
    )

out_of_range = sorted(
    {
        int(number)
        for text in PROMPT_TEXTS
        for number in re.findall(r"([0-9]+)절", text)
    }
    - set(range(1, 36))
)
check(
    not out_of_range,
    f"The prompt refers to patterns that do not exist: {out_of_range}",
)

# Pattern 14 removes commas after connective endings and sentence-initial
# conjunctions. Agents copy the after examples, so those examples must not carry
# such a comma. The ending list also catches 그리고, 그런데, and 그러므로; 그러나
# needs its own entry. Add a line here only when the comma prevents a misreading
# or the regex catches a noun.
ALLOWED_AFTER_EXAMPLE_COMMAS: set[str] = set()
after_example_commas = []
in_after_example = False
for line in "\n".join(PROMPT_TEXTS).splitlines():
    if line.startswith("**후"):
        in_after_example = True
        continue
    if not line.startswith(">"):
        in_after_example = False
        continue
    prose = re.sub(r"`[^`]*`", "", line)
    if (
        in_after_example
        and re.search(r"(?:고|며|데|지만|거나|므로|서|면|그러나),", prose)
        and line not in ALLOWED_AFTER_EXAMPLE_COMMAS
    ):
        after_example_commas.append(line)
check(
    not after_example_commas,
    "Remove the comma after the connective ending or conjunction in these after "
    "examples: " + " | ".join(after_example_commas),
)

# Agents load SKILL.md whole on every run. Put situational rules in references/.
check(len(SKILL.splitlines()) <= 500, "Keep SKILL.md at 500 lines or fewer")

exit_on_errors()
print(f"Koreanizer package v{skill_version} is valid")
