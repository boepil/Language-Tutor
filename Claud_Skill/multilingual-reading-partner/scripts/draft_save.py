#!/usr/bin/env python3
"""Compose the body of ONE story's Gmail draft, changing only what this save is meant to change.

Draft layout (plain text, because it is saved as an email draft body):

    STORY: <Title> (<Author>)

    THINGS I FOUND IMPORTANT
    1. "<the learner's sentence>" (<Place>, PDF page 27)
    2. ...

    === HANDOFF ===
    <the handoff block>

    === STUDY RECORD ===
    --- SESSION <label> ---
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

Usage:
  draft_save.py --story "First Love (Samuel Beckett)" --handoff handoff.txt \\
      [--existing old_body.txt] \\
      [--add-thing '"the learner's sentence" (Introduction, PDF page 27)']... \\
      [--session-label "2026-11-07" --record record.txt] \\
      [--out merged.txt]

What it does:
  - Replaces the handoff block with the new one.
  - Keeps THINGS I FOUND IMPORTANT exactly as it was and appends each --add-thing as the next number.
  - Adds the session's study-record entries, or replaces that one session if the label already exists.
  - Leaves every other session untouched.
Aborts (exit 1, nothing written) if any existing point or any other session would change.
"""
import argparse
import re
import sys

HANDOFF_HDR = "=== HANDOFF ==="
RECORD_HDR = "=== STUDY RECORD ==="
THINGS_HDR = "THINGS I FOUND IMPORTANT"
STORY_RE = re.compile(r"^STORY:\s*(.*)$")
SESSION_RE = re.compile(r"^--- SESSION (.+?) ---\s*$")
# Strict notes convention: "sentence" (Place, PDF page N) or (Place, photo N)
THING_RE = re.compile(r'^"[^"].*" \([^()\n]+, (?:PDF page|photo) \d+\)$')


def parse(text):
    """Split a draft body into story line, things lines, handoff text, and ordered sessions."""
    lines = text.splitlines()
    try:
        h = lines.index(HANDOFF_HDR)
    except ValueError:
        h = None
    try:
        r = lines.index(RECORD_HDR)
    except ValueError:
        r = None

    head_end = h if h is not None else (r if r is not None else len(lines))
    head = lines[:head_end]
    handoff = lines[h + 1:(r if r is not None and r > h else len(lines))] if h is not None else []
    record = lines[r + 1:] if r is not None else []

    story = ""
    things = []
    in_things = False
    for line in head:
        m = STORY_RE.match(line)
        if m and not in_things:
            story = m.group(1).strip()
        elif line.strip() == THINGS_HDR:
            in_things = True
        elif in_things:
            things.append(line)
    while things and not things[-1].strip():
        things.pop()
    while things and not things[0].strip():
        things.pop(0)

    sessions, order, cur = {}, [], None
    for line in record:
        m = SESSION_RE.match(line)
        if m:
            cur = m.group(1).strip()
            order.append(cur)
            sessions[cur] = []
        elif cur is not None:
            sessions[cur].append(line)
    sessions = {k: "\n".join(v).strip("\n") for k, v in sessions.items()}
    return story, things, "\n".join(handoff).strip("\n"), sessions, order


def next_number(things):
    nums = [int(m.group(1)) for line in things if (m := re.match(r"^(\d+)\.\s", line))]
    return (max(nums) + 1) if nums else 1


def compose(story, things, handoff, sessions, order):
    out = [f"STORY: {story}", "", THINGS_HDR]
    out += things if things else []
    out += ["", HANDOFF_HDR, handoff, "", RECORD_HDR]
    for label in order:
        out += [f"--- SESSION {label} ---", sessions[label], ""]
    return "\n".join(out).rstrip("\n") + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--existing", help="file holding the draft body just re-read from Gmail")
    ap.add_argument("--story", help='"Title (Author)"; required when there is no existing draft')
    ap.add_argument("--handoff", required=True, help="file with the new handoff block")
    ap.add_argument("--add-thing", action="append", default=[], help="a new point for THINGS I FOUND IMPORTANT")
    ap.add_argument("--session-label", help="label for this session's study-record entries")
    ap.add_argument("--record", help="file with this session's study-record entries")
    ap.add_argument("--out")
    a = ap.parse_args()

    if bool(a.session_label) != bool(a.record):
        sys.exit("ABORT: --session-label and --record go together")

    old = open(a.existing, encoding="utf-8").read() if a.existing else ""
    story, things, _old_handoff, sessions, order = parse(old)
    if a.story:
        story = a.story if not story else story  # never rename an existing draft's story line
    if not story:
        sys.exit("ABORT: no story line in the existing draft and no --story given")

    old_things, old_sessions = list(things), dict(sessions)

    for t in a.add_thing:
        if not THING_RE.match(t.strip()):
            sys.exit('ABORT: note does not follow the convention "sentence" (Place, PDF page N) or (Place, photo N): ' + t)
    n = next_number(things)
    for t in a.add_thing:
        things.append(f"{n}. {t.strip()}")
        n += 1

    handoff = open(a.handoff, encoding="utf-8").read().strip("\n")

    if a.session_label:
        entries = open(a.record, encoding="utf-8").read().strip("\n")
        if a.session_label not in sessions:
            order.append(a.session_label)
        sessions[a.session_label] = entries

    merged = compose(story, things, handoff, sessions, order)

    # Verify by re-parsing: nothing the learner owns, and no other session, may have changed.
    _s, chk_things, _h, chk_sessions, _o = parse(merged)
    if chk_things[:len(old_things)] != old_things:
        sys.exit("ABORT: an existing THINGS I FOUND IMPORTANT point would change")
    for label, body in old_sessions.items():
        if label != a.session_label and chk_sessions.get(label) != body:
            sys.exit(f"ABORT: session '{label}' would change")

    if a.out:
        open(a.out, "w", encoding="utf-8").write(merged)
        print(f"OK: wrote {a.out} ({len(chk_things)} lines in the notes list, {len(chk_sessions)} sessions)", file=sys.stderr)
    else:
        sys.stdout.write(merged)


if __name__ == "__main__":
    main()
