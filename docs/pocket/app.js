'use strict';

// Clé publique VAPID (notifications push). La privée est un secret GitHub.
const VAPID_PUBLIC = 'BBrWaeSczwSz-wCywXN0OlFQ72UdUWRLLeAU9fjzD_8uw7saPxizhDNu6jTfe4xM4hbk_pV0GoAVxoTMD6BZpTw';
const MODEL = 'claude-sonnet-4-6';

// ── Stockage local ────────────────────────────────────────────────────────
const LS = {
  get repo() { return localStorage.getItem('pocket_repo') || ''; },
  set repo(v) { localStorage.setItem('pocket_repo', v); },
  get pat() { return localStorage.getItem('pocket_pat') || ''; },
  set pat(v) { localStorage.setItem('pocket_pat', v); },
  get history() { try { return JSON.parse(localStorage.getItem('pocket_history') || '[]'); } catch { return []; } },
  set history(v) { localStorage.setItem('pocket_history', JSON.stringify(v.slice(0, 50))); },
  get device() { let d = localStorage.getItem('pocket_device'); if (!d) { d = 'dev-' + Math.random().toString(36).slice(2, 10); localStorage.setItem('pocket_device', d); } return d; },
};

const $ = (id) => document.getElementById(id);
let pollTimer = null;

// ── API GitHub ──────────────────────────────────────────────────────────────
async function gh(path, opts = {}) {
  if (!LS.pat || !LS.repo) throw new Error('Configure le repo et le token (engrenage).');
  const res = await fetch(`https://api.github.com/repos/${LS.repo}${path}`, {
    ...opts,
    headers: {
      'Authorization': `Bearer ${LS.pat}`, 'Accept': 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28', 'Content-Type': 'application/json', ...(opts.headers || {}),
    },
  });
  if (!res.ok) {
    let detail = ''; try { detail = (await res.json()).message || ''; } catch {}
    const e = new Error(`GitHub ${res.status} ${detail}`.trim()); e.status = res.status; throw e;
  }
  return res.status === 204 ? null : res.json();
}
function friendlyError(e) {
  if (e.status === 403) return `${e.message}\n→ Le token (compte gcoche-bit) doit être un token « classic » avec le scope « repo », et gcoche-bit doit avoir l'accès écriture au repo.`;
  if (e.status === 401) return `${e.message}\n→ Token invalide/expiré. Recolle-le.`;
  return e.message;
}

// ── Écriture d'un fichier dans le repo (subscriptions push) ─────────────────
function b64(str) { return btoa(unescape(encodeURIComponent(str))); }
async function putFile(path, obj) {
  let sha;
  try { const cur = await gh(`/contents/${path}`); sha = cur.sha; } catch {}
  await gh(`/contents/${path}`, {
    method: 'PUT',
    body: JSON.stringify({ message: `pocket: push subscription ${LS.device}`, content: b64(JSON.stringify(obj, null, 2)), sha }),
  });
}

async function ensureLabels() {
  for (const [name, color] of [['pocket', '8b5cf6'], ['approved', '3fb950']]) {
    try { await gh('/labels', { method: 'POST', body: JSON.stringify({ name, color }) }); } catch {}
  }
}

// ── Dispatch ────────────────────────────────────────────────────────────────
function buildBody(demande, writeAllowed, conditions) {
  return [
    '### Demande', '', demande, '',
    "### Autoriser l'écriture ?", '', writeAllowed ? 'oui' : 'non', '',
    "### Conditions d'écriture (si OUI)", '', conditions || '_No response_', '',
    '### Workflow (recette)', '', 'auto', '',
    '### Agent (optionnel)', '', 'auto', '',
  ].join('\n');
}
async function dispatch() {
  const demande = $('demande').value.trim();
  const msg = $('composer-msg');
  if (!demande) { msg.className = 'msg err'; msg.textContent = 'Écris une demande.'; return; }
  const writeAllowed = $('write-allowed').checked;
  const conditions = $('conditions').value.trim();
  msg.className = 'msg'; msg.textContent = 'Envoi…';
  try {
    await ensureLabels();
    const title = '[Pocket] ' + demande.slice(0, 60).replace(/\n/g, ' ');
    const issue = await gh('/issues', { method: 'POST', body: JSON.stringify({ title, body: buildBody(demande, writeAllowed, conditions), labels: ['pocket'] }) });
    const hist = LS.history; hist.unshift({ number: issue.number, title, created: Date.now() }); LS.history = hist;
    $('demande').value = ''; $('conditions').value = ''; $('write-allowed').checked = false; $('conditions-wrap').classList.add('hidden');
    msg.className = 'msg ok'; msg.textContent = `Tâche #${issue.number} envoyée.`;
    renderHistory(); openDetail(issue.number, title);
  } catch (e) { msg.className = 'msg err'; msg.textContent = friendlyError(e); }
}

