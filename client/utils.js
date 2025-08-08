const MH_USER_KEY = 'mh_user_id';
const MH_OUTBOX_KEY = 'mh_outbox';
const MH_API_BASE_KEY = 'mh_api_base';

function getQueryParam(name) {
  const url = new URL(window.location.href);
  return url.searchParams.get(name);
}

export function getApiBase() {
  return getQueryParam('api') || localStorage.getItem(MH_API_BASE_KEY) || 'http://localhost:8000';
}
export function setApiBase(url) {
  localStorage.setItem(MH_API_BASE_KEY, url);
}

export function getUserId() {
  let id = localStorage.getItem(MH_USER_KEY);
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem(MH_USER_KEY, id);
  }
  return id;
}

// --- batching ---
let outbox = []; // array of {session_id, user_id, events: [...]}
let sending = false;
let backoff = 1000; // ms
let lastSessionId = null;

// restore from storage
try {
  const raw = localStorage.getItem(MH_OUTBOX_KEY);
  if (raw) outbox = JSON.parse(raw);
} catch { outbox = []; }

function persistOutbox() {
  try { localStorage.setItem(MH_OUTBOX_KEY, JSON.stringify(outbox)); } catch {}
}

export function beginSession(sessionId) {
  lastSessionId = sessionId;
  const user_id = getUserId();
  outbox.push({ session_id: sessionId, user_id, events: [] });
  persistOutbox();
}

export function track(name, props = {}) {
  const ts = new Date().toISOString();
  if (!lastSessionId || outbox.length === 0) {
    // create implicit session if needed
    beginSession(crypto.randomUUID());
    // also push game_start implicitly
    outbox[outbox.length-1].events.push({ name: 'game_start', ts, props: {} });
  }
  outbox[outbox.length-1].events.push({ name, ts, props });
  persistOutbox();
}

async function sendBatch(apiBase, batch) {
  const res = await fetch(`${apiBase}/events`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-MagnosHutch-Client': 'web@1.0' },
    body: JSON.stringify(batch),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return await res.json();
}

async function pump(apiBase) {
  if (sending || outbox.length === 0) return;
  sending = true;
  try {
    const batch = outbox[0];
    await sendBatch(apiBase, batch);
    // success
    outbox.shift();
    persistOutbox();
    backoff = 1000;
  } catch (e) {
    console.warn('[MH] send failed, retry later:', e);
    backoff = Math.min(backoff * 2, 30000);
  } finally {
    sending = false;
  }
}

export function flushNow() {
  // aggressive pump attempts
  const apiBase = getApiBase();
  pump(apiBase);
  setTimeout(() => pump(apiBase), 500);
  setTimeout(() => pump(apiBase), 1500);
}

// background sender
setInterval(() => pump(getApiBase()), 3000);
