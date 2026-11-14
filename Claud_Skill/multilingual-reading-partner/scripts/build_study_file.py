#!/usr/bin/env python3
"""Render a finished story's Study File (.md) from its draft.

The script does the mechanical parts (the learner's notebook, reading record, vocabulary,
recurring problems, sessions at a glance, and an appendix with the book's own sentences). The two
written parts, the story summary and the closing synthesis, come from files Claude writes after
the closing conversation.

The file is built to be glanced at: short bullets, one idea per line, headings, the vocabulary as
"word: short meaning", and the long sentences kept in an appendix at the end.

Usage:
  build_study_file.py --draft draft_body.txt --summary summary.txt --synthesis synthesis.txt \\
      --reader Boaz [--level B2] [--style "literary sparring partner"] \\
      [--source "First Love and Other Shorts (Grove Press), folios 9-36"] \\
      --out "First Love - Study File.md"

File name rule: "<Story title> - Study File.md" (the story first, so the folder scans by title).

Section order: notebook (word for word), summary, closing synthesis, reading record, open
questions, vocabulary (the draft's own short list), recurring problems, strengths, sessions at a
glance, appendix (vocabulary with the book's sentences).
"""
import argparse
import re
import sys
from collections import OrderedDict

sys.path.insert(0, __import__("os").path.dirname(__file__))
from draft_save import parse  # noqa: E402

TAG_RE = re.compile(r"^\[(VOCAB|ERRORS|READINGS|OPEN|STRENGTHS|POSITION|LETTERS)\]\s*$")


def split_blocks(body):
    blocks, cur = {}, None
    for line in body.splitlines():
        m = TAG_RE.match(line.strip())
        if m:
            cur = m.group(1)
            blocks.setdefault(cur, [])
        elif cur and line.strip():
            blocks[cur].append(line.strip())
    return blocks


def fields(line, n):
    parts = [p.strip() for p in line.split("|")]
    if len(parts) > n:
        parts = parts[:n - 1] + [" | ".join(parts[n - 1:])]
    return parts + [""] * (n - len(parts))


def read_text(path):
    return open(path, encoding="utf-8").read().strip() if path else ""


def session_heading(label):
    """'Session 2026-11-07' for dated sessions, the label itself for others (e.g. 'Earlier sittings ...')."""
    return f"Session {label}" if label[:1].isdigit() else label


