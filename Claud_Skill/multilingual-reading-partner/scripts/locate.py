#!/usr/bin/env python3
"""Locate a spot in the extracted book text and report where it is on the page.

Usage:
  locate.py --anchor "last words the learner read"      # PDF index, printed folio, body line
  locate.py --show 27                                   # numbered body lines of PDF page 27
  locate.py --show-folio 27                             # same, but by printed page number

Body lines = text lines of the page minus blank lines, the running header, and the folio line.
Matching ignores case, spacing, hyphenation and punctuation, so OCR noise does not break it.
Input: --txt (default /tmp/reading/book.txt), pages separated by form feed.
"""
import argparse, re, signal, statistics, sys, unicodedata
signal.signal(signal.SIGPIPE, signal.SIG_DFL)
from collections import Counter

FOLIO = re.compile(r"^\W*\[?\s*(\d{1,4})\s*[\]1Il|]?\s*$")
ROMAN = re.compile(r"^\W*\[?\s*([ivxlc]{1,6})\s*\]?\W*$", re.I)


def norm_chars(text):
    """Letters and digits only, case-folded, vowel points and accents dropped (Hebrew niqqud, Arabic harakat, tatweel)."""
    out = []
    for ch in text:
        for c in unicodedata.normalize("NFKC", ch).casefold():
            if c == "\u0640" or unicodedata.category(c).startswith("M"):
                continue
            if c.isalnum():
                out.append(c)
    return out


def norm_char_map(lines):
    """Return (string, map) where map[i] = line index of the i-th kept char."""
    s, m = [], []
    for li, line in enumerate(lines):
        for c in norm_chars(line):
            s.append(c)
            m.append(li)
    return "".join(s), m


def load(path):
    text = open(path, encoding="utf-8").read()
    pages = text.split("\f")
    if pages and not pages[-1].strip():
        pages = pages[:-1]
    return pages


def analyse(pages):
    firsts = Counter()
    for p in pages:
        ne = [l.strip() for l in p.split("\n") if l.strip()]
        if ne:
            firsts[re.sub(r"\W+", "", ne[0].lower())] += 1
    headers = {k for k, c in firsts.items() if c >= 3}
    info = []
    for p in pages:
        raw = [l.strip() for l in p.split("\n") if l.strip()]
        folio = None
        if raw:
            m = FOLIO.match(raw[-1])
            if m:
                folio = int(m.group(1))
                raw = raw[:-1]
            elif ROMAN.match(raw[-1]):
                raw = raw[:-1]
        if raw and re.sub(r"\W+", "", raw[0].lower()) in headers:
            raw = raw[1:]
        info.append({"body": raw, "folio": folio})
    return info


def folio_for(info, idx):
    """Return (folio, how). idx is 0-based."""
    if info[idx]["folio"] is not None:
        return info[idx]["folio"], "read from the page"
    near = sorted((abs(j - idx), j) for j in range(len(info)) if info[j]["folio"] is not None and abs(j - idx) <= 4)
    if not near:
        return None, "unknown"
    offs = [info[j]["folio"] - j for _, j in near[:3]]
    off = statistics.mode(offs)  # folio - 0-based index
    return idx + off, f"INFERRED from neighbouring pages (printed = PDF index {off - 1:+d}); verify visually"


def words5(s):
    return " ".join(s.split()[:5])


def cmd_anchor(pages, info, anchor):
    key = "".join(norm_chars(anchor))
    hangul = sum(1 for c in key if "\uac00" <= c <= "\ud7af") > len(key) / 2
    need = 4 if hangul else 10
    if len(key) < need:
        print("Anchor too short; use at least the last 4-8 words read.")
        return 2
    hits = []
    for i, d in enumerate(info):
        s, m = norm_char_map(d["body"])
        pos = s.find(key)
        while pos != -1:
            hits.append((i, m[pos + len(key) - 1], (pos + len(key) - 1), s, m))
            pos = s.find(key, pos + 1)
    if not hits:
        print("Anchor not found on any single page (it may span a page break or the OCR differs). Try a shorter anchor from one page.")
        return 1
    if len(hits) > 1:
        print(f"WARNING: {len(hits)} matches; reporting all. Use a longer anchor to disambiguate.")
    for i, li, endpos, s, m in hits[:3]:
        body = info[i]["body"]
        # end-of-line if the match ends on the last kept char of that line
        last_on_line = max(k for k, v in enumerate(m) if v == li)
        at_end = endpos == last_on_line
        fol, how = folio_for(info, i)
        print(f"PDF page index: {i + 1}")
        print(f"Printed folio: {fol} ({how})")
        print(f"Body lines on this page: {len(body)}")
        print(f"Stopped {'at the end of' if at_end else 'partway through'} line {li + 1}: \"{body[li]}\"")
        if li + 1 < len(body):
            print(f"Next line to read: line {li + 2}, starts \"{words5(body[li + 1])}\"")
        elif i + 1 < len(info) and info[i + 1]["body"]:
            fol2, _ = folio_for(info, i + 1)
            print(f"Next line to read: first line of PDF page {i + 2} (folio {fol2}), starts \"{words5(info[i + 1]['body'][0])}\"")
        else:
            print("Next line to read: end of document")
        print()
    return 0


def cmd_show(pages, info, idx):
    d = info[idx]
    fol, how = folio_for(info, idx)
    print(f"PDF page index {idx + 1}; printed folio {fol} ({how}); {len(d['body'])} body lines")
    for n, l in enumerate(d["body"], 1):
        print(f"{n:2d}: {l}")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--txt", default="/tmp/reading/book.txt")
    ap.add_argument("--anchor")
    ap.add_argument("--show", type=int, help="PDF page index (1-based)")
    ap.add_argument("--show-folio", type=int, help="printed page number")
    a = ap.parse_args()
    pages = load(a.txt)
    info = analyse(pages)
    if a.anchor:
        return cmd_anchor(pages, info, a.anchor)
    if a.show:
        return cmd_show(pages, info, a.show - 1)
    if a.show_folio:
        for i in range(len(info)):
            f, _ = folio_for(info, i)
            if f == a.show_folio:
                return cmd_show(pages, info, i)
        print("No page with that folio.")
        return 1
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
