# pocket-diff

A Claude Code skill that turns `git diff` into a self-contained page you can actually read on a
phone — file tabs, Source/Tests groups, whole-file view, and jump-to-next-change, published as a
private Artifact link.

It was built for **Remote Control sessions**: you are following a Claude Code run from your phone,
the change is ready, and there is no good way to read it. Terminal output wraps into soup, a
downloaded file arrives without line numbers or colour, and pasting the diff into the conversation
burns context for nothing.

The same link works from a desk — hand it to a reviewer who would rather not check out your branch,
or read a change without opening an IDE.

## Install

```
/plugin marketplace add tahaakocer/pocket-diff
/plugin install pocket-diff@tahaakocer-plugins
```

Then, in any repository:

```
/pocket-diff
```

Claude runs the build script, publishes the page and hands you the link. Asking for it in plain
words works too — "show me the diff", "send me the changes so I can read them on my phone".

## What the page gives you

| | |
|---|---|
| **Source / Tests** | Test files land in their own tab group instead of burying the real change |
| **Changes / Context / Whole file** | Just the changed lines, 12 lines of context, or the complete file with change markers |
| **Pinned gutters** | Line numbers stay put while the code scrolls horizontally as one block — or turn on "Wrap lines" |
| **`‹ ›` navigation** | Jump change to change; `n` / `p` and arrow keys on a keyboard |
| **Themes** | Light and dark, following the viewer's setting |

Syntax highlighting covers Java, JavaScript/TypeScript, Python and anything close enough to their
token shapes; everything else still renders, just unhighlighted.

## Why a script instead of the model

The model never reads the diff. `scripts/build_diff_page.py` runs `git diff`, parses it, embeds the
result into `assets/template.html` and writes the finished page; all Claude sees is a summary line
per file.

Measured on a real change — 7 files (4 source, 3 tests), +262 −4:

| | characters | ~tokens | reaches the model |
|---|---|---|---|
| Script summary on stdout | 1,174 | ~330 | **yes** — the only part that does |
| `SKILL.md`, loaded per call | 4,049 | ~1,125 | **yes** |
| Raw diff, 12 lines of context | 35,441 | ~9,845 | no |
| Raw diff of the whole files | 84,036 | ~23,343 | no |
| The generated page | 235,399 | ~65,389 | no |

One run costs roughly **1,600 tokens** — against ~9,800 for pasting the diff into the conversation,
or ~65,000 for having the model write the page itself.

What scales is the file count, not the diff size: stdout is one line per file, so a 50-file review
still lands near 1,800 tokens while its raw diff would clear 100,000. Token figures are estimates
(characters ÷ 3.6); the gap is the point, not the third digit.

## Options

The skill passes these through when you ask for something specific:

| Flag | Meaning |
|---|---|
| `--repo PATH` | Repository to read, repeatable — useful when one change spans a service and a library |
| `--range REV` | `main...HEAD`, `HEAD~3`, `abc..def`; default is working tree + staged against `HEAD` |
| `--staged` | Staged changes only |
| `--paths ...` | Pathspec filter |
| `--context N` | Context lines, default 12 |
| `--title`, `--eyebrow` | Page heading; the default title is the ticket key in your branch name, else the repo name |
| `--no-tests` | Leave test files out |
| `--max-lines N` | Page line budget (default 120000); over it, the whole-file view is dropped first |

You can also run it directly, without Claude:

```bash
python3 skills/pocket-diff/scripts/build_diff_page.py --out /tmp/diff.html --repo .
```

It needs nothing but Python 3 and git — no third-party packages.

## Customising the look

Everything visual lives in `skills/pocket-diff/assets/template.html`: a single file with the CSS
tokens (light and dark), the highlighter and the page logic, plus a `__DATA_JSON__` placeholder the
script fills. Edit it and re-run the script; every future diff picks up the change.

## Notes

- Untracked files never show up in `git diff`. The script counts them and says so in the page
  footer; `git add -N <file>` makes them visible.
- Binary files are skipped and counted.
- Published Artifacts are private to your account until you share them from the page's Share menu.

## Licence

MIT — see [LICENSE](LICENSE). Built by [@tahaakocer](https://github.com/tahaakocer).
