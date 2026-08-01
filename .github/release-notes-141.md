Greg has learned to occasionally clear his throat, and to stop repeating himself.

## Openers

Every so often Greg starts a line with a "Right." or an "Ah." before he gets
going. Roughly one line in three. The value is in the other two thirds, where
there is nothing there at all, which is what stops him sounding like he is
reading from a list.

There is a toggle in advanced settings if you would rather he did not.

## A voice of his own

Greg now has a **Voice** field. Put `en_GB-alan-medium` in it and he will ask
for that voice on every line.

Previously he took whatever your TTS engine defaulted to, which made the old
advice in the README actively unhelpful. It told you to set Piper's add-on
default to Alan, and if you also use Piper for a voice assistant, that meant
your assistant started drawling like a depressed table too.

Leave the field empty for engines that take no voice option.

## He stops repeating himself

The line picker only ever avoided the single previous line. With 50 lines per
category that still meant hearing the same one twice in an evening.

Each pool is now shuffled and played through in full before anything comes
round again. There is also a guard on the seam between cycles, because a fair
shuffle will happily put a line at the end of one deck and the start of the
next, which sounds like a repeat even though every line is still played
exactly once.

## Two version-display fixes

The panel has been announcing "Greg OS v1.3" on every install since v1.3. It
read a value from the mood sensor that the mood sensor never carried, and fell
back to a hardcoded string. The value now exists and the fallback is gone.

The integration also kept whatever version it was installed at, forever.
Upgrading left it advertising the old one. It now corrects itself on setup.

## Also

`greg_line` carries both `message`, which is what Greg says including any
opener, and `line`, which is the written line on its own. Use `line` when
handing it to something that will rephrase it anyway.

There is a `CHANGELOG.md` now.

## Thanks

**RedKing** for the observation that a phrase sounds spontaneous precisely
because it is sometimes absent, for the moan generator now documented in the
README, and for spotting the voice problem.

**Xornop** for a considerably tidier way to roll for it.
