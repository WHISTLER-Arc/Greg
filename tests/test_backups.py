"""Reading and writing a backup file.

The file is the only thing that carries somebody's lines between two Gregs, so
what it means has to be pinned rather than assumed. tests/fixtures/sample-backup.txt
is the same file the panel's writer is tested against in ladder.test.mjs, which
is what stops the reader here and the writer there drifting apart.
"""
import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location(
    "greg_const", ROOT / "custom_components" / "greg" / "const.py"
)
const = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(const)

parse = const.parse_lines_backup
write = const.format_lines_backup

POOLS = ("soft", "medium", "chaos", "existential", "silence")
LANGUAGES = ("en", "nl", "pt")
SAMPLE = (ROOT / "tests" / "fixtures" / "sample-backup.txt").read_text(encoding="utf8")

BLOB = {
    "en": {
        "soft": ["Oh. You again.", "I felt that in my drawers."],
        "chaos": ["This is fine. I am fine. Nothing is fine."],
        "silence": ["Hello? No, nothing. Good."],
    },
    "nl": {"soft": ["Daar ben je weer."]},
    "pt": {"medium": ["Outra vez, não."]},
}


class TestWriting(unittest.TestCase):
    def test_writes_the_sample_file_exactly(self):
        self.assertEqual(
            write(BLOB, POOLS, "Greg lines, exported 2026-10-07 from Greg v1.7.0"),
            SAMPLE,
        )

    def test_pools_come_out_in_gregs_order_not_alphabetical(self):
        text = write({"en": {"silence": ["c"], "soft": ["a"], "chaos": ["b"]}}, POOLS)
        self.assertEqual(
            [l for l in text.splitlines() if l.startswith("### ")],
            ["### soft", "### chaos", "### silence"],
        )

    def test_empty_pools_and_languages_are_left_out(self):
        text = write({"en": {"soft": [], "chaos": ["only this"]}, "nl": {}}, POOLS)
        self.assertNotIn("## nl", text)
        self.assertNotIn("### soft", text)
        self.assertIn("### chaos", text)

    def test_nothing_written_gives_an_empty_file_rather_than_an_error(self):
        self.assertEqual(write({}, POOLS).strip(), "")


class TestReading(unittest.TestCase):
    def test_reads_the_sample_file_back_to_what_made_it(self):
        found, skipped = parse(SAMPLE, LANGUAGES, POOLS)
        self.assertEqual(found, BLOB)
        self.assertEqual(skipped["lines"], 0)
        self.assertEqual(skipped["orphans"], 0)

    def test_round_trips_through_both(self):
        found, _ = parse(write(BLOB, POOLS, "a title line"), LANGUAGES, POOLS)
        self.assertEqual(found, BLOB)

    def test_a_file_typed_by_hand_is_forgiven(self):
        # No title, inconsistent blank lines, a note in the middle, trailing
        # spaces, and headings in the wrong case.
        text = (
            "## EN\n"
            "### Soft\n"
            "-   Oh. You again.   \n"
            "\n"
            "some notes to myself here\n"
            "- I felt that in my drawers.\n"
        )
        found, skipped = parse(text, LANGUAGES, POOLS)
        self.assertEqual(
            found, {"en": {"soft": ["Oh. You again.", "I felt that in my drawers."]}}
        )
        self.assertEqual(skipped["lines"], 0)

    def test_whitespace_inside_a_line_is_collapsed(self):
        found, _ = parse("## en\n### soft\n- Oh.   You    again.", LANGUAGES, POOLS)
        self.assertEqual(found["en"]["soft"], ["Oh. You again."])

    def test_duplicates_within_a_pool_are_dropped(self):
        found, _ = parse("## en\n### soft\n- Same\n- Same\n- Other", LANGUAGES, POOLS)
        self.assertEqual(found["en"]["soft"], ["Same", "Other"])

    def test_an_unknown_language_is_skipped_and_counted(self):
        text = "## kl\n### soft\n- Qapla'\n## en\n### soft\n- Fine."
        found, skipped = parse(text, LANGUAGES, POOLS)
        self.assertEqual(found, {"en": {"soft": ["Fine."]}})
        self.assertEqual(skipped["languages"], ["kl"])
        self.assertEqual(skipped["lines"], 1)

    def test_an_unknown_pool_is_skipped_and_counted(self):
        text = "## en\n### funny\n- Not a pool\n### soft\n- A pool."
        found, skipped = parse(text, LANGUAGES, POOLS)
        self.assertEqual(found, {"en": {"soft": ["A pool."]}})
        self.assertEqual(skipped["pools"], ["funny"])
        self.assertEqual(skipped["lines"], 1)

    def test_lines_before_any_heading_are_counted_as_orphans(self):
        found, skipped = parse("- homeless line\n- another", LANGUAGES, POOLS)
        self.assertEqual(found, {})
        self.assertEqual(skipped["orphans"], 2)

    def test_a_pool_does_not_leak_into_the_next_language(self):
        # Without resetting the pool at a language heading, these lines would
        # land in English's soft pool, which is somebody else's language.
        text = "## en\n### soft\n- English line\n## nl\n- Dutch line with no pool"
        found, skipped = parse(text, LANGUAGES, POOLS)
        self.assertEqual(found, {"en": {"soft": ["English line"]}})
        self.assertEqual(skipped["lines"], 1)

    def test_accents_survive_the_trip(self):
        found, _ = parse(SAMPLE, LANGUAGES, POOLS)
        self.assertEqual(found["pt"]["medium"], ["Outra vez, não."])

    def test_nothing_usable_is_not_an_error(self):
        for text in ["", "   ", None, "just some prose\nwith no headings"]:
            with self.subTest(text=text):
                found, _ = parse(text, LANGUAGES, POOLS)
                self.assertEqual(found, {})

    def test_a_markdown_heading_for_something_else_is_ignored(self):
        # "# Greg" is a title, not a language. Only ## and ### mean anything.
        found, _ = parse("# Greg\n## en\n### soft\n- Fine.", LANGUAGES, POOLS)
        self.assertEqual(found, {"en": {"soft": ["Fine."]}})

    def test_a_github_issue_body_can_be_read_straight_back(self):
        # What the Share button writes, which has no language heading: it
        # names the language in prose instead. Nothing is recovered from it,
        # but it must not be mistaken for lines in the wrong language.
        text = "Language: `en`\n\n### soft\n\n- A line from an issue."
        found, skipped = parse(text, LANGUAGES, POOLS)
        self.assertEqual(found, {})
        self.assertEqual(skipped["lines"], 1)


if __name__ == "__main__":
    unittest.main()
