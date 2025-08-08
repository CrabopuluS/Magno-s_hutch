import { getApiBase, setApiBase, getUserId, beginSession, track, flushNow } from './utils.js';

const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');
const scoreEl = document.getElementById('score');
const apiInput = document.getElementById('apiBase');
const saveApiBtn = document.getElementById('saveApi');
const startBtn = document.getElementById('startBtn');
const restartBtn = document.getElementById('restartBtn');

// init API UI
apiInput.value = getApiBase();
saveApiBtn.addEventListener('click', () => {
  setApiBase(apiInput.value.trim() || 'http://localhost:8000');
  alert('API base saved.');
});

// Game state
const GRAVITY = 0.6;
const JUMP_VELOCITY = -10.5;
const GROUND_Y = canvas.height - 40;

let state = 'idle'; // idle | running | over
let player, obstacles, score, lastScoreTrack, sessionId;

function resetGame() {
  player = { x: 60, y: GROUND_Y, vy: 0, w: 20, h: 20, onGround: true };
  obstacles = [];
  score = 0;
  lastScoreTrack = 0;
  scoreEl.textContent = '0';
}

function spawnObstacle() {
  const height = 20 + Math.random() * 30;
  const width = 12 + Math.random() * 18;
  const gap = 240 + Math.random() * 160;
  // position at right edge
  obstacles.push({ x: canvas.width + 20, y: GROUND_Y + 20 - height, w: width, h: height, gap });
}

function update(dt) {
  // player physics
  player.vy += GRAVITY;
  player.y += player.vy;
  if (player.y >= GROUND_Y) {
    player.y = GROUND_Y;
    player.vy = 0;
    player.onGround = true
  }

  // spawn obstacles
  if (obstacles.length === 0 || obstacles[obstacles.length-1].x < canvas.width - (obstacles[obstacles.length-1].gap || 260)) {
    spawnObstacle();
  }

  // move obstacles and check collisions
  const speed = 3.2 + Math.min(2.0, score / 200);
  for (const o of obstacles) o.x -= speed;
  obstacles = obstacles.filter(o => o.x + o.w > -10);

  for (const o of obstacles) {
    if (rectsCollide(player.x, player.y, player.w, player.h, o.x, o.y, o.w, o.h)) {
      gameOver();
      return;
    }
  }

  // score
  score += dt * 0.01 * 10;
  scoreEl.textContent = String(Math.floor(score));

  // track score each 2s
  if (performance.now() - lastScoreTrack > 2000) {
    lastScoreTrack = performance.now();
    track('score', { value: Math.floor(score) });
  }
}

function draw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  // ground
  ctx.fillStyle = '#122';
  ctx.fillRect(0, GROUND_Y + 20, canvas.width, 40);
  // player
  ctx.fillStyle = '#0bf';
  ctx.fillRect(player.x, player.y - player.h, player.w, player.h);
  // obstacles
  ctx.fillStyle = '#f55';
  for (const o of obstacles) {
    ctx.fillRect(o.x, o.y - o.h, o.w, o.h);
  }
  // title
  if (state === 'idle') {
    ctx.fillStyle = '#9ab';
    ctx.fillText('Press SPACE or click to jump. Press Start to begin.', 16, 24);
  }
}

function rectsCollide(x1,y1,w1,h1, x2,y2,w2,h2) {
  const a = { left: x1, right: x1 + w1, top: y1 - h1, bottom: y1 };
  const b = { left: x2, right: x2 + w2, top: y2 - h2, bottom: y2 };
  return !(a.right < b.left || a.left > b.right || a.bottom < b.top || a.top > b.bottom);
}

let lastTime = 0;
function loop(ts) {
  if (!lastTime) lastTime = ts;
  const dt = ts - lastTime;
  lastTime = ts;
  if (state === 'running') update(dt);
  draw();
  requestAnimationFrame(loop);
}

function startGame() {
  resetGame();
  state = 'running';
  sessionId = crypto.randomUUID();
  beginSession(sessionId);
  track('game_start', {});
}

function gameOver() {
  state = 'over';
  const finalScore = Math.floor(score);
  track('game_over', { final_score: finalScore });
  flushNow();
}

function jump() {
  if (state !== 'running') return;
  if (player.onGround) {
    player.vy = JUMP_VELOCITY;
    player.onGround = false;
    track('jump', { height: Math.round(Math.random()*10+10) });
  }
}

// controls
canvas.addEventListener('click', jump);
window.addEventListener('keydown', (e) => {
  if (e.code === 'Space') { e.preventDefault(); jump(); }
});
startBtn.addEventListener('click', () => startGame());
restartBtn.addEventListener('click', () => startGame());

// bootstrap
resetGame();
requestAnimationFrame(loop);
