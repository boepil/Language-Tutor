#!/usr/bin/env python3
"""Find and read a story's draft in the Language-Tutor repo (Study Files folder).

Drafts live in the repo, one file per story, never in Gmail:
  Study Files/Draft - <Title>.md           the story's draft (notes list, handoff, study record)
  Study Files/Letter Ledger - Arabic.md    the standing Arabic letter ledger

Usage:
  draft_io.py list                                   # titles of all drafts, most recently saved first
  draft_io.py fetch --title "Teaching to Transgress" --out /tmp/old.txt
  draft_io.py fetch --ledger --out /tmp/ledger.txt

fetch downloads the file fresh (a shallow clone, so no cache lag), writes its text to --out,
and prints JSON with the repo path and the blob sha. Pass that sha to the connector's
create_or_update_file when saving over the file; omit sha only for a file that does not exist yet.
Exit codes: 0 ok, 2 no draft or ambiguous match (candidates printed), 3 repo not reachable.
Needs git. The repo must be public for this read to work; if it is private, read the file
with the GitHub connector's get_file_contents instead.
"""
import argparse, json, os, re, shutil, subprocess, sys, unicodedata

OWNER = os.environ.get("LT_OWNER", "boepil")
REPO = os.environ.get("LT_REPO", "Language-Tutor")
BRANCH = os.environ.get("LT_BRANCH", "main")
FOLDER = os.environ.get("LT_STUDY_DIR", "Study Files")
CLONE = "/tmp/lt_clone"
LEDGER = f"{FOLDER}/Letter Ledger - Arabic.md"


def sh(*cmd, cwd=None):
    return subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True).stdout


def fresh_clone():
    shutil.rmtree(CLONE, ignore_errors=True)
    url = f"https://github.com/{OWNER}/{REPO}"
    try:
        try:
            sh("git", "clone", "--depth", "100", "--branch", BRANCH, "--filter=blob:none", "--sparse", url, CLONE)
            sh("git", "sparse-checkout", "set", FOLDER, cwd=CLONE)
        except subprocess.CalledProcessError:
            shutil.rmtree(CLONE, ignore_errors=True)
            sh("git", "clone", "--depth", "100", "--branch", BRANCH, url, CLONE)
    except subprocess.CalledProcessError as e:
        print(f"Could not reach {OWNER}/{REPO}: {e.stderr.strip()}\n"
              "Read the file with the GitHub connector's get_file_contents instead, or ask the learner to paste the draft.")
        sys.exit(3)


def words(s):
    s = unicodedata.normalize("NFKC", s).casefold()
    s = "".join(c for c in unicodedata.normalize("NFD", s) if not unicodedata.category(c).startswith("M"))
    return re.findall(r"\w+", s)


def drafts():
    d = os.path.join(CLONE, FOLDER)
    if not os.path.isdir(d):
        return []
    names = [f for f in os.listdir(d) if f.startswith("Draft - ") and f.endswith(".md")]

    def stamp(f):
        try:
            return int(sh("git", "log", "-1", "--format=%ct", "--", f"{FOLDER}/{f}", cwd=CLONE).strip() or 0)
        except (subprocess.CalledProcessError, ValueError):
            return 0
    return sorted(names, key=stamp, reverse=True)  # most recently saved first


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("action", choices=["list", "fetch"])
    ap.add_argument("--title")
    ap.add_argument("--ledger", action="store_true")
    ap.add_argument("--out")
    a = ap.parse_args()
    fresh_clone()

    if a.action == "list":
        print("\n".join(f[len("Draft - "):-3] for f in drafts()) or "(no drafts)")
        return 0

    if a.ledger:
        rel = LEDGER
    else:
        if not a.title:
            sys.exit("ABORT: fetch needs --title or --ledger")
        q = words(a.title)
        hits = [f for f in drafts() if all(any(w in fw for fw in words(f)) for w in q)]
        if len(hits) != 1:
            print("No draft matches." if not hits else "Ambiguous match.", "Candidates:")
            print("\n".join(f[len("Draft - "):-3] for f in (hits or drafts())) or "(no drafts)")
            return 2
        rel = f"{FOLDER}/{hits[0]}"
    full = os.path.join(CLONE, rel)
    if not os.path.isfile(full):
        print(f"No file at {rel} yet; this is a first save.")
        return 2
    sha = sh("git", "rev-parse", f"HEAD:{rel}", cwd=CLONE).strip()
    text = open(full, encoding="utf-8").read()
    if a.out:
        open(a.out, "w", encoding="utf-8").write(text)
    print(json.dumps({"path": rel, "sha": sha, "bytes": len(text.encode()), "out": a.out}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
