"""The panel carries copies of a few of Greg's constants. They have to match.

greg-panel.js cannot import from const.py, so it restates the handful of
numbers it needs. Nothing fails when one of them drifts: the panel simply
starts describing limits Greg does not have, which is the same quiet kind of
wrong that MAINTAINING.md exists to prevent for the docs.

Read out of the JS with regular expressions rather than by running it. This
runs on a bare machine with no node, and the point is only to compare numbers.
"""
import importlib.util
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PANEL = ROOT / "custom_components" / "greg" / "panel" / "greg-panel.js"

_spec = importlib.util.spec_from_file_location(
    "greg_const", ROOT / "custom_components" / "greg" / "const.py"
)
const = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(const)

SOURCE = PANEL.read_text(encoding="utf8")


class TestPanelParity(unittest.TestCase):
    def test_timing_limits_match(self):
        # _timingLimits() returns { key: [low, high, fallback] }.
        block = re.search(r"_timingLimits\(\)\s*\{.*?return\s*\{(.*?)\};", SOURCE, re.S)
        self.assertIsNotNone(block, "could not find _timingLimits() in greg-panel.js")

        found = {
            key: (int(low), int(high), int(fallback))
            for key, low, high, fallback in re.findall(
                r"(\w+):\s*\[\s*(\d+),\s*(\d+),\s*(\d+)\s*\]", block.group(1)
            )
        }
        expected = {key: tuple(value) for key, value in const.TIMING_LIMITS.items()}
        self.assertEqual(found, expected)

    def test_ladder_track_max_matches(self):
        # The panel falls back to this when the integration has not published
        # ladder_max yet, which is the case for the first render after a
        # restart.
        fallback = re.search(r"Number\.isFinite\(published\) \? published : (\d+)", SOURCE)
        self.assertIsNotNone(fallback, "could not find the ladder_max fallback")
        self.assertEqual(int(fallback.group(1)), const.LADDER_TRACK_MAX)

    def test_conditions_max_matches(self):
        found = re.search(r"const CONDITIONS_MAX = (\d+);", SOURCE)
        self.assertIsNotNone(found)
        self.assertEqual(int(found.group(1)), const.CONDITIONS_MAX)

    def test_dead_states_match(self):
        found = re.search(r"const DEAD_STATES = \[(.*?)\];", SOURCE)
        self.assertIsNotNone(found)
        states = tuple(re.findall(r'"([^"]+)"', found.group(1)))
        self.assertEqual(states, const.SPEAKER_DEAD_STATES)

    def test_default_thresholds_match(self):
        # The ladder's own fallbacks, used before the first config arrives.
        for key, expected in [
            ("soft_threshold", const.DEFAULT_SOFT_THRESHOLD),
            ("medium_threshold", const.DEFAULT_MEDIUM_THRESHOLD),
            ("chaos_threshold", const.DEFAULT_CHAOS_THRESHOLD),
        ]:
            with self.subTest(key=key):
                found = re.findall(rf"{key}: Number\(\w+\.{key} \?\? (\d+)\)", SOURCE)
                self.assertTrue(found, f"no fallback found for {key}")
                self.assertEqual(
                    set(found), {str(expected)},
                    f"{key} falls back to {set(found)}, const.py says {expected}",
                )


if __name__ == "__main__":
    unittest.main()
