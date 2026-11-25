// 팝업 동화 in three.js: the bookshelf, then a tale played back from its Godot export (player.js).
// URL: ?tale=<id> opens a tale straight away, &beat=<id> starts at that beat, &auto=1 plays unattended (taps simulated
// after 1 s, like Godot autoplay), &hud=1 shows draw calls / memory.
import * as THREE from 'three';
import { AudioPlayer } from './audio.js';
import { playTale } from './player.js';

const Q = new URLSearchParams(location.search);
const DATA = './data/';
const $ = (id) => document.getElementById(id);
const errors = [];
window.addEventListener('error', (e) => errors.push(String(e.message)));
window.addEventListener('unhandledrejection', (e) => errors.push(String(e.reason)));

const canvas = $('c');
const renderer = new THREE.WebGLRenderer({ canvas, antialias: false, powerPreference: 'high-performance', stencil: false });
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, Number(Q.get('dpr') || 2)));
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFShadowMap;
renderer.outputColorSpace = THREE.LinearSRGBColorSpace; // the post pass writes display values itself
renderer.toneMapping = THREE.NoToneMapping;
renderer.info.autoReset = false;
const audio = new AudioPlayer(DATA);
audio.ensure();
const app = { renderer, audio, Q, data: DATA, errors };
window.__audioLevel = () => audio.level();
window.__app = { errors, state: 'shelf' };

// ------------------------------------------------------------------ shelf
let shelfData = null;
async function showShelf() {
  window.__app.state = 'shelf';
  document.body.classList.add('shelf-on');
  $('shelf').classList.add('on');
  if (!shelfData) shelfData = await (await fetch(DATA + 'tales.json')).json();
  const grid = $('books');
  grid.innerHTML = '';
  shelfData.tales.forEach((t, i) => {
    const b = document.createElement('button');
    b.className = 'book' + (t.ready ? '' : ' off');
    b.style.setProperty('--cloth', t.cloth);
    b.style.setProperty('--cloth-dark', t.cloth_dark);
    b.style.setProperty('--tilt', `${[-2.2, 1.6, -1.2, 2.4, -1.8, 1.2, 1.9, -2.6][i % 8]}deg`);
    b.dataset.tale = t.id;
    const board = document.createElement('div');
    board.className = 'board';
    if (t.art_img) board.style.backgroundImage = `url(${DATA + t.art_img})`;
    if (t.title_img) {
      const ti = document.createElement('img');
      ti.className = 'title';
      ti.src = DATA + t.title_img;
      ti.alt = t.name;
      const [cx, cy, w] = t.title_rect;
      ti.style.left = (cx - w / 2) * 100 + '%';
      ti.style.width = w * 100 + '%';
      ti.style.top = cy * 100 + '%';
      board.appendChild(ti);
    }
    const name = document.createElement('div');
    name.className = 'name';
    name.textContent = t.name;
    b.append(board, name);
    if (t.ready) b.addEventListener('click', () => { audio.unlock(); openTale(t.id, {}); });
    grid.appendChild(b);
  });
  window.__app.shelf = shelfData.tales.map((t) => [t.id, t.ready]);
}

// ------------------------------------------------------------------ tale
let current = null;
async function openTale(id, opt) {
  $('shelf').classList.remove('on');
  document.body.classList.remove('shelf-on');
  $('load').classList.add('on');
  window.__app.state = 'tale';
  if (current) { current.dispose(); current = null; }
  try {
    current = await playTale(app, id, opt);
  } catch (e) {
    errors.push(String(e && e.stack || e));
    console.error(e);
  }
  $('load').classList.remove('on');
}
function backToShelf() {
  if (current) { current.dispose(); current = null; }
  audio.clear();
  if (Q.has('tale')) history.replaceState(null, '', location.pathname);
  showShelf();
}
$('back').addEventListener('click', (e) => { e.stopPropagation(); backToShelf(); });
$('again').addEventListener('click', (e) => { e.stopPropagation(); const t = window.__pilot && window.__pilot.tale; audio.unlock(); openTale(t, {}); });
$('other').addEventListener('click', (e) => { e.stopPropagation(); backToShelf(); });
$('subs').addEventListener('click', (e) => {
  e.stopPropagation();
  const off = $('cap').classList.toggle('off');
  $('subs').textContent = off ? '자막 꺼짐' : '자막 켜짐';
});
document.addEventListener('pointerdown', () => audio.unlock(), { capture: true });

if (Q.get('tale')) openTale(Q.get('tale'), { beat: Q.get('beat') || '', auto: Q.has('auto') && Q.get('auto') !== '0' });
else showShelf();
