#!/usr/bin/env python3
"""Fetch a book PDF (from the Language-Tutor repo, or an attached file) and extract its text.

Usage:
  get_book.py "loose title or author words"        # find in repo Books/, download, extract
  get_book.py --file "Exact Name.pdf"              # exact file name from the connector's Books/ listing
  get_book.py --pdf /mnt/user-data/uploads/x.pdf   # use an attached PDF instead of the repo
  get_book.py --list                               # list Books/ via the public API (can be rate-limited)

Writes <out>/book.pdf and <out>/book.txt (default out: /tmp/reading), pages separated by form feed.
The text is normalised (NFC, NFKC for Arabic, direction marks and soft hyphens removed) and its language reported.
Exit codes: 0 ok, 2 no/ambiguous match (candidates printed), 3 download failed, 4 no extractor.
Needs: pdftotext (poppler-utils). Fallback: PyMuPDF.
  install hints: apt-get install -y poppler-utils   |   pip install pymupdf --break-system-packages
"""
import argparse, json, os, re, shutil, subprocess, sys, unicodedata, urllib.parse, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import detect_lang

OWNER = os.environ.get("LT_OWNER", "boepil")
REPO = os.environ.get("LT_REPO", "Language-Tutor")
BRANCH = os.environ.get("LT_BRANCH", "main")
BOOKS_DIR = os.environ.get("LT_BOOKS_DIR", "Books")


def http_get(url, binary=False):
    req = urllib.request.Request(url, headers={"User-Agent": "reading-partner"})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read()
    return data if binary else data.decode("utf-8")


def list_books():
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{urllib.parse.quote(BOOKS_DIR)}?ref={BRANCH}"
    items = json.loads(http_get(url))
    return sorted(i["name"] for i in items if i["name"].lower().endswith(".pdf"))


def words(s):
    """Unicode-aware words: any script, vowel points and accents ignored."""
    s = unicodedata.normalize("NFKC", s).casefold()
    s = "".join(c for c in unicodedata.normalize("NFD", s) if not unicodedata.category(c).startswith("M"))
    return re.findall(r"\w+", s)


def match(books, query):
    q = words(query)
    if not q:
        return books
    hits = [b for b in books if all(any(w in bw for bw in words(b)) for w in q)]
    return hits


def extract(pdf, txt):
    if shutil.which("pdftotext"):
        subprocess.run(["pdftotext", "-layout", pdf, txt], check=True)
        return "pdftotext"
    try:
        import fitz  # PyMuPDF
    except ImportError:
        return None
    doc = fitz.open(pdf)
    with open(txt, "w", encoding="utf-8") as f:
        f.write("\f".join(p.get_text() for p in doc))
    return "pymupdf"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("query", nargs="?", default="")
    ap.add_argument("--pdf")
    ap.add_argument("--file", help="exact file name in Books/ (skips the listing call)")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--out", default="/tmp/reading")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    pdf = os.path.join(a.out, "book.pdf")
    txt = os.path.join(a.out, "book.txt")

    if a.pdf:
        shutil.copyfile(a.pdf, pdf)
        source = f"attachment:{os.path.basename(a.pdf)}"
    else:
        books = None
        if a.file:
            hits = [a.file]
        else:
            try:
                books = list_books()
            except Exception as e:
                print(f"Could not list {OWNER}/{REPO}/{BOOKS_DIR}: {e}\n"
                      "The public API may be rate-limited. List Books/ with the GitHub connector and rerun with --file \"<exact name>\", "
                      "or ask the learner to attach the PDF.")
                return 3
            if a.list:
                print("\n".join(books))
                return 0
            hits = match(books, a.query)
            if len(hits) != 1:
                print("No match." if not hits else "Ambiguous match.", "Candidates:")
                print("\n".join(hits or books))
                return 2
        name = hits[0]
        url = f"https://raw.githubusercontent.com/{OWNER}/{REPO}/{BRANCH}/{urllib.parse.quote(BOOKS_DIR)}/{urllib.parse.quote(name)}"
        try:
            with open(pdf, "wb") as f:
                f.write(http_get(url, binary=True))
        except Exception as e:
            print(f"Download failed for {name}: {e}\nAsk the learner to attach the PDF.")
            return 3
        source = f"{BOOKS_DIR}/{name}"

    tool = extract(pdf, txt)
    if tool is None:
        print("No PDF text extractor found. Install: apt-get install -y poppler-utils  or  pip install pymupdf --break-system-packages")
        return 4
    text = open(txt, encoding="utf-8").read()
    info = detect_lang.analyse(text)
    text = detect_lang.normalize(text, info.get("dominant"))
    open(txt, "w", encoding="utf-8").write(text)
    info = detect_lang.analyse(text)
    pages = text.split("\f")
    if pages and not pages[-1].strip():
        pages = pages[:-1]
    avg = len(text) / max(len(pages), 1)
    print(json.dumps({"source": source, "pdf": pdf, "txt": txt, "extractor": tool,
                      "pages": len(pages), "avg_chars_per_page": round(avg),
                      "language": info["language"], "rtl_reversed_suspected": info["rtl_reversed_suspected"]},
                     ensure_ascii=False, indent=2))
    if info["language"] in ("latin-other", "mixed", "unknown"):
        print("NOTE: language is not clear from the text. Ask the learner which language this is.")
    if info["rtl_reversed_suspected"]:
        print("NOTE: text looks stored in visual order. Run: python3 scripts/detect_lang.py --txt " + txt + " --fix-rtl")
    if avg < 300:
        print("WARNING: very little text per page. The PDF may be scans with no text layer; tell the learner.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