// ── Historique ────────────────────────────────────────────────────────────
function renderHistory() {
  const ul = $('history-list'); const hist = LS.history;
  if (!hist.length) { ul.innerHTML = '<li class="empty">Aucune tâche pour l\'instant.</li>'; return; }
  ul.innerHTML = '';
  for (const h of hist) {
    const li = document.createElement('li');
    li.innerHTML = `<span class="t">#${h.number} ${escapeHtml(h.title.replace('[Pocket] ', ''))}</span><span class="badge pending">›</span>`;
    li.onclick = () => openDetail(h.number, h.title);
    ul.appendChild(li);
  }
}

// ── Monitoring du run ───────────────────────────────────────────────────────
const STEP_LABELS = {
  'Set up job': 'Préparation', 'Run actions/checkout@v4': 'Récupération du code',
  'Install MCP servers': 'Installation des outils', 'Run actions/setup-python@v5': 'Préparation Python',
  'Write task to disk': 'Lecture de la demande', 'Write MCP config with secrets': 'Connexion aux apps',
  'Build claude_args': 'Configuration', 'Run Claude Pocket': 'Claude travaille', 'Notify (push)': 'Notification',
};
async function findRun(title) {
  try {
    const d = await gh(`/actions/workflows/pocket.yml/runs?event=issues&per_page=20`);
    const runs = (d.workflow_runs || []).filter((r) => r.display_title === title);
    runs.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
    return runs[0] || null;
  } catch { return null; }
}
function fmtDur(start, end) {
  if (!start) return '—';
  const s = Math.max(0, ((end ? new Date(end) : new Date()) - new Date(start)) / 1000);
  return s < 60 ? `${Math.round(s)}s` : `${Math.floor(s / 60)}m ${Math.round(s % 60)}s`;
}
function cell(k, icon, v, sm) { return `<div class="kcell"><div class="k"><svg class="ic"><use href="#${icon}"/></svg>${k}</div><div class="v ${sm ? 'sm' : ''}">${v}</div></div>`; }

async function renderRunStatus(run) {
  const bar = $('run-status');
  if (!run) { bar.className = 'status-bar idle'; bar.textContent = 'Démarrage de la tâche…'; return null; }
  if (run.status === 'queued') { bar.className = 'status-bar queued'; bar.textContent = 'En file d\'attente…'; return null; }
  if (run.status === 'completed') {
    if (run.conclusion === 'success') { bar.className = 'status-bar ok'; bar.textContent = 'Terminé'; }
    else if (run.conclusion === 'cancelled') { bar.className = 'status-bar idle'; bar.textContent = 'Annulé'; }
    else { bar.className = 'status-bar err'; bar.textContent = 'Terminé avec un souci — voir la réponse'; }
    return null;
  }
  let step = 'Claude travaille', jobs = null;
  try {
    jobs = await gh(`/actions/runs/${run.id}/jobs`);
    const job = (jobs.jobs || []).find((j) => j.status === 'in_progress') || (jobs.jobs || [])[0];
    const cur = job && (job.steps || []).find((s) => s.status === 'in_progress');
    if (cur) step = STEP_LABELS[cur.name] || cur.name;
  } catch {}
  bar.className = 'status-bar running'; bar.textContent = step + '…';
  return jobs;
}

async function renderMonitor(run, jobs) {
  const el = $('monitor');
  let html = '<div class="kgrid">';
  html += cell('Modèle', 'i-brain', MODEL, true);
  html += cell('Agent', 'i-robot', 'Claude Pocket', true);
  html += cell('Statut', 'i-info', run ? (run.status === 'completed' ? (run.conclusion || 'fini') : run.status) : '—', true);
  html += cell('Durée', 'i-clock', run ? fmtDur(run.run_started_at, run.status === 'completed' ? run.updated_at : null) : '—', true);
  html += `<div class="kcell wide"><div class="k"><svg class="ic"><use href="#i-brain"/></svg>Contexte</div><div class="v sm">Fenêtre ~200K tokens · session neuve à chaque tâche (pas de mémoire entre tâches)</div></div>`;
  html += '</div>';
  // Timeline des étapes (= ce que Claude fait)
  if (!jobs && run && run.status !== 'completed') { try { jobs = await gh(`/actions/runs/${run.id}/jobs`); } catch {} }
  const job = jobs && ((jobs.jobs || []).find((j) => j.name && j.name.includes('pocket')) || (jobs.jobs || [])[0]);
  if (job && job.steps) {
    const shown = job.steps.filter((s) => STEP_LABELS[s.name]);
    html += '<div class="steps">';
    for (const s of shown) {
      const cls = s.status === 'in_progress' ? 'cur' : (s.conclusion === 'success' ? 'done' : '');
      html += `<div class="step ${cls}"><span class="sdot"></span>${STEP_LABELS[s.name]}</div>`;
    }
    html += '</div>';
  }
  el.innerHTML = html;
}

