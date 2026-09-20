---
name: pocket-diff
description: "Publishes the current git diff as a self-contained Artifact page that reads like an IDE diff on a phone — file tabs, Source/Tests groups, whole-file view, change-to-change navigation. Built for Remote Control sessions, where terminal output is unreadable on a phone: use it whenever the user wants to see or review changes, especially away from their desk — 'show me the diff', 'send me the diff', 'I want to read this on my phone', 'let me review the changes on mobile' — or when /pocket-diff is invoked. Prefer this over printing a diff into the conversation: a script builds the page, so the diff never passes through the model's context."
---

# Pocket diff

Turns `git diff` into a standalone HTML page and publishes it as an Artifact — the way to show
code to someone reading from a phone, which is what a Remote Control session usually is.

**Publish it without reading the diff.** The script reads git, fills the template and writes the
page. That is the point: measured on a 7-file change, one run costs about **2.1k tokens** (this
file, one summary line per file, and the tool calls) where pasting the same diff into the
conversation costs ~10k and writing the page inline costs ~65k. Cost scales with the number of
files, not the size of the diff, so a 50-file review still lands near 4k.

## Usage

1. Build the page into the scratchpad directory. The script sits next to this SKILL.md under
   `scripts/build_diff_page.py` — derive the path from there rather than assuming a home directory:

```bash
# installed as a plugin
python3 "${CLAUDE_PLUGIN_ROOT}/skills/pocket-diff/scripts/build_diff_page.py" --out <scratchpad>/diff-page.html
# installed as a personal skill
python3 ~/.claude/skills/pocket-diff/scripts/build_diff_page.py --out <scratchpad>/diff-page.html
```

2. Read the script's stdout summary (file list, +/−, title). Do **not** open, read or edit the page.
3. Publish it:

```
Artifact(file_path="<scratchpad>/diff-page.html", icon="diff",
         description="<title> — file-by-file diff")
```

4. Give the user the link plus a two-line summary (how many files, source vs test, +/−).

Called again in the same session: write to the **same path** and publish again — the URL stays and
an open page updates itself. To update a page from an earlier session, pass its `url` (find it with
`Artifact(action="list")` or ask the user).

## Options

| Flag | What it does |
|---|---|
| `--repo PATH` | Repository path, repeatable. Default: the working directory. Pass several when one change spans a service and a library. |
| `--range REV` | `main...HEAD`, `HEAD~3`, `abc..def`. Default: working tree + staged against `HEAD`. |
| `--staged` | Staged changes only. |
| `--paths ...` | Pathspec filter, e.g. `--paths src/main`. |
| `--context N` | Context lines, default 12. |
| `--title`, `--eyebrow` | Page title and the small line above it. Default title: the ticket key found in the branch name (`ABC-1234`), else the repo name. |
| `--no-tests` | Leave test files out entirely. |
| `--max-lines N` | Line budget for the page (default 120000). Over budget, the whole-file view is dropped first. |

Tests are **included by default** in their own tab group; only pass `--no-tests` when the user asks
for it.

## What the page gives the reader

- **Source / Tests** group buttons (shown only when both groups have files)
- File tabs, each with its own `+n −m`
- **Changes / Context / Whole file** — the third opens the complete file with the change markers
- Line numbers pinned left, the code block scrolls horizontally as one; "Wrap lines" turns that off
- `‹ ›` to jump change to change, plus `n`/`p` and arrow-key shortcuts
- Light syntax highlighting (Java, JS/TS, Python and friends), light + dark themes, phone widths

## Rules

- Never dump the diff into the conversation; the page is where it gets read. Answer with the link
  and a short summary.
- Never hand-edit the generated page. To change how it looks, edit this skill's
  `assets/template.html` and re-run the script.
- If the script exits with "no textual changes found", the selection is empty — say so instead of
  publishing an empty page.
- Untracked files never appear in `git diff`; the script counts them and notes it in the page
  footer. To include one, it has to be `git add -N`'d first.
