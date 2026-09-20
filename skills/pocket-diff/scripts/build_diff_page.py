#!/usr/bin/env python3
"""Build a self-contained diff review page (HTML) from one or more git repositories.

The page is the deliverable: file tabs, source/test groups, three context modes
(changes / context / whole class), pinned line gutters and change-to-change navigation.
Nothing about the diff passes through the model — this script reads git and writes the
finished page, so a 20-file diff costs the same context as a 1-file diff.

Examples
--------
  build_diff_page.py --out page.html
  build_diff_page.py --out page.html --repo . --repo ../application-model
  build_diff_page.py --out page.html --range develop...HEAD --title "DDYS-6890"
  build_diff_page.py --out page.html --staged --paths src/main
"""

import argparse
import html
import json
import re
import subprocess
import sys
import time
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parent.parent / "assets" / "template.html"

FULL_CONTEXT = 100000

TEST_PATTERNS = [
    re.compile(r"(^|/)src/test/"),
    re.compile(r"(^|/)tests?/"),
    re.compile(r"(^|/)__tests__/"),
    re.compile(r"(^|/)spec/"),
    re.compile(r"(Test|Tests|IT|ITCase|Spec)\.(java|kt|scala|cs|groovy)$"),
    re.compile(r"\.(test|spec)\.[jt]sx?$"),
    re.compile(r"(^|/)test_[^/]+\.py$"),
    re.compile(r"_test\.(py|go|rb|ex|exs)$"),
    re.compile(r"_spec\.(rb|lua)$"),
]

HUNK_RE = re.compile(r"@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@ ?(.*)")
FILE_RE = re.compile(r"diff --git a/(.*) b/(.*)")
TICKET_RE = re.compile(r"[A-Z][A-Z0-9]{1,9}-\d+")


def git(repo, args):
    return subprocess.run(
        ["git", "-C", str(repo)] + args, capture_output=True, text=True, check=False
    )


def is_test(path):
    return any(pattern.search(path) for pattern in TEST_PATTERNS)


def parse_diff(text):
    """Turn unified diff text into [{path, added, removed, hunks:[{context, lines}]}]."""
    files, current, hunk = [], None, None
    old_no = new_no = 0
    for line in text.split("\n"):
        if line.startswith("diff --git"):
            match = FILE_RE.match(line)
            current = {
                "path": match.group(2) if match else line,
                "hunks": [],
                "added": 0,
                "removed": 0,
            }
            files.append(current)
            hunk = None
        elif line.startswith("@@") and current is not None:
            match = HUNK_RE.match(line)
            if not match:
                continue
            old_no, new_no = int(match.group(1)), int(match.group(2))
            hunk = {"context": match.group(3), "lines": []}
            current["hunks"].append(hunk)
        elif hunk is not None and line[:1] in (" ", "+", "-") and not line.startswith(("+++", "---")):
            kind, text_ = line[0], line[1:]
            if kind == " ":
                hunk["lines"].append({"t": "c", "o": old_no, "n": new_no, "s": text_})
                old_no += 1
                new_no += 1
            elif kind == "+":
                hunk["lines"].append({"t": "a", "o": None, "n": new_no, "s": text_})
                new_no += 1
                current["added"] += 1
            else:
                hunk["lines"].append({"t": "d", "o": old_no, "n": None, "s": text_})
                old_no += 1
                current["removed"] += 1
        elif hunk is not None and line == "":
            # a blank context line inside a hunk; git also ends the stream with one
            hunk["lines"].append({"t": "c", "o": old_no, "n": new_no, "s": ""})
            old_no += 1
            new_no += 1

    for entry in files:
        for block in entry["hunks"]:
            while block["lines"] and block["lines"][-1]["t"] == "c" and block["lines"][-1]["s"] == "":
                block["lines"].pop()
        entry["hunks"] = [block for block in entry["hunks"] if block["lines"]]
    return files


def diff_selector(opts):
    if opts.range:
        return [opts.range]
    if opts.staged:
        return ["--cached"]
    return ["HEAD"]


def collect(repo, opts, context):
    args = ["diff", "-U%d" % context, "--no-color", "--no-ext-diff"] + diff_selector(opts)
    if opts.paths:
        args += ["--"] + opts.paths
    result = git(repo, args)
    if result.returncode != 0:
        sys.exit("git diff failed in %s:\n%s" % (repo, result.stderr.strip()))
    return parse_diff(result.stdout)


def line_count(files, key="hunks"):
    return sum(len(block["lines"]) for entry in files for block in entry.get(key, []))


