'use strict';

const VAPID_PUBLIC = 'BBrWaeSczwSz-wCywXN0OlFQ72UdUWRLLeAU9fjzD_8uw7saPxizhDNu6jTfe4xM4hbk_pV0GoAVxoTMD6BZpTw';
const MODEL = 'claude-opus-4-8';
const APP_VERSION = 'v10';
const CTX_WINDOW = 200000; // fenêtre de contexte (tokens) du modèle
function estTokens(text) { return Math.round((text || '').length / 4); }
function slugify(s) { return (s || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '').slice(0, 40); }
function decodeB64(c) { try { return decodeURIComponent(escape(atob((c || '').replace(/\s/g, '')))); } catch { return ''; } }
const CATS = {
  'cat:crm': { label: 'CRM', color: '#3b6fd4' },
  'cat:enrich': { label: 'Enrichissement', color: '#8957e5' },
  'cat:outreach': { label: 'Outreach', color: '#2da44e' },
  'cat:web': { label: 'Web', color: '#bf8700' },
  'cat:vault': { label: 'Vault', color: '#1f8f9a' },
  'cat:code': { label: 'Code', color: '#bf3989' },
  'cat:other': { label: 'Autre', color: '#57606a' },
};

const LS = {
  get repo() { return localStorage.getItem('pocket_repo') || ''; }, set repo(v) { localStorage.setItem('pocket_repo', v); },
  get pat() { return localStorage.getItem('pocket_pat') || ''; }, set pat(v) { localStorage.setItem('pocket_pat', v); },
  get history() { try { return JSON.parse(localStorage.getItem('pocket_history') || '[]'); } catch { return []; } },
  set history(v) { localStorage.setItem('pocket_history', JSON.stringify(v.slice(0, 50))); },
  get device() { let d = localStorage.getItem('pocket_device'); if (!d) { d = 'dev-' + Math.random().toString(36).slice(2, 10); localStorage.setItem('pocket_device', d); } return d; },
  get theme() { return localStorage.getItem('pocket_theme') || 'auto'; }, set theme(v) { localStorage.setItem('pocket_theme', v); },
};
const $ = (id) => document.getElementById(id);
let pollTimer = null, allIssues = [], currentFilter = 'all', connectedLogin = '', detailNum = null, attachedFiles = [];
let allModes = [], selectedMode = 'auto', editingMode = null;

