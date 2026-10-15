// Loads the real greg-panel.js so its logic can be tested without a browser.
//
// The panel is a custom element and expects a DOM, so the few globals it
// touches while defining itself are stubbed, and the class is caught as it
// registers itself with the fake customElements.
//
// Beware when comparing: anything the sandbox builds (arrays, objects) carries
// its own realm's prototypes, which node's strict deep-equal counts as a
// difference. Copy values out before comparing them.
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
import vm from "node:vm";

export function loadPanel() {
  const here = path.dirname(fileURLToPath(import.meta.url));
  const source = readFileSync(
    path.join(here, "..", "custom_components", "greg", "panel", "greg-panel.js"),
    "utf8"
  );

  let GregPanel = null;
  const sandbox = {
    HTMLElement: class {},
    customElements: { define: (_name, cls) => { GregPanel = cls; } },
    document: { createElement: () => ({ style: {} }) },
    window: {},
    console,
  };
  sandbox.globalThis = sandbox;
  vm.createContext(sandbox);
  vm.runInContext(source, sandbox);
  if (!GregPanel) throw new Error("greg-panel.js did not register the panel element");
  return GregPanel;
}

export function run(tests) {
  let failed = 0;
  for (const [name, fn] of Object.entries(tests)) {
    try {
      fn();
      console.log(`ok   ${name}`);
    } catch (err) {
      failed++;
      console.error(`FAIL ${name}\n     ${err.message}`);
    }
  }
  console.log(`\n${Object.keys(tests).length - failed} passed, ${failed} failed`);
  process.exit(failed ? 1 : 0);
}
