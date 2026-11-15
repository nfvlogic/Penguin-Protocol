"use strict";
// Penguin Protocol, web edition: the real Python game runs in the browser (Pyodide); this file is the terminal.
const PYODIDE_VERSION = "0.26.4";
const PYODIDE_URL = `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/`;
const SAVE_KEY = "penguin_save";
const SAVE_PATH = "/tmp/penguin_save.json";
const MAX_CHILDREN = 4000;

const $ = (id) => document.getElementById(id);
const out = $("out"), promptEl = $("prompt"), input = $("input"), screen = $("screen");
// Grows the text box with its text. A long command moves under the prompt (full width) and the screen follows it,
// so what is being typed never ends up below the visible area.
function fit() {
  input.style.height = "auto";
  const one = parseFloat(getComputedStyle(input).lineHeight) || 19;
  const lineEl_ = $("line");
  lineEl_.classList.remove("multi");
  input.style.height = "auto";
  if (input.scrollHeight > one * 1.5) lineEl_.classList.add("multi");
  input.style.height = "auto"; input.style.height = input.scrollHeight + "px";
  schedCur();
  if (document.activeElement === input) scrollDown();
}

// ---- block cursor: the text box is a <textarea>, so the cursor is drawn by hand. A hidden copy of the text up to the
// cursor tells us where it is, even when a long command wraps onto several lines.
const cur = $("cur"), lineEl = $("line");
const mirror = document.createElement("div"); mirror.id = "mirror"; lineEl.appendChild(mirror);
let curQueued = false;
function schedCur() { if (!curQueued) { curQueued = true; setTimeout(() => { curQueued = false; updateCursor(); }, 16); } }   // a timer: also runs while an app view throttles animation frames
function updateCursor() {
  if (input.disabled || input.selectionStart !== input.selectionEnd) { cur.className = ""; return; }
  const cs = getComputedStyle(input), pos = input.selectionEnd ?? input.value.length;
  mirror.style.cssText = `left:${input.offsetLeft}px;top:${input.offsetTop}px;width:${input.clientWidth}px;font:${cs.font};letter-spacing:${cs.letterSpacing};line-height:${cs.lineHeight}`;
  mirror.textContent = input.value.slice(0, pos);
  const mark = document.createElement("span"); mark.textContent = input.value[pos] && input.value[pos] !== "\n" ? input.value[pos] : "x";
  mirror.appendChild(mark);
  const w = mark.getBoundingClientRect().width || 9, h = parseFloat(cs.lineHeight) || 21;
  const focused = document.activeElement === input;
  cur.style.width = w + "px"; cur.style.height = h + "px";
  cur.style.left = input.offsetLeft + mark.offsetLeft + "px"; cur.style.top = input.offsetTop + mark.offsetTop + "px";
  cur.className = "on" + (focused ? "" : " idle");
  if (focused) { cur.classList.add("solid"); void cur.offsetWidth; cur.classList.remove("solid"); }   // stays solid while typing, blinks again at rest
}
let py = null, api = null, busy = true, alive = false;
const history = []; let hpos = 0, draft = "";
let tabCount = 0;

