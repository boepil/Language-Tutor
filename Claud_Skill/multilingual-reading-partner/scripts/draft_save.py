#!/usr/bin/env python3
"""Compose the body of ONE story's draft, changing only what this save is meant to change.

The draft is a readable markdown page, built to be glanced at on GitHub. Layout:

    # <Title> (<Author>) - draft

    ## My notebook
    1. "<the learner's sentence>" (<Place>, PDF page 27)

    ## Where we stopped
    - ...                      <- the handoff: every "## " section from here down to "## Session log"
    ## Settings
    ## Vocabulary covered (one word per bullet, newest on top)
    ...

    ## Session log
    <details>
    <summary>Full detail per session (the Study File is built from this)</summary>

    ### Session <label>

    ```text
    [VOCAB]
    word | folio | exact sentence from the book | meaning and notes | status
    [ERRORS]
    pattern | examples
    [READINGS]
    place in the text | the learner's reading | where it landed
    [OPEN]
    an unresolved question
    [STRENGTHS]
    a specific strength
    [LETTERS]
    letter | sound | shape notes | status        (Arabic only)
    [POSITION]
    folios covered this session, e.g. 33-35
    ```

    </details>

Older drafts (STORY: line, === HANDOFF ===, === STUDY RECORD ===) are still read; any save writes the
new layout.

Usage:
  draft_save.py --story "First Love (Samuel Beckett)" --handoff handoff.md \\
      [--existing old_body.txt] \\
      [--add-thing '"the learner's sentence" (Introduction, PDF page 27)']... \\
      [--session-label "2026-11-07" --record record.txt] \\
      [--out merged.txt]

What it does:
  - Replaces the handoff sections with the new ones (the handoff must start with a "## " heading).
  - Keeps "My notebook" exactly as it was and appends each --add-thing as the next number.
  - Adds the session's log entries, or replaces that one session if the label already exists.
  - Leaves every other session untouched.
Aborts (exit 1, nothing written) if any existing point or any other session would change.
"""
import argparse
import re
import sys

OLD_HANDOFF_HDR = "=== HANDOFF ==="
OLD_RECORD_HDR = "=== STUDY RECORD ==="
OLD_THINGS_HDR = "THINGS I FOUND IMPORTANT"
OLD_STORY_RE = re.compile(r"^STORY:\s*(.*)$")
OLD_SESSION_RE = re.compile(r"^--- SESSION (.+?) ---\s*$")

NOTEBOOK_HDR = "## My notebook"
LOG_HDR = "## Session log"
TITLE_RE = re.compile(r"^#\s+(.*?)(?:\s+-\s+draft)?\s*$")
SESSION_RE = re.compile(r"^### Session (.+?)\s*$")
WRAPPER = ("```text", "```", "<details>", "</details>")
# Strict notes convention: "sentence" (Place, PDF page N) or (Place, photo N)
THING_RE = re.compile(r'^"[^"].*" \([^()\n]+, (?:PDF page|photo) \d+\)$')


def _trim(lines):
    lines = list(lines)
    while lines and not lines[-1].strip():
        lines.pop()
    while lines and not lines[0].strip():
        lines.pop(0)
    return lines


def _parse_old(lines):
    h = lines.index(OLD_HANDOFF_HDR) if OLD_HANDOFF_HDR in lines else None
    r = lines.index(OLD_RECORD_HDR) if OLD_RECORD_HDR in lines else None
    head_end = h if h is not None else (r if r is not None else len(lines))
    handoff = lines[h + 1:(r if r is not None and r > h else len(lines))] if h is not None else []
    record = lines[r + 1:] if r is not None else []
    story, things, in_things = "", [], False
    for line in lines[:head_end]:
        m = OLD_STORY_RE.match(line)
        if m and not in_things:
            story = m.group(1).strip()
        elif line.strip() == OLD_THINGS_HDR:
            in_things = True
        elif in_things:
            things.append(line)
    sessions, order, cur = {}, [], None
    for line in record:
        m = OLD_SESSION_RE.match(line)
        if m:
            cur = m.group(1).strip()
            order.append(cur)
            sessions[cur] = []
        elif cur is not None:
            sessions[cur].append(line)
    return story, _trim(things), "\n".join(_trim(handoff)), {k: "\n".join(_trim(v)) for k, v in sessions.items()}, order


