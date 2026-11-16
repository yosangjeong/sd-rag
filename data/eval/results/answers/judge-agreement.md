# Judge vs a reference grading (20 answers, v6)

20 answers of the v6 answer run (labor 100 + real estate 82), seeded draw: 10 the v2 judge graded correct, 10 it graded partial / wrong. Reference grades by Claude Code (the AI coding assistant this project was built with; Claude is used nowhere in the pipeline), 2026-11-13, made before looking at the judge's grade, against the gold passage and the statutes themselves (an answer stating a rule from another article of the corpus is checked there). This is a better-informed model's reading, not a human one.

| # | qid | reference | judge v1 | judge v2 | note |
|---|---|---|---|---|---|
| 1 | r0176 | correct | wrong | wrong | the question asks about inspecting a broker: form 26 is right; the reference is the association form 27 |
| 2 | g0218 | partial | partial | partial | gives the repealed 2 days next to the current 4 |
| 3 | g0175 | correct | correct | correct |  |
| 4 | g0257 | correct | correct | correct |  |
| 5 | r0020 | correct | partial | partial | the exemption / 50% reduction and the exclusions are in the decree |
| 6 | g0207 | correct | correct | correct |  |
| 7 | r0141 | correct | partial | partial | the early-sale rule is in the same decree item |
| 8 | g0279 | partial | wrong | wrong | gives next year's $9.85 (also in the corpus) instead of the current $9.55 |
| 9 | r0084 | correct | partial | partial | item (G), no effect on other loan terms, is in the statute |
| 10 | g0330 | correct | correct | correct |  |
| 11 | g0223 | correct | correct | correct |  |
| 12 | r0146 | correct | partial | correct |  |
| 13 | r0133 | correct | partial | partial | grounds 5 and 6 (respondent refuses, applicant does not appear) are in the same paragraph |
| 14 | r0182 | correct | correct | correct |  |
| 15 | g0308 | correct | wrong | wrong | corrects the question's reversed premise; lists the right data |
| 16 | g0631 | correct | partial | partial | the prior deliberation is in 시행령 제13조의4 |
| 17 | r0038 | correct | correct | correct |  |
| 18 | r0111 | correct | wrong | wrong | right: the 100 is a conversion multiplier, not a cap (reference flagged) |
| 19 | g0413 | correct | correct | correct |  |
| 20 | g0167 | correct | correct | correct |  |

Agreement: judge v1 10/20, judge v2 11/20. Every disagreement is the judge being stricter than the reference grade; none the other way.

- Judge said correct (10): the reference agrees 10 of 10.
- Judge said partial / wrong (10): the reference says correct for 8, partial for 2 (the judge's wrong for g0279 is a partial).
- Cause: the judge sees the question, the reference and the gold passage only, so a correct rule the answer takes from another article (the decree's exemption, a later item of the same list) reads as invented. The groundedness judge, which sees the cited sources, rated all 8 of them supported.
- So the correctness figures are a lower bound. Scaling by this sample (judge-correct kept, 8 of 10 judge-non-correct correct), v6's 141 of 182 judge-correct becomes about 174 of 182 (95%); with 10 items behind the 8/10 the interval is wide (roughly 85-98%).
- Comparisons between versions and systems stand: all are graded by the same judge, and the strictness is the same for all. For the Claude / ChatGPT comparison the non-correct grades of all three systems are read again the same way.

# Human grading (20 answers, v8, 2026-11-16)

20 answers of the v8 answer run, seeded draw (10 the v2 judge graded correct, 10 not), graded by the user on the grading page. Reading them against the statutes first showed that 9 items had a faulty reference answer or gold quote (a bare list item without the sentence naming who holds the power, a reference listing 4 of 6 grounds, an amendment not yet in force as gold, ...); the page then showed every gold as its whole article and the corrected references, and the user graded against those. One question was garbled and left out (r0178). "judge v2" is the run's grade (old references, gold quote only); "judge, corrected" is the same judge prompt given the corrected reference and the whole article(s).

| # | qid | human | judge v2 | judge, corrected | Claude Code | note |
|---|---|---|---|---|---|---|
| 1 | g0589 | correct | wrong | partial | partial | Act gives the power to the Minister, the decree delegates it to the regional office; human reads the question literally (boundary case) |
| 2 | g0279 | correct | wrong | wrong | partial | leads with next year's $9.85 and calls the current $9.55 'was'; human: correct but misleading (fixed since by the future-date rule) |
| 3 | g0274 | no_answer | wrong | wrong | no_answer | retrieval missed 별표 2 (found since, v11); judge labels it wrong, not no_answer |
| 4 | r0118 | correct | correct | correct | correct |  |
| 5 | r0133 | correct | partial | correct | correct | reference listed 4 of the 6 grounds (corrected) |
| 6 | g0571 | correct | correct | correct | correct |  |
| 7 | g0201 | correct | partial | correct | correct | the question asks only for the years |
| 8 | r0066 | correct | partial | correct | correct | reference said what is refunded, not when (corrected: within 15 days) |
| 9 | g0437 | correct | correct | correct | correct |  |
| 10 | g0364 | partial | correct | partial | correct | says 'by the confirmation report deadline' without the date (the 15th of the next month); human: partial |
| 11 | r0073 | correct | correct | correct | correct |  |
| 12 | g0246 | correct | correct | correct | correct |  |
| 13 | r0178 | invalid | partial | partial | partial | question garbled (flagged); left out |
| 14 | r0082 | partial | partial | partial | partial | 'Yes, a landlord may not ...': yes/no reversed, protected-class condition dropped |
| 15 | r0137 | correct | correct | correct | correct |  |
| 16 | g0136 | correct | correct | correct | correct | gold was the amendment taking effect 11-27 (same text in force today) |
| 17 | g0170 | correct | correct | correct | correct | reference and gold named different ones of five reasons (corrected: any one) |
| 18 | g0395 | wrong | wrong | wrong | no_answer | the cited list items of Article 39(3) are split from its lead-in with the amount; answer says the amount is not given |
| 19 | g0330 | correct | partial | partial | correct | gold was the amendment not yet in force, reference had 1 of 2 kinds (corrected) |
| 20 | g0394 | correct | correct | correct | correct |  |

Agreement with the human grade (19): judge v2 11, judge with corrected references and whole articles 15, Claude Code 15. Correct vs not: 12 -> 16 (Claude Code 16). The human graded 15 of 19 correct, the judge 10, 12 after the corrections: the judge is stricter, and half its disagreements came from the faulty references, not from the judge.

The four left after the corrections: g0589 and g0279 are boundary cases the human graded more leniently (and Claude Code, too, graded partial); g0274 is a label (wrong vs no_answer, both not correct); g0330 the judge marks down for a detail taken from another cited source than the gold article, the weakness judge v3's pooled spans address.

Judge v4's passage (`eval/judges.wide_passage`, 2026-11-16: the gold chunks widened to the
run under the same heading and one chunk on each side, built automatically) on the same 19
with the corrected references: 14 agree with the human, against 15 with the passages picked
by hand per item (`data/raw/scratch/judge-check/rejudge_wide.py`, local). On the 80 grades
of the one-file comparison it agrees with the hand-read grades 68 times, against 65 with the
gold article only (`data/eval/single_file/README.md`). The corrected references are now in
`data/eval/reference_fixes.json`, which `eval/answers.py` uses.
