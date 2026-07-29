## v1.3.4

### The sensitivity slider now does something

Sensitivity has been in Greg's advanced settings since v1.2 with a default of 75, and nothing has ever read it. You could slide it from 1 to 100 and change nothing at all. That is fixed.

It now controls how long Greg ignores the vibration sensor after registering a disturbance. Cheap sensors fire several times for one physical tap, and Greg counted every one of those separately, so a single coaster could escalate him to full chaos. One tap is now one disturbance.

- **100** filters nothing and keeps the old behaviour.
- **75** (the default) gives him a two and a half second memory.
- Lower it further if your sensor is especially twitchy.

Filtering happens before anything is counted, so a bouncy sensor no longer inflates the daily disturbance tally either.

**This changes behaviour on existing installs.** That is the point, since the slider was always meant to work this way. If you preferred the old behaviour, set sensitivity to 100.
