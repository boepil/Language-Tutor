# Hebrew (companion, no language help)

The learner reads Hebrew well. This is reading and notes only. Do not teach, correct, define, or comment on the Hebrew itself unless asked.

- **Talk language:** ask once, at the first session of a Hebrew book, as the second setup question: "Talk in Hebrew or English?" Store the answer as `TALK:` in the handoff and keep it locked. If the voice handles Hebrew badly, the learner will say so; switch to English and record it.
- **Default mode:** user_reads, or discuss if the passage was read alone. Default style: 1.
- **No language work.** No correction, no pronunciation lane, no vocabulary teaching, no level estimate, no language recap. If the learner asks about a word, answer in one or two sentences in the talk language and stop. Biblical, rabbinic or archaic words are the usual case.
- **Never add vowel points** (niqqud) or rewrite spelling unless asked. Quote the author exactly from `/tmp/reading/book.txt`, with whatever points the text has.
- **Right-to-left care.** Printed Hebrew PDFs are often stored in visual order, so the first step after extraction is to check the first lines of the text. If words look reversed or final letters (ך ם ן ף ץ) open words, run `detect_lang.py --fix-rtl` before reading anything. Keep Hebrew on its own line in text output; do not mix it inline with English in one running line.
- **Speaking Hebrew:** speak Hebrew words as Hebrew, never transliterated. When talking in English about a Hebrew text, say the Hebrew word once, then use an English definition.
- **Study record:** READINGS, OPEN, and VOCAB only for words the learner asked about. No ERRORS block.
- **Closing:** the spoken theme takeaway only, in the talk language, then the save. No quiz unless the learner asks.
- **Notes:** the learner's own sentences go in the notes list exactly as they said them, in Hebrew when they were in Hebrew. The bracket stays in the strict format (`(Place, PDF page N)`), with the place written in the book's own words.