// ------------------------------------------------------------------ ANSI -> HTML
const ANSI_RE = /\x1b\[([0-9;?]*)([A-Za-z])|\x1b\]([^\x07]*)\x07/g;
function Ansi() { this.cls = new Set(); }
Ansi.prototype.sgr = function (params) {
  const codes = params === "" ? [0] : params.split(";").map((n) => parseInt(n || "0", 10));
  for (const n of codes) {
    if (n === 0) this.cls.clear();
    else if (n === 1) this.cls.add("b");
    else if (n === 4) this.cls.add("u");
    else if (n === 22) this.cls.delete("b");
    else if ((n >= 30 && n <= 37) || (n >= 90 && n <= 97)) {
      for (const c of [...this.cls]) if (c[0] === "f") this.cls.delete(c);
      this.cls.add("f" + n);
    } else if (n === 39) { for (const c of [...this.cls]) if (c[0] === "f") this.cls.delete(c); }
  }
};
// Turns text with ANSI codes into DOM nodes appended to `parent`. Returns true if the screen was cleared.
Ansi.prototype.render = function (text, parent, onClear) {
  text = text.replace(/\r\n/g, "\n").replace(/\r/g, "");
  let last = 0, m, pip = null;             // pip: inside one of Pip's rows (pip.js draws it, the text is a placeholder)
  const put = (s) => {
    if (!s || pip) return;
    if (this.cls.size === 0) { parent.appendChild(document.createTextNode(s)); return; }
    const sp = document.createElement("span");
    sp.className = [...this.cls].join(" ");
    sp.textContent = s;
    parent.appendChild(sp);
  };
  ANSI_RE.lastIndex = 0;
  while ((m = ANSI_RE.exec(text))) {
    put(text.slice(last, m.index));
    last = ANSI_RE.lastIndex;
    if (m[3] !== undefined) {
      const [kind, mood, row] = m[3].split(";");
      if (kind === "pip" && mood === "end") pip = null;
      else if (kind === "pip" && typeof Pip === "object") { pip = document.createElement("span"); parent.appendChild(pip); Pip.row(pip, mood, +row || 0); }
    } else if (m[2] === "m") this.sgr(m[1]);
    else if (m[2] === "J" && (m[1] === "2" || m[1] === "3")) { onClear && onClear(); }
  }
  put(text.slice(last));
};
const outAnsi = new Ansi();
function clearScreen() { out.textContent = ""; }
function write(text) {
  outAnsi.render(text, out, clearScreen);
  while (out.childNodes.length > MAX_CHILDREN) out.removeChild(out.firstChild);
}
function writeErr(text) { const sp = document.createElement("span"); sp.className = "err"; sp.textContent = text; out.appendChild(sp); }
function setPrompt(text) {
  promptEl.textContent = "";
  new Ansi().render(text, promptEl);
}
function scrollDown() { screen.scrollTop = screen.scrollHeight; }

// ------------------------------------------------------------------ Python side
const BOOT = `
import os, sys, builtins, getpass, traceback
import js
os.environ["PENGUIN_TTY"] = "1"
os.environ["PENGUIN_WEB"] = "1"
os.environ["PENGUIN_SAVE"] = "${SAVE_PATH}"
os.environ["COLUMNS"] = "80"
sys.path.insert(0, "/home/pyodide/game")
from penguin.shell import Shell

def _ask(prompt=""):
    try:
        v = js.window.prompt(prompt)
    except Exception:
        v = None
    if v is None:
        raise EOFError
    return str(v)

def _input(prompt=""):
    v = _ask(prompt)
    print(prompt + v)
    return v

def _getpass(prompt="", stream=None):
    v = _ask(prompt)
    print(prompt)
    return v

builtins.input = _input
getpass.getpass = _getpass
sh = None

def _guard(fn, *a):
    try:
        return fn(*a)
    except Exception:
        sys.stdout.flush()
        print("\\x1b[31m" + traceback.format_exc(limit=-3) + "\\x1b[0m")
        return sh.prompt()
    finally:
        sys.stdout.flush()

def boot(cols):
    global sh
    os.environ["COLUMNS"] = str(cols)
    sh = Shell()
    sh.fresh, sh.start_expert = False, False
    return _guard(sh.start)

def feed(line, cols):
    os.environ["COLUMNS"] = str(cols)
    return _guard(sh.feed, line)

def interrupt():
    return _guard(sh.interrupt)

def eof():
    return _guard(sh.eof)

def comp(buf, text):
    return sh.completions(buf, text)

def is_running():
    return sh.running

def close():
    sh.save(session_open=False)
    sys.stdout.flush()
`;

function cols() {
  const probe = $("probe");
  const cw = probe.getBoundingClientRect().width / 10 || 8;
  const style = getComputedStyle(screen);
  const w = screen.clientWidth - parseFloat(style.paddingLeft) - parseFloat(style.paddingRight);
  return Math.max(40, Math.floor(w / cw));
}

function persist() {
  try { localStorage.setItem(SAVE_KEY, py.FS.readFile(SAVE_PATH, { encoding: "utf8" })); } catch (e) { /* no save yet */ }
}

