A one line fix for a problem that has been quietly breaking every panel update
Greg has ever shipped.

## Panel updates never reached anyone

His panel script was served from `/greg_panel/greg-panel.js`, with nothing in
the address to tell one release from the next. Once your browser had fetched
that file, the URL never changed, so it never fetched it again.

Which means every change to the panel, in every version, stayed invisible
until you cleared your caches by hand. The integration updated underneath
perfectly well. You just kept looking at the old panel.

A hard refresh did not fix it either. Home Assistant registers a service
worker, and a service worker keys on the URL and answers from its own store no
matter what the HTTP cache has been told.

The address now carries the version, so each release serves something neither
cache has seen and the update simply arrives.

## If you are updating from 1.4.2 or earlier

This release is the one that fixes the mechanism, so it cannot fix its own
delivery. You may need one manual cache clear to see the settings column that
1.4.2 introduced. After that it should never be necessary again.

The quickest check is to open Greg's panel in a private window, which has no
service worker at all.

## While you are here

The clear-your-caches step in the uninstall wizard exists because of this same
behaviour. It was written from the other end of the problem, without either of
us realising what was actually causing it.