// ── API GitHub ──────────────────────────────────────────────────────────────
async function gh(path, opts = {}) {
  if (!LS.pat || !LS.repo) throw new Error('Configure le repo et le token (engrenage).');
  const res = await fetch(`https://api.github.com/repos/${LS.repo}${path}`, {
    ...opts, headers: { 'Authorization': `Bearer ${LS.pat}`, 'Accept': 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28', 'Content-Type': 'application/json', ...(opts.headers || {}) },
  });
  if (!res.ok) { let d = ''; try { d = (await res.json()).message || ''; } catch {} const e = new Error(`GitHub ${res.status} ${d}`.trim()); e.status = res.status; throw e; }
  return res.status === 204 ? null : res.json();
}
function friendlyError(e) {
  if (e.status === 403) return `${e.message}\n→ Token « classic » (scope repo) du compte gcoche-bit requis + accès écriture au repo.`;
  if (e.status === 401) return `${e.message}\n→ Token invalide/expiré.`;
  return e.message;
}
function b64(s) { return btoa(unescape(encodeURIComponent(s))); }
async function putFile(path, obj) {
  let sha; try { sha = (await gh(`/contents/${path}`)).sha; } catch {}
  await gh(`/contents/${path}`, { method: 'PUT', body: JSON.stringify({ message: `pocket: sub ${LS.device}`, content: b64(JSON.stringify(obj, null, 2)), sha }) });
}
async function putRaw(path, b64content) {
  let sha; try { sha = (await gh(`/contents/${path}`)).sha; } catch {}
  await gh(`/contents/${path}`, { method: 'PUT', body: JSON.stringify({ message: `pocket: upload ${path}`, content: b64content, sha }) });
}

// ── Import de fichiers ──────────────────────────────────────────────────────
function addFiles(fileList) {
  for (const f of fileList) {
    if (f.size > 4 * 1024 * 1024) { alert(`${f.name} dépasse 4 Mo — ignoré.`); continue; }
    const r = new FileReader();
    r.onload = () => { attachedFiles.push({ name: f.name, size: f.size, b64: String(r.result).split(',')[1] || '' }); renderFileList(); };
    r.readAsDataURL(f);
  }
}
function renderFileList() {
  const el = $('file-list'); el.innerHTML = '';
  attachedFiles.forEach((f, i) => {
    const kb = Math.max(1, Math.round(f.size / 1024));
    const row = document.createElement('div'); row.className = 'file-row';
    row.innerHTML = `<span class="fx">📎 ${escapeHtml(f.name)} · ${kb} Ko</span><button title="Retirer">×</button>`;
    row.querySelector('button').onclick = () => { attachedFiles.splice(i, 1); renderFileList(); };
    el.appendChild(row);
  });
}
async function ensureLabels() {
  const labels = [['pocket', '8b5cf6'], ['approved', '3fb950'], ...Object.entries(CATS).map(([k, v]) => [k, v.color.replace('#', '')])];
  for (const [name, color] of labels) { try { await gh('/labels', { method: 'POST', body: JSON.stringify({ name, color }) }); } catch {} }
}

// ── Dispatch ────────────────────────────────────────────────────────────────
function buildBody(d, w, c) {
  return ['### Demande', '', d, '', "### Autoriser l'écriture ?", '', w ? 'oui' : 'non', '', "### Conditions d'écriture (si OUI)", '', c || '_No response_', '', '### Workflow (recette)', '', 'auto', '', '### Agent (optionnel)', '', 'auto', ''].join('\n');
}
async function dispatch() {
  const demande = $('demande').value.trim(); const msg = $('composer-msg');
  if (!demande) { msg.className = 'msg err'; msg.textContent = 'Écris une demande.'; return; }
  const w = $('write-allowed').checked, c = $('conditions').value.trim();
  msg.className = 'msg'; msg.textContent = 'Envoi…';
  try {
    await ensureLabels();
    let attachNote = '';
    if (attachedFiles.length) {
      msg.textContent = 'Envoi des fichiers…';
      const paths = [];
      for (const f of attachedFiles) {
        const path = `pocket-data/uploads/${Date.now()}-${f.name.replace(/[^a-zA-Z0-9._-]/g, '_')}`;
        await putRaw(path, f.b64); paths.push(path);
      }
      attachNote = '\n\n### Fichiers joints\n' + paths.map((p) => '- `' + p + '` (lis-le avec `cat ' + p + '`)').join('\n');
      msg.textContent = 'Envoi…';
    }
    const title = '[Pocket] ' + demande.slice(0, 60).replace(/\n/g, ' ');
    const modeNote = '\n\n### Mode\n\n' + (selectedMode || 'auto');
    const issue = await gh('/issues', { method: 'POST', body: JSON.stringify({ title, body: buildBody(demande, w, c) + modeNote + attachNote, labels: ['pocket'] }) });
    $('demande').value = ''; $('conditions').value = ''; $('write-allowed').checked = false; $('conditions-wrap').classList.add('hidden');
    attachedFiles = []; renderFileList();
    msg.className = 'msg ok'; msg.textContent = `Tâche #${issue.number} envoyée.`;
    navigate('detail:' + issue.number);
  } catch (e) { msg.className = 'msg err'; msg.textContent = friendlyError(e); }
}

// ── Historique classé par système ───────────────────────────────────────────
function issueCat(issue) { const l = (issue.labels || []).map((x) => x.name || x).find((n) => n.startsWith('cat:')); return l || null; }
async function loadHistory() {
  try { allIssues = await gh('/issues?labels=pocket&state=all&per_page=40&sort=created&direction=desc'); }
  catch { allIssues = LS.history.map((h) => ({ number: h.number, title: h.title, labels: [], state: 'open' })); }
  renderFilters(); renderHistory();
}
function renderFilters() {
  const present = new Set(allIssues.map(issueCat).filter(Boolean));
  const el = $('cat-filters'); el.innerHTML = '';
  const mk = (key, label) => { const b = document.createElement('button'); b.className = 'chip' + (currentFilter === key ? ' active' : ''); b.textContent = label; b.onclick = () => { currentFilter = key; renderFilters(); renderHistory(); }; return b; };
  el.appendChild(mk('all', 'Tout'));
  for (const k of Object.keys(CATS)) if (present.has(k)) el.appendChild(mk(k, CATS[k].label));
}
function renderHistory() {
  const ul = $('history-list'); ul.innerHTML = '';
  let items = allIssues; if (currentFilter !== 'all') items = items.filter((i) => issueCat(i) === currentFilter);
  if (!items.length) { ul.innerHTML = '<li class="empty">Aucune tâche.</li>'; return; }
  for (const i of items) {
    const cat = issueCat(i) || 'cat:other'; const cm = CATS[cat] || CATS['cat:other'];
    const li = document.createElement('li');
    li.style.setProperty('--cat', cm.color);
    li.innerHTML = `<span class="t">#${i.number} ${escapeHtml((i.title || '').replace('[Pocket] ', ''))}</span>
      <span class="meta-r"><span class="cat-badge" style="background:${cm.color}">${cm.label}</span>
      <span class="badge ${i.state === 'open' ? 'open' : 'pending'}">${i.state === 'open' ? '●' : '✓'}</span></span>`;
    li.onclick = () => navigate('detail:' + i.number);
    ul.appendChild(li);
  }
}

// ── Modes agentiques (CRUD via repo) ────────────────────────────────────────
async function loadModes() {
  try {
    const items = await gh('/contents/pocket-modes');
    const files = (Array.isArray(items) ? items : []).filter((f) => f.name.endsWith('.json'));
    const out = [];
    for (const f of files) {
      try { const c = await gh('/contents/' + f.path); const o = JSON.parse(decodeB64(c.content)); o._sha = c.sha; out.push(o); } catch {}
    }
    allModes = out.sort((a, b) => (a.name || '').localeCompare(b.name || ''));
  } catch { allModes = []; }
  renderModeChips();
}
function renderModeChips() {
  const el = $('mode-chips'); if (!el) return; el.innerHTML = '';
  const mk = (slug, label) => { const b = document.createElement('button'); b.className = 'chip' + (selectedMode === slug ? ' active' : ''); b.textContent = label; b.onclick = () => { selectedMode = slug; renderModeChips(); }; return b; };
  el.appendChild(mk('auto', '⚡ Généraliste'));
  for (const m of allModes) el.appendChild(mk(m.slug, m.name));
}
function renderModes() {
  const ul = $('modes-list'); ul.innerHTML = '';
  if (!allModes.length) { ul.innerHTML = '<li class="empty">Aucun mode pour l\'instant. Crée ton premier agent.</li>'; return; }
  for (const m of allModes) {
    const cm = CATS[m.category] || CATS['cat:other'];
    const li = document.createElement('li'); li.style.setProperty('--cat', cm.color);
    li.innerHTML = `<div class="mh"><div><div class="mn">${escapeHtml(m.name)}</div><div class="md">${escapeHtml(m.description || '')}</div></div><div class="actions"><button class="edit">Éditer</button></div></div>`;
    li.querySelector('.edit').onclick = () => openModeEditor(m);
    ul.appendChild(li);
  }
}
async function openModeEditor(mode) {
  editingMode = mode || null;
  $('mode-editor').classList.remove('hidden');
  $('mode-name').value = mode ? mode.name : '';
  $('mode-cat').value = mode ? mode.category : 'cat:other';
  $('mode-desc').value = mode ? mode.description : '';
  $('mode-instr').value = mode ? mode.instructions : '';
  $('mode-delete').classList.toggle('hidden', !mode);
  $('mode-msg').textContent = '';
  // Programmation : reset puis charge si existante
  $('mode-freq').value = 'none'; $('sched-extra').classList.add('hidden'); $('weekday-wrap').classList.add('hidden');
  $('mode-time').value = '08:00'; $('mode-sched-demande').value = '';
  if (mode) {
    try {
      const c = await gh('/contents/pocket-schedules/' + mode.slug + '.json');
      const sc = JSON.parse(decodeB64(c.content));
      $('mode-freq').value = sc.freq; $('sched-extra').classList.remove('hidden');
      $('mode-time').value = String(sc.hour).padStart(2, '0') + ':' + String(sc.minute || 0).padStart(2, '0');
      $('mode-weekday').value = sc.weekday || 0; $('mode-sched-demande').value = sc.demande || '';
      $('weekday-wrap').classList.toggle('hidden', sc.freq !== 'weekly');
    } catch {}
  }
  $('mode-editor').scrollIntoView({ behavior: 'smooth' });
}
async function saveSchedule(slug, name, cat) {
  const path = 'pocket-schedules/' + slug + '.json';
  const freq = $('mode-freq').value;
  if (freq === 'none') {
    try { const c = await gh('/contents/' + path); await gh('/contents/' + path, { method: 'DELETE', body: JSON.stringify({ message: 'pocket: unschedule ' + slug, sha: c.sha }) }); } catch {}
    return;
  }
  const [hh, mm] = ($('mode-time').value || '08:00').split(':');
  const obj = { id: slug, mode: slug, name, category: cat, freq, hour: parseInt(hh, 10), minute: parseInt(mm, 10), weekday: parseInt($('mode-weekday').value, 10), demande: $('mode-sched-demande').value.trim() || ('Lance le mode ' + name + '.'), enabled: true, tz: 'Europe/Brussels', last_fired: '' };
  let sha; try { sha = (await gh('/contents/' + path)).sha; } catch {}
  await gh('/contents/' + path, { method: 'PUT', body: JSON.stringify({ message: 'pocket: schedule ' + slug, content: b64(JSON.stringify(obj, null, 2)), sha }) });
}
async function saveMode() {
  const name = $('mode-name').value.trim(), instr = $('mode-instr').value.trim(), m = $('mode-msg');
  if (!name || !instr) { m.className = 'msg err'; m.textContent = 'Nom et instructions requis.'; return; }
  const slug = editingMode ? editingMode.slug : slugify(name);
  const obj = { name, slug, category: $('mode-cat').value, description: $('mode-desc').value.trim(), instructions: instr, created: editingMode ? editingMode.created : Date.now() };
  m.className = 'msg'; m.textContent = 'Déploiement…';
  try {
    let sha = editingMode ? editingMode._sha : undefined;
    if (!sha) { try { sha = (await gh('/contents/pocket-modes/' + slug + '.json')).sha; } catch {} }
    await gh('/contents/pocket-modes/' + slug + '.json', { method: 'PUT', body: JSON.stringify({ message: 'pocket: mode ' + slug, content: b64(JSON.stringify(obj, null, 2)), sha }) });
    await saveSchedule(slug, name, obj.category);
    m.className = 'msg ok'; m.textContent = '✅ Mode déployé' + ($('mode-freq').value !== 'none' ? ' + programmé.' : ' — utilisable au lancement d\'une tâche.');
    $('mode-editor').classList.add('hidden');
    await loadModes(); renderModes();
  } catch (e) { m.className = 'msg err'; m.textContent = friendlyError(e); }
}
async function deleteMode() {
  if (!editingMode) return; const m = $('mode-msg'); m.className = 'msg'; m.textContent = 'Suppression…';
  try {
    await gh('/contents/pocket-modes/' + editingMode.slug + '.json', { method: 'DELETE', body: JSON.stringify({ message: 'pocket: delete mode ' + editingMode.slug, sha: editingMode._sha }) });
    try { const c = await gh('/contents/pocket-schedules/' + editingMode.slug + '.json'); await gh('/contents/pocket-schedules/' + editingMode.slug + '.json', { method: 'DELETE', body: JSON.stringify({ message: 'pocket: unschedule ' + editingMode.slug, sha: c.sha }) }); } catch {}
    if (selectedMode === editingMode.slug) selectedMode = 'auto';
    $('mode-editor').classList.add('hidden'); await loadModes(); renderModes();
  } catch (e) { m.className = 'msg err'; m.textContent = friendlyError(e); }
}

// ── Monitoring run ──────────────────────────────────────────────────────────
const STEP_LABELS = { 'Set up job': 'Préparation', 'Run actions/checkout@v4': 'Récupération du code', 'Install MCP servers': 'Installation des outils', 'Run actions/setup-python@v5': 'Préparation Python', 'Write task to disk': 'Lecture de la demande', 'Write MCP config with secrets': 'Connexion aux apps', 'Build claude_args': 'Configuration', 'Run Claude Pocket': 'Claude travaille', 'Notify (push)': 'Notification' };
async function findRun(title) {
  try { const d = await gh(`/actions/workflows/pocket.yml/runs?per_page=30`); const runs = (d.workflow_runs || []).filter((r) => r.display_title === title); runs.sort((a, b) => new Date(b.created_at) - new Date(a.created_at)); return runs[0] || null; } catch { return null; }
}
function fmtDur(s, e) { if (!s) return '—'; const x = Math.max(0, ((e ? new Date(e) : new Date()) - new Date(s)) / 1000); return x < 60 ? `${Math.round(x)}s` : `${Math.floor(x / 60)}m${Math.round(x % 60)}s`; }
function cell(k, icon, v) { return `<div class="kcell"><div class="k"><svg class="ic"><use href="#${icon}"/></svg>${k}</div><div class="v sm">${v}</div></div>`; }
async function renderRunStatus(run) {
  const bar = $('run-status');
  if (!run) { bar.className = 'status-bar idle'; bar.textContent = 'Démarrage…'; return null; }
  if (run.status === 'queued') { bar.className = 'status-bar queued'; bar.textContent = 'En file…'; return null; }
  if (run.status === 'completed') { bar.className = 'status-bar ' + (run.conclusion === 'success' ? 'ok' : (run.conclusion === 'cancelled' ? 'idle' : 'err')); bar.textContent = run.conclusion === 'success' ? 'Terminé' : (run.conclusion === 'cancelled' ? 'Annulé' : 'Terminé avec un souci'); return null; }
  let step = 'Claude travaille', jobs = null;
  try { jobs = await gh(`/actions/runs/${run.id}/jobs`); const job = (jobs.jobs || []).find((j) => j.status === 'in_progress') || (jobs.jobs || [])[0]; const cur = job && (job.steps || []).find((s) => s.status === 'in_progress'); if (cur) step = STEP_LABELS[cur.name] || cur.name; } catch {}
  bar.className = 'status-bar running'; bar.textContent = step + '…'; return jobs;
}
async function renderMonitor(run, jobs, usage) {
  const el = $('monitor');
  const u = usage || { tokens: 0, pct: 0 };
  let h = '<div class="kgrid">';
  h += cell('Modèle', 'i-brain', MODEL) + cell('Agent', 'i-robot', 'Claude Pocket');
  h += cell('Statut', 'i-info', run ? (run.status === 'completed' ? (run.conclusion || 'fini') : run.status) : '—');
  h += cell('Durée', 'i-clock', run ? fmtDur(run.run_started_at, run.status === 'completed' ? run.updated_at : null) : '—');
  h += cell('Tokens (estim.)', 'i-brain', '≈ ' + u.tokens.toLocaleString('fr-FR'));
  h += cell('Contexte', 'i-brain', u.pct.toFixed(1) + '% de 200K');
  h += `<div class="kcell wide"><div class="k"><svg class="ic"><use href="#i-brain"/></svg>Remplissage du contexte</div><div class="gauge ${u.pct > 80 ? 'warn' : ''}"><i style="width:${Math.min(100, u.pct)}%"></i></div></div></div>`;
  if (!jobs && run && run.status !== 'completed') { try { jobs = await gh(`/actions/runs/${run.id}/jobs`); } catch {} }
  const job = jobs && ((jobs.jobs || []).find((j) => j.name && j.name.includes('pocket')) || (jobs.jobs || [])[0]);
  if (job && job.steps) {
    h += '<div class="steps">';
    for (const s of job.steps.filter((s) => STEP_LABELS[s.name])) {
      const cls = s.status === 'in_progress' ? 'cur' : (s.conclusion === 'success' ? 'done' : '');
      const dur = (s.started_at && s.completed_at) ? Math.max(1, Math.round((new Date(s.completed_at) - new Date(s.started_at)) / 1000)) + 's' : '';
      h += `<div class="step ${cls}"><span class="sdot"></span>${STEP_LABELS[s.name]}${dur ? '<span style="margin-left:auto;color:var(--muted);font-size:11px">' + dur + '</span>' : ''}</div>`;
    }
    h += '</div>';
  }
  el.innerHTML = h;
}

// ── Détail + chat ───────────────────────────────────────────────────────────
function loadDetail(number) {
  stopPoll(); detailNum = number;
  $('detail-title').textContent = `Tâche #${number}`;
  $('run-status').className = 'status-bar idle'; $('run-status').textContent = 'Chargement…';
  $('monitor').innerHTML = ''; $('comments').innerHTML = ''; $('approve').classList.add('hidden'); $('detail-msg').textContent = '';
  const load = async () => {
    if (detailNum !== number) return;
    try {
      const [issue, comments] = await Promise.all([gh(`/issues/${number}`), gh(`/issues/${number}/comments?per_page=100`)]);
      const approved = (issue.labels || []).map((l) => l.name).includes('approved');
      const threadText = (issue.body || '') + comments.map((c) => c.body).join('\n');
      const tokens = estTokens(threadText);
      const usage = { tokens, pct: Math.min(100, tokens / CTX_WINDOW * 100) };
      const run = await findRun(issue.title);
      const jobs = await renderRunStatus(run);
      await renderMonitor(run, jobs, usage);
      // Activité en direct (dernier message de progression) + lien logs bruts
      const prog = comments.filter((cm) => cm.user.type !== 'User' && /^▶️|^🔎|^📊|^🧠|^⏳|m'en occupe/i.test(cm.body.trim()));
      const la = $('live-activity');
      if (run && run.status !== 'completed' && prog.length) { la.classList.remove('hidden'); la.textContent = prog[prog.length - 1].body.split('\n')[0].slice(0, 130); }
      else la.classList.add('hidden');
      const rl = $('run-link'); if (run && run.html_url) { rl.href = run.html_url; rl.classList.remove('hidden'); } else rl.classList.add('hidden');
      const c = $('comments'); c.innerHTML = '';
      const body = (issue.body || '').split('### Autoriser')[0].replace('### Demande', '').trim();
      if (body) c.appendChild(bubble(connectedLogin || 'toi', body, 'user', issue.created_at));
      for (const cm of comments) {
        const isUser = cm.user.type === 'User';
        const prog = !isUser && /^▶️|^🔎|^📊|^🧠|^⏳|m'en occupe/i.test(cm.body.trim());
        c.appendChild(bubble(cm.user.login, cm.body, isUser ? 'user' : 'assistant', cm.created_at, prog));
      }
      const needsApproval = comments.some((cm) => /preview|approb|approuv/i.test(cm.body)) && !approved && issue.state === 'open';
      $('approve').classList.toggle('hidden', !needsApproval); $('approve').onclick = () => approve(number);
    } catch (e) { $('detail-msg').className = 'msg err'; $('detail-msg').textContent = friendlyError(e); stopPoll(); }
  };
  load(); pollTimer = setInterval(load, 6000);
}
function bubble(who, text, kind, ts, prog) {
  const div = document.createElement('div'); div.className = 'comment ' + kind + (prog ? ' progress' : '');
  div.innerHTML = `<div class="who">${escapeHtml(who)}${ts ? ' · ' + timeago(ts) : ''}</div>${escapeHtml(text)}`; return div;
}
async function chatSend() {
  const ta = $('chat-input'), txt = ta.value.trim(); if (!txt || detailNum == null) return;
  ta.value = ''; ta.style.height = 'auto';
  $('comments').appendChild(bubble(connectedLogin || 'toi', txt, 'user', new Date().toISOString()));
  try { await gh(`/issues/${detailNum}/comments`, { method: 'POST', body: JSON.stringify({ body: txt }) }); setTimeout(() => { if (detailNum != null) loadDetail(detailNum); }, 900); }
  catch (e) { $('detail-msg').className = 'msg err'; $('detail-msg').textContent = friendlyError(e); }
}
async function approve(number) {
  const m = $('detail-msg'); m.className = 'msg'; m.textContent = 'Approbation…';
  try { await gh(`/issues/${number}/labels`, { method: 'POST', body: JSON.stringify({ labels: ['approved'] }) }); m.className = 'msg ok'; m.textContent = 'Approuvé — Claude exécute.'; $('approve').classList.add('hidden'); }
  catch (e) { m.className = 'msg err'; m.textContent = friendlyError(e); }
}
function stopPoll() { if (pollTimer) { clearInterval(pollTimer); pollTimer = null; } }

// ── Système ─────────────────────────────────────────────────────────────────
async function renderSystem() {
  const d = [];
  d.push(cell('CPU (cœurs)', 'i-cpu', navigator.hardwareConcurrency || '—'));
  d.push(cell('Mémoire', 'i-cpu', navigator.deviceMemory ? navigator.deviceMemory + ' Go' : 'non exposé'));
  d.push(cell('Plateforme', 'i-info', escapeHtml(navigator.platform || '—')));
  d.push(cell('Écran', 'i-info', `${screen.width}×${screen.height}`));
  d.push(cell('Réseau', 'i-info', (navigator.connection && navigator.connection.effectiveType) || 'non exposé'));
  let bat = 'non exposé (iOS)'; if (navigator.getBattery) { try { const b = await navigator.getBattery(); bat = Math.round(b.level * 100) + '%' + (b.charging ? ' ⚡' : ''); } catch {} }
  d.push(cell('Batterie', 'i-info', bat));
  $('system-grid').innerHTML = d.join('');
  $('claude-grid').innerHTML = [cell('Modèle', 'i-brain', MODEL), cell('Version app', 'i-info', APP_VERSION), cell('Exécution', 'i-robot', 'GitHub Actions'), cell('Contexte', 'i-brain', '~200K, neuf/tâche')].join('');
  // Usage estimé sur la fenêtre 5h (à partir des tâches récentes)
  const now = Date.now(), WIN = 5 * 3600 * 1000;
  const recent = (allIssues || []).filter((i) => i.created_at && now - new Date(i.created_at) < WIN);
  let tok = 0;
  for (const i of recent) tok += estTokens(i.body) + (i.comments || 0) * 250;
  const REF = 1000000; // référence indicative pour une session 5h chargée
  const pct = Math.min(100, tok / REF * 100);
  $('usage-box').innerHTML =
    `<div class="kgrid">${cell('Tâches (5h)', 'i-list', recent.length)}${cell('Tokens estim. (5h)', 'i-brain', '≈ ' + tok.toLocaleString('fr-FR'))}</div>` +
    `<div class="kcell wide" style="margin-top:8px"><div class="k"><svg class="ic"><use href="#i-clock"/></svg>Fenêtre 5h (indicatif /1M)</div><div class="gauge ${pct > 80 ? 'warn' : ''}"><i style="width:${pct}%"></i></div></div>`;
}

// ── Push ────────────────────────────────────────────────────────────────────
function urlB64ToUint8Array(s) { const p = '='.repeat((4 - s.length % 4) % 4); const b = (s + p).replace(/-/g, '+').replace(/_/g, '/'); const r = atob(b); const a = new Uint8Array(r.length); for (let i = 0; i < r.length; i++) a[i] = r.charCodeAt(i); return a; }
async function enablePush() {
  const m = $('push-msg'); m.className = 'msg';
  if (!('serviceWorker' in navigator) || !('PushManager' in window)) { m.className = 'msg err'; m.textContent = 'Push indisponible. Ouvre l\'app depuis l\'écran d\'accueil (iOS 16.4+).'; return; }
  m.textContent = 'Autorisation…';
  try {
    if (await Notification.requestPermission() !== 'granted') { m.className = 'msg err'; m.textContent = 'Permission refusée.'; return; }
    const reg = await navigator.serviceWorker.ready;
    let sub = await reg.pushManager.getSubscription();
    if (!sub) sub = await reg.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: urlB64ToUint8Array(VAPID_PUBLIC) });
    await putFile(`pocket-data/sub-${LS.device}.json`, sub.toJSON());
    m.className = 'msg ok'; m.textContent = '✅ Notifications activées.';
  } catch (e) { m.className = 'msg err'; m.textContent = 'Échec : ' + (e.message || e); }
}

