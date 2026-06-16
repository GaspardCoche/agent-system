'use strict';

// ── État & stockage local ────────────────────────────────────────────────
const LS = {
  get repo() { return localStorage.getItem('pocket_repo') || ''; },
  set repo(v) { localStorage.setItem('pocket_repo', v); },
  get pat() { return localStorage.getItem('pocket_pat') || ''; },
  set pat(v) { localStorage.setItem('pocket_pat', v); },
  get history() { try { return JSON.parse(localStorage.getItem('pocket_history') || '[]'); } catch { return []; } },
  set history(v) { localStorage.setItem('pocket_history', JSON.stringify(v.slice(0, 50))); },
};

const $ = (id) => document.getElementById(id);
let pollTimer = null;

// ── Helper API GitHub ────────────────────────────────────────────────────
async function gh(path, opts = {}) {
  if (!LS.pat || !LS.repo) throw new Error('Configure le repo et le token (⚙️).');
  const res = await fetch(`https://api.github.com/repos/${LS.repo}${path}`, {
    ...opts,
    headers: {
      'Authorization': `Bearer ${LS.pat}`,
      'Accept': 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28',
      'Content-Type': 'application/json',
      ...(opts.headers || {}),
    },
  });
  if (!res.ok) {
    let detail = '';
    try { detail = (await res.json()).message || ''; } catch {}
    const err = new Error(`GitHub ${res.status} ${detail}`.trim());
    err.status = res.status;
    throw err;
  }
  return res.status === 204 ? null : res.json();
}

function friendlyError(e) {
  if (e.status === 403 || e.status === 404) {
    return `${e.message}\n→ Ton token n'a probablement pas la permission « Issues : Read and write » (et « Actions : Read and write ») sur le repo. Corrige-le dans GitHub puis ⚙️ → Enregistrer & tester.`;
  }
  if (e.status === 401) return `${e.message}\n→ Token invalide ou expiré. Recolle-le dans ⚙️.`;
  return e.message;
}

// Crée les labels s'ils n'existent pas (idempotent)
async function ensureLabels() {
  for (const [name, color] of [['pocket', '8b5cf6'], ['approved', '3fb950']]) {
    try { await gh('/labels', { method: 'POST', body: JSON.stringify({ name, color }) }); }
    catch (e) { /* déjà existant (422) ou pas de droit → ignore, l'erreur réelle remontera au POST issue */ }
  }
}

// ── Composer : Dispatch ──────────────────────────────────────────────────
function buildBody(demande, writeAllowed, conditions, workflow, agent) {
  return [
    '### Demande', '', demande, '',
    "### Autoriser l'écriture ?", '', writeAllowed ? 'oui' : 'non', '',
    "### Conditions d'écriture (si OUI)", '', conditions || '_No response_', '',
    '### Workflow (recette)', '', workflow || 'auto', '',
    '### Agent (optionnel)', '', agent || 'auto', '',
  ].join('\n');
}

async function dispatch() {
  const demande = $('demande').value.trim();
  const msg = $('composer-msg');
  if (!demande) { msg.className = 'msg err'; msg.textContent = 'Écris une demande.'; return; }
  const writeAllowed = $('write-allowed').checked;
  const conditions = $('conditions').value.trim();
  const workflow = $('workflow').value;
  const agent = $('agent').value;

  msg.className = 'msg'; msg.textContent = '⏳ Envoi…';
  try {
    await ensureLabels();
    const title = '[Pocket] ' + demande.slice(0, 60).replace(/\n/g, ' ');
    const issue = await gh('/issues', {
      method: 'POST',
      body: JSON.stringify({ title, body: buildBody(demande, writeAllowed, conditions, workflow, agent), labels: ['pocket'] }),
    });
    const hist = LS.history;
    hist.unshift({ number: issue.number, title, created: Date.now(), writeAllowed });
    LS.history = hist;
    $('demande').value = ''; $('conditions').value = '';
    $('write-allowed').checked = false; $('conditions-wrap').classList.add('hidden');
    msg.className = 'msg ok'; msg.textContent = `✅ Tâche #${issue.number} envoyée.`;
    renderHistory();
    openDetail(issue.number, title);
  } catch (e) {
    msg.className = 'msg err'; msg.textContent = '❌ ' + friendlyError(e);
  }
}