async function loadPython() {
  $("loadmsg").textContent = "Loading Python (first time only)...";
  await new Promise((res, rej) => {
    const s = document.createElement("script");
    s.src = PYODIDE_URL + "pyodide.js"; s.onload = res; s.onerror = () => rej(new Error("Could not load Pyodide. Check your connection."));
    document.head.appendChild(s);
  });
  py = await loadPyodide({ indexURL: PYODIDE_URL });
  const dec = new TextDecoder();
  // While `cap` is an array the game's output is held back, so it can be played with an animation afterwards.
  py.setStdout({ write: (buf) => { const t = dec.decode(buf, { stream: true }); if (cap) cap.push({ t }); else write(t); return buf.length; } });
  py.setStderr({ write: (buf) => { const t = dec.decode(buf, { stream: true }); if (cap) cap.push({ t, err: true }); else writeErr(t); return buf.length; } });
  $("loadmsg").textContent = "Loading the game...";
  const zip = await (await fetch("penguin.zip")).arrayBuffer();
  py.unpackArchive(zip, "zip", { extractDir: "/home/pyodide/game" });
  try {
    const saved = localStorage.getItem(SAVE_KEY);
    if (saved) py.FS.writeFile(SAVE_PATH, saved);
  } catch (e) { /* storage blocked: the game still works, it just will not remember progress */ }
  py.runPython(BOOT);
  api = {
    boot: py.globals.get("boot"), feed: py.globals.get("feed"), interrupt: py.globals.get("interrupt"),
    eof: py.globals.get("eof"), comp: py.globals.get("comp"), running: py.globals.get("is_running"), close: py.globals.get("close"),
  };
}

// ------------------------------------------------------------------ animations
// Output of the opening screen and of a new mission cascades in line by line; a submitted answer shows a short
// "sending / verifying" log first. Any tap or key skips the animation.
const TOTAL_LEVELS = 50;
const REDUCE = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let cap = null, animating = false, skip = false;
const nap = (ms) => (skip ? Promise.resolve() : sleep(ms));
const bump = () => { if (animating) skip = true; if (typeof Pip === "object") Pip.freeze(); };
window.addEventListener("pointerdown", bump, true);
window.addEventListener("keydown", bump, true);

function writeDrop(text) {                               // one line that flashes in
  const sp = document.createElement("span"); sp.className = "drop";
  out.appendChild(sp);
  outAnsi.render(text, sp, clearScreen);
  while (out.childNodes.length > MAX_CHILDREN) out.removeChild(out.firstChild);
}

