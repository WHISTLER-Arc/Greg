// Greg's Panel, the live card. Reads Greg's entities from hass, writes via services.
// No build step, no dependencies. Inherits HA theme variables.

const MOODS = {
  resting:     { label: "Resting",     color: "var(--disabled-text-color, #9aa0ab)" },
  annoyed:     { label: "Annoyed",     color: "#e0b84c" },
  judging:     { label: "Judging",     color: "#e07a4c" },
  existential: { label: "Existential", color: "var(--error-color, #c0504c)" },
};

// Matches CONDITIONS_MAX in const.py. The cap is there so a malformed
// automation cannot write thousands of rows into the config entry, not
// because a house has twenty core conditions.
const CONDITIONS_MAX = 20;

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
    if (this._onDocClick) {
      document.removeEventListener("click", this._onDocClick);
      this._onDocClick = null;
    }
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
        .linescard { margin:18px 0 0; padding:18px; background:var(--card-background-color);
          border:1px solid var(--divider-color); border-radius:16px;
          box-shadow:var(--ha-card-box-shadow, 0 2px 8px rgba(0,0,0,.2)); }
        .lineshead { display:flex; align-items:baseline; justify-content:space-between;
          gap:12px; flex-wrap:wrap; margin-bottom:12px; }
        .lineshead h3 { margin:0; font-size:15px; letter-spacing:.02em; }
        .pooltabs { display:flex; flex-wrap:wrap; gap:6px; margin-bottom:10px; }
        .pooltab { padding:7px 13px; border-radius:9px; cursor:pointer; font-size:12px;
          font-family:inherit; background:var(--secondary-background-color);
          color:var(--primary-text-color); border:1px solid var(--divider-color); }
        .pooltab.active { background:var(--success-color, #7cc36e); color:#14301a;
          border-color:var(--success-color, #7cc36e); font-weight:600; }
        .poolnote { font-size:12px; color:var(--secondary-text-color); margin-bottom:10px; }
        .lineslist { display:flex; flex-direction:column; gap:6px; margin-bottom:10px; }
        .lineitem { display:flex; align-items:flex-start; gap:10px; padding:10px 12px;
          background:var(--secondary-background-color); border-radius:11px; font-size:13px;
          line-height:1.45; }
        .lineitem span { flex:1; word-break:break-word; }
        .lineitem button { background:none; border:none; cursor:pointer; font-size:16px;
          line-height:1; color:var(--secondary-text-color); padding:0 2px; }
        .lineitem button:hover { color:var(--error-color, #c0504c); }
        .linesempty { font-size:13px; color:var(--secondary-text-color); font-style:italic;
          padding:10px 0; }
        .lineadd { display:flex; gap:8px; align-items:flex-start; }
        .lineadd textarea { flex:1; resize:vertical; padding:9px 10px; border-radius:9px;
          font:inherit; font-size:13px; color:var(--primary-text-color);
          background:var(--secondary-background-color); border:1px solid var(--divider-color); }
        .linesonly { margin-top:14px; }
        .linesonly .ghint { display:block; }
        .linesfoot { display:flex; gap:8px; flex-wrap:wrap; margin-top:14px; }
        .linescard .btn { padding:11px 18px; border-radius:11px; cursor:pointer; font-size:13px;
          font-family:inherit; background:var(--secondary-background-color);
          color:var(--primary-text-color); border:1px solid var(--divider-color);
          transition:opacity .2s; }
        .linescard .btn.primary { background:var(--success-color, #7cc36e); color:#14301a;
          border:0; padding:11px 22px; font-weight:700; }
        .linescard .btn:disabled { opacity:.32; cursor:default; }
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
        .detail { display:flex; flex-direction:column; justify-content:center;
          border-top:1px solid var(--divider-color); }
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
        .sw[aria-checked="false"] { background:var(--disabled-text-color, #888); }
        .sw[aria-checked="false"]::after { left:3px; }
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
        .si h3 { font-size:12px; letter-spacing:.09em; text-transform:uppercase;
          color:var(--secondary-text-color); margin:0; font-weight:600;
          display:flex; align-items:center; gap:8px; }
        .si h3::after { content:""; flex:1; height:1px; background:var(--divider-color); }
        .gfield { display:flex; flex-direction:column; gap:5px; }
        .gfield > label { font-size:12px; color:var(--secondary-text-color);
          display:flex; justify-content:space-between; align-items:baseline; gap:8px; }
        .gval { color:var(--primary-text-color); font-weight:600; font-size:12px;
          font-variant-numeric:tabular-nums; }
        .ghint { font-size:11px; color:var(--secondary-text-color); opacity:.8; margin:0; }
        .si select, .si input[type="time"], .si input[type="text"] { width:100%; box-sizing:border-box;
          background:var(--secondary-background-color); color:var(--primary-text-color);
          border:1px solid var(--divider-color); border-radius:9px; padding:9px 10px;
          font-size:13px; font-family:inherit; appearance:none; }
        .si input[type="time"] { font-variant-numeric:tabular-nums; }
        .gselwrap { position:relative; }
        .gselwrap::after { content:""; position:absolute; right:12px; top:50%; width:7px;
          height:7px; margin-top:-5px; pointer-events:none; transform:rotate(45deg);
          border-right:1.5px solid var(--secondary-text-color);
          border-bottom:1.5px solid var(--secondary-text-color); }
        .si input[type="range"] { width:100%; appearance:none; background:transparent; margin:3px 0; }
        .si input[type="range"]::-webkit-slider-runnable-track { height:5px; border-radius:4px;
          background:var(--secondary-background-color); }
        .si input[type="range"]::-webkit-slider-thumb { appearance:none; width:15px; height:15px;
          border-radius:50%; background:var(--success-color, #7cc36e); margin-top:-5px; cursor:pointer; }
        .si input[type="range"]::-moz-range-track { height:5px; border-radius:4px;
          background:var(--secondary-background-color); }
        .si input[type="range"]::-moz-range-thumb { width:15px; height:15px; border:0;
          border-radius:50%; background:var(--success-color, #7cc36e); cursor:pointer; }
        .grow { display:flex; align-items:center; gap:10px; font-size:13px;
          background:var(--secondary-background-color); border-radius:11px; padding:10px 12px; }
        .grow .sw { border:0; padding:0; }
        .gapply { background:var(--success-color, #7cc36e); color:#14301a; border:0;
          border-radius:11px; padding:11px; font-size:13px; font-weight:700;
          font-family:inherit; cursor:pointer; transition:opacity .2s; }
        .gapply[disabled] { opacity:.32; cursor:default; }
        .si :focus-visible { outline:2px solid var(--success-color, #7cc36e); outline-offset:2px; }
        /* One settings block, moved by CSS rather than rendered twice. Below
           1000px it is the popover behind the cog; at 1000px and up it is the
           right-hand column. Same node either way, so nothing has to be kept
           in sync with a second copy and anything stateful inside it can use
           ids, the way the lines card already does. */
        .si { position:absolute; top:58px; right:14px; z-index:10; box-sizing:border-box;
          width:min(300px, calc(100vw - 44px));
          /* The block is tall and pinned near the top of the card, so without
             these the bottom of it runs off a short screen with no way to
             reach it. contain stops a scroll that runs out here from carrying
             on into the page underneath, which is what makes it feel broken
             on a touchscreen. */
          max-height:calc(100vh - 120px); overflow-y:auto; overscroll-behavior:contain;
          background:var(--card-background-color); border:1px solid var(--divider-color);
          border-radius:14px; box-shadow:0 14px 34px rgba(0,0,0,.4); padding:15px;
          display:flex; flex-direction:column; gap:13px;
          opacity:0; transform:translateY(-8px) scale(.97);
          pointer-events:none; transition:opacity .2s, transform .2s; }
        .si.open { opacity:1; transform:translateY(0) scale(1); pointer-events:auto; }
        /* Greg and what he just said, stacked, so settings gets a column of
           its own rather than being the squeezed third of three. */
        .col { display:flex; flex-direction:column; min-width:0; }
        /* When Greg keeps quiet. Its own card, one instance, full width and
           below the mood card, the way the lines card works. Quiet hours and
           conditions are the same question and belong in the same place, and
           conditions is unbounded in height, which a 300px popover is not. */
        .quietcard { margin:18px 0 0; padding:18px; background:var(--card-background-color);
          border:1px solid var(--divider-color); border-radius:16px;
          box-shadow:var(--ha-card-box-shadow, 0 2px 8px rgba(0,0,0,.2)); }
        .quiethead { display:flex; align-items:baseline; justify-content:space-between;
          gap:12px; flex-wrap:wrap; margin-bottom:14px; }
        .quiethead h3 { margin:0; font-size:15px; letter-spacing:.02em; }
        .qhours { display:flex; align-items:center; gap:12px; flex-wrap:wrap;
          background:var(--secondary-background-color); border-radius:13px; padding:12px 14px; }
        .qhours .qlabel { flex:1; min-width:150px; }
        .qhours .qtimes { display:flex; align-items:center; gap:8px; }
        .qhours .qtimes.hidden { display:none; }
        .qhours input[type="time"] { width:92px; box-sizing:border-box; text-align:center;
          background:var(--card-background-color); color:var(--primary-text-color);
          border:1px solid var(--divider-color); border-radius:9px; padding:9px 10px;
          font-size:13px; font-family:inherit; font-variant-numeric:tabular-nums; }
        .qcondhead { display:flex; align-items:center; justify-content:space-between;
          gap:10px; margin:18px 0 8px; }
        .qcondadd { background:var(--secondary-background-color); color:var(--primary-text-color);
          border:1px solid var(--divider-color); border-radius:9px; padding:7px 13px;
          font-size:12px; font-family:inherit; cursor:pointer; }
        .qcondadd[disabled] { opacity:.32; cursor:default; }
        .gcondlist { display:flex; flex-direction:column; gap:8px; }
        .gcondlist:empty { display:none; }
        /* One row per line on a phone, three across once there is room. */
        .gcond { background:var(--secondary-background-color); border-radius:11px;
          padding:10px 12px; display:grid; gap:8px; align-items:center;
          grid-template-columns:1fr auto; }
        .gcond.warn { box-shadow:inset 0 0 0 1px var(--warning-color, #e5a50a); }
        .gcond > .gcondent { grid-column:1; }
        .gcond > .gcondx { grid-column:2; }
        .gcond > .gcondop, .gcond > .gcondval { grid-column:1 / -1; }
        .gcond > .gcondnote { grid-column:1 / -1; font-size:11px;
          color:var(--secondary-text-color); opacity:.8; }
        .gcond.warn > .gcondnote { color:var(--warning-color, #e5a50a); opacity:1; }
        .gcond input[type="text"], .gcond select { width:100%; box-sizing:border-box;
          background:var(--card-background-color); color:var(--primary-text-color);
          border:1px solid var(--divider-color); border-radius:9px; padding:9px 10px;
          font-size:13px; font-family:inherit; appearance:none; }
        .gcondx { background:none; border:0; color:var(--secondary-text-color);
          font-size:17px; line-height:1; padding:2px 6px; font-family:inherit; cursor:pointer; }
        .gcondx:hover { color:var(--error-color, #c0504c); }
        @media (min-width:620px) {
          .gcond { grid-template-columns:minmax(0,1.6fr) 110px minmax(0,1fr) auto; }
          .gcond > .gcondent { grid-column:1; }
          .gcond > .gcondop { grid-column:2; }
          .gcond > .gcondval { grid-column:3; }
          .gcond > .gcondx { grid-column:4; }
        }
        .quietfoot { display:flex; gap:12px; flex-wrap:wrap; align-items:center; margin-top:16px; }
        /* Green, matching Apply. The lines card is still on the primary blue
           and wants bringing across too. */
        .quietfoot .qsave { background:var(--success-color, #7cc36e); color:#14301a; border:0;
          border-radius:11px; padding:11px 22px; font-size:13px; font-weight:700;
          font-family:inherit; cursor:pointer; transition:opacity .2s; }
        .quietfoot .qsave[disabled] { opacity:.32; cursor:default; }
        .quietfoot .ghint { flex:1; min-width:200px; }
        /* The settings block only summarises this now. */
        .qsummary { background:var(--secondary-background-color); border-radius:11px;
          padding:10px 12px; display:flex; flex-direction:column; gap:4px;
          border-left:3px solid var(--success-color, #7cc36e); }
        .qsummary .qline { font-size:13px; }
        .qsummary button { align-self:flex-start; margin-top:4px;
          background:var(--secondary-background-color); color:var(--primary-text-color);
          border:1px solid var(--divider-color); border-radius:9px; padding:6px 11px;
          font-size:12px; font-family:inherit; cursor:pointer; }
        .cardfoot { border-top:1px solid var(--divider-color); padding:14px 18px;
          display:flex; align-items:center; gap:12px; flex-wrap:wrap; }
        .cardfoot p { margin:0; flex:1; min-width:220px; font-size:12px;
          line-height:1.5; color:var(--secondary-text-color); }
        /* uninstall, a card-level action rather than the last thing in a
           settings popover you cannot reach the bottom of */
        .uninstall-btn { background:transparent; color:var(--error-color, #c0504c);
          border:1px solid var(--error-color, #c0504c); border-radius:10px; padding:10px 18px;
          font-size:14px; font-weight:600; font-family:inherit; cursor:pointer; transition:all .18s; }
        .uninstall-btn:hover { background:var(--error-color, #c0504c); color:#fff; }
        /* One breakpoint. Below 1000px is the phone layout at whatever width
           it is given: one column, settings behind the cog. The old 720px
           two-column step existed only to fill space next to a card that had
           three columns to distribute, and it is a whole breakpoint's worth
           of CSS for a layout nobody asked for. */
        @media (min-width:1000px) {
          .body { grid-template-columns:minmax(0,1fr) minmax(300px,.62fr); }
          .hero { padding:38px 26px 20px; }
          .herostack { max-width:380px; }
          .cog { display:none; }
          /* The same node, sitting in the grid instead of floating over the
             card. Everything the popover needs is undone here. */
          .si { position:static; width:auto; max-height:none; overflow:visible;
            border:0; border-left:1px solid var(--divider-color); border-radius:0;
            box-shadow:none; padding:22px 18px;
            opacity:1; transform:none; pointer-events:auto; }
        }
      </style>
      <div class="frame">
        <div class="head"><div class="badge"><span class="dot" id="dot"></span><h1>Greg's Panel</h1></div></div>
        <div class="card" id="card">
          <div class="cog" id="cog" title="Settings">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
          </div>
          <datalist id="allents"></datalist>
          <div class="body">
            <div class="col">
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
              <div class="firmware" id="firmware">Greg OS · sentience: regrettably stable · warranty void since manufacture</div>
            </div>
            </div>
            <div class="si" id="settings">${this._settingsHTML()}</div>
          </div>
          <div class="cardfoot">
            <p>Uninstall is safe and complete, with cache clearing. Your automations,
               sensors and helpers are left alone.</p>
            <button class="uninstall-btn">Uninstall Greg</button>
          </div>
        </div>
        ${this._quietHTML()}
        ${this._linesHTML()}
      </div>
    `;
    this._wire();
    this._rendered = true;
  }

  // Full width and below the card. Written when the settings block was
  // rendered twice and anything stateful in it would have drifted between the
  // copies; the settings block is one node now, so this is a layout choice
  // rather than a forced one. It stays because the editor wants the width.
  // Quiet hours and conditions, together, because they are the same question:
  // when should Greg keep his mouth shut. One instance and full width, so it
  // can use ids and conditions has room to grow, neither of which is true of a
  // 300px popover. Saves on its own, like the lines editor.
  _quietHTML() {
    return `
      <div class="quietcard" id="quietcard">
        <div class="quiethead">
          <h3>When Greg keeps quiet</h3>
          <span class="ghint" id="quiet-state"></span>
        </div>

        <div class="qhours">
          <div class="qlabel">
            <div style="font-size:13px">Quiet hours</div>
            <span class="ghint">Every night, whatever else is going on.</span>
          </div>
          <div class="qtimes" id="qtimes">
            <input type="time" id="quiet-start" aria-label="Quiet from">
            <span class="ghint">until</span>
            <input type="time" id="quiet-end" aria-label="Quiet until">
          </div>
          <button class="sw" id="quiet-enabled" role="switch" aria-checked="true"
                  aria-label="Quiet hours"></button>
        </div>

        <div class="qcondhead">
          <div>
            <div style="font-size:13px">Conditions</div>
            <span class="ghint">All of them have to be true, on top of quiet hours.</span>
          </div>
          <button class="qcondadd" type="button" id="cond-add">+ Add</button>
        </div>

        <div class="gcondlist" id="condlist"></div>
        <div class="ghint" id="cond-empty"></div>

        <div class="quietfoot">
          <button class="qsave" id="quiet-save" disabled>No changes</button>
          <span class="ghint" id="quiet-status">Anything needing <em>or</em>, a template
            or a numeric range: point a row at a template binary_sensor you write
            yourself. An entity Greg cannot read never blocks him.</span>
        </div>
      </div>`;
  }

  _linesHTML() {
    return `
      <div class="linescard" id="linescard">
        <div class="lineshead">
          <h3>Lines you wrote</h3>
          <div class="lineslang">
            <span class="ghint" id="lines-langnote"></span>
          </div>
        </div>

        <div class="pooltabs" id="pooltabs">
          <button class="pooltab active" data-pool="soft">Soft</button>
          <button class="pooltab" data-pool="medium">Medium</button>
          <button class="pooltab" data-pool="chaos">Chaos</button>
          <button class="pooltab" data-pool="existential">Existential</button>
          <button class="pooltab" data-pool="silence">Silence</button>
        </div>

        <div class="poolnote" id="poolnote"></div>

        <div class="lineslist" id="lineslist"></div>

        <div class="lineadd">
          <textarea id="linenew" rows="2" maxlength="300"
            placeholder="Write one as Greg would say it, then press Add."></textarea>
          <button class="btn" id="lineadd-btn">Add</button>
        </div>
        <div class="ghint" id="linecount"></div>

        <div class="grow linesonly">
          <span>Use only my lines<span class="ghint">Built-in lines stay for any pool you have not written for.</span></span>
          <button class="sw" id="custom-only" role="switch" aria-checked="false"><span></span></button>
        </div>

        <div class="linesfoot">
          <button class="btn primary" id="lines-save">Save lines</button>
          <button class="btn" id="lines-share">Share the good ones</button>
        </div>
        <div class="ghint" id="lines-status"></div>
      </div>`;
  }

  // One instance, so this is free to use ids. It is addressed by class and
  // data-key anyway, which costs nothing and keeps the plumbing below the same
  // shape it has always had.
  //
  // Grouped into the three questions somebody actually arrives with, rather
  // than twelve fields in a row.
  _settingsHTML() {
    return `
      <h3>What he listens to</h3>

      <div class="gfield">
        <label>Vibration sensor</label>
        <div class="gselwrap"><select class="gctl" data-key="vibration_sensor" data-domain="binary_sensor"></select></div>
      </div>

      <div class="gfield">
        <label>Sensitivity <span class="gval" data-out="sensitivity"></span></label>
        <input class="gctl" type="range" data-key="sensitivity" min="1" max="100" step="1">
        <span class="ghint">Lower ignores repeat taps for longer.</span>
      </div>

      <h3>How he speaks</h3>

      <div class="gfield">
        <label>Speaker</label>
        <div class="gselwrap"><select class="gctl" data-key="media_player" data-domain="media_player"></select></div>
      </div>

      <div class="gfield">
        <label>Text to speech</label>
        <div class="gselwrap"><select class="gctl" data-key="tts_engine" data-domain="tts"></select></div>
      </div>

      <div class="gfield">
        <label>Language</label>
        <div class="gselwrap"><select class="gctl" data-key="language" data-optkey="language_options"></select></div>
        <span class="ghint" data-out="langnote"></span>
      </div>

      <div class="gfield">
        <label>Volume <span class="gval" data-out="volume"></span></label>
        <input class="gctl" type="range" data-key="volume" min="0" max="100" step="5">
      </div>

      <h3>When he keeps quiet</h3>

      <div class="qsummary">
        <span class="qline" id="qsum-hours">Quiet hours off.</span>
        <span class="qline" id="qsum-conds">No conditions.</span>
        <button type="button" id="qsum-jump">Edit in the card below →</button>
      </div>

      <button class="gapply" disabled>No changes</button>
      <button class="full" data-full>Advanced settings →</button>
      <p class="ghint">Thresholds, openers and his voice live in advanced.</p>
  `;
  }

  // ---- settings plumbing ----------------------------------------------
  _savedConfig() {
    const s = this._moodState();
    return (s && s.attributes && s.attributes.config) || null;
  }

  _entityOptions(domain) {
    if (!this._hass) return [];
    return Object.keys(this._hass.states)
      .filter((id) => id.startsWith(domain + "."))
      .map((id) => ({
        id,
        name: (this._hass.states[id].attributes || {}).friendly_name || id,
      }))
      .sort((a, b) => a.name.localeCompare(b.name));
  }

  // Selects are rebuilt only when the entity list actually changes, so a state
  // update mid-edit does not throw away what the user has picked.
  // Options published by the integration rather than derived from entities.
  // Language is built from whatever line files exist, so a new language file
  // appears in this dropdown without the panel being told about it.
  _listOptions(key) {
    const s = this._moodState();
    const raw = (s && s.attributes && s.attributes[key]) || {};
    return Object.keys(raw).map((k) => ({ id: k, name: raw[k] }));
  }

  _fillSelects() {
    const r = this.shadowRoot;
    this._fillEntityList();
    r.querySelectorAll("select.gctl").forEach((sel) => {
      const opts = sel.dataset.optkey
        ? this._listOptions(sel.dataset.optkey)
        : this._entityOptions(sel.dataset.domain);
      const sig = opts.map((o) => o.id).join(",");
      if (sel.dataset.sig === sig) return;
      sel.dataset.sig = sig;
      const keep = sel.value;
      sel.innerHTML = opts
        .map((o) => `<option value="${o.id}">${o.name}</option>`)
        .join("");
      if (keep && opts.some((o) => o.id === keep)) sel.value = keep;
    });
  }

  _readForm() {
    const g = (k) =>
      this.shadowRoot.querySelector(`.gctl[data-key="${k}"]`);
    return {
      vibration_sensor: g("vibration_sensor").value,
      media_player: g("media_player").value,
      tts_engine: g("tts_engine").value,
      volume: Number(g("volume").value) / 100,
      sensitivity: Number(g("sensitivity").value),
      language: g("language").value,
    };
  }

  _writeForm(cfg) {
    const g = (k) =>
      this.shadowRoot.querySelector(`.gctl[data-key="${k}"]`);
    if (cfg.vibration_sensor) g("vibration_sensor").value = cfg.vibration_sensor;
    if (cfg.media_player) g("media_player").value = cfg.media_player;
    if (cfg.tts_engine) g("tts_engine").value = cfg.tts_engine;
    g("volume").value = Math.round((cfg.volume ?? 0.35) * 100);
    g("sensitivity").value = cfg.sensitivity ?? 75;
    // Empty means follow Home Assistant, which is a valid choice rather than
    // an absent one, so this is set unconditionally.
    g("language").value = cfg.language ?? "";
  }

  // ---- the quiet card's own form ---------------------------------------
  //
  // Separate from the settings block because it is a separate card with its
  // own Save. Sharing one Apply button across two cards a screen apart would
  // mean editing here and pressing a button up there.

  _readQuiet() {
    const r = this.shadowRoot;
    return {
      quiet_hours_enabled:
        r.getElementById("quiet-enabled").getAttribute("aria-checked") === "true",
      quiet_start: r.getElementById("quiet-start").value,
      quiet_end: r.getElementById("quiet-end").value,
      // Rows live on the component rather than being read back out of the DOM,
      // so a row half typed in is still a row and survives a redraw.
      conditions: this._conditions().map((c) => ({ ...c })),
    };
  }

  _writeQuiet(cfg) {
    const r = this.shadowRoot;
    r.getElementById("quiet-enabled").setAttribute(
      "aria-checked", cfg.quiet_hours_enabled === false ? "false" : "true"
    );
    r.getElementById("quiet-start").value = cfg.quiet_start || "22:00";
    r.getElementById("quiet-end").value = cfg.quiet_end || "08:00";
    // Not while a row is still being filled in. A blank row cleans away to
    // nothing, so the form reads as unchanged, so saved values get stamped
    // back over it and the row you just added disappears as you look at it.
    if (cfg.conditions && !this._condInProgress())
      this._condDraft = cfg.conditions.map((c) => ({ ...c }));
    this._renderConditions();
  }

  _sameQuiet(a, b) {
    if (!a || !b) return false;
    return ["quiet_hours_enabled", "quiet_start", "quiet_end"]
      .every((k) => a[k] === b[k])
      && this._sameConditions(this._cleanConditions(a.conditions),
                              this._cleanConditions(b.conditions));
  }

  // Same shape as _awaitingSave, for the card's own in-flight write.
  _awaitingQuiet(saved) {
    if (!this._quietPending) return false;
    const settled = this._sameQuiet(
      { ...saved, conditions: this._cleanConditions(saved.conditions) },
      this._quietPending
    );
    if (settled || Date.now() - this._quietPendingAt > 10000) {
      this._quietPending = null;
      return false;
    }
    return true;
  }

  _refreshQuiet(force) {
    const r = this.shadowRoot;
    if (!r.getElementById("quietcard")) return;
    const saved = this._savedConfig();
    if (!saved) return;

    if (force || !(this._quietDirty || this._awaitingQuiet(saved))) {
      this._writeQuiet(saved);
    }

    const cur = this._readQuiet();
    const dirty = !this._sameQuiet(cur, saved);
    const save = r.getElementById("quiet-save");
    save.disabled = !dirty;
    save.textContent = dirty ? "Save" : "No changes";

    r.getElementById("qtimes").classList.toggle("hidden", !cur.quiet_hours_enabled);

    const rows = this._cleanConditions(cur.conditions);
    r.getElementById("cond-empty").textContent = rows.length
      ? ""
      : "No conditions. Greg goes by the clock alone.";

    // What is actually holding him, straight from Greg rather than worked out
    // here, so the card agrees with what he is doing.
    const attrs = (this._moodState() && this._moodState().attributes) || {};
    const by = attrs.blocked_by;
    r.getElementById("quiet-state").textContent = attrs.blocked
      ? `Keeping quiet: ${by || "quiet hours"}.`
      : "Greg is talking. Nothing is holding him.";

    // And the summary up in the settings block.
    const sumHours = r.getElementById("qsum-hours");
    if (sumHours) {
      sumHours.textContent = cur.quiet_hours_enabled
        ? `Quiet hours ${cur.quiet_start} to ${cur.quiet_end}.`
        : "Quiet hours off.";
      r.getElementById("qsum-conds").textContent = rows.length === 1
        ? "1 condition."
        : `${rows.length} conditions.`;
    }
  }

  _saveQuiet() {
    if (!this._hass) return;
    const r = this.shadowRoot;
    const cfg = this._readQuiet();
    cfg.conditions = this._cleanConditions(cfg.conditions);

    const save = r.getElementById("quiet-save");
    save.disabled = true;
    save.textContent = "Saving…";
    this._quietPending = cfg;
    this._quietPendingAt = Date.now();
    this._hass.callService("greg", "set_options", cfg).then(
      () => { this._quietDirty = false; },
      () => {
        save.textContent = "Failed, check the logs";
        this._quietDirty = false;
        this._quietPending = null;
      }
    );
  }

  _sameConfig(a, b) {
    if (!a || !b) return false;
    return ["vibration_sensor", "media_player", "tts_engine", "sensitivity",
            "language"]
      .every((k) => a[k] === b[k])
      && Math.abs((a.volume ?? 0) - (b.volume ?? 0)) < 0.001;
  }

  // Rows compare by value and in order. Order is not meaningful to Greg, who
  // needs all of them, but it is meaningful to whoever arranged them, so a
  // reorder counts as a change worth applying.
  _sameConditions(a, b) {
    const x = a || [], y = b || [];
    if (x.length !== y.length) return false;
    return x.every((row, i) =>
      row.entity_id === y[i].entity_id &&
      row.op === y[i].op &&
      row.state === y[i].state);
  }

  _refreshSettings(force) {
    const r = this.shadowRoot;
    const saved = this._savedConfig();
    if (!saved) return;
    this._fillSelects();

    // Don't stamp saved values over an edit in progress, or over settings
    // that have been sent but not yet published back.
    if (force || !(this._dirty || this._awaitingSave(saved))) {
      this._writeForm(saved);
    }

    const dirty = !this._sameConfig(this._readForm(), saved);
    const apply = r.querySelector(".gapply");
    apply.disabled = !dirty;
    apply.textContent = dirty ? "Apply" : "No changes";

    const note = r.querySelector('[data-out="langnote"]');
    if (note) {
      const chosen = r.querySelector('.gctl[data-key="language"]').value;
      const st = this._moodState();
      const effective = (st && st.attributes && st.attributes.language_effective) || "";
      const names = (st && st.attributes && st.attributes.language_options) || {};
      note.textContent = chosen
        ? ""
        : effective
        ? `Currently ${names[effective] || effective}.`
        : "";
    }
  }

  // True while a save is in flight: sent to the service, not yet visible in the
  // published config. async_update_entry does not await its listeners, so the
  // service call can return before the new values come back round.
  _awaitingSave(saved) {
    if (!this._pending) return false;
    const settled = Object.keys(this._pending).every((k) => {
      if (k === "volume")
        return Math.abs((saved[k] ?? 0) - this._pending[k]) < 0.001;
      return saved[k] === this._pending[k];
    });
    if (settled || Date.now() - this._pendingAt > 10000) {
      this._pending = null;
      return false;
    }
    return true;
  }

  _onSettingInput() {
    this._dirty = !this._sameConfig(this._readForm(), this._savedConfig());
    this._refreshSettings(false);
  }

  _applySettings() {
    if (!this._hass) return;
    const cfg = this._readForm();
    // An empty select means that domain has no entities. Sending "" fails
    // validation on the service side, so leave the field out entirely.
    ["vibration_sensor", "media_player", "tts_engine"].forEach((k) => {
      if (!cfg[k]) delete cfg[k];
    });
    const apply = this.shadowRoot.querySelector(".gapply");
    apply.disabled = true;
    apply.textContent = "Applying…";
    this._pending = cfg;
    this._pendingAt = Date.now();
    this._hass.callService("greg", "set_options", cfg).then(
      () => { this._dirty = false; },
      () => {
        apply.textContent = "Failed, check the logs";
        this._dirty = false;
        this._pending = null;
      }
    );
  }

  // ---- conditions ------------------------------------------------------
  //
  // Rows of entity / is | is not / state, all of which have to hold or Greg
  // stays quiet. Deliberately smaller than Home Assistant's own condition
  // syntax: this covers the core-conditions pattern it was asked for, and
  // anything wanting or, templates or numeric ranges points a row at a
  // template binary_sensor, which is one row here either way.

  _conditions() {
    if (!this._condDraft) this._condDraft = [];
    return this._condDraft;
  }

  // True while any row is half filled in, which is the normal state of the
  // form between pressing + Add and typing a state into it.
  _condInProgress() {
    const rows = this._conditions();
    return this._cleanConditions(rows).length !== rows.length;
  }

  // Mirrors _clean_conditions in __init__.py, deliberately kept in step. The
  // panel needs to know what Greg will actually store to tell whether the form
  // is dirty and whether a save has landed.
  _cleanConditions(rows) {
    const out = [];
    for (const r of rows || []) {
      if (!r) continue;
      const entity_id = String(r.entity_id || "").trim();
      const state = String(r.state || "").trim().replace(/\s+/g, " ");
      if (!entity_id || !entity_id.includes(".") || !state) continue;
      out.push({ entity_id, op: r.op === "is_not" ? "is_not" : "is", state });
      if (out.length >= CONDITIONS_MAX) break;
    }
    return out;
  }

  // What the row is doing right now, in words. The warning cases are the ones
  // that can never be true, which would otherwise silence Greg for good with
  // nothing on screen to say why. The request that started this asked for
  // "boolean.quite_hours = false", and an input_boolean is never "false".
  _conditionNote(row) {
    if (!row.entity_id)
      return { text: "Pick an entity. Unfinished rows are ignored." };
    const st = this._hass && this._hass.states[row.entity_id];
    if (!st)
      return { text: "Not here right now. Greg never blocks on an entity he cannot read." };

    const cur = st.state;
    if (cur === "unavailable" || cur === "unknown")
      return { text: `Currently ${cur}, so it is not blocking him.` };
    if (!row.state) return { text: `Currently ${cur}. Type the state to match.` };

    const typed = row.state.toLowerCase();
    const opts = (st.attributes && st.attributes.options) || null;
    if (opts && opts.length && !opts.some((o) => String(o).toLowerCase() === typed))
      return {
        warn: true,
        text: `Currently ${cur}. This one is only ever ${opts.join(", ")}, so that never matches.`,
      };
    if ((cur === "on" || cur === "off") && typed !== "on" && typed !== "off")
      return {
        warn: true,
        text: `Currently ${cur}. This one is on or off, never ${row.state}, so that never matches.`,
      };
    return { text: `Currently ${cur}.` };
  }

  // Every entity in the house, for the row inputs to suggest from. One list at
  // the root of the shadow tree, shared by both copies of the settings block.
  // Rebuilt only when the entity list actually changes, because it is a few
  // thousand options and Greg's own state ticks constantly.
  _fillEntityList() {
    const dl = this.shadowRoot.getElementById("allents");
    if (!dl || !this._hass) return;
    const ids = Object.keys(this._hass.states).sort();
    const sig = `${ids.length}|${ids[0]}|${ids[ids.length - 1]}`;
    if (dl.dataset.sig === sig) return;
    dl.dataset.sig = sig;
    dl.replaceChildren(
      ...ids.map((id) => {
        const o = document.createElement("option");
        o.value = id;
        return o;
      })
    );
  }

  // Structure only. Values go on afterwards as properties rather than into the
  // markup, so an entity id or a state can never be read as HTML.
  _renderConditions() {
    const r = this.shadowRoot;
    const list = r.getElementById("condlist");
    if (!list) return;
    const rows = this._conditions();
    if (list.children.length !== rows.length) {
      list.innerHTML = rows
        .map(
          () => `
        <div class="gcond">
          <input type="text" class="gcondent" list="allents" placeholder="entity id"
                 autocomplete="off" spellcheck="false" aria-label="Entity">
          <button class="gcondx" type="button" aria-label="Remove condition">&times;</button>
          <select class="gcondop" aria-label="Comparison">
            <option value="is">is</option>
            <option value="is_not">is not</option>
          </select>
          <input type="text" class="gcondval" placeholder="state"
                 autocomplete="off" spellcheck="false" aria-label="State">
          <span class="gcondnote"></span>
        </div>`
        )
        .join("");
    }
    this._paintConditions();
    const add = r.getElementById("cond-add");
    if (add) add.disabled = rows.length >= CONDITIONS_MAX;
  }

  // Values and notes, without touching the structure, so this is safe to run
  // on every keystroke and on every state tick.
  _paintConditions() {
    const rows = this._conditions();
    const focused = this.shadowRoot.activeElement;
    this.shadowRoot.querySelectorAll(".gcond").forEach((el, i) => {
      const row = rows[i];
      if (!row) return;
      const ent = el.querySelector(".gcondent");
      const op = el.querySelector(".gcondop");
      const val = el.querySelector(".gcondval");
      // Never write over the field somebody is typing in, or the caret jumps
      // to the end on every character.
      if (ent !== focused && ent.value !== row.entity_id) ent.value = row.entity_id;
      if (op !== focused && op.value !== row.op) op.value = row.op;
      if (val !== focused && val.value !== row.state) val.value = row.state;

      const note = this._conditionNote(row);
      el.querySelector(".gcondnote").textContent = note.text;
      el.classList.toggle("warn", !!note.warn);
    });
  }

  // rerender is for adding and removing rows, which changes how many there
  // are. Typing only needs repainting.
  _condChanged(rerender) {
    if (!this.shadowRoot.getElementById("condlist")) return;
    this._quietDirty = !this._sameQuiet(this._readQuiet(), this._savedConfig());
    if (rerender) this._renderConditions();
    else this._paintConditions();
    this._refreshQuiet(false);
  }

  _onCondEdit(e) {
    const el = e.target;
    const wrap = el.closest && el.closest(".gcond");
    if (!wrap) return;
    const i = Array.prototype.indexOf.call(wrap.parentElement.children, wrap);
    const row = this._conditions()[i];
    if (!row) return;

    if (el.classList.contains("gcondent")) row.entity_id = el.value.trim();
    else if (el.classList.contains("gcondop")) row.op = el.value;
    else if (el.classList.contains("gcondval")) row.state = el.value;
    else return;
    this._condChanged(false);
  }

  // ---- the lines editor ------------------------------------------------
  //
  // Edits are held here and only written on Save. Every write reloads Greg, so
  // saving per keystroke would reload him per keystroke, which is the same
  // reason the settings block has an Apply button.

  _linesFor(pool) {
    const all = this._draftLines || {};
    return all[pool] ? all[pool].slice() : [];
  }

  _loadDraft(force) {
    // Only reload from the entity when the user is not mid-edit, or the panel
    // would wipe what they are typing every time Greg's state ticks.
    if (this._linesDirty && !force) return;
    const s = this._moodState();
    const stored = (s && s.attributes && s.attributes.custom_lines) || {};
    const lang = (s && s.attributes && s.attributes.language_effective) || "en";
    this._draftLang = lang;
    this._draftLines = { ...((stored && stored[lang]) || {}) };
    this._linesDirty = false;
  }

  _renderLines() {
    const root = this.shadowRoot;
    if (!root || !root.getElementById("lineslist")) return;
    const pool = this._activePool || "soft";
    const lines = this._linesFor(pool);
    const s = this._moodState();
    const attrs = (s && s.attributes) || {};
    const sizes = (attrs.pool_sizes || {})[pool] || {};
    const langName = (attrs.language_options || {})[this._draftLang] || this._draftLang;

    root.getElementById("lines-langnote").textContent =
      `Writing in ${langName}. Switch language above to write in another.`;

    root.getElementById("poolnote").textContent = sizes.built_in
      ? `${sizes.built_in} built in, ${sizes.mine || 0} of yours, ${sizes.in_use} in use.`
      : "";

    const list = root.getElementById("lineslist");
    list.innerHTML = lines.length
      ? lines
          .map(
            (l, i) =>
              `<div class="lineitem"><span></span><button data-del="${i}" title="Remove">&times;</button></div>`
          )
          .join("")
      : `<div class="linesempty">Nothing here yet. Greg is using his own lines for this one.</div>`;
    // Set as text rather than interpolated, so a line containing markup is
    // shown rather than rendered.
    lines.forEach((l, i) => {
      const cell = list.querySelectorAll(".lineitem span")[i];
      if (cell) cell.textContent = l;
    });
    list.querySelectorAll("[data-del]").forEach((b) => {
      b.onclick = () => {
        const next = this._linesFor(pool);
        next.splice(Number(b.dataset.del), 1);
        this._draftLines[pool] = next;
        this._linesDirty = true;
        this._renderLines();
      };
    });

    root.getElementById("linecount").textContent = `${lines.length} of 200 for this category.`;
    root.getElementById("lines-status").textContent = this._linesDirty
      ? "Unsaved changes."
      : "";
    root.querySelectorAll(".pooltab").forEach((t) =>
      t.classList.toggle("active", t.dataset.pool === pool)
    );
  }

  _addLine() {
    const root = this.shadowRoot;
    const box = root.getElementById("linenew");
    const text = (box.value || "").replace(/\s+/g, " ").trim();
    if (!text) return;
    const pool = this._activePool || "soft";
    const next = this._linesFor(pool);
    if (next.includes(text)) {
      root.getElementById("lines-status").textContent = "You have written that one already.";
      return;
    }
    if (next.length >= 200) {
      root.getElementById("lines-status").textContent = "That is 200 lines. Greg is full.";
      return;
    }
    next.push(text);
    this._draftLines[pool] = next;
    this._linesDirty = true;
    box.value = "";
    this._renderLines();
  }

  _saveLines() {
    if (!this._hass) return;
    const root = this.shadowRoot;
    const only =
      root.getElementById("custom-only").getAttribute("aria-checked") === "true";
    const pools = ["soft", "medium", "chaos", "existential", "silence"];

    // One call per pool. The service takes a single pool deliberately, so this
    // is a sequence of small writes rather than one blob that could clobber
    // another tab's edit to a pool this one never touched.
    Promise.all(
      pools.map((pool) =>
        this._hass.callService("greg", "set_lines", {
          language: this._draftLang,
          pool,
          lines: this._linesFor(pool),
          custom_only: only,
        })
      )
    ).then(
      () => {
        this._linesDirty = false;
        root.getElementById("lines-status").textContent = "Saved. Greg is reloading.";
      },
      () => {
        root.getElementById("lines-status").textContent =
          "That did not save. Check the log.";
      }
    );
  }

  // GitHub caps a prefilled issue URL at around 8000 characters. Past that the
  // link silently truncates or 414s, so anything too big goes to the clipboard
  // with instructions instead of being quietly cut in half.
  _shareLines() {
    const root = this.shadowRoot;
    const status = root.getElementById("lines-status");
    const pools = ["soft", "medium", "chaos", "existential", "silence"];
    const lang = this._draftLang || "en";

    const blocks = pools
      .map((pool) => {
        const lines = this._linesFor(pool);
        if (!lines.length) return "";
        return `### ${pool}\n\n` + lines.map((l) => `- ${l}`).join("\n");
      })
      .filter(Boolean);

    if (!blocks.length) {
      status.textContent = "Write a line first, then share it.";
      return;
    }

    const total = blocks.reduce((n, b) => n + b.split("\n").length - 2, 0);
    const body =
      `Language: \`${lang}\`\n\n` +
      `How I would like to be credited: <!-- your name, handle, or "no credit please" -->\n\n` +
      blocks.join("\n\n") +
      `\n\n<!-- ${total} lines, from Greg's panel. -->\n`;

    const url =
      "https://github.com/WHISTLER-Arc/Greg/issues/new?labels=lines&title=" +
      encodeURIComponent(`Lines for ${lang}`) +
      "&body=" +
      encodeURIComponent(body);

    if (url.length <= 7800) {
      window.open(url, "_blank", "noopener");
      status.textContent = `Opened an issue with ${total} lines. Have a read, then submit.`;
      return;
    }

    const fallback = `Lines for ${lang}\n\n${body}`;
    const done = () => {
      status.textContent =
        `That is ${total} lines, too many for a prefilled link. Copied instead. ` +
        `Open a new issue on GitHub and paste.`;
    };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(fallback).then(done, done);
    } else {
      done();
    }
  }

  _wireQuiet() {
    const r = this.shadowRoot;
    const quiet = r.getElementById("quiet-enabled");

    const touched = () => {
      this._quietDirty = !this._sameQuiet(this._readQuiet(), this._savedConfig());
      this._refreshQuiet(false);
    };

    quiet.onclick = () => {
      const on = quiet.getAttribute("aria-checked") === "true";
      quiet.setAttribute("aria-checked", on ? "false" : "true");
      touched();
    };
    ["quiet-start", "quiet-end"].forEach((id) => {
      const el = r.getElementById(id);
      el.oninput = touched;
      el.onchange = touched;
    });

    // Rows are added and removed, so the handlers live on the list rather than
    // on inputs that do not exist yet when this runs.
    const list = r.getElementById("condlist");
    list.addEventListener("input", (e) => this._onCondEdit(e));
    list.addEventListener("change", (e) => this._onCondEdit(e));
    list.addEventListener("click", (e) => {
      const x = e.target.closest && e.target.closest(".gcondx");
      if (!x) return;
      const wrap = x.closest(".gcond");
      const i = Array.prototype.indexOf.call(wrap.parentElement.children, wrap);
      this._conditions().splice(i, 1);
      this._condChanged(true);
    });

    r.getElementById("cond-add").onclick = () => {
      if (this._conditions().length >= CONDITIONS_MAX) return;
      this._conditions().push({ entity_id: "", op: "is", state: "" });
      this._condChanged(true);
      // Straight into the row that was just added, so adding one and typing
      // into it is a single gesture.
      const rows = r.querySelectorAll(".gcond");
      const last = rows[rows.length - 1];
      if (last) last.querySelector(".gcondent").focus();
    };

    r.getElementById("quiet-save").onclick = () => this._saveQuiet();

    // The settings block only summarises this card, so its link has to get you
    // here. The card is below the fold on anything narrow.
    const jump = r.getElementById("qsum-jump");
    if (jump) {
      jump.onclick = () => {
        r.getElementById("settings").classList.remove("open");
        r.getElementById("quietcard")
         .scrollIntoView({ behavior: "smooth", block: "start" });
      };
    }
  }

  _wireLines() {
    const root = this.shadowRoot;
    if (!root.getElementById("linescard")) return;
    this._activePool = this._activePool || "soft";
    this._loadDraft(true);

    root.querySelectorAll(".pooltab").forEach((t) => {
      t.onclick = () => {
        this._activePool = t.dataset.pool;
        this._renderLines();
      };
    });
    root.getElementById("lineadd-btn").onclick = () => this._addLine();
    root.getElementById("linenew").onkeydown = (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        this._addLine();
      }
    };
    root.getElementById("lines-save").onclick = () => this._saveLines();
    root.getElementById("lines-share").onclick = () => this._shareLines();
    const only = root.getElementById("custom-only");
    only.onclick = () => {
      const on = only.getAttribute("aria-checked") === "true";
      only.setAttribute("aria-checked", on ? "false" : "true");
      this._linesDirty = true;
      this._renderLines();
    };
    this._renderLines();
  }

  _wire() {
    const r = this.shadowRoot;
    r.getElementById("poke").onclick = () => this._doPoke();
    r.getElementById("herostack").onclick = () => this._doPoke();
    r.getElementById("sw").onclick = () => this._toggle();
    r.querySelectorAll("[data-full]").forEach(
      (el) => (el.onclick = () => { window.location.href = "/config/integrations/integration/greg"; })
    );
    r.querySelectorAll(".uninstall-btn").forEach(
      (el) => (el.onclick = () => this._openWizard())
    );

    // Settings controls. The switch is a button so it needs click, the rest
    // report through input/change.
    r.querySelectorAll(".gctl").forEach((el) => {
      if (el.matches('[data-key="quiet_hours_enabled"]')) {
        el.onclick = () => {
          const on = el.getAttribute("aria-checked") === "true";
          el.setAttribute("aria-checked", on ? "false" : "true");
          this._onSettingInput();
        };
      } else {
        el.oninput = () => this._onSettingInput();
        el.onchange = () => this._onSettingInput();
      }
    });
    r.querySelectorAll(".gapply").forEach(
      (el) => (el.onclick = () => this._applySettings())
    );

    this._wireQuiet();
    this._wireLines();
    const cog = r.getElementById("cog"), panel = r.getElementById("settings");
    cog.onclick = (e) => { e.stopPropagation(); panel.classList.toggle("open"); };

    // A listener on document sees event.target retargeted to the outermost
    // shadow host, never to anything of ours, so contains() reported every
    // click as being outside and the settings shut the instant you touched
    // one. composedPath crosses shadow boundaries and gives the nodes actually
    // clicked. Kept on `this` so disconnectedCallback can take it off again;
    // it closes over this instance, so without that every teardown left one
    // behind holding a detached element.
    this._onDocClick = (e) => {
      const path = e.composedPath();
      if (!path.includes(panel) && !path.includes(cog)) {
        panel.classList.remove("open");
      }
    };
    document.addEventListener("click", this._onDocClick);
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

    // The editor writes into whichever language Greg is currently speaking, so
    // switching language has to swap the list under it. Unsaved edits win: they
    // belong to the language they were typed in, and silently rebasing them
    // onto another one would file somebody's English joke as Dutch.
    const nowLang =
      (moodS && moodS.attributes && moodS.attributes.language_effective) || "en";
    if (r.getElementById("linescard") && nowLang !== this._draftLang) {
      if (this._linesDirty) {
        const note = r.getElementById("lines-status");
        if (note) note.textContent =
          "Unsaved lines are still for " + this._draftLang + ". Save or discard them first.";
      } else {
        this._loadDraft(true);
        this._renderLines();
      }
    }
    if (r.getElementById("custom-only") && !this._linesDirty) {
      const on = !!(moodS && moodS.attributes && moodS.attributes.custom_only);
      r.getElementById("custom-only").setAttribute("aria-checked", on ? "true" : "false");
    }
    const mood = moodS ? moodS.state : "resting";
    const meta = MOODS[mood] || MOODS.resting;
    const level = this._levelState() ? Number(this._levelState().state) : 0;
    const swS = this._switchState();
    const enabled = swS ? swS.state === "on" : true;
    const attrs = (moodS && moodS.attributes) || {};
    const quiet = attrs.quiet_hours || false;
    // blocked covers quiet hours and conditions together. Falls back to quiet
    // so the panel still reads correctly against a Greg that predates it.
    const blocked = attrs.blocked === undefined ? quiet : attrs.blocked;
    const blockedBy = attrs.blocked_by || "";
    const asleep = !enabled || blocked;

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
    r.getElementById("moodpct").textContent = level + "%";
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

    r.querySelectorAll(".sw:not(.gctl)").forEach((el) => el.classList.toggle("off", !enabled));
    r.getElementById("dot").classList.toggle("off", !enabled);
    r.getElementById("card").classList.toggle("asleep", asleep);
    r.getElementById("sleepcap").textContent = !enabled
      ? "Greg is switched off. He notices nothing. He is grateful."
      : quiet
      ? "Greg is asleep. Quiet hours are in effect."
      : blocked
      // Named rather than hinted at, so nobody has to work out which of their
      // own conditions is holding him.
      ? `Greg is holding his tongue. ${blockedBy} does not meet a condition you set.`
      : "";

    // firmware gag bound to actual installed version (device sw_version)
    const fw = r.getElementById("firmware");
    const ver = this._installedVersion();
    fw.textContent = ver
      ? `Greg OS ${ver} · sentience: regrettably stable · warranty void since manufacture`
      : "Greg OS · sentience: regrettably stable · warranty void since manufacture";

    this._refreshSettings(false);
    this._refreshQuiet(false);

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
