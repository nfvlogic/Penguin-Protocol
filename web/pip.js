"use strict";
// Pip, your partner inside Atlas: a tiny pixel penguin in a detective hat (the terminal version is in penguin/pip.py).
// The game marks the spot for him with \x1b]pip;MOOD;0\x07 ... \x1b]pip;end\x07; app.js hands that spot to Pip.row().
// On the page he is a small canvas two text lines tall. He moves for a moment, then holds still, so the
// text around him stays easy to read. Any tap freezes him at once.
const Pip = (() => {
  const W = 10, H = 11;
  const PAL = { O: "#f5a031", D: "#b8650f", K: "#555c6c", W: "#e8e8e8", G: "#ffd166" };
  const BASE = [
    "...O...",   // hat button
    ".OOOOO.",   // crown
    "OOOOOOO",   // brim
    "DWWWWWD",   // ear flaps and face (the eyes are cut out below)
    "KWWOWWK",   // beak
    "KWWWWWK",   // belly
    ".KWWWK.",
    ".O...O."];  // feet
  // How long each mood plays (ms). After that the newest Pip stays alive (blinks, glances around) and older ones hold still.
  const LIFE = { wave: 3500, think: 3500, hint: 3500, win: 3500, fail: 2500, vault: 5000, vaultwin: 5000, sleep: Infinity, idle: Infinity };
  const STILL = { hint: 300 };          // the moment of each mood an older Pip keeps when he stops
  // Pip moves a pixel or two in place, so he keeps moving with Reduce Motion on (it still calms the text effects).
  const REDUCE = false;

  function compose(mood, t) {
    const g = Array.from({ length: H }, () => Array(W).fill(null));
    const put = (x, y, c) => { if (x >= 0 && x < W && y >= 0 && y < H) g[y][x] = c; };
    const step = (ms) => Math.floor(t / ms);
    let ox = 1, oy = 2, head = 0, look = 0, blink = false, hat = 0;
    const extra = [];
    switch (mood) {
      case "idle": { const c = t % 7000; blink = c % 2600 > 2420; look = c > 3500 && c < 4400 ? -1 : c > 4400 && c < 5300 ? 1 : 0; break; }
      case "think": look = [0, 1, 1, 0, -1, -1][step(300) % 6]; head = step(1800) % 2 && step(300) % 6 > 2 ? 1 : 0; break;
      case "win": { const k = step(110) % 10; oy -= [0, 1, 2, 2, 1, 0, 0, 0, 0, 0][k]; hat = k === 5 || k === 6 ? 1 : 0; break; }
      case "fail": head = t % 1300 < 800 ? [0, -1, 0, 1][step(100) % 4] : 0; look = head ? 0 : 0; break;
      case "sleep": { blink = true; oy += step(900) % 2; const ph = step(450) % 5; if (ph < 4) extra.push(() => put(ox + 7 + (ph > 1 ? 1 : 0), oy + 4 - ph, "O")); break; }
      case "hint": look = 1; if (step(250) % 2) extra.push(() => { put(ox + 8, oy, "O"); put(ox + 8, oy + 1, "O"); put(ox + 8, oy + 3, "O"); }); break;
      case "vault": {                 // walks in from the left, then turns a golden key
        if (t < 800) { ox = -6 + Math.min(7, step(110)); blink = false; extra.push(() => put(ox + 1 + (step(110) % 2 ? 4 : 0), oy + 7, null)); }
        else { look = 1; const turn = step(260) % 2;
          extra.push(() => { put(ox + 8, oy + 3, "G"); put(ox + 8, oy + 4, "G"); if (turn) put(ox + 9, oy + 3, "G"); else put(ox + 8, oy + 5, "G"); });
          if (step(400) % 3 === 0) extra.push(() => put(ox + 4, oy, "G")); }      // the hat glints
        break; }
      case "vaultwin": { const k = step(110) % 10; oy -= [0, 1, 2, 2, 1, 0, 0, 0, 0, 0][k]; hat = k === 5 || k === 6 ? 1 : 0;
        extra.push(() => [0, 3, 6, 9].forEach((x, i) => put(x, (step(90) + i * 3) % H, "G"))); break; }
      case "wave": { const up = step(220) % 2; extra.push(() => { put(ox + 7, oy + 4 - up, "K"); put(ox + 8, oy + 3 - up, up ? "K" : null); }); break; }
    }
    BASE.forEach((r, y) => [...r].forEach((c, x) => {
      if (c !== ".") put(ox + x + (y <= 3 ? head : 0), oy + y - (y <= 2 ? hat : 0), c);
    }));
    const ey = oy + 3, h = ox + head;
    if (blink) { put(h + 2, ey, "K"); put(h + 4, ey, "K"); } else { put(h + 2 + look, ey, null); put(h + 4 + look, ey, null); }
    extra.forEach((f) => f());
    return g;
  }

  function draw(cv, g) {
    const ctx = cv.getContext("2d");
    ctx.clearRect(0, 0, W, H);
    for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) if (g[y][x]) { ctx.fillStyle = PAL[g[y][x]]; ctx.fillRect(x, y, 1, 1); }
  }

  // A timer, not requestAnimationFrame: it keeps going when the page is in the background or inside an app view.
  let groups = [], timer = null, newest = null;
  const paint = (gr, t) => draw(gr.cv, compose(gr.mood, t));
  function stop(gr) { gr.until = 0; paint(gr, STILL[gr.mood] || 0); }
  function idle(gr) { gr.mood = "idle"; gr.t0 = performance.now(); gr.until = Infinity; gr.last = -1; }

  function tick() {
    const now = performance.now();
    groups = groups.filter((gr) => gr.cv.isConnected || gr.box);
    for (const gr of groups) {
      if (!gr.until) continue;
      if (now >= gr.until) { if (gr === newest) idle(gr); else { stop(gr); continue; } }
      const t = Math.floor((now - gr.t0) / 83) * 83;        // 12 frames a second: pixel art should step, not glide
      if (t !== gr.last) { gr.last = t; paint(gr, t); }
    }
    if (!groups.some((gr) => gr.until)) { clearInterval(timer); timer = null; }
  }
  function wake() { if (!timer && !REDUCE) timer = setInterval(tick, 83); }

  function add(el, mood, box) {
    const cv = document.createElement("canvas");
    cv.width = W; cv.height = H;
    el.textContent = ""; el.appendChild(cv);
    const life = REDUCE ? 0 : box ? Infinity : (LIFE[mood] ?? 0);
    const gr = { cv, mood, box, t0: performance.now(), until: life ? performance.now() + life : 0, last: -1 };
    groups.push(gr);
    if (!box) { if (newest && newest.mood === "idle") stop(newest); newest = gr; }   // only the newest Pip stays alive
    paint(gr, gr.until ? 0 : (STILL[mood] || 0));
    if (gr.until) wake();
    return gr;
  }

  // The spot the game marked for Pip (he spills into the empty line the game leaves under it).
  function row(el, mood) { el.className = "pipr"; add(el, mood, false); }

  // A bigger Pip of his own inside `box` (the loading screen), moving until the page is ready.
  function mount(box, mood) { add(box, mood, true); }

  // A tap: cut the mood short. The newest Pip goes back to idling, older ones hold still.
  function freeze() { for (const gr of groups) if (gr.until && !gr.box && gr.mood !== "idle") { if (gr === newest) idle(gr); else stop(gr); } }
  return { row, mount, freeze };
})();