// ── Router ──────────────────────────────────────────────────────────────────
function applyView(view) {
  const isDetail = view.startsWith('detail:');
  $('detail').classList.toggle('hidden', !isDetail);
  $('system').classList.toggle('hidden', view !== 'system');
  $('modes').classList.toggle('hidden', view !== 'modes');
  const isMain = !isDetail && view !== 'system' && view !== 'modes';
  for (const id of ['composer', 'history']) $(id).classList.toggle('hidden', !isMain);
  if (!isDetail) stopPoll();
  if (view === 'system') renderSystem();
  else if (view === 'modes') { renderModes(); $('mode-editor').classList.add('hidden'); }
  else if (isDetail) loadDetail(parseInt(view.split(':')[1], 10));
  else { detailNum = null; loadHistory(); }
  window.scrollTo(0, 0);
}
function navigate(view) { history.pushState({ view }, '', '#' + view); applyView(view); }

function escapeHtml(s) { return String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])); }
function timeago(iso) { const s = Math.max(0, (Date.now() - new Date(iso)) / 1000); if (s < 60) return 'à l\'instant'; if (s < 3600) return `il y a ${Math.floor(s / 60)} min`; if (s < 86400) return `il y a ${Math.floor(s / 3600)} h`; return `il y a ${Math.floor(s / 86400)} j`; }
async function testConn(silent) {
  const dot = $('conn-dot');
  try { const r = await gh(''); dot.className = 'dot ok'; try { const u = await (await fetch('https://api.github.com/user', { headers: { Authorization: `Bearer ${LS.pat}`, Accept: 'application/vnd.github+json' } })).json(); if (u && u.login) connectedLogin = u.login; } catch {} return r; }
  catch { dot.className = 'dot err'; if (!silent) throw new Error('non connecté'); return null; }
}

