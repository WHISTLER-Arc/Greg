// The panel's half of a backup: writing the file, and reading enough of one
// to tell the user what they are about to import.
//
// Pinned against tests/fixtures/sample-backup.txt, the same file the reader in
// const.py is tested against by test_backups.py. Those two tests are what stop
// the writer here and the reader there drifting apart, which nothing else
// would catch until somebody's restore came back empty.
//
// Run with `node tests/backup.test.mjs`, which is what CI does.
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { loadPanel, run } from "./load-panel.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));
const SAMPLE = readFileSync(path.join(here, "fixtures", "sample-backup.txt"), "utf8");

const BLOB = {
  en: {
    soft: ["Oh. You again.", "I felt that in my drawers."],
    chaos: ["This is fine. I am fine. Nothing is fine."],
    silence: ["Hello? No, nothing. Good."],
  },
  nl: { soft: ["Daar ben je weer."] },
  pt: { medium: ["Outra vez, não."] },
};

const GregPanel = loadPanel();

// A panel holding somebody's lines, with nothing else on it.
function panelWith(customLines) {
  const panel = Object.create(GregPanel.prototype);
  panel._moodState = () => ({
    attributes: { custom_lines: customLines, version: "v1.7.0" },
  });
  return panel;
}

// Everything but the title line, which carries today's date.
const body = (text) => text.split("\n").slice(1).join("\n");

run({
  "writes the same file const.py reads"() {
    assert.equal(body(panelWith(BLOB)._backupText()), body(SAMPLE));
  },

  "titles the file with the date and Greg's version"() {
    const first = panelWith(BLOB)._backupText().split("\n")[0];
    assert.match(first, /^Greg lines, exported \d{4}-\d{2}-\d{2} from Greg v1\.7\.0$/);
  },

  "pools come out in Greg's order, not alphabetical"() {
    const text = panelWith({ en: { silence: ["c"], soft: ["a"], chaos: ["b"] } })._backupText();
    assert.deepEqual(
      Array.from(text.split("\n").filter((l) => l.startsWith("### "))),
      ["### soft", "### chaos", "### silence"]
    );
  },

  "empty pools and languages are left out"() {
    const text = panelWith({ en: { soft: [], chaos: ["only this"] }, nl: {} })._backupText();
    assert.ok(!text.includes("## nl"));
    assert.ok(!text.includes("### soft"));
    assert.ok(text.includes("### chaos"));
  },

  "nothing written gives a file with no lines in it"() {
    const text = panelWith({})._backupText();
    assert.equal(panelWith({})._countBackup(text).lines, 0);
  },

  "counts what is in a file before importing it"() {
    const counted = panelWith({})._countBackup(SAMPLE);
    assert.equal(counted.lines, 6);
    assert.deepEqual(Array.from(counted.languages), ["en", "nl", "pt"]);
  },

  "counting ignores headings, notes and blank bullets"() {
    const counted = panelWith({})._countBackup(
      "# Greg\nsome notes\n## en\n### soft\n- a line\n-   \n- another\n"
    );
    assert.equal(counted.lines, 2);
    assert.deepEqual(Array.from(counted.languages), ["en"]);
  },

  "counting survives a file saved with Windows line endings"() {
    // A backup edited in Notepad comes back with \r\n, and a \r left on the
    // end of a heading would make every language name wrong.
    const counted = panelWith({})._countBackup(SAMPLE.replace(/\n/g, "\r\n"));
    assert.equal(counted.lines, 6);
    assert.deepEqual(Array.from(counted.languages), ["en", "nl", "pt"]);
  },

  "a file with no lines is distinguishable from one with lines"() {
    assert.equal(panelWith({})._countBackup("just prose, no bullets").lines, 0);
  },
});
