# Maintaining Greg

Notes for whoever is working on him, including future me, who will have
forgotten all of this.

## Documentation is part of the change

Every change gets evaluated against the surfaces below **before** it is
committed. Proposed wording goes to WHISTLER-Arc for signoff. Nothing is
updated without it.

The reason for the rule: none of these break when they go stale. They just
quietly stop describing what Greg actually does, and nobody notices until a
user follows an instruction that has not been true for three releases.

| Surface | Covers | Goes stale when |
|---|---|---|
| `README.md` | Behaviour, settings, install, recipes | A setting moves, or an install path changes |
| `CHANGELOG.md` | Every user-visible change | Always. It is the easiest one to skip |
| `custom_components/greg/strings.json` | Labels and help text in the config flow | A setting is added or its meaning shifts |
| `custom_components/greg/translations/en.json` | The same, and must match `strings.json` exactly | Someone edits one and not the other |
| `custom_components/greg/services.yaml` | Service names, fields, descriptions | A service gains a field |
| Release notes | What changed and why, per release | Written at release time, so rarely stale |
| Forum post | The same, in WHISTLER-Arc's voice | Written at release time |

The two easiest to forget are `strings.json` and `services.yaml`, because
nothing fails when they are wrong. The integration loads happily and simply
describes itself incorrectly.

## Versions

The version lives in **two** files and they must agree:

- `custom_components/greg/manifest.json` -> `version`
- `custom_components/greg/const.py` -> `VERSION` and `VERSION_DISPLAY`

`VERSION_DISPLAY` is always `VERSION` with a `v` in front.

CI fails the build if they disagree. See `.github/workflows/checks.yml`.

**A git tag must match what the files say.** This is not currently automated,
and it has already caused one bug: `v1.4.4-beta.1` was cut while both files
said `1.4.4`, so the panel reported a stable version for a beta build. When
cutting a pre-release, set the files to the pre-release version too, for
example `1.4.5b1`, which is what the panel will then display.

## Releasing

HACS installs from release tags, not from `main`, so documentation fixes reach
users as soon as they land on `main` but code does not.

Local git in the working container cannot push tags, so releases go out through
a one-shot `workflow_dispatch` workflow that is pushed, run, then deleted. Tag
targets must be full 40 character SHAs, since abbreviated ones are rejected.

Betas are cut as GitHub pre-releases from a feature branch. `main` stays on the
last stable. HACS shows them to anyone who enables beta versions in the
Redownload dialog for Greg.

## Things that bite

**The panel script is cached hard.** Its URL carries the version for exactly
this reason. Change `PANEL_JS_URL` at your peril: without a changing query
string, neither the browser cache nor Home Assistant's service worker will ever
refetch it, and every panel change becomes invisible. A hard refresh does not
clear it.

**The settings block renders twice.** Once in the cog balloon below 1000px,
once inline in the right column above it. Both live in the DOM at once, so
everything there is addressed by class and the two copies mirror each other.
Ids will collide.

**Entities survive a reload.** `async_reload` must call `_notify()`, or the
entities never re-read their attributes and the panel is served settings from
before the change it just made.

**Greg's voice.** Formal, measured, deadpan. Contractions are fine. No
em-dashes, no semicolons, no tricolons. He is never called Marvin, and no line
is ever lifted from Adams. Same factory, different unit.

**No em-dashes anywhere**, in documentation or user-facing strings. They read
as machine-written.
