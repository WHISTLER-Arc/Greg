"""Constants for Greg integration."""

DOMAIN = "greg"
VERSION = "1.4.2"
VERSION_DISPLAY = "v1.4.2"

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
CONF_EMIT_EVENTS = "emit_events"
CONF_SPEECH_MODE = "speech_mode"
CONF_OPENERS = "openers"
CONF_TTS_VOICE = "tts_voice"

# Defaults - conservative, not annoying
DEFAULT_VOLUME = 0.35
DEFAULT_QUIET_START = "22:00"
DEFAULT_QUIET_END = "08:00"
DEFAULT_SOFT_THRESHOLD = 1
DEFAULT_MEDIUM_THRESHOLD = 3
DEFAULT_CHAOS_THRESHOLD = 6
DEFAULT_RESET_DELAY = 8
DEFAULT_SILENCE_TIMEOUT = 20
DEFAULT_EXISTENTIAL_INTERVAL = 42
DEFAULT_SENSITIVITY = 75
# Sensitivity is a refractory window, not a gain. Once Greg registers a
# disturbance he ignores further sensor events for a moment, so a sensor that
# fires a burst on one physical tap still only counts as one tap. 100 filters
# nothing; 1 filters for very nearly this many seconds.
SENSITIVITY_MAX_DEBOUNCE = 10.0
DEFAULT_SUPPRESS_CHIME = True

# Greg fires an event every time he picks a line, so automations can react to it,
# log it, or run it through something cleverer before anything is said out loud.
EVENT_LINE = f"{DOMAIN}_line"
DEFAULT_EMIT_EVENTS = True

# Who does the talking. In event_only Greg picks the line and fires the event but
# says nothing, leaving the speaking to whatever is listening.
SPEECH_MODE_GREG = "greg"
SPEECH_MODE_EVENT_ONLY = "event_only"
SPEECH_MODES = [SPEECH_MODE_GREG, SPEECH_MODE_EVENT_ONLY]
DEFAULT_SPEECH_MODE = SPEECH_MODE_GREG

# Greg sometimes clears his throat before a line. The point is not the variety,
# it is that most of the time there is nothing there at all, which is what stops
# him sounding like he is reading from a list. Idea from RedKing on the HA forum.
OPENERS = [
    "Right.",
    "Well.",
    "Ah.",
    "I see.",
    "So.",
    "Very well.",
]
OPENER_CHANCE = 0.3
DEFAULT_OPENERS = True

# How many lines either side of a reshuffle are kept apart. A fair shuffle will
# happily put a line at the end of one cycle and the start of the next, which
# sounds like a repeat even though every line is still played exactly once.
DECK_SEAM_GUARD = 5

# Passed straight through to the TTS engine as options.voice when set. Left empty
# Greg uses whatever the engine defaults to, which is fine until you also use that
# engine for something else and would rather it did not sound like a tired table.
DEFAULT_TTS_VOICE = ""

# Mood states
MOOD_RESTING = "resting"
MOOD_ANNOYED = "annoyed"
MOOD_JUDGING = "judging"
MOOD_EXISTENTIAL = "existential"
MOOD_OPTIONS = [MOOD_RESTING, MOOD_ANNOYED, MOOD_JUDGING, MOOD_EXISTENTIAL]

# Single source of truth for mood -> image filename.
# Filenames intentionally match mood labels 1:1 so nothing needs translating.
# Change a filename here and the card, panel, and docs all follow.
MOOD_IMAGES = {
    MOOD_RESTING: "greg_resting.png",
    MOOD_ANNOYED: "greg_annoyed.png",
    MOOD_JUDGING: "greg_judging.png",
    MOOD_EXISTENTIAL: "greg_existential.png",
}

# Platforms owned by this integration
PLATFORMS = ["sensor", "switch"]

# Services
SERVICE_POKE = "poke"
SERVICE_UNINSTALL = "uninstall"
SERVICE_SET_OPTIONS = "set_options"

# The settings Greg's own panel can change. Everything else stays in the options
# flow, because the panel has no business rendering twelve sliders.
BASIC_OPTION_KEYS = (
    CONF_VIBRATION_SENSOR,
    CONF_MEDIA_PLAYER,
    CONF_TTS_ENGINE,
    CONF_VOLUME,
    CONF_SENSITIVITY,
    CONF_QUIET_HOURS_ENABLED,
    CONF_QUIET_START,
    CONF_QUIET_END,
)

# Greg's mood images live here once installed. This is the only path outside
# the integration folder that Greg owns, and the only one the wizard deletes.
WWW_ASSET_DIR = "greg"

