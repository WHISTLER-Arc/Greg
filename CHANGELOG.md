# Changelog

All notable changes to Greg. He would like it noted that he did not ask to be
versioned.

## [1.6.5]

### Added
- **Conditions.** Greg can now consult the same core conditions the rest of
  your automations use, rather than only his own clock. Rows of entity /
  `is` or `is not` / state in his panel, all of which have to hold or he keeps
  quiet. Requested by
  [euf0ria](https://community.home-assistant.io/u/euf0ria) on the forum thread.
- Conditions sit alongside quiet hours rather than replacing them, so anyone
  who has not written any notices no change at all.
- Each row shows the entity's current state, and warns when what you have typed
  can never match it. `input_boolean.x is false` never fires, because an
  `input_boolean` is `on` or `off`.
- The panel says which condition is keeping him quiet, rather than leaving you
  to work out why a poke did nothing.
- `blocked` and `blocked_by` attributes on the mood sensor. `quiet_hours` still
  means only the clock, so automations reading it are unaffected.
- `greg.set_options` takes a `conditions` list, so the same thing can be
  scripted.

### Fixed
- **Greg's options no longer eat his settings.** Pressing Submit in Greg's
  options replaced the whole stored options rather than merging into them, so
  it deleted any lines you had written and any conditions you had set, and
  reverted advanced settings changed since install. Present since custom lines
  shipped in 1.6.0.

### Notes
- An entity that is missing, unavailable or unknown does not block Greg. A
  renamed entity leaving him permanently silent is the worse failure by a
  distance.
- Twenty conditions is the cap, which is there to stop a malformed automation
  writing thousands of rows into the config entry rather than because a house
  has twenty core conditions.

## [1.6.0]

### Added
- **Write your own lines, in his panel.** A Lines you wrote section under the
  card, one tab per category. Type a line, press Add, press Save, and Greg says
  it. No pull request, no waiting for anyone to approve it. Your table, your
  jokes.
- Lines belong to the language you wrote them in, so a Dutch one only comes up
  while Greg is speaking Dutch.
- **Use only my lines**, for anyone who wants a different table rather than a
  slightly expanded one. It never empties a pool: switch it on with nothing
  written for a category and that category keeps its fifty built-in lines.
- **Share the good ones.** A button that opens a GitHub issue with your lines
  already in it, sorted by category and tagged with the language, and a field
  for how you would like crediting. Read it, press submit, done. No account
  needed beyond the GitHub one, and nothing is sent anywhere until you press it.
- A bot sorts each submission into a checklist and marks anything already in
  the pools, so accepted lines can be picked in about a minute and turn up in a
  later release with credit.
- `greg.set_lines` service behind the editor, so the same thing can be scripted.

### Notes
- Lines live in the config entry, so they survive updates and reinstalls of the
  integration, and are removed with it.
- Two hundred lines per category is the cap, and three hundred characters per
  line. Both are far beyond anything that reads well out loud.
- Prefilled GitHub links have a size limit of their own, so a very large batch
  is copied to the clipboard with instructions instead of being silently cut in
  half.
- **Reload the page after updating.** Greg's panel script is versioned so a new
  release is never served from cache, but the panel registers its address once
  when Home Assistant starts, and the frontend holds that address until the page
  itself is reloaded. So the editor will not appear until you refresh, and a
  hard refresh if your browser is being stubborn. This has always been true of
  panel changes; it is simply more obvious when the change is a whole new
  section rather than a tweak.

## [1.5.5]

### Added
- **Greg actually speaks Dutch and European Portuguese now.** v1.5.0 built the
  mechanism and left the pools empty. They are full. Two hundred and fifty
  lines in each language, all five pools, plus his openers.
- Every line was written natively and then reviewed one by one by a native
  speaker of both. None of them are translations of the English, which is the
  whole point and is why the wording often diverges. A translated joke is a
  correct sentence that is not funny, and there are none of those in here.
- **A voice per language.** One voice cannot pronounce three languages, so
  there is now a voice box for each language Greg speaks, in advanced settings.
  Piper names its voices for their language, `nl_NL-ronnie-medium` and
  `pt_PT-tugão-medium` among them, and the right one has to be picked per
  language rather than once for everything. The fields are generated from
  whatever languages are installed, so adding a language file still brings its
  own voice field with it.

### Fixed
- **He read the new lines in an English voice.** Greg picked the right line in
  the right language and then handed it to the TTS engine without saying which
  language it was, so the engine used whatever it defaults to. With Piper on
  `en_GB-alan-low` that is an English voice reading Dutch letters aloud, which
  is not the joke. He now tells the engine the language. The omission was
  always there and only became audible once the pools stopped being English.
- **And then he said nothing at all.** The first attempt at the above sent
  Greg's own language code straight through. Greg's codes are bare, `nl` and
  `pt` and `en`. Engines advertise locales, `nl_NL` and `en_GB`, and Home
  Assistant refuses an unrecognised code rather than falling back, so every
  line raised `Language 'nl' not supported` and nothing was spoken in any
  language. Greg now checks what the engine has actually advertised, picks the
  locale that matches, and leaves the field out entirely when it cannot tell.
  Worst case he is exactly as he was before any of this, which is the correct
  worst case. Where a language has several regions he prefers the one matching
  itself, so Dutch is `nl_NL` rather than `nl_BE` and Portuguese is `pt_PT`
  rather than `pt_BR`.
- **A wrong voice name no longer silences him.** Voice names are matched
  character for character, so `pt_PT-tugao-medium` is not `pt_PT-tugão-medium`
  and the near miss is refused outright rather than falling back. Greg now
  checks the name against what the engine offers, drops it if it does not
  match, and says so in the log with the list of valid names. A table speaking
  in the wrong voice tells you where to look. A table that has gone quiet tells
  you nothing.
- The help text for the Portuguese voice gave the example without its tilde,
  which is exactly the near miss described above. Fixed, and all three now say
  to copy the name from the engine's own list.

### Changed
- Eleven English lines are better than they were. Writing a line twice in two
  other languages turns out to be an unusually good way of noticing that the
  original was slightly off. `Peak chaos. I have now seen peak chaos.` became
  `Peak chaos. I have now seen it.`, and ten others like it.

### Notes
- The old single Voice setting still works and now applies to English only. It
  predates Greg speaking anything else, so anyone who set it set an English
  voice, and letting it carry into Dutch would recreate the bug fixed above.
  Existing English setups are unchanged.
- Leave a language's voice empty and the engine picks for itself, which for
  most engines is the right voice for the language once Greg names it.
- `pt-BR` still resolves to English rather than European Portuguese, as it has
  since v1.5.0. Brazilian and European Portuguese are different enough that
  the wrong one is worse than none.
- Nothing falls back to English any more for Dutch or Portuguese. Before this
  release an empty pool quietly served the English one, which was correct
  behaviour and no longer applies to either language.
- The reviewed source lives in `.translations/`, with the English line recorded
  above each pair. `lines/nl.py` and `lines/pt.py` are generated from it by
  matching on that English text.

## [1.5.0]

### Added
- **Greg speaks more than one language.** English, Dutch and European
  Portuguese. The setting sits in his panel under Text to speech, and defaults
  to following whatever Home Assistant is set to. Dutch and Portuguese are
  stubbed and waiting to be written, and anything unwritten falls back to
  English one reaction at a time.
- `greg_line` now carries the `language` a line came out in.
- `lines/TEMPLATE.py`, so adding a language is one file and a pull request.

### Changed
- Line pools moved out of `const.py` into a `lines` package, one module per
  language. `const.py` is 131 lines instead of 405 and holds only constants
  again. The English lines are byte-identical to before.
- Shuffled decks are keyed by language, so changing it starts a clean cycle
  rather than carrying half of the old one across.

### Notes
- `pt-BR` resolves to English rather than European Portuguese. Regional codes
  normally collapse to their base language, so `nl-BE` is served by Dutch, but
  Brazilian and European Portuguese are different enough that the wrong one is
  worse than none. This is deliberate, not a bug.
- No new lines in this release. Greg sounds exactly as he did, unless you
  change the setting.

## [1.4.4]

### Fixed
- **Settings jumped back to their old values after Apply.** Two faults stacked.
  The coordinator updated its own copy of the config on reload but never told
  the entities to re-read their attributes, and the settings the panel reads are
  published from there. Home Assistant went on serving the values as they were
  before the change, and the panel read those and wrote them back over the edit.
  Underneath that, updating a config entry schedules its listeners rather than
  awaiting them, so the service call could return before the new values were
  published at all. The panel now holds what it sent until the published config
  agrees, with a timeout so a failed write cannot leave the form stuck.

## [1.4.3]

### Fixed
- **Panel updates never reached anyone.** The panel's script was served from a
  URL with no version in it, so once a browser had fetched it that URL never
  changed and it was never fetched again. Every change to the panel Greg has
  ever shipped stayed invisible until the user cleared their caches by hand. A
  hard refresh was not enough either, because Home Assistant's service worker
  keys on the URL and answers from its own store. The URL now carries the
  version, so each release serves an address nothing has cached.

  This is also why the uninstall wizard has a step about clearing caches. Same
  cause, spotted from the other end.

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
