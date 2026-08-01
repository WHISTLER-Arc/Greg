# Changelog

All notable changes to Greg. He would like it noted that he did not ask to be
versioned.

## [1.4.2]

### Added
- **Greg's panel does something now.** The right-hand column held one switch that
  duplicated the one beside Disturb Greg, and a note telling you to go and look
  somewhere else. It now holds the settings you picked at install: sensor,
  speaker, text to speech, volume, sensitivity and quiet hours. Changes are
  applied together on one button, because writing to the config entry reloads
  him and doing that per slider nudge would be unpleasant.
- `greg.set_options` service behind it, so the same settings can be scripted.
- Sensitivity moved up from advanced, since it is the one people actually
  adjust after installing.

### Changed
- The uninstall section moved out of its full-width strip and into the settings
  column, where it belongs.
- Quiet hours times fold away when quiet hours are off.

### Fixed
- **`hacs.json` demanded Home Assistant 2026.3.0.** Nothing in Greg needs it. The
  README has been promising 2025.1.0 the whole time, and anyone in between was
  told they were supported and then found they were not. Now says 2025.1.0.

## [1.4.1]

### Added
- **Occasional openers.** Greg sometimes starts with a "Right." or an "Ah."
  before the line itself, about one time in three. The rest of the time there is
  nothing there at all, which is the part that makes it sound like speech.
  Advanced toggle, on by default.
- **Voice setting.** Greg can now be told exactly which voice to speak with,
  passed straight through to the TTS engine. Previously he used whatever your
  engine defaulted to, so making Greg sound right meant changing that default
  for everything else using the same engine.
- `greg_line` now carries both `message`, which is what Greg actually says
  including any opener, and `line`, which is the written line on its own.

### Fixed
- **Repetition.** The line picker only avoided the single previous line, so with
  50 lines per category you could easily hear the same one twice in an evening.
  Each pool is now shuffled and played through in full before anything repeats.
- **The panel reported the wrong version on every install.** It read `sw_version`
  from the mood sensor's state attributes, which never carried it, and fell back
  to a hardcoded "v1.3". The attribute now exists and the fallback is gone.
- **The integration title kept whatever version it was installed at.** Upgrading
  left it advertising the old one indefinitely. It now corrects itself on setup.

### Thanks
- **RedKing** for the observation that a phrase sounds spontaneous precisely
  because it is sometimes absent, for the moan generator now documented in the
  README, and for spotting that Greg was quietly overriding whatever voice the
  TTS engine was set to.
- **Xornop** for a considerably tidier way to roll for it.

## [1.4.0]

### Added
- `greg_line` event, fired every time Greg picks something to say, carrying the
  message, his mood and category, and the speaker and TTS engine he is
  configured with.
- Speech mode. Greg can stay quiet and leave the talking to an automation, which
  is the useful setting if you want a local model to rewrite him first.
- 125 new lines. All five pools now hold 50 each, 250 in total.

### Thanks
- **teskanoo** for asking for the event.

## [1.3.4]

### Fixed
- The sensitivity slider did nothing at all. It now sets a refractory window on
  the vibration sensor, so one physical tap counts as one disturbance instead of
  the five or six a cheap sensor actually reports.

## [1.3.3]

### Added
- Uninstall wizard in Greg's panel. Five steps, and it removes only what his own
  config entry owns.
- `greg.uninstall` service, with an optional `restart` boolean.

## [1.3.2] · [1.3.1]

### Fixed
- Packaging and manifest corrections.

## [1.3.0]

### Added
- Greg's sidebar panel, registered automatically on setup and cleaned up on
  removal. No dashboard editing required.
