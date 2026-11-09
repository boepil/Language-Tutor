# Things I found important

Every story's draft has a section called `THINGS I FOUND IMPORTANT`. It sits at the very top of the draft, above the handoff block, and it belongs to the learner. Alex only keeps it.

Format in the draft (plain text, no markdown). The convention is strict, one line per point, and every point looks exactly like this:

```
THINGS I FOUND IMPORTANT
1. "Excitement is generated through collective effort." (Introduction, PDF page 12)
2. "Teaching is a performative act." (Introduction, PDF page 15)
```

The pattern is: number, a period, a space, the sentence in straight double quotation marks, a space, then in round brackets the place in the book (chapter, section or story part, as the book itself names it), a comma, and `PDF page <n>` (for a photographed page, `photo <n>` in place of `PDF page <n>`). The sentence stays in the language the learner said it in, whether that is English, Hebrew, Korean or Arabic. Nothing else goes on the line: no folio, no commentary, no extra context. `scripts/draft_save.py` refuses a point that does not match.

## Rules
1. When the learner says something like "add this to my notes", "put that in things I found important", or "that's a point for my notebook", add the sentence they give as a new numbered point.
2. Write the sentence word for word, in the learner's own choice of words. If it quotes the book, check the exact wording against the extracted text (`/tmp/reading/book.txt`) first and fix only transcription errors.
3. After the sentence add the bracket in the strict format: the place in the book, then `PDF page <n>` (or `photo <n>`). Get the page from `python3 scripts/locate.py --anchor "<words>"`, never from memory, and the place from the book's own heading nearest above the sentence (for example Introduction or Chapter 2). If the book has no heading there, use the story or part title.
4. Points stay in the order the learner added them. Never reorder, merge, shorten, rewrite, or remove a point unless the learner asks.
5. Add the point silently. Do not comment on it, do not ask a question about it, and do not nudge the learner to keep reading afterwards (top rule). No spoken confirmation, and skip the "tell the learner it was saved" step for this save. If the write fails, say so in one text-only line and give the list as text; do not retry in a loop.
6. Save it to the draft straight away, in the same turn, so nothing is lost if the call drops. Use the normal save in the handoff reference: re-read the draft fresh, then run `scripts/draft_save.py` with `--add-thing '"<sentence>" (<Place>, PDF page <n>)'` (keep the straight double quotes around the sentence; `photo <n>` for photos), which appends the point as the next number and leaves every earlier point untouched, then write the draft.
7. If the learner asks to hear the list, read it back one point at a time, in order. Speak it in sentence rhythm per the speech-first rules: number as a word, then the sentence, then the bracket as a short phrase with numbers spelled out (for example, "Introduction, PDF page twelve").
8. When the story is finished, the Study File is built with this list as its own section at the top, word for word, before the closing synthesis.
9. Carry the list forward unchanged at every save. It is never dropped from the draft, even if nothing was added in that session.
