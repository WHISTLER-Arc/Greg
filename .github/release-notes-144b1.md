Test build. Not for general use.

Fixes the settings column jumping back to its old values after you press Apply.

## What was wrong

Two faults stacked on each other.

The coordinator updated its own copy of the config on reload but never told the
entities to re-read their attributes. The entities survive a reload rather than
being recreated, so nothing prompted them, and the settings the panel reads are
published from there. Home Assistant went on serving the values as they were
before your change, and the panel read those and wrote them straight back over
what you had just set.

Underneath that, updating a config entry schedules its listeners rather than
waiting for them, so the service call can return before the new values are
published at all. Even with the first fix, the panel could refresh in that gap
and stamp the old values back. It now holds what it sent until the published
config agrees, with a timeout so a failed write cannot leave the form stuck.

## What to check

Nudge the volume, press Apply, and watch whether the slider stays where you put
it. Same with the quiet hours toggle. Then reload Greg from the integration
page and confirm the values survived.
