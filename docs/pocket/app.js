'use strict';

const VAPID_PUBLIC = 'BBrWaeSczwSz-wCywXN0OlFQ72UdUWRLLeAU9fjzD_8uw7saPxizhDNu6jTfe4xM4hbk_pV0GoAVxoTMD6BZpTw';
const MODEL = 'claude-opus-4-8';
const APP_VERSION = 'v7';
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
    const issue = await gh('/issues', { method: 'POST', body: JSON.stringify({ title, body: buildBody(demande, w, c) + attachNote, labels: ['pocket'] }) });
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
    li.innerHTML = `<span class="t">#${i.number} ${escapeHtml((i.title || '').replace('[Pocket] ', ''))}</span>
      <span class="meta-r"><span class="cat-badge" style="background:${cm.color}">${cm.label}</span>
      <span class="badge ${i.state === 'open' ? 'open' : 'pending'}">${i.state === 'open' ? '●' : '✓'}</span></span>`;
    li.onclick = () => navigate('detail:' + i.number);
    ul.appendChild(li);
  }
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
async function renderMonitor(run, jobs) {
  const el = $('monitor');
  let h = '<div class="kgrid">';
  h += cell('Modèle', 'i-brain', MODEL) + cell('Agent', 'i-robot', 'Claude Pocket');
  h += cell('Statut', 'i-info', run ? (run.status === 'completed' ? (run.conclusion || 'fini') : run.status) : '—');
  h += cell('Durée', 'i-clock', run ? fmtDur(run.run_started_at, run.status === 'completed' ? run.updated_at : null) : '—');
  h += `<div class="kcell wide"><div class="k"><svg class="ic"><use href="#i-brain"/></svg>Contexte</div><div class="v sm">~200K tokens · session neuve par tâche (le fil de chat sert de mémoire)</div></div></div>`;
  if (!jobs && run && run.status !== 'completed') { try { jobs = await gh(`/actions/runs/${run.id}/jobs`); } catch {} }
  const job = jobs && ((jobs.jobs || []).find((j) => j.name && j.name.includes('pocket')) || (jobs.jobs || [])[0]);
  if (job && job.steps) { h += '<div class="steps">'; for (const s of job.steps.filter((s) => STEP_LABELS[s.name])) { const cls = s.status === 'in_progress' ? 'cur' : (s.conclusion === 'success' ? 'done' : ''); h += `<div class="step ${cls}"><span class="sdot"></span>${STEP_LABELS[s.name]}</div>`; } h += '</div>'; }
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
      const run = await findRun(issue.title);
      const jobs = await renderRunStatus(run);
      await renderMonitor(run, jobs);
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
  for (const id of ['composer', 'history']) $(id).classList.toggle('hidden', isDetail || view === 'system');
  if (!isDetail) stopPoll();
  if (view === 'system') renderSystem();
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
  $('nav-settings').onclick = () => $('settings').classList.toggle('hidden');
  $('nav-system').onclick = () => navigate('system');
  $('system-back').onclick = () => history.back();
  $('back').onclick = () => history.back();
  $('save-settings').onclick = async () => {
    LS.repo = $('repo').value.trim(); LS.pat = $('pat').value.trim();
    const m = $('settings-msg'); m.className = 'msg'; m.textContent = 'Test…';
    try { const r = await testConn(false); m.className = 'msg ok'; m.textContent = `Connecté à ${r.full_name}${connectedLogin ? ' · ' + connectedLogin : ''}`; loadHistory(); setTimeout(() => $('settings').classList.add('hidden'), 1400); }
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
  if (LS.repo && LS.pat) { testConn(true).then(loadHistory); } else { renderHistory(); }
  if ('serviceWorker' in navigator) {
    let refreshing = false;
    navigator.serviceWorker.addEventListener('controllerchange', () => { if (refreshing) return; refreshing = true; location.reload(); });
    navigator.serviceWorker.register('sw.js').catch(() => {});
  }
}
document.addEventListener('DOMContentLoaded', init);