// ── Historique ───────────────────────────────────────────────────────────
function renderHistory() {
  const ul = $('history-list');
  const hist = LS.history;
  if (!hist.length) { ul.innerHTML = '<li class="empty">Aucune tâche pour l\'instant.</li>'; return; }
  ul.innerHTML = '';
  for (const h of hist) {
    const li = document.createElement('li');
    li.innerHTML = `<span class="t">#${h.number} ${escapeHtml(h.title.replace('[Pocket] ', ''))}</span><span class="badge pending">ouvrir ›</span>`;
    li.onclick = () => openDetail(h.number, h.title);
    ul.appendChild(li);
  }
}

// ── Vue console : statut du run GitHub Actions ───────────────────────────
async function findRun(title) {
  try {
    const data = await gh(`/actions/workflows/pocket.yml/runs?event=issues&per_page=20`);
    const runs = (data.workflow_runs || []).filter((r) => r.display_title === title);
    runs.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
    return runs[0] || null;
  } catch { return null; }
}

const STEP_LABELS = {
  'Set up job': 'Préparation…',
  'Run actions/checkout@v4': 'Récupération du code…',
  'Install MCP servers': 'Installation des outils…',
  'Run actions/setup-python@v5': 'Préparation Python…',
  'Write task to disk': 'Lecture de ta demande…',
  'Write MCP config with secrets': 'Connexion aux apps (HubSpot…)',
  'Build claude_args': 'Configuration…',
  'Run Claude Pocket': '🧠 Claude travaille…',
};

async function renderRunStatus(run) {
  const bar = $('run-status');
  if (!run) { bar.className = 'status-bar idle'; bar.textContent = '⏳ Démarrage de la tâche…'; return; }
  if (run.status === 'queued') { bar.className = 'status-bar queued'; bar.textContent = '⏳ En file d\'attente…'; return; }
  if (run.status === 'completed') {
    if (run.conclusion === 'success') { bar.className = 'status-bar ok'; bar.textContent = '✅ Terminé — réponse ci-dessous.'; }
    else if (run.conclusion === 'cancelled') { bar.className = 'status-bar idle'; bar.textContent = '⏹️ Annulé.'; }
    else { bar.className = 'status-bar err'; bar.textContent = '⚠️ Terminé avec un souci — voir la réponse.'; }
    return;
  }
  // in_progress → essayer de montrer l'étape courante
  let step = 'Claude travaille…';
  try {
    const jobs = await gh(`/actions/runs/${run.id}/jobs`);
    const job = (jobs.jobs || []).find((j) => j.status === 'in_progress') || (jobs.jobs || [])[0];
    const cur = job && (job.steps || []).find((s) => s.status === 'in_progress');
    if (cur) step = STEP_LABELS[cur.name] || cur.name;
  } catch {}
  bar.className = 'status-bar running'; bar.textContent = '▶️ ' + step;
}

// ── Détail d'une tâche (+ console live) ──────────────────────────────────
async function openDetail(number, title) {
  stopPoll();
  show('detail');
  $('detail-title').textContent = `Tâche #${number}`;
  $('run-status').className = 'status-bar idle'; $('run-status').textContent = '⏳ Chargement…';
  $('detail-meta').textContent = '';
  $('comments').innerHTML = '';
  $('approve').classList.add('hidden');
  $('detail-msg').textContent = '';

  const load = async () => {
    try {
      const [issue, comments] = await Promise.all([
        gh(`/issues/${number}`),
        gh(`/issues/${number}/comments`),
      ]);
      const t = title || issue.title;
      const labels = issue.labels.map((l) => l.name);
      const approved = labels.includes('approved');
      $('detail-meta').innerHTML =
        `écriture : ${issue.body.includes('\noui') ? 'demandée' : 'non'}` + (approved ? ' · ✅ approuvée' : '');

      // Console : statut du run
      const run = await findRun(t);
      await renderRunStatus(run);

      // Feed des commentaires
      const c = $('comments');
      c.innerHTML = '';
      if (!comments.length) {
        c.innerHTML = '<p class="empty">En attente de la première mise à jour de Claude…</p>';
      } else {
        for (const cm of comments) {
          const div = document.createElement('div');
          div.className = 'comment';
          div.innerHTML = `<div class="who">${escapeHtml(cm.user.login)} · ${timeago(cm.created_at)}</div>${escapeHtml(cm.body)}`;
          c.appendChild(div);
        }
      }
      const needsApproval = comments.some((cm) => /preview|approb|approuv|approved/i.test(cm.body)) && !approved && issue.state === 'open';
      $('approve').classList.toggle('hidden', !needsApproval);
      $('approve').onclick = () => approve(number);

      // Stopper le poll si terminé
      if (run && run.status === 'completed') stopPoll();
    } catch (e) {
      $('detail-msg').className = 'msg err';
      $('detail-msg').textContent = '❌ ' + friendlyError(e);
      stopPoll();
    }
  };

  await load();
  pollTimer = setInterval(load, 8000);
}

