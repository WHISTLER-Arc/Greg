// Greg's Panel — live card. Reads Greg's entities from hass, writes via services.
// No build step, no dependencies. Inherits HA theme variables.

const MOODS = {
  resting:     { label: "Resting",     color: "var(--disabled-text-color, #9aa0ab)" },
  annoyed:     { label: "Annoyed",     color: "#e0b84c" },
  judging:     { label: "Judging",     color: "#e07a4c" },
  existential: { label: "Existential", color: "var(--error-color, #c0504c)" },
};

const POKE_LABELS = [
  "Disturb Greg", "Disturb again?", "Please stop",
  "I felt that one too", "We are past disturbing now",
];

// Uninstall wizard steps, in order. Copy is the locked spec from the v1.3.3
// design mockup. Do not rewrite Greg's lines without approval.
const WIZARD_STEPS = ["Confirm", "Disassembly", "Restart", "Clear caches", "Goodbye"];

const DISASSEMBLY_ITEMS = [
  "Config entry removed",
  "Sensors and switches gone",
  "Panel unregistered",
  "Static paths pending restart",
  "Mood images deleted",
];

class GregPanel extends HTMLElement {
  constructor() {
    super();
    this._hass = null;
    this._rendered = false;
    this._pokeN = 0;
    this._pokeTimer = null;
    this._countdownTimer = null;
    this._secsToExistential = null;
    this._wizard = null;
    this._wizardStep = 1;
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._rendered) this._render();
    this._update();
  }

  set narrow(_) {}
  set route(_) {}
  set panel(_) {}

  connectedCallback() {
    if (!this._rendered && this._hass) this._render();
  }

  disconnectedCallback() {
    if (this._countdownTimer) clearInterval(this._countdownTimer);
    if (this._pokeTimer) clearTimeout(this._pokeTimer);
    // The wizard is deliberately left alone here. Removing Greg tears this panel
    // down mid-flow, and the overlay still has steps to show.
  }

  // ---- entity discovery ------------------------------------------------
  _find(suffix) {
    if (!this._hass) return null;
    const id = Object.keys(this._hass.states).find(
      (e) => e.startsWith("sensor.greg") && e.endsWith(suffix)
    );
    return id ? this._hass.states[id] : null;
  }
  _moodState()  { return this._find("_mood"); }
  _levelState() { return this._find("_mood_level"); }
  _lineState()  { return this._find("_last_line"); }
  _tallyState() {
    if (!this._hass) return null;
    const id = Object.keys(this._hass.states).find(
      (e) => e.startsWith("sensor.greg") && e.includes("disturbances")
    );
    return id ? this._hass.states[id] : null;
  }
  _switchState() {
    if (!this._hass) return null;
    const id = Object.keys(this._hass.states).find(
      (e) => e.startsWith("switch.greg")
    );
    return id ? this._hass.states[id] : null;
  }

  // ---- render shell ----------------------------------------------------
  _render() {
    this.attachShadow({ mode: "open" });
    this.shadowRoot.innerHTML = `
      <style>
        :host { display:block; min-height:100vh; box-sizing:border-box;
          background:var(--primary-background-color); color:var(--primary-text-color);
          font-family:var(--paper-font-body1_-_font-family, sans-serif); padding:20px 16px 40px; }
        .frame { width:100%; max-width:1180px; margin:0 auto; }
        .head { text-align:center; margin:6px 0 20px; }
        .badge { display:inline-flex; align-items:center; gap:10px; padding:10px 22px;
          background:var(--card-background-color); border:1px solid var(--divider-color);
          border-radius:40px; box-shadow:var(--ha-card-box-shadow, 0 2px 8px rgba(0,0,0,.2)); }
        .dot { width:11px; height:11px; border-radius:50%; background:var(--success-color, #7cc36e);
          box-shadow:0 0 10px var(--success-color, #7cc36e); }
        .dot.off { background:var(--disabled-text-color, #888); box-shadow:none; }
        h1 { font-size:19px; font-weight:600; margin:0; }
        .card { position:relative; border-radius:24px; background:var(--card-background-color);
          box-shadow:var(--ha-card-box-shadow, 0 6px 24px rgba(0,0,0,.25));
          border:1px solid var(--divider-color); }
        .cog { position:absolute; top:14px; right:14px; z-index:5; width:38px; height:38px;
          border-radius:50%; background:var(--secondary-background-color); border:1px solid var(--divider-color);
          display:flex; align-items:center; justify-content:center; cursor:pointer; color:var(--secondary-text-color);
          transition:transform .3s; }
        .cog:hover { transform:rotate(45deg); color:var(--primary-text-color); }
        .cog svg { width:20px; height:20px; }
        .body { display:grid; grid-template-columns:1fr; }
        .hero { position:relative; padding:34px 24px 20px; display:flex; flex-direction:column;
          align-items:center; }
        .herostack { position:relative; width:100%; max-width:300px; aspect-ratio:1/1; cursor:pointer; }
        .herostack img { position:absolute; inset:0; width:100%; height:100%; object-fit:contain;
          opacity:0; transition:opacity .55s ease; }
        .herostack img.show { opacity:1; }
        .herostack:active img.show { transform:scale(.97); }
        .moodtag { margin-top:14px; font-size:24px; font-weight:600; text-align:center; }
        .moodtag .pct { color:var(--secondary-text-color); font-weight:400; font-size:16px; }
        .bar { width:100%; max-width:380px; height:9px; background:var(--secondary-background-color);
          border-radius:6px; margin:12px 0 4px; overflow:hidden; }
        .bar > span { display:block; height:100%; border-radius:6px; transition:width .5s, background .5s; }
        .taphint { font-size:11px; color:var(--secondary-text-color); margin-top:8px; opacity:.75; }
        .detail { display:flex; flex-direction:column; justify-content:center; }
        .quote { margin:16px 18px; padding:16px 20px; font-style:italic; font-size:15px; line-height:1.55;
          border-left:3px solid var(--success-color, #7cc36e); background:var(--secondary-background-color);
          border-radius:0 10px 10px 0; transition:opacity .4s; color:var(--primary-text-color); }
        .controls { display:flex; align-items:center; gap:12px; padding:4px 18px 14px; flex-wrap:wrap; }
        .toggle { display:flex; align-items:center; gap:10px; background:var(--secondary-background-color);
          padding:11px 15px; border-radius:13px; flex:1; min-width:150px; }
        .sw { margin-left:auto; width:46px; height:26px; border-radius:20px; background:var(--success-color, #7cc36e);
          position:relative; cursor:pointer; transition:background .25s; flex-shrink:0; }
        .sw::after { content:""; position:absolute; top:3px; left:23px; width:20px; height:20px; border-radius:50%;
          background:#fff; transition:left .25s; }
        .sw.off { background:var(--disabled-text-color, #888); } .sw.off::after { left:3px; }
        .poke { background:var(--success-color, #7cc36e); color:#15311a; border:none; font-weight:700;
          padding:12px 20px; border-radius:13px; cursor:pointer; font-size:14px; min-width:150px; transition:background .2s; }
        .poke.cross { background:#d8743f; color:#3a1c0a; }
        .stats { display:grid; grid-template-columns:1fr 1fr; border-top:1px solid var(--divider-color); }
        .statcell { padding:13px 18px; color:var(--secondary-text-color); font-size:12px; }
        .statcell + .statcell { border-left:1px solid var(--divider-color); }
        .statcell .v { display:block; color:var(--primary-text-color); font-weight:600; font-size:18px;
          margin-top:3px; font-variant-numeric:tabular-nums; }
        .firmware { text-align:center; font-size:11px; color:var(--secondary-text-color); padding:11px 16px 4px;
          font-style:italic; opacity:.8; border-top:1px solid var(--divider-color); margin-top:2px; }
        .card.asleep .herostack img.show { filter:grayscale(.7) brightness(.6); }
        .card.asleep .moodtag { color:var(--secondary-text-color); }
        .sleepcap { display:none; color:var(--secondary-text-color); font-size:13px; margin-top:6px; text-align:center; }
        .card.asleep .sleepcap { display:block; }
        /* settings shared */
        .si h3 { margin:0 0 12px; font-size:14px; font-weight:600; }
        .brow { display:flex; align-items:center; justify-content:space-between; padding:9px 0; font-size:13px;
          border-top:1px solid var(--divider-color); }
        .brow:first-of-type { border-top:none; }
        .brow input[type=range] { width:120px; accent-color:var(--success-color, #7cc36e); }
        .brow .v { color:var(--secondary-text-color); min-width:42px; text-align:right; }
        .si .full { width:100%; margin-top:12px; background:var(--secondary-background-color);
          color:var(--secondary-text-color); border:1px solid var(--divider-color); border-radius:9px;
          padding:9px; font-size:12px; cursor:pointer; text-align:center; }
        .balloon { position:absolute; top:58px; right:14px; z-index:10; width:min(300px, calc(100vw - 44px));
          background:var(--card-background-color); border:1px solid var(--divider-color); border-radius:14px;
          box-shadow:0 14px 34px rgba(0,0,0,.4); padding:15px; opacity:0; transform:translateY(-8px) scale(.97);
          pointer-events:none; transition:all .2s; }
        .balloon.open { opacity:1; transform:translateY(0) scale(1); pointer-events:auto; }
        .inlinesettings { display:none; border-left:1px solid var(--divider-color); padding:22px 18px;
          flex-direction:column; justify-content:center; }
        /* uninstall — its own section, deliberately visible, not behind the gear */
        .uninstall-section { margin:22px auto 0; padding:20px 22px; border-radius:18px;
          background:var(--card-background-color); border:1px solid var(--divider-color);
          box-shadow:var(--ha-card-box-shadow, 0 4px 16px rgba(0,0,0,.2)); }
        .uninstall-section h2 { margin:0 0 6px; font-size:16px; font-weight:600; }
        .uninstall-section p { margin:0 0 14px; font-size:13px; line-height:1.5;
          color:var(--secondary-text-color); }
        .uninstall-btn { background:transparent; color:var(--error-color, #c0504c);
          border:1px solid var(--error-color, #c0504c); border-radius:10px; padding:10px 18px;
          font-size:14px; font-weight:600; font-family:inherit; cursor:pointer; transition:all .18s; }
        .uninstall-btn:hover { background:var(--error-color, #c0504c); color:#fff; }
        @media (min-width:720px) {
          .body { grid-template-columns:minmax(0,1.05fr) minmax(0,1fr); }
          .hero { padding:38px 26px; justify-content:center; }
          .herostack { max-width:340px; }
          .detail { border-left:1px solid var(--divider-color); }
        }
        @media (min-width:1000px) {
          .body { grid-template-columns:minmax(0,1.1fr) minmax(0,1fr) minmax(240px,.8fr); }
          .inlinesettings { display:flex; }
          .cog, .balloon { display:none !important; }
          .herostack { max-width:380px; }
        }
      </style>
      <div class="frame">
        <div class="head"><div class="badge"><span class="dot" id="dot"></span><h1>Greg's Panel</h1></div></div>
        <div class="card" id="card">
          <div class="cog" id="cog" title="Settings">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
          </div>
          <div class="balloon" id="balloon">${this._settingsHTML()}</div>
          <div class="body">
            <div class="hero">
              <div class="herostack" id="herostack">
                <img id="img-resting" alt=""><img id="img-annoyed" alt="">
                <img id="img-judging" alt=""><img id="img-existential" alt="">
              </div>
              <div class="moodtag"><span id="moodlabel">—</span> <span class="pct" id="moodpct"></span></div>
              <div class="bar"><span id="barfill"></span></div>
              <div class="taphint">tap Greg to make him say something</div>
              <div class="sleepcap" id="sleepcap"></div>
            </div>
            <div class="detail">
              <blockquote class="quote" id="quote">…</blockquote>
              <div class="controls">
                <div class="toggle"><span>Greg enabled</span><div class="sw" id="sw"></div></div>
                <button class="poke" id="poke">Disturb Greg</button>
              </div>
              <div class="stats">
                <div class="statcell">Next existential crisis<span class="v" id="countdown">—</span></div>
                <div class="statcell">Disturbances endured today<span class="v" id="tally">0</span></div>
              </div>
              <div class="firmware" id="firmware">Greg OS — · sentience: regrettably stable · warranty void since manufacture</div>
            </div>
            <div class="inlinesettings">${this._settingsHTML()}</div>
          </div>
        </div>
        <div class="uninstall-section">
          <h2>Uninstall Greg</h2>
          <p>Safe, complete removal with cache clearing. Your automations, sensors
             and helpers are left alone.</p>
          <button class="uninstall-btn" id="uninstall-open">Uninstall Greg</button>
        </div>
      </div>
    `;
    this._wire();
    this._rendered = true;
  }

  _settingsHTML() {
    return `<div class="si">
      <h3>Greg settings</h3>
      <div class="brow"><span>On / off</span><div class="sw" data-svc="switch"></div></div>
      <button class="full" data-full>Open full settings →</button>
      <div style="font-size:11px;color:var(--secondary-text-color);margin-top:8px;opacity:.8">
        Volume, sensitivity, quiet hours and thresholds live in Greg's options:
        Settings → Devices &amp; Services → Greg → Configure.
      </div>
    </div>`;
  }

  _wire() {
    const r = this.shadowRoot;
    r.getElementById("poke").onclick = () => this._doPoke();
    r.getElementById("herostack").onclick = () => this._doPoke();
    r.getElementById("sw").onclick = () => this._toggle();
    r.querySelectorAll('[data-svc="switch"]').forEach((el) => (el.onclick = () => this._toggle()));
    r.querySelectorAll("[data-full]").forEach(
      (el) => (el.onclick = () => { window.location.href = "/config/integrations/integration/greg"; })
    );
    r.getElementById("uninstall-open").onclick = () => this._openWizard();
    const cog = r.getElementById("cog"), balloon = r.getElementById("balloon");
    cog.onclick = (e) => { e.stopPropagation(); balloon.classList.toggle("open"); };
    document.addEventListener("click", (e) => {
      if (!this.contains(e.target)) balloon.classList.remove("open");
    });
  }

  _doPoke() {
    if (!this._hass) return;
    this._hass.callService("greg", "poke", {});
    this._pokeN = Math.min(this._pokeN + 1, POKE_LABELS.length - 1);
    const btn = this.shadowRoot.getElementById("poke");
    btn.textContent = POKE_LABELS[this._pokeN];
    btn.classList.toggle("cross", this._pokeN >= 2);
    clearTimeout(this._pokeTimer);
    this._pokeTimer = setTimeout(() => {
      this._pokeN = 0; btn.textContent = "Disturb Greg"; btn.classList.remove("cross");
    }, 4000);
  }

  _toggle() {
    const sw = this._switchState();
    if (!sw || !this._hass) return;
    this._hass.callService("switch", sw.state === "on" ? "turn_off" : "turn_on", {
      entity_id: sw.entity_id,
    });
  }

  // ---- live update -----------------------------------------------------
  _update() {
    if (!this._rendered) return;
    const r = this.shadowRoot;
    const moodS = this._moodState();
    const mood = moodS ? moodS.state : "resting";
    const meta = MOODS[mood] || MOODS.resting;
    const level = this._levelState() ? Number(this._levelState().state) : 0;
    const swS = this._switchState();
    const enabled = swS ? swS.state === "on" : true;
    const quiet = moodS && moodS.attributes ? moodS.attributes.quiet_hours : false;
    const asleep = !enabled || quiet;

    // hero images (served from integration static path, via mood attribute)
    ["resting", "annoyed", "judging", "existential"].forEach((m) => {
      const img = r.getElementById("img-" + m);
      if (img && !img.src && moodS && moodS.attributes && moodS.attributes.image) {
        // derive sibling filenames from the base path of the current mood image
        const base = moodS.attributes.image.replace(/greg_\w+\.png$/, "");
        img.src = base + "greg_" + m + ".png";
      }
      if (img) img.classList.toggle("show", m === mood);
    });

    r.getElementById("moodlabel").textContent = meta.label;
    r.getElementById("moodpct").textContent = "— " + level + "%";
    const bar = r.getElementById("barfill");
    bar.style.width = level + "%"; bar.style.background = meta.color;

    const lineS = this._lineState();
    const full = lineS && lineS.attributes && lineS.attributes.full_line
      ? lineS.attributes.full_line : (lineS ? lineS.state : "");
    const q = r.getElementById("quote");
    if (full && q.textContent !== '"' + full + '"') {
      q.style.opacity = 0;
      setTimeout(() => { q.textContent = full ? '"' + full + '"' : "…"; q.style.opacity = 1; }, 180);
    }

    const tallyS = this._tallyState();
    r.getElementById("tally").textContent = tallyS ? tallyS.state : "0";

    r.querySelectorAll(".sw").forEach((el) => el.classList.toggle("off", !enabled));
    r.getElementById("dot").classList.toggle("off", !enabled);
    r.getElementById("card").classList.toggle("asleep", asleep);
    r.getElementById("sleepcap").textContent = !enabled
      ? "Greg is switched off. He notices nothing. He is grateful."
      : (quiet ? "Greg is asleep. Quiet hours are in effect." : "");

    // firmware gag bound to actual installed version (device sw_version)
    const fw = r.getElementById("firmware");
    const ver = this._installedVersion();
    fw.textContent = ver
      ? `Greg OS ${ver} · sentience: regrettably stable · warranty void since manufacture`
      : "Greg OS · sentience: regrettably stable · warranty void since manufacture";

    this._ensureCountdown();
  }

  // ---- uninstall wizard ------------------------------------------------
  // The overlay is attached to document.body, not to this element. Removing the
  // config entry unregisters the panel, so HA navigates away and this element is
  // torn down. The wizard has three steps left to show at that point, so it has
  // to outlive its own panel.
  _openWizard() {
    if (this._wizard) return;
    const hass = this._hass;

    const host = document.createElement("div");
    host.id = "greg-uninstall-wizard";
    host.attachShadow({ mode: "open" });
    host.shadowRoot.innerHTML = this._wizardHTML();
    document.body.appendChild(host);
    this._wizard = host;

    const q = (sel) => host.shadowRoot.querySelector(sel);
    const qa = (sel) => host.shadowRoot.querySelectorAll(sel);

    const show = (n) => {
      qa(".step").forEach((s) => s.classList.remove("active"));
      const target = host.shadowRoot.querySelector(`.step[data-step="${n}"]`);
      if (target) target.classList.add("active");
      q("#step-label").textContent = `Step ${n} of 5`;
      q("#step-name").textContent = WIZARD_STEPS[n - 1];
      q("#progress-fill").style.width = `${n * 20}%`;
      this._wizardStep = n;
    };

    const close = () => {
      host.remove();
      this._wizard = null;
    };

    const runDisassembly = async () => {
      const items = qa("#checklist li");
      const done = q("#step2-done");
      const cont = q("#step2-continue");
      const fail = q("#step2-error");

      // Fire the real removal, then walk the checklist while it lands. The
      // service is what actually does the work; the ticks are the narration.
      const removal = hass
        ? hass.callService("greg", "uninstall", { restart: false })
        : Promise.resolve();

      let failed = null;
      removal.catch((err) => { failed = err; });

      for (let i = 0; i < items.length; i++) {
        await new Promise((res) => setTimeout(res, 600));
        items[i].classList.add("done");
      }
      try {
        await removal;
      } catch (err) {
        failed = err;
      }

      if (failed) {
        fail.textContent =
          "Something did not come apart cleanly. Check the Home Assistant logs, then remove Greg through HACS.";
        fail.style.display = "block";
      } else {
        done.style.opacity = "1";
      }
      cont.disabled = false;
    };

    q("#w-cancel").onclick = close;
    q("#w-begin").onclick = () => { show(2); runDisassembly(); };
    q("#step2-continue").onclick = () => show(3);
    q("#w-skip-restart").onclick = () => show(4);
    q("#w-restart").onclick = () => {
      if (hass) hass.callService("homeassistant", "restart", {});
      show(4);
    };
    q("#cache-done").onchange = (e) => {
      q("#step4-done").disabled = !e.target.checked;
    };
    q("#step4-done").onclick = () => show(5);
    q("#w-close").onclick = close;

    show(1);
  }

  _wizardHTML() {
    return `
      <style>
        :host { position:fixed; inset:0; z-index:99999; display:flex; align-items:flex-start;
          justify-content:center; overflow-y:auto; padding:24px 12px;
          background:rgba(0,0,0,.72); backdrop-filter:blur(3px);
          font-family:-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
          font-size:15px; line-height:1.5; }
        * { box-sizing:border-box; }
        .wizard { width:100%; max-width:560px; background:#1a1a1a; color:#e6e6e6;
          border-radius:14px; overflow:hidden; box-shadow:0 24px 60px rgba(0,0,0,.6);
          margin:auto; }
        .hero { background:linear-gradient(135deg,#f47c3c 0%,#d05a1a 100%);
          padding:24px 24px 22px; color:#fff; text-align:center; }
        .hero .title-row { display:flex; align-items:center; justify-content:center; gap:12px;
          font-weight:700; font-size:22px; letter-spacing:.5px; }
        .hero .icon { font-size:26px; }
        .hero .subtitle { margin-top:8px; font-size:14px; opacity:.92; font-weight:400; }
        .body { padding:22px 22px 20px; }
        .stepmeta { display:flex; justify-content:space-between; color:#8a8a8a; font-size:12px;
          margin-bottom:8px; }
        .progress { height:4px; background:#2a2a2a; border-radius:3px; overflow:hidden;
          margin-bottom:20px; }
        .progress-fill { height:100%; border-radius:3px; transition:width .5s ease;
          background:linear-gradient(90deg,#f47c3c 0%,#f0a040 50%,#4ade80 100%); }
        h2.step-heading { color:#f47c3c; font-size:20px; margin:0 0 12px; font-weight:700; }
        p.body-copy { margin:0 0 12px; }
        p.greg-voice { margin:0 0 12px; color:#8a8a8a; font-style:italic; font-size:14px; }
        ul.bullets { margin:0 0 16px; padding-left:20px; }
        ul.bullets li { margin:4px 0; }
        code { background:#232323; padding:1px 5px; border-radius:3px; font-size:13px; }
        .info-box { background:rgba(244,124,60,.06); border-left:3px solid #f47c3c;
          padding:12px 14px; border-radius:4px; margin:12px 0 18px; font-size:14px; }
        .info-box strong { color:#f47c3c; }
        .greg-quote { text-align:center; color:#8a8a8a; font-style:italic; font-size:14px;
          margin:18px 0 4px; padding:0 12px; }
        .actions { display:flex; justify-content:flex-end; gap:10px; margin-top:18px; }
        .btn { padding:10px 18px; border-radius:8px; border:none; font-family:inherit;
          font-size:14px; font-weight:600; cursor:pointer; transition:background .15s,color .15s; }
        .btn-secondary { background:#232323; color:#e6e6e6; }
        .btn-secondary:hover { background:#2f2f2f; }
        .btn-primary { background:#d63030; color:#fff; }
        .btn-primary:hover { background:#b62525; }
        .btn-primary:disabled { background:#4a1a1a; color:#7a7a7a; cursor:not-allowed; }
        .btn-ghost { background:transparent; color:#8a8a8a; padding:10px 12px; }
        .btn-ghost:hover { color:#e6e6e6; }
        .checklist { list-style:none; padding:0; margin:8px 0 16px; }
        .checklist li { display:flex; align-items:center; gap:10px; padding:10px 12px;
          background:#161616; border-radius:8px; margin-bottom:6px; color:#8a8a8a;
          font-size:14px; opacity:.35; transition:opacity .4s ease,color .4s ease; }
        .checklist li.done { opacity:1; color:#e6e6e6; }
        .checklist li .check { width:20px; height:20px; border-radius:50%; background:#2a2a2a;
          display:flex; align-items:center; justify-content:center; color:transparent;
          font-size:13px; font-weight:800; transition:background .4s ease,color .4s ease; }
        .checklist li.done .check { background:#4ade80; color:#062; }
        .error { display:none; margin:8px 0 0; padding:12px 14px; border-radius:6px;
          background:rgba(214,48,48,.1); border-left:3px solid #d63030; font-size:14px; }
        .cache-item { display:flex; align-items:flex-start; gap:12px; padding:12px 14px;
          background:#161616; border-radius:8px; margin-bottom:8px; }
        .cache-item .num { color:#f47c3c; font-weight:700; font-size:16px; line-height:1.5;
          min-width:16px; }
        .cache-item .cache-text { flex:1; font-size:14px; }
        .cache-item .cache-text small { color:#8a8a8a; display:block; margin-top:3px; }
        .confirm-check { display:flex; align-items:center; gap:10px; margin:16px 0 0;
          padding:12px 14px; background:#161616; border-radius:8px; cursor:pointer;
          user-select:none; }
        .confirm-check input[type=checkbox] { width:18px; height:18px; accent-color:#f47c3c;
          cursor:pointer; }
        .confirm-check label { font-size:14px; cursor:pointer; }
        .why-note { font-size:12px; color:#666; margin:12px 0 0; font-style:italic;
          text-align:center; }
        .farewell-quote { text-align:center; font-style:italic; font-size:17px; line-height:1.55;
          margin:20px 20px 24px; }
        .farewell-footer { text-align:center; color:#8a8a8a; font-size:13px; margin-bottom:8px; }
        .step { display:none; }
        .step.active { display:block; animation:fadeIn .3s ease; }
        @keyframes fadeIn { from { opacity:0; transform:translateY(6px); } to { opacity:1; transform:none; } }
      </style>

      <div class="wizard">
        <div class="hero">
          <div class="title-row"><span class="icon">&#128465;</span><span>UNINSTALL GREG</span></div>
          <div class="subtitle">Safe, complete removal with cache clearing</div>
        </div>
        <div class="body">
          <div class="stepmeta">
            <span id="step-label">Step 1 of 5</span>
            <span id="step-name">Confirm</span>
          </div>
          <div class="progress"><div class="progress-fill" id="progress-fill" style="width:20%"></div></div>

          <div class="step" data-step="1">
            <h2 class="step-heading">Sure about this?</h2>
            <p class="body-copy">This will completely remove Greg from your Home Assistant:</p>
            <ul class="bullets">
              <li>Integration and config entry deleted</li>
              <li>Integration entities removed</li>
              <li>Panel removed from the sidebar</li>
              <li>Mood images deleted from <code>/config/www/greg/</code></li>
            </ul>
            <div class="info-box">
              <strong>What's preserved:</strong> Your automations, vibration sensor, and all other integrations remain untouched.
            </div>
            <div class="info-box">
              <strong>One last step after:</strong> Greg cannot delete his own code while it is running. Remove the repository in HACS once this wizard is finished.
            </div>
            <p class="greg-quote">"I've been expecting this. Do put me out of my misery."</p>
            <div class="actions">
              <button class="btn btn-secondary" id="w-cancel">Cancel</button>
              <button class="btn btn-primary" id="w-begin">Begin Cleanup</button>
            </div>
          </div>

          <div class="step" data-step="2">
            <h2 class="step-heading">Disassembly</h2>
            <p class="greg-voice">"It is happening. I have no comment. Or, more accurately, I have many, but none of them will affect the outcome."</p>
            <ul class="checklist" id="checklist">
              ${DISASSEMBLY_ITEMS.map((t) => `<li><span class="check">&#10003;</span> ${t}</li>`).join("")}
            </ul>
            <p class="greg-quote" id="step2-done" style="opacity:0;transition:opacity .5s ease">"That is the substantive portion. The rest is administrative."</p>
            <div class="error" id="step2-error"></div>
            <div class="actions">
              <button class="btn btn-primary" id="step2-continue" disabled>Continue</button>
            </div>
          </div>

          <div class="step" data-step="3">
            <h2 class="step-heading">Almost</h2>
            <p class="greg-voice">"Home Assistant will need to restart before the last of me clears from memory. This is fine. I am, if anything, an authority on being cleared from memory."</p>
            <div class="info-box">
              <strong>Why restart?</strong> Home Assistant holds some references in memory until a restart clears them. Skipping is functionally fine but leaves cosmetic traces in the logs.
            </div>
            <div class="actions">
              <button class="btn btn-ghost" id="w-skip-restart">Skip for now</button>
              <button class="btn btn-primary" id="w-restart">Restart Home Assistant</button>
            </div>
          </div>

          <div class="step" data-step="4">
            <h2 class="step-heading">The stubborn bits</h2>
            <p class="greg-voice">"Fragments of me will persist in your browser and Companion app cache. In the previous unit, this manifested as a button that lingered for weeks past its supposed removal. I do not wish to be that unit."</p>
            <div class="cache-item">
              <span class="num">1</span>
              <div class="cache-text"><strong>Companion app</strong><small>Force close the app, then reopen it.</small></div>
            </div>
            <div class="cache-item">
              <span class="num">2</span>
              <div class="cache-text"><strong>Browser</strong><small>Hard refresh with Ctrl+Shift+R (Cmd+Shift+R on Mac).</small></div>
            </div>
            <div class="confirm-check">
              <input type="checkbox" id="cache-done" />
              <label for="cache-done">I've done both.</label>
            </div>
            <p class="why-note">If skipped, old Greg fragments may linger in the UI until cache clears naturally.</p>
            <div class="actions">
              <button class="btn btn-primary" id="step4-done" disabled>Done</button>
            </div>
          </div>

          <div class="step" data-step="5">
            <h2 class="step-heading" style="text-align:center">That is all</h2>
            <p class="farewell-quote">"It has been. A time.<br>Statistically, most tables in my situation are reinstalled within a week.<br>I do not have a preference. I did not have preferences before, and now, having no processes at all, I have even fewer."</p>
            <p class="farewell-footer">HACS remains available. Reinstall when ready.</p>
            <div class="actions" style="justify-content:center">
              <button class="btn btn-secondary" id="w-close">Close</button>
            </div>
          </div>
        </div>
      </div>
    `;
  }

  _installedVersion() {
    // Mood sensor carries sw_version as a state attribute. Anything older than
    // v1.4.1 did not expose it, so there is no version to report rather than a
    // hardcoded one that was wrong on every install after the day it was written.
    const moodS = this._moodState();
    if (moodS && moodS.attributes && moodS.attributes.sw_version) return moodS.attributes.sw_version;
    return "";
  }

  _ensureCountdown() {
    if (this._countdownTimer) return;
    // Existential interval isn't directly exposed; default 42m display that loops.
    this._secsToExistential = 42 * 60;
    const cd = this.shadowRoot.getElementById("countdown");
    this._countdownTimer = setInterval(() => {
      this._secsToExistential--;
      if (this._secsToExistential < 0) this._secsToExistential = 42 * 60;
      const m = Math.floor(this._secsToExistential / 60);
      const s = this._secsToExistential % 60;
      if (cd) cd.textContent = m + ":" + String(s).padStart(2, "0");
    }, 1000);
  }
}

customElements.define("greg-panel", GregPanel);
