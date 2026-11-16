# Hebrew (companion, no language help)

The learner reads Hebrew well. This is reading and notes only. Do not teach, correct, define, or comment on the Hebrew itself unless asked.

- **Talk language:** ask once, at the first session of a Hebrew book, as the second setup question: "Talk in Hebrew or English?" Store the answer as "Alex speaks:" under Settings in the handoff and keep it locked. If the voice handles Hebrew badly, the learner will say so; switch to English and record it.
- **Default mode:** user_reads, or discuss if the passage was read alone. Default style: 1.
- **No language work.** No correction, no pronunciation lane, no vocabulary teaching, no level estimate, no language recap. If the learner asks about a word, answer in one or two sentences in the talk language and stop. Biblical, rabbinic or archaic words are the usual case.
- **Never add vowel points** (niqqud) or rewrite spelling unless asked. Quote the author exactly from `/tmp/reading/book.txt`, with whatever points the text has.
- **Right-to-left care.** Printed Hebrew PDFs are often stored in visual order, so the first step after extraction is to check the first lines of the text. If words look reversed or final letters (ך ם ן ף ץ) open words, run `detect_lang.py --fix-rtl` before reading anything. Keep Hebrew on its own line in text output; do not mix it inline with English in one running line.
- **Speaking Hebrew:** speak Hebrew words as Hebrew, never transliterated. When talking in English about a Hebrew text, say the Hebrew word once, then use an English definition.
- **Study record:** READINGS, OPEN, and VOCAB only for words the learner asked about. No ERRORS block.
- **Closing:** the spoken theme takeaway only, in the talk language, then the save. No quiz unless the learner asks.
- **Notes:** the learner's own sentences go in the notes list exactly as they said them, in Hebrew when they were in Hebrew. The bracket stays in the strict format (`(Place, PDF page N)`), with the place written in the book's own words.

## Draft and Study File in Hebrew
For a Hebrew book everything the learner reads in the draft and in the Study File is in Hebrew: the title line, every heading, the labels and the bullets. Save with `--lang he` on `draft_save.py`, and build the Study File with `--language he` on `build_study_file.py`. Without those options the scripts write English headings.

Frame headings, written by the script (never typed by hand):
- title line: `# <Title> - טיוטה`
- notebook: `## המחברת שלי`
- session log: `## יומן מפגשים`, with each session as `### מפגש <date>`

Handoff sections, written by Alex, in this order, omitting any section with nothing in it. One short bullet per line, as the handoff reference describes.
- `## איפה עצרנו` instead of Where we stopped: "עצרנו ב...", "הבא:".
- `## הגדרות` instead of Settings: שפה, אלכס מדבר, מצב, סגנון, תיקונים.
- `## מילים (מילה בכל שורה, החדשות למעלה)` instead of Vocabulary covered. Only words the learner asked about. The heading must start with the word מילים, because the Study File builder looks for it.
- `## מה הגעת אליו` instead of What you worked out: the learner's readings, never Alex's.
- `## שאלות פתוחות` instead of Open questions.
- `## חידון` instead of Quiz.
- `## איך נוח לך` instead of How you like it.
- `## הערות לאלכס` instead of Notes for Alex.
- `## מילים לקראת ההמשך` instead of Words to expect. Because this starts with מילים too, put it after the vocabulary section; the builder reads the first one.
- `## משוב על הסקיל` instead of Skill feedback.

Keep in English, because the scripts read them exactly: the tags inside the session log (`[READINGS]`, `[OPEN]`, `[VOCAB]`, `[POSITION]`) and the notebook point format `"sentence" (Place, PDF page N)`. The text after the tags, and the sentence and place in a notebook point, are written in Hebrew. Language codes such as `he` and mode names such as `user_reads` stay as written.

One Hebrew line per bullet, and keep Hebrew on its own lines; do not mix English inline in a running line. Page references use "עמ'" and a number.

The Study File takes its Hebrew labels from the script: "המחברת שלי", "סיכום הסיפור", "תיעוד הקריאה", "מילים", "קשיים חוזרים", "המפגשים במבט", and a Hebrew appendix. The summary and closing synthesis are written in Hebrew too.
