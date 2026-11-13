# Judge vs hand grading (20 answers, v6)

20 answers of the v6 answer run (labor 100 + real estate 82), seeded draw: 10 the v2 judge graded correct, 10 it graded partial / wrong. Graded by hand (Claude Code, 2026-11-13) before looking at the judge's grade, against the gold passage and the statutes themselves (an answer stating a rule from another article of the corpus is checked there).

| # | qid | hand | judge v1 | judge v2 | note |
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

Agreement: judge v1 10/20, judge v2 11/20. Every disagreement is the judge being stricter than the hand grade; none the other way.

- Judge said correct (10): hand agrees 10 of 10.
- Judge said partial / wrong (10): hand says correct for 8, partial for 2 (the judge's wrong for g0279 is a partial).
- Cause: the judge sees the question, the reference and the gold passage only, so a correct rule the answer takes from another article (the decree's exemption, a later item of the same list) reads as invented. The groundedness judge, which sees the cited sources, rated all 8 of them supported.
- So the correctness figures are a lower bound. Scaling by this sample (judge-correct kept, 8 of 10 judge-non-correct correct), v6's 141 of 182 judge-correct becomes about 174 of 182 (95%); with 10 items behind the 8/10 the interval is wide (roughly 85-98%).
- Comparisons between versions and systems stand: all are graded by the same judge, and the strictness is the same for all. For the Claude / ChatGPT comparison the non-correct grades of all three systems are read by hand the same way.
