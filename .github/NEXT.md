# Next: two fixes to the settings balloon

A note to self, written in a web session so a desktop session can pick it up
cold. **Delete this file once the work below has shipped.** It is a handover
note, not documentation.

Nothing here is implemented yet. Both fixes are diagnosed and agreed, and they
are deliberately on hold. See "On hold" at the bottom for why.

---

## The bug that was reported

In Greg's panel, open the cog and change any setting. The settings close
immediately and nothing is saved. You have to click the cog again to get back in
and press Apply.

It only happens below 1000px wide. The settings block is rendered twice, inline
in the right-hand column on wide screens and inside the cog balloon on narrow
ones, and above 1000px the cog and balloon are `display:none`. So it never shows
up on a desktop browser, and it shows up on every single interaction on a phone.

Two details that match the report exactly, and are worth knowing so the fix is
not aimed at the wrong thing. The values are not actually lost when it closes:
`_onSettingInput` mirrors the form into both copies and sets `_dirty`, and
`_refreshSettings` refuses to stamp saved values over a dirty form, which is why
reopening the cog shows the change still sitting there with Apply live. And
pressing Apply inside the balloon does work, it just slams shut at the same
moment, which reads as though nothing happened.

---

## Fix one: composedPath, not contains

**File:** `custom_components/greg/panel/greg-panel.js`, in `_wire()`, currently
around lines 840 to 844.

The cause is the click-outside-to-close handler:

```js
document.addEventListener("click", (e) => {
  if (!this.contains(e.target)) balloon.classList.remove("open");
});
```

That would be correct in a normal page. It is wrong inside a shadow DOM. Greg's
panel lives in Home Assistant's shadow tree, so by the time a click reaches a
listener on `document` the browser has retargeted `event.target` to the
outermost shadow host, `<home-assistant>`. It never reports the select, the
slider, or the balloon. So `this.contains(e.target)` is asking whether
`<home-assistant>` is inside `<greg-panel>`, which is false for every click on
the page, the settings included.

The balloon therefore closes on any click that is not the cog. The cog survives
only because its own handler calls `e.stopPropagation()` before the document
listener ever runs.

`composedPath()` is the shadow-DOM-aware answer to "what did this click actually
pass through". It crosses shadow boundaries and returns the real nodes. `click`
is a composed event, so this is exactly what it is for.

```js
const cog = r.getElementById("cog"), balloon = r.getElementById("balloon");
cog.onclick = (e) => { e.stopPropagation(); balloon.classList.toggle("open"); };
// A listener on document sees event.target retargeted to the outermost shadow
// host, never to anything of ours, so contains() reports every click as being
// outside and the balloon shuts the instant you touch a setting. composedPath
// crosses shadow boundaries and gives the nodes actually clicked.
this._onDocClick = (e) => {
  const path = e.composedPath();
  if (!path.includes(balloon) && !path.includes(cog)) {
    balloon.classList.remove("open");
  }
};
document.addEventListener("click", this._onDocClick);
```

After this the balloon stays open while you work in it, through every select,
slider, switch and time field, and through Apply itself, so you get to watch it
go "Applying…" then "No changes". It closes on a click outside it, on the cog
again, or when a Home Assistant dialog opens over it.

Store the handler on `this` and remove it in `disconnectedCallback`, which
already exists around line 55. The listener is on `document` but closes over
this instance's balloon, so today every panel teardown leaves one behind holding
a detached element. Small leak, free to fix while the line is open.

## Fix two: the balloon cannot scroll

Same file, the `.balloon` rule, currently around line 245. No `max-height` and
no `overflow`, and it holds nine fields, Apply, Advanced settings and the whole
uninstall block at 300px wide. On a short screen the bottom of it runs off the
edge of the viewport with no way to reach it, which is why the uninstall button
is effectively unreachable on a phone.

```css
.balloon { position:absolute; top:58px; right:14px; z-index:10;
  width:min(300px, calc(100vw - 44px));
  /* The settings block is tall and the balloon is pinned near the top of the
     card, so on a short screen the bottom of it, uninstall included, ends up
     off the viewport with no way to reach it. */
  max-height:calc(100vh - 120px); overflow-y:auto; overscroll-behavior:contain;
  ... rest of the rule unchanged ... }
```

`overscroll-behavior:contain` stops a scroll that reaches the end of the balloon
from carrying on into the page underneath, which is the thing that makes these
feel broken on a touchscreen.

The 120px is a heuristic, not a measurement. It covers Home Assistant's toolbar,
the panel's own top padding and the header above the card. Check it on a real
phone, and nudge the number if it is off.

---

## On hold

Do not commit these on their own. There are three other things outstanding that
should all go out under one version bump:

- **Issue #2**, "Voice not getting to HomePod", from geraldebberink.
- **PR #3**, "Made _react synchronous but the _speak async.", from the same
  person, `geraldebberink:speech-update` into `main`. Related to #2 and not yet
  reviewed.
- A report on the Home Assistant forum thread, not yet triaged.

## Release mechanics, for when it does go out

No version bump in the fix commits. The convention is feature and fix commits
first, then a separate `chore: <version>` at release time touching `const.py`,
`manifest.json` and the README, the way `e276aad chore: 1.6.0` did.

The bump is not optional for this one. `PANEL_JS_URL` is
`/greg_panel/greg-panel.js?v={VERSION}` (`const.py:180`), so a panel change is
invisible to anyone already running v1.6.0 until the version changes and busts
the cache. Neither fix can reach a single user without a release. Beta first, as
always.

Already sitting on this branch and riding along in the same release: the v1.7
roadmap line for Greg on your phone, committed as `docs: park Greg on your phone
as v1.7`. Docs only, unrelated to the panel.

## Testing, once the fixes are made

Static:

- `node --check custom_components/greg/panel/greg-panel.js`
- `grep -n 'contains(e.target)' custom_components/greg/panel/greg-panel.js`
  should return nothing
- The diff should be one file, three hunks: the `.balloon` rule, `_wire`, and
  the listener removal in `disconnectedCallback`

On hardware. The panel is still served as `?v=1.6.0`, so the browser answers
from cache and the service worker will not refetch. Force it by loading
`/greg_panel/greg-panel.js?v=test` once, or test after the version bump.

- Narrow the window below 1000px so the cog appears
- Open the cog, change the language dropdown. The balloon stays open
- Move the volume slider, toggle quiet hours, set a time. Still open
- Press Apply. Reads "Applying…", then "No changes", still open
- Click the mood image outside the balloon. It closes
- Scroll inside the balloon, reach the uninstall button, and confirm that
  carrying on scrolling does not drag the page behind it
- Widen past 1000px and confirm the inline column is unaffected

The one to judge on an actual phone rather than a narrowed desktop window is the
`max-height` number, since that is the part that was guessed at.
