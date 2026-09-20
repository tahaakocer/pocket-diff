# pocket-diff

A Claude Code skill that turns `git diff` into a self-contained page you can actually read on a
phone — file tabs, Source/Tests groups, whole-file view, and jump-to-next-change, published as a
private Artifact link.

It exists because reviewing a diff away from your desk is miserable: a terminal dump wraps into
soup, and pasting the diff into chat burns context for nothing.

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
per file. A 50-file diff costs the same context as a 1-file diff, which is the whole trick.

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
