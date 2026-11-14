"use strict";
// Penguin Protocol, web edition: the real Python game runs in the browser (Pyodide); this file is the terminal.
const PYODIDE_VERSION = "0.26.4";
const PYODIDE_URL = `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/`;
const SAVE_KEY = "penguin_save";
const SAVE_PATH = "/tmp/penguin_save.json";
const MAX_CHILDREN = 4000;

const $ = (id) => document.getElementById(id);
const out = $("out"), promptEl = $("prompt"), input = $("input"), screen = $("screen");
function fit() { input.style.height = "auto"; input.style.height = input.scrollHeight + "px"; }
let py = null, api = null, busy = true, alive = false;
const history = []; let hpos = 0, draft = "";
let tabCount = 0;

// ------------------------------------------------------------------ ANSI -> HTML
const ANSI_RE = /\x1b\[([0-9;?]*)([A-Za-z])|\x1b\][^\x07]*\x07/g;
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
  let last = 0, m;
  const put = (s) => {
    if (!s) return;
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
    if (m[2] === "m") this.sgr(m[1]);
    else if (m[2] === "J" && (m[1] === "2" || m[1] === "3")) { onClear && onClear(); }
  }
  put(text.slice(last));
};
const outAnsi = new Ansi();
function clearScreen() { out.textContent = ""; }
let cmdText = "";                                       // everything the game printed for the current command
function write(text) {
  cmdText += text;
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
  py.setStdout({ write: (buf) => { write(dec.decode(buf, { stream: true })); return buf.length; } });
  py.setStderr({ write: (buf) => { writeErr(dec.decode(buf, { stream: true })); return buf.length; } });
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

// ------------------------------------------------------------------ mission-complete readout
// Printed inside the terminal, right above the "Objective secured" line, like a fast test run with an upload bar.
const TOTAL_LEVELS = 50;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
async function celebrate(text) {
  const m = /Objective secured: Operation (.+?) \((ATL-\d+)\)/.exec(text);
  if (!m) return;
  const final = /Mission complete: all (\d+) objectives/.test(text);
  const anchor = [...out.querySelectorAll("span.f32")].reverse().find((e) => e.textContent.includes("Objective secured"));
  if (!anchor) return;
  const reduce = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;
  // one line, redrawn in place: sending [######----]  60%  ->  sent [##########] PASSED
  const line = document.createElement("div"); line.className = "verify";
  const lbl = document.createElement("span"), res = document.createElement("span");
  lbl.className = "hl"; res.className = "ok";
  line.append(lbl, res);
  out.insertBefore(line, anchor);
  const draw = (k) => { lbl.textContent = "sending " + m[2] + " [" + "#".repeat(k) + "-".repeat(10 - k) + "] " + (k < 10 ? String(k * 10).padStart(3) + "%" : ""); res.textContent = k < 10 ? "" : "PASSED"; };
  if (reduce) { draw(10); return; }
  for (let k = 0; k <= 10; k++) { draw(k); await sleep(k === 10 ? 0 : 60); }
  if (final) { line.append(document.createTextNode("  you were never here.")); }
}

// ------------------------------------------------------------------ the terminal
function setBusy(b) { busy = b; input.readOnly = b; input.disabled = !alive; }

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
  celebrate(cmdText); cmdText = "";
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
function showPrompt(p) { currentPrompt = p; setPrompt(p); }

async function submit() {
  if (busy || !alive) return;
  const line = input.value;
  input.value = ""; fit(); tabCount = 0; cmdText = "";
  // echo what was typed, with the coloured prompt
  const p = document.createElement("span"); out.appendChild(p);
  marker = p;
  new Ansi().render(currentPrompt, p);
  out.appendChild(document.createTextNode(line + "\n"));
  if (line.trim() && history[history.length - 1] !== line) history.push(line);
  hpos = history.length; draft = "";
  setBusy(true);
  await new Promise((r) => setTimeout(r, 0));          // let the browser paint the echo first
  const next = api.feed(line, cols());
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

function backspace() {
  const s = input.selectionStart ?? 0, e = input.selectionEnd ?? s;
  if (s !== e) input.setRangeText("", s, e, "end");
  else if (s > 0) input.setRangeText("", s - 1, s, "end");
  fit();
}
let repeatT = null;
function stopRepeat() { clearTimeout(repeatT); clearInterval(repeatT); repeatT = null; }
function startRepeat() {
  stopRepeat();
  repeatT = setTimeout(() => { repeatT = setInterval(backspace, 55); }, 380);
}
function kbPress(b) {
  const act = b.dataset.act;
  if (act === "ch") {
    insertAtCursor(b.dataset.ch);
    if (shift === 1) { shift = 0; renderKb(); }
  } else if (act === "bksp") { focusInput(); backspace(); startRepeat(); }
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
  kbPress(b);
});
window.addEventListener("pointerup", stopRepeat);
window.addEventListener("pointercancel", stopRepeat);
window.addEventListener("blur", stopRepeat);

function insertAtCursor(text) {
  const s = input.selectionStart ?? input.value.length, e = input.selectionEnd ?? s;
  input.setRangeText(text, s, e, "end"); fit();
  focusInput();
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
  const next = api.boot(cols());
  showPrompt(next); after(next);
}

// ------------------------------------------------------------------ wiring
input.addEventListener("input", fit);
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

if (window.visualViewport) {
  const fit = () => { $("app").style.height = visualViewport.height + "px"; scrollDown(); };
  visualViewport.addEventListener("resize", fit); fit();
}
window.addEventListener("pagehide", persist);
applyKbd();

(async function main() {
  if ("serviceWorker" in navigator) navigator.serviceWorker.register("sw.js").catch(() => {});
  try {
    await loadPython();
    $("loading").classList.add("done");
    await startSession();
  } catch (e) {
    $("loadmsg").textContent = String(e.message || e);
  }
})();
