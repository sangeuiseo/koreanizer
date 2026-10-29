# Guide for agents

This file explains how to change Koreanizer without breaking its package or prompt.

## What this repo contains

Koreanizer is an agent skill written in Markdown. `SKILL.md` is the prompt that agents read. The repo has no build step.

Keep the skill portable. Do not write instructions that limit it to one or two agent tools.

## Key files

- `SKILL.md` is the source of truth and the repo's only skill file. It contains portable YAML metadata, the routing table, 35 numbered patterns, their examples, and the rewrite process. Agents load it whole on every run.
- `references/technical.md`, `references/translation.md`, and `references/fiction.md` hold the rules for one situation each. Agents read one only when the routing table in `SKILL.md` sends them there.
- `README.md` explains installation, use, patterns, and version history.
- `.claude-plugin/plugin.json` describes the Claude plugin and points its skill loader at the root `SKILL.md`.
- `.claude-plugin/marketplace.json` lets users add this repo as a Claude marketplace.
- `scripts/validate-package.py` checks package files and shared values.
- `scripts/pattern-snapshot.json` records each pattern's title and the groups
  that hold it in `SKILL.md` and `README.md`.
- `scripts/release-notes.py` prints the release notes for one version from its README entry.
- `.github/workflows/validate.yml` runs the checks on pull requests and on `main`.
- `.github/workflows/release.yml` creates the `vX.Y.Z` tag and GitHub release when `main` has a version without a release.
- `agents/openai.yaml` sets how Codex shows and invokes the skill.

## Rules for changes

Keep `SKILL.md` and `README.md` in sync.

- **Patterns:** The skill has 35 numbered patterns. If you add, remove, or renumber a pattern, update the README table, heading, validator, and every pattern reference.
- **Size:** Keep `SKILL.md` at 500 lines or fewer. Put a rule that applies to one kind of input in its `references/` file, not in `SKILL.md`. If you add a file there, add it to the routing table and to `REFERENCE_NAMES` in the validator. Keep a rule that general prose needs in `SKILL.md`, even if a reference file repeats it.
- **Evidence:** Change a pattern only on evidence that AI writes the form more often than people. If people use a form as often or more, move it to the false-positive list. Name the source in README.
- **Snapshot:** Run `python3 scripts/validate-package.py --update-snapshot` after you change a pattern title or move a pattern between groups. Review the resulting diff; the validator does not update it for you.
- **Version:** Keep the same version in `SKILL.md` under `metadata.version`, the first README version entry, and `.claude-plugin/plugin.json`. Do not add a top-level `version` field to the skill.
- **Compatibility:** Keep install and use instructions neutral across agents. Names such as Claude Code, OpenCode, and Codex are examples, not limits.
- **History:** Add a short README version note for any behavior change or non-obvious fix.
- **Release:** Bump the version whenever `SKILL.md`, a `references/` file, or the plugin metadata in `.claude-plugin/` changes. Plugin users receive new content only when the version changes. Changes only to `README.md`, `AGENTS.md`, `scripts/`, or `.github/` need no bump.
- **Bump size:** Pick the part to raise by what users notice. Raise one part per release and reset the parts after it to 0.

  | Raise | When the change | Examples |
  |---|---|---|
  | Major (`2.0.0`) | makes users act or breaks how they use the skill | rename the skill or its command, change the install layout, remove a mode, change the output format that other tools read |
  | Minor (`1.6.0`) | changes what the skill rewrites or keeps | add, replace, or remove a pattern, add a `references/` file, change a rule, a false-positive item, or the rewrite process |
  | Patch (`1.5.1`) | keeps the behavior the same | fix wording, a typo, an example that breaks its own rule, a link, or plugin metadata |

  If you cannot tell minor from patch, pick minor. State the chosen part and the reason in the pull request description. After the bump reaches `main`, the release workflow creates the tag and the GitHub release from the README note. Do not create release tags by hand.
- **After examples:** Agents copy the `**후**` examples in `SKILL.md` and `references/`. Do not put a comma after a connective ending in them; pattern 14 removes those commas. The validator fails on such a comma unless you add the line to `ALLOWED_AFTER_EXAMPLE_COMMAS`.
- **Checks:** Before publishing, run `python3 scripts/validate-package.py`, `npx skills add . --list`, and `claude plugin validate .`.

## Writing style

Use Plain Language in code comments, prompts, documentation, descriptions, validation messages, and progress reports.

- Lead with the main point.
- Use common words and active voice.
- Keep sentences and paragraphs short.
- Use one term for the same item.
- Use `must` for requirements.
- Use headings, lists, and tables when they help the reader.
- Remove repeated or unnecessary words.
- Limit acronyms and explain technical terms.
- Avoid double negatives.
- Keep exact identifiers, commands, paths, schema fields, quotations, watched phrases, and behavior-bearing examples.
- Keep the full technical meaning.

Koreanizer's prompt is in Korean. When you edit `SKILL.md`, write the prompt in Korean. Keep identifiers, commands, paths, and pattern numbers exact. Do not translate watched phrases into English.

## Korean text

All Korean prose you write or change in this repo must go through Koreanizer before you commit it. This covers `README.md`, the release notes in its version list, files under `references/`, Korean sentences you add to `SKILL.md`, commit messages, and pull request descriptions.

- Use this repo's own `SKILL.md` and `references/`, not an installed copy. An installed copy may be an older version.
- Use file mode for files and embedded mode for commit messages and pull request descriptions.
- Have a separate agent or a fresh session apply it, so the writer does not review their own text. Review its diff before you commit.
- Keep code, identifiers, quoted examples, and the `**전**` examples as they are.
- `README.md`, its release notes, and pull request descriptions use 합니다체. `SKILL.md`, `references/`, and commit messages use 한다체.
- The validator checks only mechanical tells in README prose: dashes and commas after connective endings. Passing it does not show that the text went through Koreanizer.

## Editing the skill

- Keep the YAML metadata valid.
- Treat the prompt below the metadata as the product.
- Prefer a short, clear instruction over another exception or repeated explanation.
- Keep the product contract: do not invent facts, match the writer's sample, and apply fiction craft only in fiction mode.