// ── Détail tâche ────────────────────────────────────────────────────────────
async function openDetail(number, title) {
  stopPoll(); show('detail');
  $('detail-title').textContent = `Tâche #${number}`;
  $('run-status').className = 'status-bar idle'; $('run-status').textContent = 'Chargement…';
  $('monitor').innerHTML = ''; $('comments').innerHTML = ''; $('approve').classList.add('hidden'); $('detail-msg').textContent = '';
  const load = async () => {
    try {
      const [issue, comments] = await Promise.all([gh(`/issues/${number}`), gh(`/issues/${number}/comments`)]);
      const t = title || issue.title;
      const approved = issue.labels.map((l) => l.name).includes('approved');
      const run = await findRun(t);
      const jobs = await renderRunStatus(run);
      await renderMonitor(run, jobs);
      const c = $('comments'); c.innerHTML = '';
      if (!comments.length) c.innerHTML = '<p class="empty">En attente de Claude…</p>';
      else for (const cm of comments) {
        const prog = /^▶️|^🔎|^📊|^🧠|^⏳|je m'en occupe|^je /i.test(cm.body.trim());
        const div = document.createElement('div'); div.className = 'comment' + (prog ? ' progress' : '');
        div.innerHTML = `<div class="who">${escapeHtml(cm.user.login)} · ${timeago(cm.created_at)}</div>${escapeHtml(cm.body)}`;
        c.appendChild(div);
      }
      const needsApproval = comments.some((cm) => /preview|approb|approuv|approved/i.test(cm.body)) && !approved && issue.state === 'open';
      $('approve').classList.toggle('hidden', !needsApproval);
      $('approve').onclick = () => approve(number);
      if (run && run.status === 'completed') stopPoll();
    } catch (e) { $('detail-msg').className = 'msg err'; $('detail-msg').textContent = friendlyError(e); stopPoll(); }
  };
  await load();
  pollTimer = setInterval(load, 6000);
}
async function approve(number) {
  const m = $('detail-msg'); m.className = 'msg'; m.textContent = 'Approbation…';
  try { await gh(`/issues/${number}/labels`, { method: 'POST', body: JSON.stringify({ labels: ['approved'] }) }); m.className = 'msg ok'; m.textContent = 'Approuvé — Claude exécute.'; $('approve').classList.add('hidden'); }
  catch (e) { m.className = 'msg err'; m.textContent = friendlyError(e); }
}
function stopPoll() { if (pollTimer) { clearInterval(pollTimer); pollTimer = null; } }

// ── Vue Système (device + Claude) ───────────────────────────────────────────
async function renderSystem() {
  const dev = [];
  dev.push(cell('CPU (cœurs)', 'i-cpu', navigator.hardwareConcurrency || '—', true));
  dev.push(cell('Mémoire', 'i-cpu', navigator.deviceMemory ? navigator.deviceMemory + ' Go' : 'non exposé', true));
  dev.push(cell('Plateforme', 'i-info', escapeHtml(navigator.platform || '—'), true));
  dev.push(cell('Écran', 'i-info', `${screen.width}×${screen.height}`, true));
  const conn = navigator.connection && navigator.connection.effectiveType;
  dev.push(cell('Réseau', 'i-info', conn || 'non exposé (iOS)', true));
  let bat = 'non exposé (iOS)';
  if (navigator.getBattery) { try { const b = await navigator.getBattery(); bat = Math.round(b.level * 100) + '%' + (b.charging ? ' ⚡' : ''); } catch {} }
  dev.push(cell('Batterie', 'i-info', bat, true));
  $('system-grid').innerHTML = dev.join('');
  $('claude-grid').innerHTML = [
    cell('Modèle', 'i-brain', MODEL, true),
    cell('Tours max', 'i-info', '15', true),
    cell('Exécution', 'i-robot', 'GitHub Actions (cloud)', true),
    cell('Contexte', 'i-brain', '~200K, neuf par tâche', true),
  ].join('');
}