def main():
    parser = argparse.ArgumentParser(description="Build a diff review page from git diffs.")
    parser.add_argument("--out", required=True, help="output .html path")
    parser.add_argument("--repo", action="append", default=[], help="repository path (repeatable)")
    parser.add_argument("--range", help="commit range or revision, e.g. develop...HEAD or HEAD~2")
    parser.add_argument("--staged", action="store_true", help="staged changes only")
    parser.add_argument("--paths", nargs="*", default=[], help="pathspec filter")
    parser.add_argument("--context", type=int, default=12, help="context lines (default 12)")
    parser.add_argument("--title", help="page title; default is the ticket key or repo name")
    parser.add_argument("--eyebrow", help="small line above the title")
    parser.add_argument("--no-tests", action="store_true", help="drop test files entirely")
    parser.add_argument("--max-lines", type=int, default=120000, help="line budget for the page")
    args = parser.parse_args()

    repos = [Path(p).resolve() for p in (args.repo or ["."])]
    for repo in repos:
        if git(repo, ["rev-parse", "--is-inside-work-tree"]).returncode != 0:
            sys.exit("not a git repository: %s" % repo)

    files, binary, untracked_total = [], 0, 0
    for repo in repos:
        name = git(repo, ["rev-parse", "--show-toplevel"]).stdout.strip() or str(repo)
        name = Path(name).name
        windowed = collect(repo, args, args.context)
        whole = {entry["path"]: entry["hunks"] for entry in collect(repo, args, FULL_CONTEXT)}
        for entry in windowed:
            if not entry["hunks"]:
                binary += 1
                continue
            group = "test" if is_test(entry["path"]) else "src"
            if group == "test" and args.no_tests:
                continue
            entry["repo"] = name
            entry["group"] = group
            entry["full"] = whole.get(entry["path"], entry["hunks"])
            files.append(entry)
        if not args.range and not args.staged:
            untracked = git(repo, ["ls-files", "--others", "--exclude-standard"]).stdout.split()
            untracked_total += len(untracked)

    if not files:
        sys.exit("no textual changes found for this selection")

    files.sort(key=lambda entry: (entry["group"] != "src", entry["repo"], entry["path"]))

    # keep the page inside a sane size: drop the whole-file view first, then the context
    full_on = True
    if line_count(files, "hunks") + line_count(files, "full") > args.max_lines:
        full_on = False
        for entry in files:
            entry.pop("full", None)
    if full_on is False and line_count(files, "hunks") > args.max_lines:
        for entry in files:
            for block in entry["hunks"]:
                block["lines"] = block["lines"][:400]

    head = repos[0]
    branch = git(head, ["rev-parse", "--abbrev-ref", "HEAD"]).stdout.strip()
    ticket = TICKET_RE.search(branch)
    title = args.title or (ticket.group(0) if ticket else "%s changes" % Path(head).name)
    selector = " ".join(diff_selector(args))
    eyebrow = args.eyebrow or " · ".join(
        [", ".join(sorted({entry["repo"] for entry in files}))] + ([branch] if branch else [])
    )

    added = sum(entry["added"] for entry in files)
    removed = sum(entry["removed"] for entry in files)
    tests = sum(1 for entry in files if entry["group"] == "test")
    notes = [
        "<strong>%d files</strong> (%d source, %d tests) · +%d −%d"
        % (len(files), len(files) - tests, tests, added, removed),
        "<code>git diff %s</code> · %d lines of context" % (html.escape(selector), args.context),
    ]
    if not full_on:
        notes.append("<b>Whole file</b> view is off — the diff is too large for it.")
    if binary:
        notes.append("%d binary file(s) skipped." % binary)
    if untracked_total:
        notes.append("%d untracked file(s) not shown — git does not diff them yet." % untracked_total)
    notes.append(time.strftime("%Y-%m-%d %H:%M"))

    payload = {
        "meta": {
            "title": title,
            "eyebrow": eyebrow,
            "footer": " · ".join(notes),
            "groups": [{"key": "src", "label": "Source"}, {"key": "test", "label": "Tests"}],
            "full": full_on,
        },
        "files": files,
    }

    template = TEMPLATE.read_text(encoding="utf-8")
    page = template.replace("__PAGE_TITLE__", html.escape(title))
    page = page.replace(
        "__DATA_JSON__", json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    )

    out = Path(args.out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")

    print("wrote %s (%.1f KB)" % (out, len(page.encode()) / 1024))
    print(
        "%d files (%d source, %d test) · +%d -%d · whole-class view: %s"
        % (len(files), len(files) - tests, tests, added, removed, "on" if full_on else "off")
    )
    print("title: %s | eyebrow: %s" % (title, eyebrow))
    for entry in files:
        print(
            "  [%s] %s/%s  +%d -%d"
            % (entry["group"], entry["repo"], entry["path"], entry["added"], entry["removed"])
        )


if __name__ == "__main__":
    main()
