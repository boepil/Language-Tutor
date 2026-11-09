#!/usr/bin/env python3
"""Detect a book's language, normalise extracted text, and repair right-to-left text stored in visual order.

Usage:
  detect_lang.py --txt /tmp/reading/book.txt                 # report language and warnings (JSON)
  detect_lang.py --txt /tmp/reading/book.txt --normalize     # NFKC for Arabic, NFC otherwise; drop bidi marks, soft hyphens
  detect_lang.py --txt /tmp/reading/book.txt --fix-rtl       # also reverse lines that were stored in visual order

Language codes: en, he, ko, ar. 'latin-other' = Latin script but not clearly English (ask the learner).
'mixed' = a second script makes up more than 20% of the letters (ask the learner).
Edits keep a backup next to the file as <name>.orig (made once).
To add a language, add its Unicode ranges to SCRIPTS and a branch in code_for().
"""
import argparse
import json
import os
import re
import shutil
import sys
import unicodedata

SCRIPTS = {
    "hebrew": [(0x0590, 0x05FF), (0xFB1D, 0xFB4F)],
    "arabic": [(0x0600, 0x06FF), (0x0750, 0x077F), (0x08A0, 0x08FF), (0xFB50, 0xFDFF), (0xFE70, 0xFEFF)],
    "hangul": [(0x1100, 0x11FF), (0x3130, 0x318F), (0xAC00, 0xD7AF)],
    "han": [(0x4E00, 0x9FFF), (0x3400, 0x4DBF)],
    "latin": [(0x0041, 0x005A), (0x0061, 0x007A), (0x00C0, 0x024F)],
}
BIDI = dict.fromkeys(list(range(0x200E, 0x2010)) + list(range(0x202A, 0x202F)) + list(range(0x2066, 0x206A)) + [0x00AD, 0xFEFF, 0x200B], None)
EN_STOP = set("the of and to a in that is was he she it for with as his her on be at by had not but they from this have are or an which you were their there been would who what when we all".split())
HEB_FINALS = "ךםןףץ"


def script_of(ch):
    o = ord(ch)
    for name, ranges in SCRIPTS.items():
        for lo, hi in ranges:
            if lo <= o <= hi:
                return name
    return None


def code_for(counts, text):
    total = sum(counts.values()) or 1
    ranked = sorted(counts.items(), key=lambda kv: -kv[1])
    top, n = ranked[0]
    # Hanja inside Korean text does not make it mixed with Chinese
    if top == "hangul" or (top == "han" and counts.get("hangul", 0) > n * 0.3):
        top, n = "hangul", counts.get("hangul", n)
    second = [kv for kv in ranked if kv[0] != top and not (top == "hangul" and kv[0] == "han")]
    mixed = bool(second) and second[0][1] / total > 0.20
    if top == "hebrew":
        code = "he"
    elif top == "arabic":
        code = "ar"
    elif top == "hangul":
        code = "ko"
    elif top == "latin":
        words = re.findall(r"[a-z]+", text.lower())
        ratio = sum(w in EN_STOP for w in words) / max(len(words), 1)
        code = "en" if ratio >= 0.12 else "latin-other"
    else:
        code = "unknown"
    return ("mixed" if mixed else code), code


def normalize(text, code=None):
    form = "NFKC" if code == "ar" else "NFC"
    text = unicodedata.normalize(form, text)
    text = text.translate(BIDI)
    return text


def final_letter_stats(text):
    """Hebrew final letters belong at the END of words. Many at the START means visual (reversed) order."""
    start = end = 0
    for w in re.findall(r"[\u05d0-\u05ea]+", text):
        if w[0] in HEB_FINALS:
            start += 1
        if w[-1] in HEB_FINALS:
            end += 1
    return start, end


def arabic_article_stats(text):
    """In logical order Arabic words begin with the article ال often; reversed, they end with لا."""
    start = end = 0
    for w in re.findall(r"[\u0621-\u064a]+", text):
        if len(w) > 3 and w.startswith("\u0627\u0644"):
            start += 1
        if len(w) > 3 and w.endswith("\u0644\u0627"):
            end += 1
    return start, end


def rtl_reversed_suspected(text, code):
    if code == "he":
        s, e = final_letter_stats(text)
        return s >= 20 and s > 2 * max(e, 1)
    if code == "ar":
        s, e = arabic_article_stats(text)
        return e >= 10 and e > 2 * max(s, 1)
    return False


def fix_visual_line(line):
    """Reverse a line stored in visual order, keeping digit and Latin runs readable."""
    rev = line[::-1]
    return re.sub(r"[A-Za-z0-9][A-Za-z0-9.,:/%-]*", lambda m: m.group(0)[::-1], rev)


def analyse(text):
    counts = {}
    for ch in text:
        if ch.isalpha():
            sc = script_of(ch)
            if sc:
                counts[sc] = counts.get(sc, 0) + 1
    if not counts:
        return {"language": "unknown", "scripts": {}, "rtl_reversed_suspected": False}
    label, code = code_for(counts, text)
    return {
        "language": label,
        "dominant": code,
        "scripts": counts,
        "rtl_reversed_suspected": rtl_reversed_suspected(text, code),
    }


def backup_once(path):
    bak = path + ".orig"
    if not os.path.exists(bak):
        shutil.copyfile(path, bak)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--txt", default="/tmp/reading/book.txt")
    ap.add_argument("--normalize", action="store_true")
    ap.add_argument("--fix-rtl", action="store_true")
    a = ap.parse_args()

    text = open(a.txt, encoding="utf-8").read()
    info = analyse(text)

    if a.normalize or a.fix_rtl:
        backup_once(a.txt)
        text = normalize(text, info.get("dominant"))
        if a.fix_rtl:
            if info.get("dominant") not in ("he", "ar"):
                sys.exit("ABORT: --fix-rtl only applies to Hebrew or Arabic text")
            text = "\n".join(fix_visual_line(l) for l in text.split("\n"))
            if rtl_reversed_suspected(text, info["dominant"]):
                print("WARNING: text still looks reversed after the fix; the file was written, but check it", file=sys.stderr)
        open(a.txt, "w", encoding="utf-8").write(text)
        info = analyse(text)
        info["edited"] = True
    print(json.dumps(info, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