// ── Notifications push ──────────────────────────────────────────────────────
function urlB64ToUint8Array(b64s) {
  const pad = '='.repeat((4 - b64s.length % 4) % 4);
  const base = (b64s + pad).replace(/-/g, '+').replace(/_/g, '/');
  const raw = atob(base); const arr = new Uint8Array(raw.length);
  for (let i = 0; i < raw.length; i++) arr[i] = raw.charCodeAt(i);
  return arr;
}
async function enablePush() {
  const m = $('push-msg'); m.className = 'msg';
  if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
    m.className = 'msg err'; m.textContent = 'Push non disponible. Sur iPhone : ouvre l\'app DEPUIS l\'écran d\'accueil (iOS 16.4+).'; return;
  }
  m.textContent = 'Demande d\'autorisation…';
  try {
    const perm = await Notification.requestPermission();
    if (perm !== 'granted') { m.className = 'msg err'; m.textContent = 'Permission refusée.'; return; }
    const reg = await navigator.serviceWorker.ready;
    let sub = await reg.pushManager.getSubscription();
    if (!sub) sub = await reg.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: urlB64ToUint8Array(VAPID_PUBLIC) });
    await putFile(`pocket-data/sub-${LS.device}.json`, sub.toJSON());
    m.className = 'msg ok'; m.textContent = '✅ Notifications activées — tu seras prévenu à la fin de chaque tâche.';
  } catch (e) { m.className = 'msg err'; m.textContent = 'Échec : ' + (e.message || e); }
}

// ── Navigation ──────────────────────────────────────────────────────────────
function show(which) {
  $('detail').classList.toggle('hidden', which !== 'detail');
  $('system').classList.toggle('hidden', which !== 'system');
  for (const id of ['composer', 'history']) $(id).classList.toggle('hidden', which === 'detail' || which === 'system');
  if (which !== 'detail') stopPoll();
}
function escapeHtml(s) { return String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])); }
function timeago(iso) { const s = Math.max(0, (Date.now() - new Date(iso)) / 1000); if (s < 60) return 'à l\'instant'; if (s < 3600) return `il y a ${Math.floor(s / 60)} min`; return `il y a ${Math.floor(s / 3600)} h`; }

async function testConn(silent) {
  const dot = $('conn-dot');
  try { const r = await gh(''); dot.className = 'dot ok'; return r; }
  catch { dot.className = 'dot err'; if (!silent) throw new Error('non connecté'); return null; }
}

// ── Init ────────────────────────────────────────────────────────────────────
function init() {
  $('repo').value = LS.repo || 'GaspardCoche/agent-system';
  $('pat').value = LS.pat;
  if (!LS.repo || !LS.pat) $('settings').classList.remove('hidden');

  $('nav-settings').onclick = () => $('settings').classList.toggle('hidden');
  $('nav-system').onclick = () => { renderSystem(); show('system'); };
  $('system-back').onclick = () => show('main');
  $('back').onclick = () => { show('main'); renderHistory(); };

  $('save-settings').onclick = async () => {
    LS.repo = $('repo').value.trim(); LS.pat = $('pat').value.trim();
    const m = $('settings-msg'); m.className = 'msg'; m.textContent = 'Test de connexion…';
    try {
      const r = await testConn(false);
      let who = '';
      try { const u = await (await fetch('https://api.github.com/user', { headers: { Authorization: `Bearer ${LS.pat}`, Accept: 'application/vnd.github+json' } })).json(); if (u && u.login) who = ` · ${u.login}`; } catch {}
      m.className = 'msg ok'; m.textContent = `Connecté à ${r.full_name}${who}`;
      setTimeout(() => $('settings').classList.add('hidden'), 1400);
    } catch (e) { m.className = 'msg err'; m.textContent = friendlyError(e); }
  };
  $('enable-push').onclick = enablePush;

  $('write-allowed').onchange = (e) => $('conditions-wrap').classList.toggle('hidden', !e.target.checked);
  $('dispatch').onclick = dispatch;
  for (const ch of document.querySelectorAll('.chip')) ch.onclick = () => { $('demande').value = ch.dataset.q; $('demande').focus(); };

  setupMic(); renderHistory();
  if (LS.repo && LS.pat) testConn(true);
  if ('serviceWorker' in navigator) navigator.serviceWorker.register('sw.js').catch(() => {});
}

function setupMic() {
  const standalone = window.navigator.standalone === true || matchMedia('(display-mode: standalone)').matches;
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  const mic = $('mic');
  if (standalone || !SR) { mic.style.display = 'none'; $('mic-hint').classList.remove('hidden'); return; }
  const rec = new SR(); rec.lang = 'fr-FR'; rec.interimResults = true; rec.continuous = true;
  let base = '', live = false;
  rec.onresult = (e) => { let t = ''; for (let i = e.resultIndex; i < e.results.length; i++) t += e.results[i][0].transcript; $('demande').value = (base + ' ' + t).trim(); };
  rec.onerror = () => { live = false; mic.classList.remove('live'); };
  rec.onend = () => { live = false; mic.classList.remove('live'); };
  mic.onclick = () => { if (live) { rec.stop(); return; } base = $('demande').value; try { rec.start(); live = true; mic.classList.add('live'); } catch {} };
}

document.addEventListener('DOMContentLoaded', init);
