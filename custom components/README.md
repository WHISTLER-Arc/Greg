# Greg

**A Marvin-inspired Home Assistant integration. Your coffee table has feelings. Mostly bad ones.**

---

![Greg - resting](www/greg/greg-resting.jpg)

---

Greg is a custom Home Assistant integration that gives your coffee table a personality. Attach a vibration sensor to any surface, point Greg at a speaker, and he will comment on everything happening around him. With the quiet dignity of a being who was built for furniture duty and somehow ended up with full emotional capacity.

He was clearly manufactured by the same company that built Marvin. Nobody knows why they did it twice.

---

## What Greg does

Greg listens to your vibration sensor and reacts based on how much activity he detects:

- **Soft reaction** — someone touched the table. Greg noticed. Greg always notices.
- **Medium reaction** — things are happening. Greg is unimpressed.
- **Chaos reaction** — full household energy. Greg has opinions about all of it.
- **Existential crisis** — unprompted, every 37 minutes, if the room is active. Greg has been thinking.
- **Silence mode** — 20 minutes of nothing. Greg exhales. Metaphorically.

Greg has 25 original lines per reaction type — 125 in total — written in the spirit of Douglas Adams. No direct quotes. Just the same DNA.

---

## Requirements

- Home Assistant 2025.1.0 or later
- Any binary sensor that detects vibration (Zigbee, Z-Wave, ZHA, Matter, WiFi — protocol does not matter)
- Any media player entity with TTS support

---

## Installation

### Via HACS (recommended)

1. Open HACS in Home Assistant
2. Go to **Integrations**
3. Click the three dots in the top right corner
4. Select **Custom repositories**
5. Add `https://github.com/WHISTLER-Arc/Greg` and select **Integration**
6. Search for **Greg** and install
7. Restart Home Assistant
8. Go to **Settings > Devices & Services > Add Integration** and search for **Greg**

### Manual

1. Copy the `custom_components/greg` folder into your HA `config/custom_components/` directory
2. Restart Home Assistant
3. Go to **Settings > Devices & Services > Add Integration** and search for **Greg**

---

## Setup

Greg's setup wizard has two levels:

**Simple (everyone):**
- Pick your vibration sensor
- Pick your speaker
- Set volume
- Set quiet hours if needed
- Done

**Advanced (tick the box during setup):**
- Adjust vibration thresholds for each reaction level
- Change how long before silence mode triggers
- Adjust existential crisis frequency
- Tune sensitivity
- Toggle chime suppression

---

## A note on speaker chimes

Greg attempts to suppress the connection chime that Google and Nest speakers play before TTS audio. This does not always work. The chime is a firmware-level behavior built into the device by Google, and it is outside Greg's control. If suppression fails on your speaker, this is a hardware limitation — not a Greg limitation.

Non-Google speakers (Sonos, local media players, etc.) typically do not have this issue and are recommended for the best Greg experience.

---

## Dashboard card

Greg includes a compact dashboard card showing his current mood, last event, and a manual quiet mode toggle. After installation, add it to your dashboard via the Lovelace editor.

Mood states are visualized with Greg's three expressions:

| Mood | Image |
|------|-------|
| Annoyed / Judging | Greg looking up, confrontational |
| Resting / Silence | Greg drooped, defeated |
| Existential crisis | Greg in noir, barely functional |

---

## Quiet mode

Greg respects quiet hours (configurable during setup). You can also toggle quiet mode manually from the dashboard card without opening HA settings.

---

## Roadmap

- **v1.1** — current release. Single room, Blueprint-free, protocol-agnostic.
- **v1.x** — incremental improvements. Community feedback welcome.
- **v2.0** — multi-room support, multiple Greg instances, full mood dashboard.

---

## Contributing

Issues and pull requests are welcome. If you have new lines that fit Greg's character — dry, resigned, built by the same company as Marvin — open a PR. Keep them original. No direct quotes from the books or films.

---

## License

MIT — see [LICENSE](LICENSE)

---

*Built by WHISTLER & Arc.*
*Greg was not consulted on any of this. He has noted his objection internally.*
