---
name: pocket-diff
description: "Publishes the current git diff as a self-contained Artifact page that reads like an IDE diff on a phone. Built for Remote Control sessions, where the phone shows only the chat: use it whenever the user wants to see or review changes away from their desk — 'show me the diff', 'send me the diff', 'let me read this on my phone', 'review the changes on mobile' — or when /pocket-diff is invoked. Prefer it over printing a diff into the conversation: a script builds the page, so the diff never reaches the model's context."
---

# Pocket diff

**Build and publish without reading the diff.** The script runs git and fills the template; you read
only its summary. That is the point — a 50-file diff costs barely more than a 1-file diff.

## Usage

The script sits next to this file. Derive its path from here rather than assuming a home directory:
`${CLAUDE_PLUGIN_ROOT}/skills/pocket-diff/scripts/build_diff_page.py` as a plugin,
`~/.claude/skills/pocket-diff/scripts/build_diff_page.py` as a personal skill.

1. `python3 <path>/build_diff_page.py --out <scratchpad>/diff-page.html`
2. Read the stdout summary. Do **not** open, read or edit the page.
3. `Artifact(file_path="<scratchpad>/diff-page.html", icon="diff", description="<title> — file-by-file diff")`
4. Reply with the link and one line: how many files, source vs tests, +/−.

Called again in the same session, write to the same path and publish again — the URL stays and open
pages update themselves. To update a page from an earlier session, pass its `url`.

## Options

| Flag | What it does |
|---|---|
| `--repo PATH` | Repository, repeatable. Default: working directory. Pass several when one change spans a service and a library. |
| `--range REV` | `main...HEAD`, `HEAD~3`, `abc..def`. Default: working tree + staged against `HEAD`. |
| `--staged` | Staged changes only. |
| `--paths ...` | Pathspec filter, e.g. `--paths src/main`. |
| `--context N` | Context lines, default 12. |
| `--title`, `--eyebrow` | Page heading. Default title: the ticket key in the branch name, else the repo name. |
| `--no-tests` | Drop test files. They are included by default, in their own tab group. |
| `--max-lines N` | Page line budget (default 120000); over it the whole-file view is dropped. |

## Rules

- Never dump the diff into the conversation; answer with the link and a short summary.
- Never hand-edit the generated page — change this skill's `assets/template.html` and re-run.
- "no textual changes found" means the selection is empty; say so instead of publishing.
- Untracked files never appear in `git diff`; the script counts them in the page footer.
