#!/usr/bin/env python3
"""Render a finished story's Study File (.md) from its draft.

The script does the mechanical parts (the learner's notebook, reading record, vocabulary,
recurring problems, sessions at a glance, and an appendix with the book's own sentences). The two
written parts, the story summary and the closing synthesis, come from files Claude writes after
the closing conversation.

The file is built to be glanced at: short bullets, one idea per line, headings, the vocabulary as
"word: short meaning", and the long sentences kept in an appendix at the end.

Hebrew books: pass --language he (or Hebrew) and every heading and label is written in Hebrew.
Any other language gets the English labels.

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


# Labels for the finished Study File. English is the default; Hebrew books get Hebrew throughout.
L_EN = {
    "title_suffix": "Study File", "reader": "Reader", "partner": "Partner", "language": "Language",
    "level": "Level", "style": "Style", "source": "Source",
    "notebook": "My notebook", "no_notebook": "*No points were added to the notebook for this story.*",
    "summary": "Summary of the story", "synthesis": "Closing synthesis", "not_written": "*Not written.*",
    "readings": "Reading record", "no_place": "(no place noted)", "your_reading": "your reading",
    "landed": "where it landed", "no_readings": "*No readings were recorded.*",
    "open": "Open questions", "vocab": "Vocabulary", "no_vocab": "*No vocabulary was recorded.*",
    "letters": "Letters met", "problems": "Recurring problems", "no_problems": "*No recurring problems were recorded.*",
    "tbl": ("Pattern", "Examples", "Sessions seen"), "strengths": "Strengths", "glance": "Sessions at a glance",
    "appendix": "Appendix: vocabulary with the book's sentences",
    "appendix_note": "Newest first. Format: **word** (folio): sentence from the book → meaning and notes · status.",
    "session": "Session", "folio": "f.",
    "status": {"unquizzed": "unquizzed", "right": "right", "wrong": "wrong"},
}
L_HE = {
    "title_suffix": "קובץ לימוד", "reader": "קורא", "partner": "שותף", "language": "שפה",
    "level": "רמה", "style": "סגנון", "source": "מקור",
    "notebook": "המחברת שלי", "no_notebook": "*לא נוספו נקודות למחברת בסיפור הזה.*",
    "summary": "סיכום הסיפור", "synthesis": "סיכום מסכם", "not_written": "*לא נכתב.*",
    "readings": "תיעוד הקריאה", "no_place": "(לא צוין מקום)", "your_reading": "הקריאה שלך",
    "landed": "לאן זה הגיע", "no_readings": "*לא תועדו קריאות.*",
    "open": "שאלות פתוחות", "vocab": "מילים", "no_vocab": "*לא תועדו מילים.*",
    "letters": "אותיות שנפגשו", "problems": "קשיים חוזרים", "no_problems": "*לא תועדו קשיים חוזרים.*",
    "tbl": ("דפוס", "דוגמאות", "מפגשים"), "strengths": "חוזקות", "glance": "המפגשים במבט",
    "appendix": "נספח: מילים עם משפטי הספר",
    "appendix_note": "החדשות למעלה. מבנה: **מילה** (עמוד): משפט מהספר → משמעות והערות · מצב.",
    "session": "מפגש", "folio": "עמ' ",
    "status": {"unquizzed": "טרם נבחן", "right": "נכון", "wrong": "שגוי"},
}

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


def session_heading(label, word="Session"):
    """'Session 2026-11-07' for dated sessions, the label itself for others (e.g. 'Earlier sittings ...')."""
    return f"{word} {label}" if label[:1].isdigit() else label


def handoff_section(handoff, prefix):
    """Text of the '## <prefix>...' section of the draft's handoff, without its heading.
    prefix may be a string or a tuple of strings (English and Hebrew headings)."""
    prefixes = (prefix,) if isinstance(prefix, str) else tuple(prefix)
    out, on = [], False
    for line in handoff.splitlines():
        if line.startswith("## "):
            if on:
                break
            on = any(line[3:].strip().lower().startswith(p.lower()) for p in prefixes)
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
    L = L_HE if (a.language or "").lower() in ("he", "hebrew", "עברית") else L_EN
    title = story or L["title_suffix"]

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

    out = [f"# {title} - {L['title_suffix']}", ""]
    meta = [f"{L['reader']}: {a.reader}" if a.reader else "", f"{L['partner']}: Alex (multilingual-reading-partner)",
            f"{L['language']}: {a.language}" if a.language else "",
            f"{L['level']}: {a.level}" if a.level else "", f"{L['style']}: {a.style}" if a.style else ""]
    out.append(" · ".join(m for m in meta if m))
    if a.source:
        out += ["", f"{L['source']}: {a.source}"]
    out += ["", "---", "", f"## {L['notebook']}", ""]
    out += things if things else [L["no_notebook"]]

    out += ["", "---", "", f"## {L['summary']}", ""]
    out.append(read_text(a.summary) or L["not_written"])
    out += ["", "---", "", f"## {L['synthesis']}", ""]
    out.append(read_text(a.synthesis) or L["not_written"])

    out += ["", "---", "", f"## {L['readings']}", ""]
    last = None
    for label, place, reading, landed in readings:
        if label != last:
            if last is not None:
                out.append("")
            out += [f"### {session_heading(label, L['session'])}", ""]
            last = label
        out.append(f"- **{place}**" if place else f"- {L['no_place']}")
        if reading:
            out.append(f"  - {L['your_reading']}: {reading}")
        if landed:
            out.append(f"  - {L['landed']}: {landed}")
    if not readings:
        out.append(L["no_readings"])
    if opens:
        out += ["", f"### {L['open']}", ""] + [f"- {q}" for q in opens]

    out += ["", "---", "", f"## {L['vocab']}", ""]
    short = handoff_section(handoff, ("Vocabulary", "מילים"))
    if short:
        out.append(short)   # the draft's own short list, newest on top, as the learner approved it
    elif vocab:
        out += [f"- {v['word']}: {v['meaning'].split(';')[0].strip()}" for v in reversed(list(vocab.values()))]
    else:
        out.append(L["no_vocab"])

    if letters:
        out += ["", "---", "", f"## {L['letters']}", ""]
        for lt in letters.values():
            bits = [x for x in (lt["sound"], lt["shape"], lt["status"]) if x]
            out.append(f"- **{lt['letter']}**: " + " · ".join(bits))
    out += ["", "---", "", f"## {L['problems']}", ""]
    if errors:
        out += ["| " + " | ".join(L["tbl"]) + " |", "|---|---|---|"]
        for e in errors.values():
            out.append(f"| {e['pattern']} | {'; '.join(e['examples'])} | {e['n']} |")
    else:
        out.append(L["no_problems"])
    if strengths:
        out += ["", f"**{L['strengths']}**", ""] + [f"- {s}" for s in strengths]

    out += ["", "---", "", f"## {L['glance']}", ""]
    for label, pos in positions:
        out.append(f"- {label}" + (f": {pos}" if pos else ""))

    out += ["", "---", "", f"## {L['appendix']}", "",
            L["appendix_note"], ""]
    for v in reversed(list(vocab.values())):
        folios = ", ".join(f"{L['folio']}{f}" for f in v["folios"])
        head = f"**{v['word']}**" + (f" ({folios})" if folios else "")
        sent_text = v["sentence"].strip().strip('"“”')
        if sent_text.startswith("("):
            sent = f" {sent_text}"
        else:
            sent = f' "{sent_text}"' if sent_text else ""
        out.append(f"- {head}:{sent} → {v['meaning']} · {L['status'].get(v['status'], v['status'])}")
    if not vocab:
        out.append(L["no_vocab"])

    open(a.out, "w", encoding="utf-8").write("\n".join(out).rstrip("\n") + "\n")
    print(f"OK: wrote {a.out} ({len(vocab)} words, {len(errors)} patterns, {len(readings)} readings)", file=sys.stderr)


if __name__ == "__main__":
    main()
