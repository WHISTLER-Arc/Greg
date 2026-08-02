The settings column in Greg's panel works properly now. If you took 1.4.2 or
1.4.3, this is the one that makes it usable.

## Settings stayed where you put them, briefly

You could change the volume, press Apply, and watch the slider slide back to
where it had been. The quiet hours toggle did the same. The setting was
actually saved. The panel just went on showing you the old value, which is
arguably worse than not saving at all.

Two faults stacked on each other.

Greg updates his own copy of the config when he reloads, but never told his
entities to re-read their attributes. The entities survive a reload rather than
being recreated, so nothing prompted them, and the settings the panel reads are
published from there. Home Assistant carried on serving the values as they were
before the change, and the panel read those and wrote them back over the edit.

Underneath that, updating a config entry schedules its listeners rather than
waiting for them, so the service call could return before the new values were
published at all. Even with the first fix, the panel could refresh in that gap
and stamp the old values back. It now holds what it sent until the published
config agrees, with a timeout so a failed write cannot leave the form stuck.

## Thanks

Found and confirmed through a beta build before this went anywhere near a
release, which is the first time that has happened here and considerably better
than the alternative.