function setupMic() {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition; const mic = $('mic');
  $('mic-hint').classList.remove('hidden'); // l'astuce clavier reste toujours dispo
  if (!SR) { mic.style.display = 'none'; return; }
  const rec = new SR(); rec.lang = 'fr-FR'; rec.interimResults = true; rec.continuous = true; let base = '', live = false;
  rec.onresult = (e) => { let t = ''; for (let i = e.resultIndex; i < e.results.length; i++) t += e.results[i][0].transcript; $('demande').value = (base + ' ' + t).trim(); };
  rec.onerror = (e) => { live = false; mic.classList.remove('live'); if (e && e.error === 'not-allowed') { const m = $('composer-msg'); m.className = 'msg err'; m.textContent = 'Micro refusé. Utilise le micro du clavier iOS (astuce ci-dessus).'; } };
  rec.onend = () => { live = false; mic.classList.remove('live'); };
  mic.onclick = () => { if (live) { rec.stop(); return; } base = $('demande').value; try { rec.start(); live = true; mic.classList.add('live'); } catch { mic.classList.remove('live'); } };
}

// ── Thème ───────────────────────────────────────────────────────────────────
function applyTheme(t) {
  if (t === 'auto') document.documentElement.removeAttribute('data-theme');
  else document.documentElement.setAttribute('data-theme', t);
  for (const b of document.querySelectorAll('#theme-seg button')) b.classList.toggle('active', b.dataset.theme === t);
  const meta = document.querySelector('meta[name=theme-color]'); if (meta) meta.setAttribute('content', t === 'light' ? '#eef1f7' : '#0a0e16');
}

