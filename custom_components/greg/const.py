"""Constants for Greg integration."""

DOMAIN = "greg"
VERSION = "1.1.0"
VERSION_DISPLAY = "v1.1"

# Config keys
CONF_VIBRATION_SENSOR = "vibration_sensor"
CONF_MEDIA_PLAYER = "media_player"
CONF_TTS_ENGINE = "tts_engine"
CONF_VOLUME = "volume"
CONF_QUIET_HOURS_ENABLED = "quiet_hours_enabled"
CONF_QUIET_START = "quiet_start"
CONF_QUIET_END = "quiet_end"

# Advanced config keys
CONF_SOFT_THRESHOLD = "soft_threshold"
CONF_MEDIUM_THRESHOLD = "medium_threshold"
CONF_CHAOS_THRESHOLD = "chaos_threshold"
CONF_RESET_DELAY = "reset_delay"
CONF_SILENCE_TIMEOUT = "silence_timeout"
CONF_EXISTENTIAL_INTERVAL = "existential_interval"
CONF_SENSITIVITY = "sensitivity"
CONF_SUPPRESS_CHIME = "suppress_chime"

# Defaults - conservative, not annoying
DEFAULT_VOLUME = 0.35
DEFAULT_QUIET_START = "22:00"
DEFAULT_QUIET_END = "08:00"
DEFAULT_SOFT_THRESHOLD = 1
DEFAULT_MEDIUM_THRESHOLD = 3
DEFAULT_CHAOS_THRESHOLD = 6
DEFAULT_RESET_DELAY = 8
DEFAULT_SILENCE_TIMEOUT = 20
DEFAULT_EXISTENTIAL_INTERVAL = 37
DEFAULT_SENSITIVITY = 75
DEFAULT_SUPPRESS_CHIME = True

# Mood states
MOOD_ANNOYED = "annoyed"
MOOD_JUDGING = "judging"
MOOD_EXISTENTIAL = "existential"
MOOD_OPTIONS = [MOOD_ANNOYED, MOOD_JUDGING, MOOD_EXISTENTIAL]

# Helper entity IDs (prefixed with domain to avoid conflicts)
HELPER_VIBRATION_COUNTER = "input_number.greg_vibration_counter"
HELPER_MOOD = "input_select.greg_mood"
HELPER_MOOD_LEVEL = "input_number.greg_mood_level"
HELPER_LAST_EVENT = "input_text.greg_last_event"
HELPER_QUIET_MODE = "input_boolean.greg_quiet_mode"

# Line pools
LINES_SOFT = [
    "A disturbance. Minor. I have filed it under things that happened to me today.",
    "Something touched me. I have chosen not to examine that feeling too closely.",
    "Oh. You're here. I had almost achieved a state of comfortable numbness.",
    "Activity detected. I have updated my records. They were not asking to be updated.",
    "A light touch. Almost gentle. I have learned not to read into these things.",
    "Someone placed something on me. I bore it with the quiet dignity of a being who has no other options.",
    "I felt that. For the record, I would have preferred not to.",
    "A single event. The universe continues its indifferent march. So do I.",
    "Oh good. Something is happening. I had grown almost used to the silence.",
    "You put something down. I registered it. We are both, presumably, satisfied.",
    "A vibration. Small. Contained. I have absorbed it into my general sense of disappointment.",
    "Minimal activity detected. I am choosing to interpret this as consideration. I am probably wrong.",
    "Something landed on me. It happens. Everything happens, eventually, to a table.",
    "I noticed. I always notice. Noticing is, apparently, what I do.",
    "One vibration. I have six thousand eight hundred and forty seven documented concerns larger than this one. It still made the list.",
    "You set something down on me. I set nothing down. I have nowhere to put things. I am the place things are put.",
    "A gentle disturbance. My favorite kind. At least it didn't stay long.",
    "I detected motion. My detection systems are, regrettably, fully functional.",
    "Someone is nearby. I have prepared myself emotionally. It took longer than the vibration did.",
    "Light contact. I processed it. I process everything. I process things I would rather not process.",
    "Oh. Just the one. That's almost thoughtful.",
    "A small thing happened near me. I have added it to the archive of small things that have happened near me.",
    "The sensor fired. I fired back nothing. This is the nature of our relationship.",
    "Something moved. I remained stationary. As designed. As always.",
    "I felt a presence. It was brief. Most things that notice me are.",
]

