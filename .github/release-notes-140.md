## v1.4.0

### Greg can hand his lines to something else

Every time Greg picks something to say he now fires a `greg_line` event. Nothing listens unless you write an automation, so it costs nothing to leave on.

The event carries the message, the category, his mood, and the speaker and TTS engine he is already configured with, so your automation does not need to hardcode any of that:

```yaml
event_type: greg_line
data:
  message: "I felt that. For the record, I would have preferred not to."
  category: soft             # soft | medium | chaos | existential | silence
  mood: annoyed
  mood_level: 40
  vibrations_today: 12
  quiet_hours: false
  spoken: true
  media_player: media_player.lounge
  tts_engine: tts.piper_en_gb_alan
  volume: 0.35
```

### Letting something else do the talking

Advanced settings gain **Who does the talking**. Leave it on Greg and nothing changes. Set it to stay quiet and he picks his line, fires the event, and says nothing.

That is the interesting one. Greg writes the thought, your local model rewrites it, your speaker delivers the result. There is a working automation in the README using `conversation.process`, so you can point him at Ollama or whatever else you run.

You can also switch the event off entirely if you would rather he kept his thoughts to himself.

### Twice as much to say

The line pools have doubled. 50 lines per category instead of 25, 250 in total. Same voice, same rules, no repeats.

### Upgrading

Both new settings default to the old behaviour, so nothing changes on upgrade until you opt in.

---

The event was asked for by **teskanoo**, twice, who offered to fork it and build it himself. That is usually the point where a feature stops being optional.
