// The ladder's rules, exercised without a browser.
//
// Run with `node tests/ladder.test.mjs`, which is what CI does.
//
// Nothing here needs a document: the ordering rules work on values held on the
// component, and the handles are drawn from those. The loading of the panel
// into a stubbed DOM is in load-panel.mjs.
import assert from "node:assert/strict";
import { loadPanel, run } from "./load-panel.mjs";

const GregPanel = loadPanel();

// A component with just enough on it for the ladder: its own values, and the
// saved config the track's length is read from.
function ladderAt(soft, medium, chaos, savedChaos = null) {
  const panel = Object.create(GregPanel.prototype);
  panel._ladderDraft = {
    soft_threshold: soft,
    medium_threshold: medium,
    chaos_threshold: chaos,
  };
  panel._savedConfig = () => ({
    ladder_max: Math.max(12, savedChaos ?? chaos),
    soft_threshold: soft,
    medium_threshold: medium,
    chaos_threshold: chaos,
  });
  return panel;
}

run({
  "defaults sit where the dialog left them"() {
    const p = ladderAt(1, 3, 6);
    assert.equal(p._ladderMax(), 12);
    // Copied out of the sandbox before comparing: an array built in there has
    // its own realm's prototype, which strict deep-equal counts as a
    // difference all by itself.
    const bounds = (key) => Array.from(p._ladderBounds(key));
    assert.deepEqual(bounds("soft_threshold"), [1, 2]);
    assert.deepEqual(bounds("medium_threshold"), [2, 5]);
    assert.deepEqual(bounds("chaos_threshold"), [4, 12]);
  },

  "the track stretches to fit a chaos above twelve"() {
    const p = ladderAt(1, 3, 20);
    assert.equal(p._ladderMax(), 20);
    // And is not dragged back down by the panel drawing it.
    assert.equal(p._ladder().chaos_threshold, 20);
  },

  "soft cannot be pushed onto medium"() {
    const p = ladderAt(1, 3, 6);
    p._setThreshold("soft_threshold", 9);
    assert.equal(p._ladder().soft_threshold, 2);
    assert.equal(p._ladder().medium_threshold, 3);
  },

  "chaos cannot be dragged below medium"() {
    const p = ladderAt(1, 3, 6);
    p._setThreshold("chaos_threshold", 1);
    assert.equal(p._ladder().chaos_threshold, 4);
  },

  "medium is penned in on both sides"() {
    const p = ladderAt(2, 5, 7);
    p._setThreshold("medium_threshold", 99);
    assert.equal(p._ladder().medium_threshold, 6);
    p._setThreshold("medium_threshold", -99);
    assert.equal(p._ladder().medium_threshold, 3);
  },

  "soft never goes below one tap"() {
    const p = ladderAt(1, 3, 6);
    p._setThreshold("soft_threshold", -40);
    assert.equal(p._ladder().soft_threshold, 1);
  },

  "chaos stops at the end of the track"() {
    const p = ladderAt(1, 3, 6);
    p._setThreshold("chaos_threshold", 500);
    assert.equal(p._ladder().chaos_threshold, 12);
  },

  "a drag reports whether anything actually moved"() {
    const p = ladderAt(1, 3, 6);
    // Every pointermove fires this, and a redraw per pixel of a drag that
    // changed nothing is wasted work.
    assert.equal(p._setThreshold("soft_threshold", 1.2), false);
    assert.equal(p._setThreshold("soft_threshold", 2), true);
  },

  "fractional positions from a drag land on whole taps"() {
    const p = ladderAt(1, 5, 9);
    p._setThreshold("medium_threshold", 6.7);
    assert.equal(p._ladder().medium_threshold, 7);
    p._setThreshold("medium_threshold", 6.2);
    assert.equal(p._ladder().medium_threshold, 6);
  },

  "labels never overlap, whatever the values"() {
    const p = ladderAt(1, 3, 6);
    // Widths of "soft 1", "medium 12", "chaos 20" at the panel's 11px, near
    // enough. The narrow case is the settings popover at 300px.
    const widths = [30, 55, 48];
    const track = 263;
    for (let soft = 1; soft <= 10; soft++) {
      for (let medium = soft + 1; medium <= 11; medium++) {
        for (let chaos = medium + 1; chaos <= 12; chaos++) {
          const centres = [soft, medium, chaos].map((v) => ((v - 1) / 11) * track);
          const placed = p._spreadLabels(centres, widths, track);
          for (let i = 1; i < placed.length; i++) {
            const gap = placed[i] - placed[i - 1];
            const needed = (widths[i - 1] + widths[i]) / 2;
            assert.ok(
              gap >= needed,
              `overlap at ${soft}/${medium}/${chaos}: gap ${gap.toFixed(1)} < ${needed}`
            );
          }
        }
      }
    }
  },

  "labels stay on the track at both ends"() {
    const p = ladderAt(1, 2, 3);
    const widths = [30, 55, 48];
    const track = 263;
    // Hard left, and hard right.
    for (const values of [[1, 2, 3], [10, 11, 12], [1, 6, 12]]) {
      const centres = values.map((v) => ((v - 1) / 11) * track);
      const placed = p._spreadLabels(centres, widths, track);
      placed.forEach((x, i) => {
        assert.ok(x - widths[i] / 2 >= -0.5, `label ${i} runs off the left at ${values}`);
        assert.ok(x + widths[i] / 2 <= track + 0.5, `label ${i} runs off the right at ${values}`);
      });
    }
  },

  "no sequence of drags can cross them"() {
    const p = ladderAt(1, 3, 6);
    const keys = ["soft_threshold", "medium_threshold", "chaos_threshold"];
    let seed = 7;
    const random = () => (seed = (seed * 1103515245 + 12345) % 2147483648) / 2147483648;
    for (let i = 0; i < 4000; i++) {
      p._setThreshold(keys[Math.floor(random() * 3)], Math.round(random() * 26) - 4);
      const v = p._ladder();
      assert.ok(
        v.soft_threshold >= 1 &&
          v.soft_threshold < v.medium_threshold &&
          v.medium_threshold < v.chaos_threshold,
        `crossed after ${i} drags: ${JSON.stringify(v)}`
      );
    }
  },
});
