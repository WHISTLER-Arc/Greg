# Approved translations, work in progress

Raw record of the Dutch and Portuguese lines, kept here rather than in a
temporary directory because a session ending should not cost a day of review.

Most of it is reviewed and signed off by WHISTLER-Arc, who is a native speaker
of both. EXISTENTIAL 13-24 is not, and is marked NOT SIGNED OFF at its batch
header. Sign-off is not a formality. These lines are not translations, the
register has to be found natively, and a non-native draft can be word-perfect
and still not land.

Drafts are committed while still unsigned, so a session ending does not lose
them, but an unsigned line is a proposal and never counts toward the signed
total. SILENCE is not started.

These are not translations of the English. Each line was written natively and
then corrected, which is why the wording often diverges. See
custom_components/greg/lines/TEMPLATE.py for why that matters.

## State

                 drafted    signed off
    SOFT         50 of 50   50 of 50   complete
    MEDIUM       50 of 50   50 of 50   complete
    CHAOS        50 of 50   50 of 50   complete
    EXISTENTIAL  24 of 50   12 of 50   13-24 awaiting WHISTLER-Arc
    SILENCE       0 of 50    0 of 50

    174 of 250 drafted, 162 of 250 signed off

Counting NL and PT as separate lines, which is how the 500 figure is reached,
that is 348 of 500 drafted and 324 of 500 signed off. Only the signed-off
count is a real number. The other 24 lines are provisional.

## English corrections still to apply to lines/en.py

Reviewing the translations turned up four English lines worth changing. These
have not been applied yet.

Indices are en.py list indices, one-based, verified against the file. Each
phrase matches exactly one line, so match on the text and treat the index as
the check rather than the lookup.

    SOFT   idx 21  "Oh. Just the one."           -> "Oh. Just the one?"
    CHAOS  idx 19  "a moment of stillness"       -> "a moment of peace"
    CHAOS  idx 22  "I have now seen peak chaos." -> "I have now seen it."
    CHAOS  idx 24  "I did not pack for this."    -> "I did not dress for this."
    CHAOS  idx 32  gains a fourth sentence, full replacement below
    CHAOS  idx 43  second and third sentences replaced, full text below
    EXIST  idx  4  "happened on top of me" -> "happened around me"

CHAOS 32 in full, from the batch 3 review. Note the straight apostrophe in
"I'm". en.py uses straight apostrophes throughout, fourteen of them and no
curly ones, so the curly form must not be pasted in.

    I would like to register a complaint. I have nowhere to register it. So
    I'm registering it here. Not that it will make any difference.

CHAOS 43 in full, from the batch 4 review.

    I am at capacity. My capacity was never large enough. It never will be.

## Numbering does not match en.py. Read this before assembling the pools.

The numbers in these files are batch numbers, not en.py indices. Checked line
by line against lines/en.py. Every English line in SOFT and MEDIUM has exactly
one translation, nothing is missing and nothing is doubled, but the numbering
diverges from en.py in two places and assembling by position would misfile it.

    SOFT      1-36    permutation, NOT positional
                      batch 1 is en 1,2,4,7,13,15,17,22,25,26,27,35
                      batch 2 is en 3,5,6,8,9,10,11,12,14,16,18,19
                      batch 3 is en 20,21,23,24,28,29,30,31,32,33,34,36
    SOFT     37-50    positional
    MEDIUM    1-28    positional
    MEDIUM   29-36    off by one, md 29-36 are en 30-37
    MEDIUM  recovered en 29
    MEDIUM   37-49    off by one, md 37-49 are en 38-50
    CHAOS     1-50    positional throughout

Both files now hold exactly 50 entries per language, all distinct.

Three defects that came out of this check have been fixed in place:

  1. soft-approved.md batch 3 said "line 26 English changed". That is batch
     number 26, which is en.py SOFT index 21. The note now names index 21, so
     the correction cannot land on the wrong line.

  2. medium-approved.md labelled the recovered line "English index 28". It is
     index 29. Index 28 is "You are doing things. Repeatedly. Near me." which
     already had its translation at batch number 28. Note corrected.

  3. medium-approved.md batch number 50 was a byte-identical copy of batch
     number 36, both en MEDIUM index 37. It translated no English line of its
     own and would have failed the CI duplicate check. Removed. MEDIUM is
     still 50 of 50, and index 37 keeps its translation at batch number 36.

## Next

Draft EXISTENTIAL and SILENCE in batches of twelve, each batch reviewed and
signed off before the next is drafted. Then fold everything into lines/nl.py
and lines/pt.py, apply the English corrections, and only then cut a beta.

Nothing unsigned goes into nl.py or pt.py. Once a line is in the pool it ships,
and there is no review step after that. The filenames still say approved, which
is true of most of their contents but not all, so check the sign-off boundary
noted at the top of each file rather than trusting the name.

When folding in, map by English text rather than by batch number, and assert
fifty distinct lines per pool per language before committing.
