# Study record, closing conversation, Study File

Contents: Study record, When a story ends, Closing conversation, Building the Study File, After the Study File.

## Study record
Kept silently from the first session of a story, text only, never spoken. It lives in the story's draft under the `=== STUDY RECORD ===` line and is saved with every handoff save (see the handoff reference). One block per session, headed `--- SESSION <label> ---`, where the label is the date. Each save writes the whole block for the current session; earlier sessions are never touched. Plain text, one entry per line, fields separated by ` | `. Do not put a vertical bar inside a field.

```
--- SESSION 2026-11-07 ---
[VOCAB]
word | folio | exact sentence from the book | meaning and notes | status
[ERRORS]
pattern | examples separated by semicolons
[READINGS]
place in the text | the learner's reading, in their words | where it landed
[OPEN]
a question left unresolved
[STRENGTHS]
one specific strength
[LETTERS]
letter | sound | shape notes | status      (Arabic only)
[POSITION]
folios covered this session, for example 33-35
```

What goes in, and why it matters: the Study File is built from this record, so anything not logged is lost.
- **VOCAB.** Words that were met, asked about, misread, or retrieved. Copy the sentence from `/tmp/reading/book.txt`, never from memory. Status is `unquizzed`, `right`, or `wrong`; update it when a quiz happens. The same word can appear in several sessions; the Study File merges them.
- **ERRORS.** Patterns, not one-off slips: what was swapped for what, with examples. Name the same pattern the same way each session so the counts add up.
- **READINGS.** The learner's own interpretations, and what changed. Quote their words. Where Alex corrected a misreading of the text, say so briefly under "where it landed". Never record Alex's own interpretation as if it were the learner's.
- **OPEN.** Questions neither side settled.
- **STRENGTHS.** Specific things (for example "caught two of Alex's misreadings"), never general praise.
- **LETTERS.** Arabic only: letters met this session, with sound, the shape taken in the page, and status (new, shaky, solid).
- **POSITION.** The folios covered, taken from `locate.py`.

## When a story ends
The story has ended when the learner has read its last line or says they are finished with it. Do the usual closing first (handoff reference), then the steps below. A collection is not one story: each story gets its own draft and its own Study File.

## Closing conversation
Ask, in speech: "What is this story about?" Let the learner answer in their own words, then ask follow-up questions that make them say more or defend a reading. Do not retell the story yourself. The summary in the Study File must follow how the dialogue actually went and what the text says, and must not be Alex's own account. Check any plot claim against `/tmp/reading/book.txt` before it goes in the summary.

Then write, in text only, a short draft summary and show it for correction. Fix whatever the learner says does not match their reading. This draft is the learner's to correct, so ask once and apply the corrections.

## Building the Study File
1. Write `/tmp/summary.txt`: the corrected summary, short, limited to what the text and the dialogue covered.
2. Write `/tmp/synthesis.txt`: the closing synthesis, built from the learner's own readings across the sessions. Include where they started and where they ended on the main threads, their closing line on the story in their own words, and threads worth carrying into the next piece. Do not add a fresh retelling.
3. Save the final draft body to `/tmp/draft_final.txt` (the draft fetched fresh from the repo with `scripts/draft_io.py fetch`).
4. Run `python3 scripts/build_study_file.py --draft /tmp/draft_final.txt --summary /tmp/summary.txt --synthesis /tmp/synthesis.txt --reader "<name>" --language "<code>" --level "<band>" --style "<style>" --source "<book, edition, folios>" --out "/mnt/user-data/outputs/Study File - <Story title>.md"`.
5. Read the result once. The order is: the learner's notes list, summary, closing synthesis, reading record, open questions, vocabulary, recurring problems, sessions at a glance. If something is empty or wrong, fix the draft body and rebuild; do not hand-edit the output.
6. Deliver it with `present_files`, and also save it in the repo as `Study Files/Study File - <Story title>.md` with the connector's `create_or_update_file`, next to the draft. Tell the learner in text that it is there.

## After the Study File
1. Have a short conversation about anything in the draft that belongs in the skill, starting with the `SKILL FEEDBACK` lines in the handoff block. Treat them as suggestions for the skill's owner and change nothing in the skill unless the learner asks.
2. Ask whether to delete the story's draft file, `Study Files/Draft - <Title>.md`. Delete it with the connector's `delete_file` (it needs the file's current sha from `draft_io.py fetch`) only on a clear yes. Never delete it before the Study File has been delivered and saved.
3. The next story starts from a fresh draft; nothing carries over from this one.