def _parse_new(lines):
    story = ""
    for line in lines:
        m = TITLE_RE.match(line)
        if m:
            story = m.group(1).strip()
            break
    idx = {l.strip(): i for i, l in reversed(list(enumerate(lines)))}
    n = idx.get(NOTEBOOK_HDR)
    r = idx.get(LOG_HDR)
    things, handoff = [], []
    if n is not None:
        stop = next((i for i in range(n + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
        things = _trim(lines[n + 1:stop])
        end = r if r is not None and r > stop else len(lines)
        handoff = lines[stop:end]
    sessions, order, cur = {}, [], None
    for line in (lines[r + 1:] if r is not None else []):
        m = SESSION_RE.match(line)
        if m:
            cur = m.group(1).strip()
            order.append(cur)
            sessions[cur] = []
        elif cur is not None:
            if line.strip() in WRAPPER or line.strip().startswith("<summary>"):
                continue
            sessions[cur].append(line)
    return story, things, "\n".join(_trim(handoff)), {k: "\n".join(_trim(v)) for k, v in sessions.items()}, order


def parse(text):
    """Return (story, notebook lines, handoff text, {label: body}, [labels in order]) from either layout."""
    lines = text.splitlines()
    if OLD_HANDOFF_HDR in lines or OLD_RECORD_HDR in lines:
        return _parse_old(lines)
    return _parse_new(lines)


def next_number(things):
    nums = [int(m.group(1)) for line in things if (m := re.match(r"^(\d+)\.\s", line))]
    return (max(nums) + 1) if nums else 1


def compose(story, things, handoff, sessions, order):
    out = [f"# {story} - draft", "", NOTEBOOK_HDR, ""]
    out += things
    out += ["", handoff, "", LOG_HDR, "", "<details>",
            "<summary>Full detail per session (the Study File is built from this)</summary>", ""]
    for label in order:
        out += [f"### Session {label}", "", "```text", sessions[label], "```", ""]
    out += ["</details>"]
    return "\n".join(out).rstrip("\n") + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--existing", help="file holding the draft body just re-read from the repo")
    ap.add_argument("--story", help='"Title (Author)"; required when there is no existing draft')
    ap.add_argument("--handoff", required=True, help="file with the new handoff sections (markdown, starts with a ## heading)")
    ap.add_argument("--add-thing", action="append", default=[], help="a new point for My notebook")
    ap.add_argument("--session-label", help="label for this session's log entries")
    ap.add_argument("--record", help="file with this session's log entries")
    ap.add_argument("--out")
    a = ap.parse_args()

    if bool(a.session_label) != bool(a.record):
        sys.exit("ABORT: --session-label and --record go together")

    old = open(a.existing, encoding="utf-8").read() if a.existing else ""
    story, things, _old_handoff, sessions, order = parse(old)
    if a.story:
        story = a.story if not story else story  # never rename an existing draft's story line
    if not story:
        sys.exit("ABORT: no title in the existing draft and no --story given")

    old_things, old_sessions = list(things), dict(sessions)

    for t in a.add_thing:
        if not THING_RE.match(t.strip()):
            sys.exit('ABORT: note does not follow the convention "sentence" (Place, PDF page N) or (Place, photo N): ' + t)
    n = next_number(things)
    for t in a.add_thing:
        things.append(f"{n}. {t.strip()}")
        n += 1

    handoff = open(a.handoff, encoding="utf-8").read().strip("\n")
    if not handoff.startswith("## "):
        sys.exit("ABORT: the handoff must be the new layout and start with a '## ' heading (for example '## Where we stopped')")
    if NOTEBOOK_HDR in handoff.splitlines() or LOG_HDR in handoff.splitlines():
        sys.exit(f"ABORT: the handoff must not contain the '{NOTEBOOK_HDR}' or '{LOG_HDR}' headings")

    if a.session_label:
        entries = open(a.record, encoding="utf-8").read().strip("\n")
        if "```" in entries:
            sys.exit("ABORT: the session record must not contain code fences")
        if a.session_label not in sessions:
            order.append(a.session_label)
        sessions[a.session_label] = entries

    merged = compose(story, things, handoff, sessions, order)

    # Verify by re-parsing: nothing the learner owns, and no other session, may have changed.
    _s, chk_things, chk_handoff, chk_sessions, _o = parse(merged)
    if chk_things[:len(old_things)] != old_things:
        sys.exit("ABORT: an existing My notebook point would change")
    if chk_handoff != handoff:
        sys.exit("ABORT: the handoff did not survive a round trip")
    for label, body in old_sessions.items():
        if label != a.session_label and chk_sessions.get(label) != body:
            sys.exit(f"ABORT: session '{label}' would change")

    if a.out:
        open(a.out, "w", encoding="utf-8").write(merged)
        print(f"OK: wrote {a.out} ({len(chk_things)} lines in the notebook, {len(chk_sessions)} sessions)", file=sys.stderr)
    else:
        sys.stdout.write(merged)


if __name__ == "__main__":
    main()
