Greg's panel had a settings column that contained one switch you already had,
and a note telling you to go and look somewhere else. It does something now.

## The settings column

Sensor, speaker, text to speech, volume, sensitivity and quiet hours, all
editable from his own panel. Change what you like and press Apply.

Changes are applied together on one button rather than saving as you go,
because writing to the config entry reloads him, and doing that on every
slider nudge would be unpleasant for both of you.

Everything else, thresholds, openers, his voice, still lives in the options
flow, and there is a link straight to it.

## Smaller things in the same area

Sensitivity has moved up out of advanced, since it is the setting people
actually adjust once he is running.

The quiet hours times fold away when quiet hours are off.

Uninstall has moved out of its full-width strip and into the settings column.

There is a `greg.set_options` service behind all of it, so the same settings
can be scripted.

## A version floor that was simply wrong

`hacs.json` demanded Home Assistant 2026.3.0. Nothing in Greg needs it. The
newest API he touches is `StaticPathConfig`, which arrived in 2024.7, and the
README has been saying 2025.1.0 since the start.

Anyone running Home Assistant between 2025.1 and 2026.2 was told they were
supported and then found Greg either invisible in HACS or refusing to update.
The floor now says 2025.1.0 and matches what was promised.