async function approve(number) {
  const m = $('detail-msg');
  m.className = 'msg'; m.textContent = '⏳ Approbation…';
  try {
    await gh(`/issues/${number}/labels`, { method: 'POST', body: JSON.stringify({ labels: ['approved'] }) });
    m.className = 'msg ok'; m.textContent = '✅ Approuvé — Claude exécute.';
    $('approve').classList.add('hidden');
  } catch (e) {
    m.className = 'msg err'; m.textContent = '❌ ' + friendlyError(e);
  }
}

function stopPoll() { if (pollTimer) { clearInterval(pollTimer); pollTimer = null; } }

// ── Dictée vocale ────────────────────────────────────────────────────────
function setupMic() {
  const standalone = window.navigator.standalone === true || matchMedia('(display-mode: standalone)').matches;
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  const mic = $('mic');
  // En PWA iOS (écran d'accueil) la reconnaissance web est peu fiable → on guide vers la dictée clavier.
  if (standalone || !SR) {
    mic.style.display = 'none';
    $('mic-hint').classList.remove('hidden');
    return;
  }
  const rec = new SR();
  rec.lang = 'fr-FR'; rec.interimResults = true; rec.continuous = true;
  let base = '', live = false;
  rec.onresult = (e) => {
    let txt = '';
    for (let i = e.resultIndex; i < e.results.length; i++) txt += e.results[i][0].transcript;
    $('demande').value = (base + ' ' + txt).trim();
  };
  rec.onerror = () => { live = false; mic.classList.remove('live'); };
  rec.onend = () => { live = false; mic.classList.remove('live'); };
  mic.onclick = () => {
    if (live) { rec.stop(); return; }
    base = $('demande').value;
    try { rec.start(); live = true; mic.classList.add('live'); } catch {}
  };
}

// ── Navigation & UI ──────────────────────────────────────────────────────
function show(which) {
  $('detail').classList.toggle('hidden', which !== 'detail');
  for (const id of ['composer', 'history']) $(id).classList.toggle('hidden', which === 'detail');
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

function timeago(iso) {
  const s = Math.max(0, (Date.now() - new Date(iso)) / 1000);
  if (s < 60) return 'à l\'instant';
  if (s < 3600) return `il y a ${Math.floor(s / 60)} min`;
  return `il y a ${Math.floor(s / 3600)} h`;
}

// ── Init ─────────────────────────────────────────────────────────────────
function init() {
  $('repo').value = LS.repo || 'GaspardCoche/agent-system';
  $('pat').value = LS.pat;
  if (!LS.repo || !LS.pat) $('settings').classList.remove('hidden');
  $('settings-btn').onclick = () => $('settings').classList.toggle('hidden');
  $('save-settings').onclick = async () => {
    LS.repo = $('repo').value.trim();
    LS.pat = $('pat').value.trim();
    const m = $('settings-msg');
    m.className = 'msg'; m.textContent = '⏳ Test de connexion…';
    try {
      const r = await gh('');
      m.className = 'msg ok'; m.textContent = `✅ Connecté à ${r.full_name}`;
      setTimeout(() => $('settings').classList.add('hidden'), 1200);
    } catch (e) {
      m.className = 'msg err'; m.textContent = '❌ ' + friendlyError(e);
    }
  };

  $('write-allowed').onchange = (e) => $('conditions-wrap').classList.toggle('hidden', !e.target.checked);
  $('dispatch').onclick = dispatch;
  $('back').onclick = () => { stopPoll(); show('main'); renderHistory(); };

  setupMic();
  renderHistory();

  if ('serviceWorker' in navigator) navigator.serviceWorker.register('sw.js').catch(() => {});
}

document.addEventListener('DOMContentLoaded', init);
