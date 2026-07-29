## v1.3.3

### Uninstall wizard

Greg can now take himself apart. There is an **Uninstall Greg** section at the bottom of his panel that walks through it in five steps: confirm, disassembly, restart, cache clearing, goodbye.

He removes only what his own config entry owns. Your automations, your vibration sensor, your other integrations and any helper you made yourself are left alone. Nothing is matched by entity name, so if you happen to own entities called `greg_something`, they survive.

Afterwards, remove the repository in HACS. Greg cannot delete his own code while he is running it.

There is also a `greg.uninstall` service if you would rather script it. It takes an optional `restart` boolean.

### Also in this release

- Options flow reaches the advanced settings page properly, and includes the TTS engine picker.
- `manifest.json` and `const.py` versions are back in sync.
