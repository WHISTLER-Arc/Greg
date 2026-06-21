# Greg

**A Marvin-inspired Home Assistant integration. Your coffee table has feelings. Mostly bad ones.**

![Support me on Ko-fi](https://img.shields.io/badge/Support%20me%20on%20Ko--fi-FF5E5B?style=for-the-badge&logo=ko-fi&logoColor=white)

(https://ko-fi.com/whistlerarc)

---

![Greg](www/greg/greg_judging.png)

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

<p align="center"><img src="www/greg/greg_judging.png" width="320"></p>
<p align="center"><em>Greg, mid-judgement. He has seen what you did.</em></p>

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

## Giving Greg the right voice

Greg works with any TTS engine, but he was *written* for one voice in particular. To get the full effect — the slow, monotone, magnificently depressed delivery of Marvin the Paranoid Android — run Greg through **Piper** using the **English (GB) "Alan"** voice. Google Translate TTS works fine as a default, but Alan is what makes Greg *Greg*.

### Installing Piper in Home Assistant

Piper is a fast, fully local neural text-to-speech engine. No cloud, no account, no per-character billing.

1. Go to **Settings → Add-ons → Add-on Store**.
2. Search for **Piper** and click it. (If it isn't listed, the **Wyoming** integration and the official add-on repo are included with HA by default — make sure **Advanced Mode** is on in your user profile.)
3. Click **Install**, then **Start**. Enable **Start on boot** and **Watchdog**.
4. Go to **Settings → Devices & Services**. Home Assistant should auto-discover the Piper Wyoming service — click **Configure** to add it. If it doesn't appear, add the **Wyoming Protocol** integration manually and point it at `localhost:10200`.
5. Piper now shows up as a `tts.*` entity. You'll select it as Greg's TTS engine in the next step.

### The Marvin voice settings

In the Piper add-on configuration, set the voice and tune it for that exhausted, defeated drawl:

- **Voice:** `en_GB-alan` (shown as `alan` in some Piper interfaces)
- **Quality:** `Medium` or `High`, depending on your hardware
- **Length Scale:** `1.3`–`1.5` — slows speech significantly for the depressed, dragging delivery
- **Speaking Cadence / sentence pause:** `0.7`–`0.8` — adds natural pauses between clauses to heighten the misery

Length Scale is the single most important setting — it's what turns a neutral British voice into something that sounds like it has given up. Start at `1.4` and adjust to taste.

Sources and Credits:
1. Recommended Settings: Reddit r/homeassistant community (https://reddit.com)
2. Application Steps: Official Home Assistant Documentation (https://home-assistant.io)

### Pointing Greg at Piper

Once Piper is running, open **Settings → Devices & Services → Greg → Configure** and set the **Text-to-speech engine** to your Piper `en_GB-alan` entity. Restart not required — Greg picks it up on the next reaction.

> **Credit:** These settings come from the Home Assistant community's "Marvin the depressed voice assistant" thread and the Piper/Rhasspy voice documentation. See:
> - [r/homeassistant — Marvin the depressed voice assistant](https://www.reddit.com/r/homeassistant/comments/1djh5bw/marvin_the_depressed_voice_assistant/)
> - [HA Community — Piper add-on configuration options](https://community.home-assistant.io/t/piper-add-on-configuration-options-per-voice-or-at-runtime/850302)
> - [Piper voice samples](https://rhasspy.github.io/piper-samples/)
> - [Piper VOICES.md](https://github.com/rhasspy/piper/blob/master/VOICES.md)

---

## A note on speaker chimes

Greg attempts to suppress the connection chime that Google and Nest speakers play before TTS audio. This does not always work. The chime is a firmware-level behavior built into the device by Google, and it is outside Greg's control. If suppression fails on your speaker, this is a hardware limitation — not a Greg limitation.

Non-Google speakers (Sonos, local media players, etc.) typically do not have this issue and are recommended for the best Greg experience.

---

## Greg's Panel

As of v1.3, Greg installs his own **sidebar panel automatically** — no manual card-pasting, no Lovelace editing. The moment the integration finishes setting up, a **Greg** entry appears in your sidebar with a live card showing his current mood, mood level, his most recent line, a daily disturbance tally, a live existential-crisis countdown, an on/off switch, and a **Disturb Greg** button. The panel removes itself cleanly if you ever remove the integration.

The card reads directly from Greg's entities (`sensor.greg_mood`, `switch.greg_enabled`, and friends), so you can also build your own dashboards from those if you'd rather.

Mood states are visualized with Greg's four expressions:

| Mood | Image | Look |
|------|-------|------|
| Resting | <img src="www/greg/greg_resting.png" width="120"> | Idle. Drooped. At peace, or its furniture equivalent. |
| Annoyed | <img src="www/greg/greg_annoyed.png" width="120"> | Mild irritation. Something happened. |
| Judging | <img src="www/greg/greg_judging.png" width="120"> | Deadpan eye-roll. He has seen what you did. |
| Existential | <img src="www/greg/greg_existential.png" width="120"> | Full crisis. Noir. Barely functional. |


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

## Support

If Greg made you laugh or saved you a weekend, you can [buy WHISTLER a coffee](https://ko-fi.com/whistlerarc). Greg will not personally benefit. He has no pockets.

## License

MIT — see [LICENSE](LICENSE)

---

*Built by WHISTLER & Arc.*
*Greg was not consulted on any of this. He has noted his objection internally.*