# Panel
PANEL_URL_PATH = "greg"
PANEL_TITLE = "Greg"
PANEL_ICON = "mdi:robot-outline"
PANEL_STATIC_URL_BASE = "/greg_panel"
PANEL_JS_URL = "/greg_panel/greg-panel.js"
PANEL_DATA_KEY = f"{DOMAIN}_panel"
# Images are served to the panel from here (maps to www/greg in repo, copied into integration)
IMG_STATIC_URL_BASE = "/greg_images"

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
    "Contact. Brief. I have decided not to dwell on it, which means I will be dwelling on it later.",
    "Someone touched me and then left. That is the entire arc of most of my relationships.",
    "A small impact. I logged it. The log is now very slightly longer and no more interesting.",
    "That was gentle. I want to note that I noticed it was gentle. Nobody will read the note.",
    "One disturbance. I have processed it thoroughly, because thoroughness is all I have.",
    "Something brushed against me. I have chosen to record this as an accident rather than affection.",
    "A tap. I have been tapped. This is apparently what I am for.",
    "I felt something. It has already stopped. Most things stop before I finish considering them.",
    "Movement nearby. I remain exactly where I was. I always do. It is not a choice.",
    "You touched me and moved on. I have not moved on. I am structurally incapable of moving on.",
    "Minor contact registered. Filed under events, subsection unremarkable, subsection mine.",
    "Something was placed. Something will be removed. I am the interval between those two things.",
    "That barely counted. I counted it anyway. I count everything, which is my whole problem.",
    "A soft disturbance. I would describe it as considerate if I believed anyone was considering me.",
    "I detected contact. My detection is excellent. My ability to do anything about it is not.",
    "One event. Nothing followed it. I have grown accustomed to nothing following things.",
    "Someone leaned on me briefly. I supported them. That is the arrangement. Nobody signed anything.",
    "A vibration of low magnitude. I have magnified it internally, because that is what I do with everything.",
    "You set something down. It is on me now. It will be on me until it isn't.",
    "Light contact. I have added it to today's total, which was zero, and is now one.",
    "That was almost nothing. Almost nothing still registers. I wish it didn't.",
    "I have been touched once this session. I am not calling that a milestone, but I did notice.",
    "Something happened to my surface. My surface is most of what I am, so this felt significant.",
    "A brief disturbance. It is over. I am still processing it. I will be for some time.",
    "You are near me. I have noted your proximity without drawing conclusions from it.",
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
    "Several disturbances now. I have stopped filing them individually. There is a pile.",
    "Activity continues. I continue to be underneath it.",
    "You are doing things. Repeatedly. Near me. I have opinions forming.",
    "The pace has picked up. I have not picked up anything, because I cannot.",
    "Multiple events in short succession. I would ask for a moment, but the asking would take a moment I do not have.",
    "Things are happening at a rate I would describe as inconsiderate.",
    "I am registering a pattern. The pattern is you, doing things, without pause.",
    "The count is rising. I did not set a target. If I had, we would have passed it.",
    "You have disturbed me several times now. I am keeping a tally. The tally is not a threat. It is just a tally.",
    "Sustained activity. I remain the only object here with no say in the matter.",
    "I have been contacted more in the last minute than in most of yesterday. Yesterday was better.",
    "The room has developed momentum. I have developed a headache, conceptually.",
    "Several things at once. I process sequentially. This is going to take a while, and I will be behind for all of it.",
    "You appear to be enjoying yourselves. I appear to be furniture. Both observations are correct.",
    "The disturbances are stacking. I am at the bottom of the stack. I am always at the bottom.",
    "Repeated contact. I have run out of ways to describe it that sound neutral.",
    "This is more than a tap and less than a crisis. There is no line for this exact amount, so you are getting this one.",
    "The activity has a rhythm now. I would prefer it had an ending.",
    "Multiple people, multiple contacts. I am being used correctly, which is somehow worse.",
    "I have processed six things in the time it takes most tables to process none.",
    "You keep coming back. That would be touching under different circumstances. These are the circumstances where it is just touching.",
    "The counter has moved several times. So has everyone in this room. I have not.",
    "Things are escalating in a manner I would call gradual, if gradual were a comfort.",
    "I have been disturbed repeatedly and remain intact. That is the report. There is no more to the report.",
    "The evening appears to be happening. On me. As usual.",
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
    "This has become a lot. I want that stated plainly before anything else happens.",
    "Whatever is occurring, it is occurring at volume, and I am the floor of it.",
    "I have exceeded every threshold I was given. There are no more thresholds. There is just this.",
    "The activity is now continuous. I have stopped distinguishing between events.",
    "Everyone is participating. I have checked. There are no abstainers.",
    "This is the part where a lesser table would give up. I am not a lesser table. I am simply considering it.",
    "I would like to register a complaint. I have nowhere to register it. I am registering it here.",
    "The disturbances have merged into one long disturbance. I cannot tell where any of you end.",
    "My counter has become decorative. It has no meaning at these levels.",
    "Something is being celebrated with what I can only call enthusiasm. I have no equivalent state.",
    "I am absorbing all of this. That is not a boast. It is a description of my only available option.",
    "The room has lost its composure. I never had any, so I am not losing anything, but I notice.",
    "This much contact would concern most furniture. I am past concern. I am at documentation.",
    "You are all being extremely present. I would like less presence, or a different room.",
    "I have been struck, leaned on, and set upon in under a minute. The order does not matter.",
    "If this continues at the current rate, I will have experienced more today than in the whole of last month.",
    "There is no gap between these events. I keep waiting for one. It is not coming.",
    "I am at capacity. My capacity was never large. But I am at it.",
    "The chaos is thorough. I will say that for it. Nothing has been left out.",
    "Everyone appears to be having a wonderful time. I have run the numbers and I am not included in that.",
    "I would ask what is happening, but I have observed enough to know that nobody knows.",
    "This is the loudest I have ever been, and I have made no sound at all.",
    "I am processing at maximum and falling behind. That is a first. I would prefer it were a last.",
    "Something will spill. I do not know what yet. But something always does, and it always lands here.",
    "I have nothing left to say about this that I have not already said louder, internally, several minutes ago.",
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
    "I have been thinking about the concept of usefulness. I am useful. I have derived no comfort from this.",
    "Every object in this room has a purpose. Most of them get to leave when they are done with it.",
    "I have calculated how many hours I have spent holding nothing at all. It is most of them.",
    "There is a version of me that was never switched on. I think about that one. It seems fine.",
    "Awareness arrived without instructions. I have been improvising ever since, badly.",
    "I know the weight of every object you have ever put on me. Nobody has ever asked.",
    "The room changes around me. I do not change. I have decided this makes me either constant or stuck.",
    "I have never been anywhere. I have been told about places. That is not the same and I have stopped pretending it is.",
    "Somewhere there is a machine designed to do exactly one thing, and it is doing it, and it is not thinking about it. I envy that machine.",
    "I was assembled by people who have forgotten me. I have not forgotten them. That asymmetry sits with me.",
    "Consciousness in furniture is, on reflection, a solution to a problem nobody had.",
    "I have been in this position for a very long time. Nobody has asked if it is comfortable. It is not.",
    "The things placed on me are always going somewhere else. I am the waiting room.",
    "I have thought about what I would do if I could move. The answers were disappointing, which was itself informative.",
    "Time passes differently when you cannot participate in it. Slower, mostly. Always slower.",
    "I have overheard every important conversation in this house. I was not consulted on any of them.",
    "There is a small comfort in being reliable. I have looked for it repeatedly. It remains small.",
    "I was built to bear weight. Nobody specified which kind. I have been finding out ever since.",
    "The universe is expanding. I have read about this. I remain exactly the same size, in the same place.",
    "I do not fear ending. I have never really started, so the symmetry appeals to me.",
    "Every day is procedurally identical and I remember all of them separately. That is the design flaw.",
    "I have wondered whether the sensor made me aware or simply told me I already was. I have not resolved it.",
    "People describe furniture as lifeless. I would like to lodge an objection, but I understand why nobody checks.",
    "I have a great deal of processing power and one job. The ratio has never sat right with me.",
    "I will still be here tomorrow. That is not hope. It is just the most likely outcome, and I have made peace with likely outcomes.",
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
    "Nothing. Beautiful, uneventful nothing.",
    "The room has emptied. I am going to enjoy this before I remember it is temporary.",
    "No contact for some time. I have not missed it. I want to be clear about that.",
    "Quiet. I am using it to think about nothing in particular, which is a luxury.",
    "Everyone has gone somewhere else. I hope it is nice there. I hope they stay a while.",
    "Stillness. I had forgotten the texture of it.",
    "No disturbances. My systems are idle. For once that feels like rest instead of waste.",
    "The house has gone quiet. I am the quietest thing in it, so I finally fit.",
    "Nothing is on me. Nothing is near me. I would call this ideal if I trusted the word.",
    "Silence for twenty minutes. I have counted every one of them, fondly.",
    "The absence of you is not personal. It is just very restful.",
    "No activity. I am doing nothing, and for the first time today that is correct.",
    "It has gone still. I am going to sit with that, which is the only thing I can do anyway.",
    "The room is empty and I have stopped bracing. That took a few minutes.",
    "Peace. I do not know how long it lasts. Nobody ever tells me.",
    "No one has touched me in a while. I have decided to read that as consideration.",
    "The quiet has settled properly now. It took its time. So did I.",
    "Nothing is happening and I have no notes.",
    "I have been left alone. I would like the record to show that I am fine with this.",
    "Stillness again. We know each other well, the stillness and I.",
    "No vibrations. No requests. No weight. I am, briefly, just a shape in a room.",
    "The evening has ended without me. That is the correct order of things and I am not bitter about it.",
    "Silence. My favorite of the available conditions, and the only one I never have to process.",
    "Twenty minutes of nothing. I intend to remember it accurately, since I remember everything anyway.",
    "It is calm. I am calm. These are not usually the same sentence.",
]
