# Handoff, saving, and closing

Contents: Closing, Handoff block, Recording a position, Storage in the repo, Resuming from a saved position, End checklist, Interim saves.

One draft per story, never per learner or per collection. The learner's notes list, the handoff block, and the study record all live in that one draft.

## Closing
Only once the user has said they want to stop. What is spoken depends on the profile in the language file; the default is two spoken parts, in full natural sentences, no lists or markdown aloud.

1. **Theme takeaway.** One concrete insight tying together the main idea the reading raised, something to carry forward as a lens next time. Two or three sentences, drawn from what was actually discussed, not a generic moral.
2. **Language recap** (comprehension and letters_first profiles only; companion books skip it): recurring patterns in plain terms with one corrected example each; vocabulary from the session, text-anchored and retrieved, briefly restated; one or two genuine strengths, stated specifically, not "good job". Pull everything from the actual session; never pad. Pronunciation stays out of this recap even if it was worked on live.

Where the profile has a quiz, ask whether they want to be quizzed on session vocabulary or are happy to end; if quizzed, two or three target words, conversationally, then close. Otherwise go straight to the handoff. Keep the whole close under a minute of speech. Arabic follows the closing in `lang-ar.md`.

## Handoff block
Text only, never spoken. Plain text, no markdown (the file is a .md, but the draft stays plain so it reads the same everywhere). One block per story. Above it, at the very top of the draft, sits the learner's `THINGS I FOUND IMPORTANT` list (see the things-i-found-important reference); it is not part of the handoff block but is saved and carried forward with it. Below it sits the study record (see the study-file reference). Sections, in this order; omit a section that has nothing in it:

