"""Which locale Greg asks for, and which voice he asks for.

Every bug in this area has had the same shape: Greg quietly not using the
thing the user configured, with no error anywhere obvious. 1.5.5 had three in
a row. So the choosing lives in const.py as plain functions and is pinned
here, rather than being reasoned about in a method that needs a running Home
Assistant to reach.

The case that started this one is rujelus22's on the forum: a Piper voice
installed by hand, working in his own automations, ignored by Greg.
"""
import importlib.util
import pathlib
import unittest

CONST = pathlib.Path(__file__).resolve().parents[1] / "custom_components" / "greg" / "const.py"
_spec = importlib.util.spec_from_file_location("greg_const", CONST)
const = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(const)

choose_locale = const.choose_locale
match_voice = const.match_voice
voice_locale = const.voice_locale

# What the Piper add-on advertises on a machine with both English voice sets.
PIPER_LANGUAGES = ["de_DE", "en_GB", "en_US", "nl_BE", "nl_NL", "pt_PT"]


class TestVoiceLocale(unittest.TestCase):
    def test_reads_the_locale_out_of_a_piper_name(self):
        self.assertEqual(voice_locale("en_US-glados-high"), "en_US")
        self.assertEqual(voice_locale("nl_NL-ronnie-medium"), "nl_NL")
        self.assertEqual(voice_locale("pt_PT-tugão-medium"), "pt_PT")

    def test_underscores_in_a_voice_name_do_not_confuse_it(self):
        # rujelus22's other voice is en_US-Jarvis_Real-medium.
        self.assertEqual(voice_locale("en_US-Jarvis_Real-medium"), "en_US")

    def test_a_name_with_no_locale_has_none(self):
        for name in ["", "alan", "glados-high", "x", None]:
            with self.subTest(name=name):
                self.assertIsNone(voice_locale(name))


class TestChooseLocale(unittest.TestCase):
    def test_the_voice_decides_when_the_engine_offers_its_locale(self):
        # The bug rujelus22 hit. Without the voice, English falls to whichever
        # locale sorts first, and his en_US voice is then checked against the
        # en_GB list and thrown away.
        self.assertEqual(
            choose_locale("en", PIPER_LANGUAGES, "en_US-glados-high"), "en_US"
        )

    def test_english_without_a_voice_is_unchanged(self):
        # Alphabetical, as it has always been. Nobody's working setup moves.
        self.assertEqual(choose_locale("en", PIPER_LANGUAGES, ""), "en_GB")

    def test_a_voice_cannot_drag_another_language_to_its_own(self):
        # An English voice left over from an English-only setup must not make
        # Dutch come out as en_US. That is the 1.5.5 bug in reverse.
        self.assertEqual(
            choose_locale("nl", PIPER_LANGUAGES, "en_US-glados-high"), "nl_NL"
        )

    def test_region_matching_still_wins_for_dutch_and_portuguese(self):
        self.assertEqual(choose_locale("nl", PIPER_LANGUAGES, ""), "nl_NL")
        self.assertEqual(choose_locale("pt", PIPER_LANGUAGES, ""), "pt_PT")

    def test_an_exact_bare_code_is_taken_as_is(self):
        self.assertEqual(choose_locale("en", ["en", "en_US"], ""), "en")

    def test_a_voice_locale_the_engine_does_not_offer_is_ignored(self):
        # Asking for a locale that was never advertised is what silenced him
        # outright in 1.5.5b2, so an unadvertised one is never sent.
        self.assertEqual(choose_locale("en", ["en_GB"], "en_US-glados-high"), "en_GB")

    def test_nothing_advertised_means_let_the_engine_choose(self):
        self.assertIsNone(choose_locale("en", [], "en_US-glados-high"))
        self.assertIsNone(choose_locale("en", None, ""))

    def test_a_language_the_engine_does_not_speak_is_left_out(self):
        self.assertIsNone(choose_locale("pt", ["en_GB", "en_US"], ""))

    def test_case_in_advertised_codes_does_not_matter(self):
        self.assertEqual(choose_locale("en", ["EN_US"], "en_US-glados-high"), "EN_US")


class TestMatchVoice(unittest.TestCase):
    def test_an_advertised_voice_is_used_as_is(self):
        self.assertEqual(
            match_voice("en_GB-alan-low", ["en_GB-alan-low", "en_GB-jenny-medium"]),
            ("en_GB-alan-low", "exact"),
        )

    def test_a_voice_installed_by_hand_is_still_asked_for(self):
        # The heart of it. Piper loads a voice sitting in its share folder
        # that Wyoming never advertised, so an unrecognised name is sent.
        self.assertEqual(
            match_voice("en_US-glados-high", ["en_US-lessac-medium"]),
            ("en_US-glados-high", "unlisted"),
        )

    def test_a_missing_accent_is_corrected_to_the_engines_spelling(self):
        # The 1.5.5 trap: the README itself gave the name without the tilde.
        self.assertEqual(
            match_voice("pt_PT-tugao-medium", ["pt_PT-tugão-medium"]),
            ("pt_PT-tugão-medium", "corrected"),
        )

    def test_case_alone_is_also_corrected(self):
        self.assertEqual(
            match_voice("EN_US-Lessac-Medium", ["en_US-lessac-medium"]),
            ("en_US-lessac-medium", "corrected"),
        )

    def test_nothing_advertised_means_trust_what_was_typed(self):
        self.assertEqual(match_voice("en_US-glados-high", []), ("en_US-glados-high", "exact"))
        self.assertEqual(match_voice("en_US-glados-high", None), ("en_US-glados-high", "exact"))

    def test_no_voice_configured_sends_nothing(self):
        self.assertEqual(match_voice("", ["en_GB-alan-low"]), (None, "none"))

    def test_objects_with_a_voice_id_are_understood(self):
        # Home Assistant hands back Voice objects, not strings.
        class Voice:
            def __init__(self, voice_id):
                self.voice_id = voice_id

        self.assertEqual(
            match_voice("en_GB-alan-low", [Voice("en_GB-alan-low")]),
            ("en_GB-alan-low", "exact"),
        )

    def test_what_is_sent_is_always_a_real_name(self):
        # Folding is for comparing only. A folded name must never reach the
        # engine, because Piper matches character for character.
        sent, _ = match_voice("pt_PT-tugao-medium", ["pt_PT-tugão-medium"])
        self.assertIn("ã", sent)


class TestTheForumCase(unittest.TestCase):
    """rujelus22's setup, end to end through both decisions."""

    def test_his_custom_voice_now_gets_asked_for(self):
        voice = "en_US-glados-high"
        # Only the voices the add-on advertises for the locale. His own are
        # not among them: they are .onnx files he dropped into the share.
        advertised_for_en_us = ["en_US-lessac-medium", "en_US-ryan-high"]

        locale = choose_locale("en", PIPER_LANGUAGES, voice)
        self.assertEqual(locale, "en_US")

        sent, how = match_voice(voice, advertised_for_en_us)
        self.assertEqual(sent, voice)
        self.assertEqual(how, "unlisted")

    def test_before_the_fix_it_would_have_been_dropped(self):
        # Pinning the old behaviour as the thing that must not come back:
        # English chose en_GB, and his en_US voice was not in that list.
        locale_without_the_voice = choose_locale("en", PIPER_LANGUAGES, "")
        self.assertEqual(locale_without_the_voice, "en_GB")
        self.assertNotEqual(
            choose_locale("en", PIPER_LANGUAGES, "en_US-glados-high"),
            locale_without_the_voice,
        )


if __name__ == "__main__":
    unittest.main()