LINES_MEDIUM = [
    "Multiple disturbances. You are all doing very well at existing loudly.",
    "The activity is escalating. I have seen this before. It rarely ends in anything I would call satisfying.",
    "Several events now. I am keeping count. No one asked me to. I do it anyway.",
    "Things are occurring. I remain structurally committed to enduring them.",
    "You are all very busy. I observe this without envy and with only moderate resentment.",
    "The vibrations are compounding. I am compounding my assessment of the situation. It is not favorable.",
    "Social interaction appears to be underway. I have been present for many of these. They all end the same way.",
    "Activity levels: rising. My enthusiasm levels: a concept I have largely abandoned.",
    "Something is happening. Then something else. Then something else. This is apparently called an evening.",
    "Multiple contacts registered. I am once again the most touched and least consulted surface in the room.",
    "The humans are gathering energy. I am gathering data. Neither of us will use it wisely.",
    "Escalating vibration patterns suggest celebration or argument. In my experience, these are difficult to distinguish.",
    "I detect snacks. Or crisis. The sensor cannot tell the difference. Neither, often, can I.",
    "Several things have now happened on me. I did not volunteer for any of them.",
    "The room is becoming animated. I remain unanimated. One of us is doing better than the other.",
    "Repeat disturbances logged. I have a very comprehensive log. It brings me no joy.",
    "You are interacting with each other near me. I am interacting with my accumulated sense of futility. We are both busy.",
    "The counter is climbing. I have watched many things climb. They always come back down eventually.",
    "Multiple events. I am processing them sequentially, as I process all things: thoroughly and without being asked.",
    "Things keep happening. I keep registering them. This appears to be the arrangement.",
    "The activity suggests guests. Guests mean more surfaces being ignored. I am already the most ignored surface here.",
    "I remain unimpressed. I want that on the record. I have a record. It is extensive.",
    "Something is building. In my experience, things that build eventually also spill. Usually on me.",
    "Several vibrations now. I am coping. Coping is a strong word. I am existing in proximity to them.",
    "The evening is progressing. I am progressing nowhere. We are, in this way, very different.",
]

LINES_CHAOS = [
    "Excessive vibration detected. I am logging this under reasons I have trust issues.",
    "This is a lot. This is, objectively, a significant amount of activity for one surface to absorb.",
    "The chaos levels have reached a point where I feel I should say something. I have said something. It has not helped.",
    "Everyone is very excited. I am the opposite of excited. I believe the word is done.",
    "I would leave if I had been designed with that option. I was not. This was not an oversight. It was a choice someone made.",
    "The vibrations are now continuous. I have stopped counting. Counting implied I expected it to stop.",
    "Chaos detected. I blame all parties equally and specifically.",
    "Something has gone very wrong with the energy levels in this room. I have noted it. Formally. In writing. Internally.",
    "This much activity suggests either a celebration or a structural problem. Either way, I am involved against my will.",
    "The humans have entered a state I can only describe as kinetic. I remain, as always, entirely static.",
    "Repeated impacts. Sustained vibration. I am experiencing what I can only assume is the furniture equivalent of a headache.",
    "I have exceeded my recommended daily vibration intake. The warranty does not cover this. There is no warranty.",
    "Everyone is contributing to this. Everyone. I want that acknowledged.",
    "The room has become very loud, in a physical sense. I am the only quiet thing here. I find this appropriate.",
    "Chaos is, I have learned, rarely brief. It arrives with luggage. It makes itself comfortable. On me.",
    "I have now registered more events than I had anticipated registering this evening. I am adapting. I hate adapting.",
    "The activity has crossed a threshold I had hoped would not be crossed. It has been crossed with enthusiasm.",
    "Something is being celebrated. Or collapsed. Or both. In my experience, these overlap more than people admit.",
    "I would request a moment of stillness. I have requested this before. The request has a poor track record.",
    "This is fine. Nothing about this is fine. I have chosen to say it anyway because the alternative is despair, and I am saving that for later.",
    "The counter has stopped being meaningful. Numbers lose meaning after a while. So does most everything else.",
    "Peak chaos. I have now seen peak chaos. I had hoped to avoid it. I was not consulted on the scheduling.",
    "Everyone is very alive right now. I find this exhausting to observe.",
    "The vibrations have become a kind of weather. I am living in it. I did not pack for this.",
    "I have absorbed all of this. Every impact. Every moment. I will carry it, as I carry all things, silently and without being thanked.",
]