function init() {
  $('repo').value = LS.repo || 'GaspardCoche/agent-system'; $('pat').value = LS.pat;
  if (!LS.repo || !LS.pat) $('settings').classList.remove('hidden');
  $('brand-home').onclick = () => navigate('main');
  $('nav-settings').onclick = () => $('settings').classList.toggle('hidden');
  $('nav-system').onclick = () => navigate('system');
  $('nav-modes').onclick = () => navigate('modes');
  $('modes-back').onclick = () => history.back();
  $('mode-new').onclick = () => openModeEditor(null);
  $('mode-save').onclick = saveMode;
  $('mode-delete').onclick = deleteMode;
  $('mode-freq').onchange = (e) => { $('sched-extra').classList.toggle('hidden', e.target.value === 'none'); $('weekday-wrap').classList.toggle('hidden', e.target.value !== 'weekly'); };
  $('system-back').onclick = () => history.back();
  $('back').onclick = () => history.back();
  $('save-settings').onclick = async () => {
    LS.repo = $('repo').value.trim(); LS.pat = $('pat').value.trim();
    const m = $('settings-msg'); m.className = 'msg'; m.textContent = 'Test…';
    try { const r = await testConn(false); m.className = 'msg ok'; m.textContent = `Connecté à ${r.full_name}${connectedLogin ? ' · ' + connectedLogin : ''}`; loadHistory(); loadModes(); setTimeout(() => $('settings').classList.add('hidden'), 1400); }
    catch (e) { m.className = 'msg err'; m.textContent = friendlyError(e); }
  };
  $('enable-push').onclick = enablePush;
  // Thème
  applyTheme(LS.theme);
  for (const b of document.querySelectorAll('#theme-seg button')) b.onclick = () => { LS.theme = b.dataset.theme; applyTheme(b.dataset.theme); };
  // Import de fichiers
  $('attach-btn').onclick = () => $('file-input').click();
  $('file-input').onchange = (e) => { addFiles(e.target.files); e.target.value = ''; };
  $('write-allowed').onchange = (e) => $('conditions-wrap').classList.toggle('hidden', !e.target.checked);
  $('dispatch').onclick = dispatch;
  for (const ch of document.querySelectorAll('#chips .chip')) ch.onclick = () => { $('demande').value = ch.dataset.q; $('demande').focus(); };
  $('chat-send').onclick = chatSend;
  $('chat-input').addEventListener('input', (e) => { e.target.style.height = 'auto'; e.target.style.height = Math.min(e.target.scrollHeight, 140) + 'px'; });
  window.addEventListener('popstate', (e) => applyView((e.state && e.state.view) || 'main'));

  const vb = $('ver-badge'); if (vb) vb.textContent = APP_VERSION;

  setupMic();
  history.replaceState({ view: 'main' }, '', '#main');
  if (LS.repo && LS.pat) { testConn(true).then(() => { loadHistory(); loadModes(); }); } else { renderHistory(); }
  if ('serviceWorker' in navigator) {
    let refreshing = false;
    navigator.serviceWorker.addEventListener('controllerchange', () => { if (refreshing) return; refreshing = true; location.reload(); });
    navigator.serviceWorker.register('sw.js').catch(() => {});
  }
}
document.addEventListener('DOMContentLoaded', init);
