"""The ladder has to climb, whatever is stored.

Run with `python -m unittest discover -s tests`, which is what CI does. No
Home Assistant and no pytest: const.py is loaded straight off disk, because
importing it as part of the package would pull in __init__.py and with it the
whole of Home Assistant, which is not installed on a laptop or on a runner.
"""
import importlib.util
import pathlib
import unittest

CONST = pathlib.Path(__file__).resolve().parents[1] / "custom_components" / "greg" / "const.py"
_spec = importlib.util.spec_from_file_location("greg_const", CONST)
const = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(const)

normalise = const.normalise_thresholds


class TestNormaliseThresholds(unittest.TestCase):
    def test_defaults_are_left_alone(self):
        self.assertEqual(
            normalise(
                const.DEFAULT_SOFT_THRESHOLD,
                const.DEFAULT_MEDIUM_THRESHOLD,
                const.DEFAULT_CHAOS_THRESHOLD,
            ),
            (1, 3, 6),
        )

    def test_any_already_climbing_ladder_is_untouched(self):
        for ladder in [(1, 2, 3), (2, 5, 9), (1, 3, 20), (4, 8, 12)]:
            with self.subTest(ladder=ladder):
                self.assertEqual(normalise(*ladder), ladder)

    def test_crossed_pair_is_sorted_rather_than_pushed_apart(self):
        # The numbers are likelier to be what somebody meant than the labels,
        # so chaos comes back as 6 rather than being shoved out past medium.
        self.assertEqual(normalise(1, 6, 4), (1, 4, 6))

    def test_fully_reversed_ladder(self):
        self.assertEqual(normalise(6, 3, 1), (1, 3, 6))

    def test_equal_values_are_separated(self):
        # Equal is as broken as crossed: with medium == chaos, medium can never
        # be reached, because Greg tests chaos first.
        self.assertEqual(normalise(3, 3, 3), (3, 4, 5))
        self.assertEqual(normalise(1, 3, 3), (1, 3, 4))

    def test_zero_and_negative_are_lifted_to_one(self):
        # One tap is the least that can set him off. Zero would fire on a
        # counter that has just been reset.
        self.assertEqual(normalise(0, 3, 6), (1, 3, 6))
        self.assertEqual(normalise(-5, -1, 0), (1, 2, 3))

    def test_missing_values_fall_back_to_the_defaults(self):
        self.assertEqual(normalise(None, None, None), (1, 3, 6))
        self.assertEqual(normalise(2, None, 9), (2, 3, 9))

    def test_junk_falls_back_rather_than_raising(self):
        # The config entry is a file a user can edit by hand, and a bad value
        # there must not stop Greg loading.
        self.assertEqual(normalise("", "three", []), (1, 3, 6))

    def test_strings_that_are_numbers_are_accepted(self):
        # Anything arriving through a service call or the panel is text.
        self.assertEqual(normalise("1", "4", "8"), (1, 4, 8))

    def test_floats_are_truncated_not_rejected(self):
        self.assertEqual(normalise(1.9, 3.2, 6.7), (1, 3, 6))

    def test_result_is_always_strictly_increasing(self):
        for soft in range(-2, 8):
            for medium in range(-2, 8):
                for chaos in range(-2, 8):
                    a, b, c = normalise(soft, medium, chaos)
                    with self.subTest(stored=(soft, medium, chaos)):
                        self.assertGreaterEqual(a, const.THRESHOLD_MIN)
                        self.assertLess(a, b)
                        self.assertLess(b, c)

    def test_normalising_twice_changes_nothing(self):
        # The panel writes back what it was given, so a value that moved on
        # read must not keep moving on every save.
        for ladder in [(1, 6, 4), (3, 3, 3), (0, 0, 0), (9, 2, 5)]:
            with self.subTest(ladder=ladder):
                once = normalise(*ladder)
                self.assertEqual(normalise(*once), once)


if __name__ == "__main__":
    unittest.main()