// Print what was held back. `cascade`: lines drop in quickly, like a terminal booting.
async function replay(parts, cascade, budget = 1000) {
  if (!cascade || REDUCE) { for (const p of parts) { if (p.err) writeErr(p.t); else write(p.t); } return; }
  const lines = [];
  for (const p of parts) for (const t of p.t.match(/[^\n]*\n|[^\n]+/g) || []) lines.push({ t, err: p.err });
  const delay = Math.min(40, budget / Math.max(lines.length, 1));
  animating = true; skip = false;
  for (const { t, err } of lines) {
    if (err) writeErr(t);
    else if (skip || /\x1b\[[23]J/.test(t)) write(t);
    else writeDrop(t);
    scrollDown();
    await nap(delay);
  }
  animating = false;
}

// "sending answer ... sent" then "verifying ATL-101 [##########] PASSED", about 1.5 s in all.
async function answerLog(isSubmit, text) {
  const m = /Objective secured: Operation (.+?) \(((?:ATL|VLT)-\d+)\)/.exec(text);
  const final = /Mission complete: all (\d+) objectives/.test(text);
  if (!isSubmit && !m) return;
  const box = document.createElement("div"); box.className = "verify"; out.appendChild(box);
  animating = true; skip = false;
  if (isSubmit) {
    const l = document.createElement("div"), msg = document.createElement("span"), st = document.createElement("span");
    msg.className = "hl"; st.className = "dm"; l.append(msg, st); box.appendChild(l);
    const frames = ["·", "+", "✳", "❄", "✳", "+"];
    for (let k = 0; k < 6; k++) { msg.textContent = "sending answer to Control ... "; st.textContent = frames[k]; scrollDown(); await nap(70); }
    st.textContent = "sent"; st.className = "ok";
    await nap(100);
  }
  if (m) {
    const l = document.createElement("div"), lbl = document.createElement("span"), res = document.createElement("span");
    lbl.className = "hl"; res.className = "ok"; l.append(lbl, res); box.appendChild(l);
    for (let k = 0; k <= 10; k++) {
      lbl.textContent = "verifying " + m[2] + " [" + "#".repeat(k) + "-".repeat(10 - k) + "] " + (k < 10 ? String(k * 10).padStart(3) + "%" : "");
      res.textContent = k < 10 ? "" : "PASSED";
      scrollDown();
      await nap(k === 10 ? 200 : 60);
    }
    if (final) l.appendChild(document.createTextNode("  you were never here."));
  }
  animating = false;
}

// ------------------------------------------------------------------ the terminal
function setBusy(b) { busy = b; input.readOnly = b; input.disabled = !alive; schedCur(); }

let marker = null;
function after(promptText) {
  persist();
  if (api.running()) {
    setPrompt(promptText || "");
    alive = true;
  } else {
    api.close(); persist();
    alive = false;
    setPrompt("");
    write("\n\x1b[90m[Session closed. Tap here to log in again]\x1b[0m\n");
  }
  setBusy(false);
  if (marker && marker.isConnected) scrollToNew(marker); else scrollDown();
  if (alive && FINE_POINTER) focusInput();       // on a computer keep typing; on a phone the keyboard stays as the user left it
}

// After a command: if its output is taller than the screen (a mission briefing), show it from the top,
// otherwise stay at the bottom with the prompt.
function scrollToNew(marker) {
  const top = marker.offsetTop - screen.offsetTop;
  if (screen.scrollHeight - top > screen.clientHeight) screen.scrollTop = Math.max(0, top - 4);
  else scrollDown();
}

function focusInput() { if (!input.disabled) input.focus({ preventScroll: true }); }

let currentPrompt = "";
function showPrompt(p) { currentPrompt = p; setPrompt(p); schedCur(); }

async function submit() {
  if (busy || !alive) return;
  const line = input.value;
  input.value = ""; fit(); tabCount = 0;
  // echo what was typed, with the coloured prompt
  const p = document.createElement("span"); out.appendChild(p);
  marker = p;
  new Ansi().render(currentPrompt, p);
  out.appendChild(document.createTextNode(line + "\n"));
  if (line.trim() && history[history.length - 1] !== line) history.push(line);
  hpos = history.length; draft = "";
  setBusy(true);
  await new Promise((r) => setTimeout(r, 0));          // let the browser paint the echo first
  cap = [];
  let next, parts;
  try { next = api.feed(line, cols()); } finally { parts = cap; cap = null; }
  const text = parts.map((p) => p.t).join("");
  const passed = /Objective secured: Operation/.test(text);
  if (!REDUCE) await answerLog(/^\s*submit\b/.test(line), text);
  await replay(parts, passed);                         // a new mission cascades in; other output is instant
  showPrompt(next);
  after(next);
}

async function control(kind) {
  if (busy || !alive) return;
  tabCount = 0;
  if (kind === "^C") {
    const p = document.createElement("span"); out.appendChild(p);
    new Ansi().render(currentPrompt, p);
    out.appendChild(document.createTextNode(input.value));
    input.value = ""; fit();
    const next = api.interrupt(); showPrompt(next); after(next);
  } else if (kind === "^D") {
    if (input.value) return;                            // like bash: Ctrl+D only acts on an empty line
    const next = api.eof(); showPrompt(next || ""); after(next);
  }
}

// ------------------------------------------------------------------ our own on-screen keyboard
const KBD_KEY = "penguin_kbd";
const KBD_MODES = ["own", "native", "off"];
const KBD_LABEL = { own: "own", native: "phone", off: "off" };
const FINE_POINTER = window.matchMedia && matchMedia("(pointer: fine)").matches;
const PAGES = {
  abc: ["qwertyuiop", "asdfghjkl", "zxcvbnm"],
  num: ["1234567890", "-/:;()$&@\"", ".,?!'"],
  sym: ["[]{}#%^*+=", "_\\|~<>`;&@", ".,?!'"],
};
const kb = $("kb");
let kbdMode = "native", page = "abc", shift = 0;          // shift: 0 off, 1 one letter, 2 caps lock
let lastShiftTap = 0;
// A phone or tablet (touch is the main input) gets our keyboard in portrait, with the Kbd key to switch it off or to the phone's own.
// A computer already has a keyboard: no on-screen one, and the Kbd key is hidden.
const TOUCH = !FINE_POINTER && (matchMedia("(pointer: coarse)").matches || navigator.maxTouchPoints > 0);
if (TOUCH) {
  kbdMode = "own";
  try { const m = localStorage.getItem(KBD_KEY); if (KBD_MODES.includes(m)) kbdMode = m; } catch (e) { /* default */ }
}

function keyBtn(label, cls, act, ch) {
  const b = document.createElement("button");
  b.type = "button"; b.textContent = label; b.className = cls || "";
  b.dataset.act = act; if (ch !== undefined) b.dataset.ch = ch;
  b.tabIndex = -1;
  return b;
}
function renderKb() {
  kb.textContent = "";
  const rows = PAGES[page], letters = page === "abc";
  const chars = (str, row) => { for (const c of str) { const ch = letters && shift ? c.toUpperCase() : c; row.appendChild(keyBtn(ch, "", "ch", ch)); } };
  const r1 = document.createElement("div"); r1.className = "row"; chars(rows[0], r1);
  const r2 = document.createElement("div"); r2.className = "row" + (letters ? " pad" : ""); chars(rows[1], r2);
  const r3 = document.createElement("div"); r3.className = "row";
  if (letters) r3.appendChild(keyBtn(shift === 2 ? "\u21EA" : "\u21E7", "fn" + (shift ? " on" : ""), "shift"));
  else r3.appendChild(keyBtn(page === "num" ? "#+=" : "123", "fn", "page"));
  chars(rows[2], r3);
  r3.appendChild(keyBtn("\u232B", "fn", "bksp"));
  const r4 = document.createElement("div"); r4.className = "row";
  r4.appendChild(keyBtn(letters ? "123" : "ABC", "fn", "toggle"));
  r4.appendChild(keyBtn("space", "sp", "ch", " "));
  r4.appendChild(keyBtn("return", "go", "enter"));
  kb.append(r1, r2, r3, r4);
}

// Our keyboard is for portrait only; on its side the phone uses its own keyboard instead.
const LANDSCAPE = matchMedia("(orientation: landscape)");
function effMode() { return kbdMode === "own" && LANDSCAPE.matches ? "native" : kbdMode; }
function applyKbd() {
  const app = $("app"), m = effMode();
  app.dataset.kbd = m;
  app.dataset.touch = TOUCH ? "1" : "0";
  input.setAttribute("inputmode", m === "native" ? "text" : "none");
  $("kbdstate").textContent = KBD_LABEL[m];
  if (m === "own") renderKb();
  scrollDown();
}
LANDSCAPE.addEventListener && LANDSCAPE.addEventListener("change", () => { if (TOUCH) { input.blur(); applyKbd(); } });
function setKbdMode(m) {
  kbdMode = m;
  try { localStorage.setItem(KBD_KEY, m); } catch (e) { /* not remembered */ }
  $("app").classList.remove("kbhide");
  input.blur();                                         // so the new inputmode applies on the next focus
  applyKbd();
  if (effMode() === "native") focusInput();                     // open the phone's keyboard right away (this is a tap, so iOS allows it)
}
function showKeyboard() {
  $("app").classList.remove("kbhide");
  if (effMode() !== "off" || document.activeElement !== input) focusInput();
  scrollDown();
}
function hideKeyboard() {
  if (effMode() === "own") { $("app").classList.add("kbhide"); scrollDown(); }
  if (document.activeElement === input) input.blur();
}

// After the phone has been away (app switched, screen locked) the text box can have lost focus and a stale caret
// (often 0, so delete does nothing). Take focus again and put the caret at the end in that case.
function ensureFocus() {
  const had = document.activeElement === input;
  focusInput();
  if (!had) { const n = input.value.length; try { input.setSelectionRange(n, n); } catch (e) { /* ignore */ } }
}
function backspace() {
  const s = input.selectionStart ?? 0, e = input.selectionEnd ?? s;
  if (s !== e) input.setRangeText("", s, e, "end");
  else if (s > 0) input.setRangeText("", s - 1, s, "end");
  fit();
}
// Held delete repeats only while a finger is really down. Some phones drop the "finger up" event after the app
// was in the background, which used to leave delete running (or stuck); so every release signal stops it, ticks
// double-check, and it never runs longer than a few seconds.
let repeatT = null, fingerDown = false, repeatStart = 0;
function stopRepeat() { clearTimeout(repeatT); clearInterval(repeatT); repeatT = null; fingerDown = false; }
function startRepeat() {
  stopRepeat();
  fingerDown = true; repeatStart = Date.now();
  repeatT = setTimeout(() => {
    repeatT = setInterval(() => {
      if (!fingerDown || document.hidden || Date.now() - repeatStart > 6000 || !input.value) { stopRepeat(); return; }
      backspace();
    }, 55);
  }, 380);
}
function kbPress(b) {
  const act = b.dataset.act;
  if (act === "ch") {
    insertAtCursor(b.dataset.ch);
    if (shift === 1) { shift = 0; renderKb(); }
  } else if (act === "bksp") { ensureFocus(); backspace(); startRepeat(); }
  else if (act === "enter") submit();
  else if (act === "shift") {
    const now = Date.now();
    shift = shift === 2 ? 0 : (shift === 1 && now - lastShiftTap < 400) ? 2 : shift === 1 ? 0 : 1;
    lastShiftTap = now; renderKb();
  } else if (act === "toggle") { page = page === "abc" ? "num" : "abc"; shift = 0; renderKb(); }
  else if (act === "page") { page = page === "num" ? "sym" : "num"; renderKb(); }
}
kb.addEventListener("pointerdown", (e) => {
  const b = e.target.closest("button"); if (!b) return;
  e.preventDefault();                                   // keep focus (and the cursor) in the text box
  stopRepeat();                                         // a release that never arrived must not leak into this press
  kbPress(b);
});
["pointerup", "pointercancel", "touchend", "touchcancel", "mouseup", "blur", "contextmenu", "pagehide"].forEach((ev) => window.addEventListener(ev, stopRepeat));
kb.addEventListener("pointerleave", stopRepeat);
kb.addEventListener("lostpointercapture", stopRepeat);

function insertAtCursor(text) {
  ensureFocus();
  const s = input.selectionStart ?? input.value.length, e = input.selectionEnd ?? s;
  input.setRangeText(text, s, e, "end"); fit();
}

function historyStep(dir) {
  if (!history.length) return;
  if (hpos === history.length) draft = input.value;
  hpos = Math.min(Math.max(hpos + dir, 0), history.length);
  input.value = hpos === history.length ? draft : history[hpos]; fit();
  const n = input.value.length; input.setSelectionRange(n, n);
}

function tab() {
  if (busy || !alive) return;
  const pos = input.selectionStart ?? input.value.length;
  const before = input.value.slice(0, pos), after_ = input.value.slice(pos);
  const text = before.split(/[ \t\n;|&<>=]/).pop();
  const matches = Array.from(api.comp(before, text).toJs ? api.comp(before, text).toJs() : api.comp(before, text));
  if (!matches.length) return;
  let common = matches[0];
  for (const m of matches) { while (!m.startsWith(common)) common = common.slice(0, -1); }
  if (matches.length === 1) {
    const add = matches[0].endsWith("/") ? "" : " ";
    input.value = before.slice(0, before.length - text.length) + matches[0] + add + after_; fit();
    const n = before.length - text.length + matches[0].length + add.length; input.setSelectionRange(n, n);
  } else {
    if (common.length > text.length) {
      input.value = before.slice(0, before.length - text.length) + common + after_; fit();
      const n = before.length - text.length + common.length; input.setSelectionRange(n, n);
    } else {
      const p = document.createElement("span"); out.appendChild(p);
      new Ansi().render(currentPrompt, p);
      out.appendChild(document.createTextNode(input.value + "\n" + matches.join("  ") + "\n"));
      scrollDown();
    }
  }
}

async function startSession() {
  setBusy(true); alive = false;
  cap = [];
  const next = api.boot(cols());
  const parts = cap; cap = null;
  let seen = false;                                    // the full opening only plays on the first visit; later it is quicker
  try { seen = localStorage.getItem("penguin_seen") === "1"; localStorage.setItem("penguin_seen", "1"); } catch (e) { /* no storage: always the full one */ }
  await replay(parts, true, seen ? 600 : 1500);
  showPrompt(next); after(next);
}

// ------------------------------------------------------------------ wiring
input.addEventListener("input", fit);
["focus", "blur", "keyup", "click", "select"].forEach((ev) => input.addEventListener(ev, schedCur));
document.addEventListener("selectionchange", () => { if (document.activeElement === input) schedCur(); });
window.addEventListener("resize", schedCur);
input.addEventListener("keydown", (e) => {
  if (e.key === "Enter") { e.preventDefault(); submit(); }
  else if (e.key === "ArrowUp") { e.preventDefault(); historyStep(-1); }
  else if (e.key === "ArrowDown") { e.preventDefault(); historyStep(1); }
  else if (e.key === "Tab") { e.preventDefault(); tab(); }
  else if (e.ctrlKey && (e.key === "c" || e.key === "C") && input.selectionStart === input.selectionEnd) { e.preventDefault(); control("^C"); }
  else if (e.ctrlKey && (e.key === "d" || e.key === "D")) { e.preventDefault(); control("^D"); }
  else if (e.ctrlKey && (e.key === "l" || e.key === "L")) { e.preventDefault(); clearScreen(); }
});

$("keys").addEventListener("pointerdown", (e) => { if (e.target.closest("button")) e.preventDefault(); });   // keep the keyboard open
$("keys").addEventListener("click", (e) => {
  const b = e.target.closest("button"); if (!b) return;
  const k = b.dataset.k;
  if (k === "Kbd") setKbdMode(KBD_MODES[(KBD_MODES.indexOf(kbdMode) + 1) % KBD_MODES.length]);
  else if (k === "Tab") tab();
  else if (k === "^C" || k === "^D") control(k);
  else if (k === "Up") historyStep(-1);
  else if (k === "Down") historyStep(1);
  else insertAtCursor(k);
});

screen.addEventListener("click", (e) => {
  if (getSelection().toString()) return;               // let people select text
  if (!alive && api && !busy) { startSession(); return; }
  if (e.target.closest("#line")) showKeyboard();       // tap the prompt: type
  else hideKeyboard();                                  // tap the text: hide the keyboard to read
});

function fitViewport() {
  if (window.visualViewport) $("app").style.height = visualViewport.height + "px";
  scrollDown(); schedCur();
}
if (window.visualViewport) { visualViewport.addEventListener("resize", fitViewport); fitViewport(); }
// Coming back after a while (or a long time away): drop any half-finished key press and re-sync the layout.
function resume() {
  stopRepeat();
  fitViewport();
  applyKbd();
  fit();
}
document.addEventListener("visibilitychange", () => { if (document.hidden) stopRepeat(); else resume(); });
window.addEventListener("pageshow", resume);
window.addEventListener("focus", resume);
window.addEventListener("orientationchange", () => setTimeout(resume, 150));
window.addEventListener("pagehide", persist);
applyKbd();

(async function main() {
  if ("serviceWorker" in navigator) navigator.serviceWorker.register("sw.js").catch(() => {});
  if (typeof Pip === "object") Pip.mount($("loadpip"), "sleep");
  try {
    await loadPython();
    $("loading").classList.add("done");
    await startSession();
  } catch (e) {
    $("loadmsg").textContent = String(e.message || e);
  }
})();