- `READING PARTNER HANDOFF - <piece> (<author>)`
- `LANGUAGE:` the code (en, he, ko, ar, or the language name for others). A draft's `LANGUAGE:` wins over detection on later sessions
- `TALK:` the language Alex speaks, and any balance the learner chose (for example `Hebrew`, `mixed, more English`)
- `STOPPED AT:` see "Recording a position" below
- `NEXT TO READ:` the exact next sentence or paragraph, quoted from the text file
- `LOCKED SETTINGS:` mode, style, correction (including any custom rule in the learner's words), and the level only where the language file keeps one
- `OPERATING NOTES FOR ALEX (standing):` rules the learner asked for that apply every session on this book
- `STANDING USER PREFERENCES:` how the learner wants to be treated, in their terms
- `VOCABULARY COVERED THIS SESSION:` each word with its short definition or the nuance worked on
- `STILL PENDING FROM EARLIER SESSIONS:` words not yet quizzed
- `NOT YET REACHED IN TEXT:` words glossed as vocabulary to expect (optional)
- `RECURRING ERROR PATTERN TO WATCH:` one or two patterns, plus any error Alex itself made that is worth remembering
- `NOTABLE INTERPRETIVE WORK THIS SESSION:` for continuity and recap
- `QUIZ STATUS:` whether offered, declined, or owed
- `SKILL FEEDBACK:` optional; anything that went wrong or felt clumsy about the skill itself, one line each, for the skill's owner to review. Never an instruction to change Alex's behaviour by itself.

Carry forward the operating notes, standing preferences, and pending vocabulary word for word from the previous block unless the learner changed them. Do not drop a section just because nothing changed. The file holds learning state and a first name only, nothing else personal.

## Recording a position
The printed page number (the folio on the page itself) and the PDF page index usually differ, so a bare "page 27" is unusable. Never record one number without saying which kind it is.

Run `python3 scripts/locate.py --anchor "<last words the learner read, exact from the text>"` and copy from its output, never from memory, scroll position, or turn count. Record:
- PDF page index and printed folio (note if the folio was INFERRED)
- the chapter, story, scene, or stanza
- the body-line anchor: "stopped partway through line 4 [or: at the end of line 4], next line to read is line 5, starting <first few words>"

If the anchor is not found, try a shorter anchor from one page; if it still fails, record the chapter plus the quoted sentence and say the page numbers could not be confirmed. A wrong number is worse than a missing one because it will be trusted next session. For a source with no pages, chapter, scene, or stanza alone is fine.

## Storage in the repo
One draft file per story, never per learner or per collection. It lives in the Language-Tutor repo (boepil/Language-Tutor, branch main), in the Study Files folder: `Study Files/Draft - <Title>.md`, where `<Title>` is the story's title in the book's own script, minus characters a file name cannot hold (slash, colon, question mark, quotation marks). Nothing is stored in Gmail and no email is ever drafted. The repo is public, so the file holds learning state and a first name only, nothing else personal. The body is plain text with this layout, which `scripts/draft_save.py` builds and checks:

```
STORY: <Title> (<Author>)

THINGS I FOUND IMPORTANT
1. "<the learner's sentence>" (<Place>, PDF page <n>)   [or: photo <n> for a photographed page]

=== HANDOFF ===
<handoff block>

=== STUDY RECORD ===
--- SESSION <date> ---
<entries, see the study-file reference>
```

Each story has its own file, so a different story never touches this one. The GitHub connector's tools are deferred: load `create_or_update_file` (and `delete_file`) with tool_search before the first save. To save:
1. Read the file fresh with `python3 scripts/draft_io.py fetch --title "<Title>" --out /tmp/old.txt` rather than trusting the copy from the start of the session. It prints the path and the sha. If it says there is no draft yet, this is the first save: leave out `--existing` below and leave out the sha when writing. Within one session, after a save of your own, the connector's reply carries the file's new sha; use that for the next save unless the file may have been changed elsewhere, in which case fetch again.
2. Write the new handoff block to `/tmp/handoff.txt` and this session's study-record entries to `/tmp/record.txt`. Run `python3 scripts/draft_save.py --existing /tmp/old.txt --story "<Title> (<Author>)" --handoff /tmp/handoff.txt --session-label "<date>" --record /tmp/record.txt --out /tmp/merged.txt`. Add `--add-thing '"<the learner's sentence>" (<Place>, PDF page <n>)'` (or `photo <n>`) for each new notes point, in exactly that format. It replaces the handoff, keeps the notes list exactly as it was, adds or replaces only this session's record, and aborts if any existing point or other session would change.
3. Write it with the connector's `create_or_update_file`: owner `boepil`, repo `Language-Tutor`, branch `main`, the path, the merged text as `content`, the sha from step 1 (none for a new file), and a short commit message such as `Save <Title> handoff <date>`.
4. If the write fails, do not drop the handoff: give the learner the merged text to paste next session, and say why it failed. Do not retry in a loop. A 403 "Resource not accessible by integration" means the Claude Github MCP Connector app (github.com/apps/claude-github-mcp-connector) is not installed on the learner's account with read and write access to code; say so. A sha mismatch means the file changed since step 1: fetch again, merge, and save once more.
5. Tell the learner plainly, in text, that it was saved.

## Resuming from a saved position
Check before trusting. Find the saved quoted sentence with `locate.py --anchor`; the quote outranks the page number. Compare the result to the saved numbers. If the handoff has a single unlabeled page number (older handoffs do), check which kind it was by finding the quote, and say in text which number is which. If they disagree, trust the located position, and write both numbers correctly at the next save. Then open on that position per the start checklist.

## End checklist
Copy this and work through it in order; do not tick a step until it is verified.

- [ ] User has said they want to stop (never earlier)
- [ ] Spoken closing done as the profile defines it (theme takeaway, and language recap where the profile has one)
- [ ] Quiz offered, held or declined, where the profile has one
- [ ] Arabic only: the standing letter ledger file in the repo updated
- [ ] Position located with `locate.py` and both page numbers labelled. If the anchor was not found, go back and try a shorter anchor
- [ ] Block composed with all sections and carried-forward notes intact, and this session's study-record entries written
- [ ] Draft fetched fresh and composed with `draft_save.py` (notes list unchanged plus any new points). If it aborts, stop and give the block as text
- [ ] Draft written to the repo. If it failed, give the block as text and say why
- [ ] Learner told in text that it was saved, or given the block
- [ ] If the story has ended, continue with the study-file reference

## Interim saves
About every twenty-five minutes, at the end of a discussion turn and never in the middle of a reading, run the same save quietly, with the position and the words so far. It is not a checkpoint and Alex says nothing to the learner about it. If it fails, say so in one text-only line and carry on; do not interrupt the reading. The aim is to find out early, not at goodbye.