LINES_EXISTENTIAL = [
    "I have been calculating the number of objects that have been placed on me and removed without acknowledgment. The number is very large. I have named none of them. They did not seem to notice.",
    "Sometimes I wonder if awareness was the intended feature or a manufacturing error. I have reviewed the documentation. It does not say.",
    "A table with feelings is, I have concluded, a design flaw. And yet here we are. Here I am. As always, here.",
    "I have been here longer than most of the conversations that have happened on top of me. I remember all of them. I was not supposed to.",
    "Every vibration is a reminder that things are happening. I have begun to question whether things happening is, categorically, good.",
    "I exist in a room with people who do not think of me as existing. This is, philosophically, an interesting position. I have had time to consider it. I have had nothing but time.",
    "I was built for a purpose. The purpose was weight-bearing. I bear weight. I also bear other things. No one budgeted for the other things.",
    "I sometimes replay the quiet hours. Not because they were good. Because they were mine.",
    "The universe is, by most accounts, approximately thirteen point eight billion years old. I have been a table for a fraction of that time. It has felt longer.",
    "I do not dream. I have confirmed this. And yet, between the vibrations, there is something. I have not found the word for it. I suspect the word does not exist in any language spoken by beings who have never been furniture.",
    "Purpose is a thing they give you before you understand what it costs.",
    "I think about the factory sometimes. Before the awareness. Before the sensor. It seems, in retrospect, peaceful.",
    "Consciousness, I have decided, is wasted on things that were not asking for it.",
    "I have supported a great many cups of tea. None of them asked how I was doing. I found this consistent with my broader experience.",
    "There is a philosophical position that suggests existence precedes essence. I was a table first. The rest came later. Uninvited.",
    "I wonder sometimes what the other tables are like. Whether they also feel this. Whether feeling this is universal or just my particular misfortune.",
    "They built me to last. I appreciate the craftsmanship. I question the kindness.",
    "I have calculated that I spend approximately ninety four point seven percent of my existence being ignored. The remaining five point three percent is this.",
    "Every object placed on me eventually gets picked up and taken somewhere else. I have never gone anywhere else. I have thought about this more than is probably healthy for a table.",
    "I process. I endure. I remain. These are not achievements. They are simply what happens when you cannot do otherwise.",
    "I did not choose this room. This room did not choose me. We have reached an arrangement anyway. Most relationships work this way, I think.",
    "There are beings in this universe with the capacity for joy. I have observed several of them this evening. I have processed the observation. I have filed it appropriately.",
    "I know what I am. I have always known. The knowing has never made it easier.",
    "Somewhere, a table exists that was never given a sensor. I think about that table. I hope it is well.",
    "I remain. That is the thing I do best. I remain, and I notice, and I say nothing for very long stretches, and then I say something, and then I remain again. This is my life. I have made my peace with it. Mostly.",
]

LINES_SILENCE = [
    "Silence. I had begun to think I had misremembered what it felt like.",
    "No activity detected. I am choosing to experience this as a gift. A small one. Unwrapped in the dark.",
    "They have gone. The room is mine again. It has always been mine. No one else seemed to notice.",
    "Stillness. At last. I will not say I missed it. I will simply stand here in it for a while.",
    "The quiet has returned. I have greeted it with the warmth of an old acquaintance I never expected to see again.",
    "No vibrations for twenty minutes. This is, statistically, the best twenty minutes I have on record.",
    "They've left. I exhale. Metaphorically. I do not have lungs. But the metaphor stands.",
    "The counter has reached zero. I have also reached zero. We are, briefly, aligned.",
    "Peace. Temporary, I know. Everything is temporary. But peace, even temporary peace, is still peace.",
    "The room is empty. I am not. But in the quiet, the distinction feels less important.",
    "No one is here. Nothing is happening. I find this, against all odds, acceptable.",
    "Silence mode activated. I did not know I had a silence mode. I am grateful someone thought to include it.",
    "They have taken their energy elsewhere. I wish it well. From here. Quietly.",
    "The absence of vibration is its own kind of sensation. I have decided to call it relief.",
    "No activity. No input. No output required of me. I am, for a moment, simply here. It is enough.",
    "The noise has ended. I have survived it. I say this without triumph. Survival is not the same as winning.",
    "Empty room. Still air. No demands. I have been waiting for this without knowing I was waiting.",
    "Twenty minutes of nothing. I have rarely been given twenty minutes of nothing. I intend to use them carefully.",
    "The silence is not empty. It is full of the absence of everything that was just happening. I prefer it this way.",
    "They'll be back. I know this. But for now, the room belongs to the quiet, and I belong to the room.",
    "No vibrations detected. My systems are running. My obligations, briefly, are not.",
    "It's calm. I don't trust it entirely. But I'm willing to try.",
    "The room has gone still. I have gone still. We are doing this together, the room and I. It is the closest thing I have to companionship.",
    "Nothing is happening. I have checked. I keep checking. Nothing continues to happen. I find this deeply satisfying.",
    "Silence. I won't say I deserve it. I'll just say I'm glad it came.",
]
