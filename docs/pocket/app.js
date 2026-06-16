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
    throw new Error(`GitHub ${res.status} ${detail}`);
  }
  return res.status === 204 ? null : res.json();
}

// Crée les labels s'ils n'existent pas (idempotent)
async function ensureLabels() {
  for (const [name, color] of [['agent', '6aa3ff'], ['pocket', '8b5cf6'], ['approved', '3fb950']]) {
    try { await gh('/labels', { method: 'POST', body: JSON.stringify({ name, color }) }); }
    catch (e) { /* déjà existant (422) → ignore */ }
  }
}

// ── Composer : Dispatch ──────────────────────────────────────────────────
function buildBody(demande, writeAllowed, conditions, agent) {
  // Mime le rendu d'un GitHub issue-form pour un parsing uniforme par Dispatch.
  return [
    '### Demande', '', demande, '',
    "### Autoriser l'écriture ?", '', writeAllowed ? 'oui' : 'non', '',
    "### Conditions d'écriture (si OUI)", '', conditions || '_No response_', '',
    '### Agent (optionnel)', '', agent || 'auto', '',
  ].join('\n');
}

async function dispatch() {
  const demande = $('demande').value.trim();
  const msg = $('composer-msg');
  if (!demande) { msg.className = 'msg err'; msg.textContent = 'Écris une demande.'; return; }
  const writeAllowed = $('write-allowed').checked;
  const conditions = $('conditions').value.trim();
  const agent = $('agent').value;

  msg.className = 'msg'; msg.textContent = '⏳ Envoi…';
  try {
    await ensureLabels();
    const title = '[Pocket] ' + demande.slice(0, 60).replace(/\n/g, ' ');
    const issue = await gh('/issues', {
      method: 'POST',
      body: JSON.stringify({
        title,
        body: buildBody(demande, writeAllowed, conditions, agent),
        labels: ['agent', 'pocket'],
      }),
    });
    const hist = LS.history;
    hist.unshift({ number: issue.number, title, created: Date.now(), writeAllowed });
    LS.history = hist;
    $('demande').value = ''; $('conditions').value = '';
    $('write-allowed').checked = false; $('conditions-wrap').classList.add('hidden');
    msg.className = 'msg ok'; msg.textContent = `✅ Tâche #${issue.number} envoyée.`;
    renderHistory();
    openDetail(issue.number);
  } catch (e) {
    msg.className = 'msg err'; msg.textContent = '❌ ' + e.message;
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
    li.innerHTML = `<span class="t">#${h.number} ${escapeHtml(h.title.replace('[Pocket] ', ''))}</span>
                    <span class="badge pending">ouvrir</span>`;
    li.onclick = () => openDetail(h.number);
    ul.appendChild(li);
  }
}

// ── Détail d'une tâche ───────────────────────────────────────────────────
async function openDetail(number) {
  stopPoll();
  show('detail');
  $('detail-title').textContent = `Tâche #${number}`;
  $('detail-meta').textContent = '⏳ Chargement…';
  $('comments').innerHTML = '';
  $('approve').classList.add('hidden');
  $('detail-msg').textContent = '';

  const load = async () => {
    try {
      const [issue, comments] = await Promise.all([
        gh(`/issues/${number}`),
        gh(`/issues/${number}/comments`),
      ]);
      const labels = issue.labels.map((l) => l.name);
      const approved = labels.includes('approved');
      $('detail-meta').innerHTML =
        `État : <span class="badge ${issue.state}">${issue.state}</span> · ` +
        `écriture : ${labels.includes('pocket') && issue.body.includes('\noui') ? 'autorisée' : 'non'}` +
        (approved ? ' · ✅ approuvée' : '');

      const c = $('comments');
      c.innerHTML = '';
      if (!comments.length) {
        c.innerHTML = '<p class="empty">Pas encore de réponse — l\'agent travaille…</p>';
      } else {
        for (const cm of comments) {
          const div = document.createElement('div');
          div.className = 'comment';
          div.innerHTML = `<div class="who">${escapeHtml(cm.user.login)}</div>${escapeHtml(cm.body)}`;
          c.appendChild(div);
        }
      }
      // Bouton approuver : si une demande d'approbation est détectée et pas encore approuvée
      const needsApproval = comments.some((cm) => /preview|approb|approuv|approved/i.test(cm.body)) && !approved && issue.state === 'open';
      $('approve').classList.toggle('hidden', !needsApproval);
      $('approve').onclick = () => approve(number);
    } catch (e) {
      $('detail-msg').className = 'msg err';
      $('detail-msg').textContent = '❌ ' + e.message;
      stopPoll();
    }
  };

  await load();
  pollTimer = setInterval(load, 15000); // poll toutes les 15 s
}

async function approve(number) {
  const m = $('detail-msg');
  m.className = 'msg'; m.textContent = '⏳ Approbation…';
  try {
    await gh(`/issues/${number}/labels`, { method: 'POST', body: JSON.stringify({ labels: ['approved'] }) });
    m.className = 'msg ok'; m.textContent = '✅ Approuvé — l\'agent va exécuter.';
    $('approve').classList.add('hidden');
  } catch (e) {
    m.className = 'msg err'; m.textContent = '❌ ' + e.message;
  }
}

function stopPoll() { if (pollTimer) { clearInterval(pollTimer); pollTimer = null; } }

// ── Dictée vocale (Web Speech API) ───────────────────────────────────────
function setupMic() {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  const mic = $('mic');
  if (!SR) { mic.style.display = 'none'; return; }
  const rec = new SR();
  rec.lang = 'fr-FR'; rec.interimResults = true; rec.continuous = true;
  let base = '';
  let live = false;
  rec.onresult = (e) => {
    let txt = '';
    for (let i = e.resultIndex; i < e.results.length; i++) txt += e.results[i][0].transcript;
    $('demande').value = (base + ' ' + txt).trim();
  };
  rec.onend = () => { live = false; mic.classList.remove('live'); };
  mic.onclick = () => {
    if (live) { rec.stop(); return; }
    base = $('demande').value;
    try { rec.start(); live = true; mic.classList.add('live'); } catch {}
  };
}

// ── Navigation & UI ──────────────────────────────────────────────────────
function show(which) {
  // 'detail' = vue détail ; sinon vue principale
  $('detail').classList.toggle('hidden', which !== 'detail');
  for (const id of ['composer', 'history']) $(id).classList.toggle('hidden', which === 'detail');
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

// ── Init ─────────────────────────────────────────────────────────────────
function init() {
  // Réglages
  $('repo').value = LS.repo;
  $('pat').value = LS.pat;
  if (!LS.repo || !LS.pat) $('settings').classList.remove('hidden');
  $('settings-btn').onclick = () => $('settings').classList.toggle('hidden');
  $('save-settings').onclick = () => {
    LS.repo = $('repo').value.trim();
    LS.pat = $('pat').value.trim();
    $('settings').classList.add('hidden');
  };

  // Toggle conditions
  $('write-allowed').onchange = (e) => $('conditions-wrap').classList.toggle('hidden', !e.target.checked);

  $('dispatch').onclick = dispatch;
  $('back').onclick = () => { stopPoll(); show('main'); renderHistory(); };

  setupMic();
  renderHistory();

  if ('serviceWorker' in navigator) navigator.serviceWorker.register('sw.js').catch(() => {});
}

document.addEventListener('DOMContentLoaded', init);