def handoff_section(handoff, prefix):
    """Text of the '## <prefix>...' section of the draft's handoff, without its heading."""
    out, on = [], False
    for line in handoff.splitlines():
        if line.startswith("## "):
            if on:
                break
            on = line[3:].strip().lower().startswith(prefix.lower())
            continue
        if on:
            out.append(line)
    return "\n".join(out).strip("\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--draft", required=True)
    ap.add_argument("--summary")
    ap.add_argument("--synthesis")
    ap.add_argument("--reader", default="")
    ap.add_argument("--language", default="")
    ap.add_argument("--level", default="")
    ap.add_argument("--style", default="")
    ap.add_argument("--source", default="")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    story, things, handoff, sessions, order = parse(open(a.draft, encoding="utf-8").read())
    title = story or "Study File"

    vocab = OrderedDict()   # word -> dict
    errors = OrderedDict()  # pattern -> {"examples": [...], "n": sessions seen}
    readings, opens, strengths, positions = [], [], [], []
    letters = OrderedDict()

    for label in order:
        b = split_blocks(sessions[label])
        for line in b.get("VOCAB", []):
            word, folio, sentence, meaning, status = fields(line, 5)
            key = word.lower()
            v = vocab.setdefault(key, {"word": word, "folios": [], "sentence": "", "meaning": "", "status": "unquizzed"})
            if folio and folio.lower() not in ("none", "-", "n/a") and folio not in v["folios"]:
                v["folios"].append(folio)
            v["sentence"] = v["sentence"] or sentence
            v["meaning"] = meaning or v["meaning"]
            st = (status or "unquizzed").lower()
            if st != "unquizzed" or v["status"] == "unquizzed":
                v["status"] = st
        for line in b.get("LETTERS", []):
            letter, sound, shape, status = fields(line, 4)
            if letter:
                letters[letter] = {"letter": letter, "sound": sound or letters.get(letter, {}).get("sound", ""),
                                   "shape": shape or letters.get(letter, {}).get("shape", ""), "status": status or "new"}
        for line in b.get("ERRORS", []):
            pattern, examples = fields(line, 2)
            e = errors.setdefault(pattern.lower(), {"pattern": pattern, "examples": [], "n": 0})
            e["n"] += 1
            for ex in [x.strip() for x in examples.split(";") if x.strip()]:
                if ex not in e["examples"]:
                    e["examples"].append(ex)
        for line in b.get("READINGS", []):
            readings.append((label,) + tuple(fields(line, 3)))
        for line in b.get("OPEN", []):
            if not re.match(r"^none\b", line, re.I) and line not in opens:
                opens.append(line)
        for line in b.get("STRENGTHS", []):
            if line not in strengths:
                strengths.append(line)
        positions.append((label, " ".join(b.get("POSITION", []))))

    out = [f"# {title} - Study File", ""]
    meta = [f"Reader: {a.reader}" if a.reader else "", "Partner: Alex (multilingual-reading-partner)",
            f"Language: {a.language}" if a.language else "",
            f"Level: {a.level}" if a.level else "", f"Style: {a.style}" if a.style else ""]
    out.append(" · ".join(m for m in meta if m))
    if a.source:
        out += ["", f"Source: {a.source}"]
    out += ["", "---", "", "## My notebook", ""]
    out += things if things else ["*No points were added to the notebook for this story.*"]

    out += ["", "---", "", "## Summary of the story", ""]
    out.append(read_text(a.summary) or "*Not written.*")
    out += ["", "---", "", "## Closing synthesis", ""]
    out.append(read_text(a.synthesis) or "*Not written.*")

    out += ["", "---", "", "## Reading record", ""]
    last = None
    for label, place, reading, landed in readings:
        if label != last:
            if last is not None:
                out.append("")
            out += [f"### {session_heading(label)}", ""]
            last = label
        out.append(f"- **{place}**" if place else "- (no place noted)")
        if reading:
            out.append(f"  - your reading: {reading}")
        if landed:
            out.append(f"  - where it landed: {landed}")
    if not readings:
        out.append("*No readings were recorded.*")
    if opens:
        out += ["", "### Open questions", ""] + [f"- {q}" for q in opens]

    out += ["", "---", "", "## Vocabulary", ""]
    short = handoff_section(handoff, "Vocabulary")
    if short:
        out.append(short)   # the draft's own short list, newest on top, as the learner approved it
    elif vocab:
        out += [f"- {v['word']}: {v['meaning'].split(';')[0].strip()}" for v in reversed(list(vocab.values()))]
    else:
        out.append("*No vocabulary was recorded.*")

    if letters:
        out += ["", "---", "", "## Letters met", ""]
        for L in letters.values():
            bits = [x for x in (L["sound"], L["shape"], L["status"]) if x]
            out.append(f"- **{L['letter']}**: " + " · ".join(bits))
    out += ["", "---", "", "## Recurring problems", ""]
    if errors:
        out += ["| Pattern | Examples | Sessions seen |", "|---|---|---|"]
        for e in errors.values():
            out.append(f"| {e['pattern']} | {'; '.join(e['examples'])} | {e['n']} |")
    else:
        out.append("*No recurring problems were recorded.*")
    if strengths:
        out += ["", "**Strengths**", ""] + [f"- {s}" for s in strengths]

    out += ["", "---", "", "## Sessions at a glance", ""]
    for label, pos in positions:
        out.append(f"- {label}" + (f": {pos}" if pos else ""))

    out += ["", "---", "", "## Appendix: vocabulary with the book's sentences", "",
            "Newest first. Format: **word** (folio): sentence from the book → meaning and notes · status.", ""]
    for v in reversed(list(vocab.values())):
        folios = ", ".join(f"f.{f}" for f in v["folios"])
        head = f"**{v['word']}**" + (f" ({folios})" if folios else "")
        sent_text = v["sentence"].strip().strip('"“”')
        if sent_text.startswith("("):
            sent = f" {sent_text}"
        else:
            sent = f' "{sent_text}"' if sent_text else ""
        out.append(f"- {head}:{sent} → {v['meaning']} · {v['status']}")
    if not vocab:
        out.append("*No vocabulary was recorded.*")

    open(a.out, "w", encoding="utf-8").write("\n".join(out).rstrip("\n") + "\n")
    print(f"OK: wrote {a.out} ({len(vocab)} words, {len(errors)} patterns, {len(readings)} readings)", file=sys.stderr)


if __name__ == "__main__":
    main()
