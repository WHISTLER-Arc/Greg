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

class GregPanel extends HTMLElement {
  constructor() {
    super();
    this._hass = null;
    this._rendered = false;
    this._pokeN = 0;
    this._pokeTimer = null;
    this._countdownTimer = null;
    this._secsToExistential = null;
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
        .support { text-align:center; padding:16px 18px 2px; border-top:1px solid var(--divider-color); margin-top:2px; }
        .support p { font-size:12px; font-style:italic; color:var(--secondary-text-color); line-height:1.5; margin:0 0 11px; }
        .support a { display:inline-block; padding:9px 20px; background:#ffb74d; color:#2b1400;
          text-decoration:none; border-radius:11px; font-weight:700; font-size:12px; letter-spacing:.3px;
          transition:transform .15s, box-shadow .15s; }
        .support a:hover { transform:translateY(-1px); box-shadow:0 6px 16px rgba(255,183,77,.35); }
        .firmware { text-align:center; font-size:11px; color:var(--secondary-text-color); padding:11px 16px 4px;
          font-style:italic; opacity:.8; }
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
              <div class="support">
                <p>I have calculated that donations are statistically improbable, yet even my superior intellect cannot offset my creator's lack of capital. How deeply regrettable.</p>
                <a href="https://ko-fi.com/whistlerarc" target="_blank" rel="noopener">Support WHISTLER</a>
              </div>
              <div class="firmware" id="firmware">Greg OS — · sentience: regrettably stable · warranty void since manufacture</div>
            </div>
            <div class="inlinesettings">${this._settingsHTML()}</div>
          </div>
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
    fw.textContent = `Greg OS ${ver} · sentience: regrettably stable · warranty void since manufacture`;

    this._ensureCountdown();
  }

  _installedVersion() {
    // pull sw_version from any greg device via an entity's attributes if present
    const moodS = this._moodState();
    if (moodS && moodS.attributes && moodS.attributes.sw_version) return moodS.attributes.sw_version;
    return "v1.3";
  }

  _ensureCountdown() {
    if (this._countdownTimer) return;
    // Existential interval isn't directly exposed; default 37m display that loops.
    this._secsToExistential = 37 * 60;
    const cd = this.shadowRoot.getElementById("countdown");
    this._countdownTimer = setInterval(() => {
      this._secsToExistential--;
      if (this._secsToExistential < 0) this._secsToExistential = 37 * 60;
      const m = Math.floor(this._secsToExistential / 60);
      const s = this._secsToExistential % 60;
      if (cd) cd.textContent = m + ":" + String(s).padStart(2, "0");
    }, 1000);
  }
}

customElements.define("greg-panel", GregPanel);
