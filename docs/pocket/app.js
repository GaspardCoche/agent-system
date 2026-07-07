'use strict';

const VAPID_PUBLIC = 'BBrWaeSczwSz-wCywXN0OlFQ72UdUWRLLeAU9fjzD_8uw7saPxizhDNu6jTfe4xM4hbk_pV0GoAVxoTMD6BZpTw';
const APP_VERSION = 'v20';
const CTX_WINDOW = 200000;
const MODELS = { fable: 'Fable 5', opus: 'Opus 4.8', sonnet: 'Sonnet' };
const CATS = {
  'cat:crm': { label: 'CRM', color: '#c96442' },
  'cat:enrich': { label: 'Enrichissement', color: '#b8863a' },
  'cat:content': { label: 'Contenu', color: '#8a6d9c' },
  'cat:web': { label: 'Web', color: '#4f8a8b' },
  'cat:vault': { label: 'Vault', color: '#6d8a4f' },
  'cat:other': { label: 'Autre', color: '#8a7f70' },
};
const MCP_BASE = [
  { name: 'github', desc: 'Repo & issues', badge: 'base' },
  { name: 'hubspot', desc: 'CRM (lecture + écriture gatée)', badge: 'base' },
  { name: 'tavily', desc: 'Recherche web', badge: 'base' },
  { name: 'firecrawl', desc: 'Scraping web', badge: 'base' },
];

function estTokens(t) { return Math.round((t || '').length / 4); }
function decodeB64(c) { try { return decodeURIComponent(escape(atob((c || '').replace(/\s/g, '')))); } catch { return ''; } }
function b64(s) { return btoa(unescape(encodeURIComponent(s))); }

const LS = {
  get repo() { return localStorage.getItem('pocket_repo') || ''; }, set repo(v) { localStorage.setItem('pocket_repo', v); },
  get pat() { return localStorage.getItem('pocket_pat') || ''; }, set pat(v) { localStorage.setItem('pocket_pat', v); },
  get device() { let d = localStorage.getItem('pocket_device'); if (!d) { d = 'dev-' + Math.random().toString(36).slice(2, 10); localStorage.setItem('pocket_device', d); } return d; },
  get theme() { return localStorage.getItem('pocket_theme') || 'auto'; }, set theme(v) { localStorage.setItem('pocket_theme', v); },
  get model() { return localStorage.getItem('pocket_model') || 'opus'; }, set model(v) { localStorage.setItem('pocket_model', v); },
};
const $ = (id) => document.getElementById(id);
let pollTimer = null, mainTimer = null, allIssues = [], currentView = 'home';
let connectedLogin = '', detailNum = null, attachedFiles = [], selectedModel = LS.model;
let mcpServers = [], editingMcp = null;

// ── API GitHub ──────────────────────────────────────────────────────────────
async function gh(path, opts = {}) {
  if (!LS.pat || !LS.repo) throw new Error('Configure le repo et le token (Administration).');
  const res = await fetch(`https://api.github.com/repos/${LS.repo}${path}`, {
    ...opts, headers: { 'Authorization': `Bearer ${LS.pat}`, 'Accept': 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28', 'Content-Type': 'application/json', ...(opts.headers || {}) },
  });
  if (!res.ok) { let d = ''; try { d = (await res.json()).message || ''; } catch {} const e = new Error(`GitHub ${res.status} ${d}`.trim()); e.status = res.status; throw e; }
  return res.status === 204 ? null : res.json();
}
async function ghJSON(path) { try { const r = await gh('/contents/' + path); return JSON.parse(decodeB64(r.content)); } catch { return null; } }
async function putJSON(path, obj, msg) {
  let sha; try { sha = (await gh(`/contents/${path}`)).sha; } catch {}
  await gh(`/contents/${path}`, { method: 'PUT', body: JSON.stringify({ message: msg || `pocket: ${path}`, content: b64(JSON.stringify(obj, null, 2)), sha }) });
}
async function putRaw(path, content) {
  let sha; try { sha = (await gh(`/contents/${path}`)).sha; } catch {}
  await gh(`/contents/${path}`, { method: 'PUT', body: JSON.stringify({ message: `pocket: upload ${path}`, content, sha }) });
}
function friendlyError(e) {
  if (e.status === 403) return `${e.message}\n→ Token « classic » (scope repo) requis + accès écriture au repo.`;
  if (e.status === 401) return `${e.message}\n→ Token invalide/expiré.`;
  return e.message;
}
function escapeHtml(s) { return String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])); }
function timeago(iso) { const s = Math.max(0, (Date.now() - new Date(iso)) / 1000); if (s < 60) return "à l'instant"; if (s < 3600) return `il y a ${Math.floor(s / 60)} min`; if (s < 86400) return `il y a ${Math.floor(s / 3600)} h`; return `il y a ${Math.floor(s / 86400)} j`; }

// ── Fichiers ──────────────────────────────────────────────────────────────
function addFiles(fileList) {
  for (const f of fileList) {
    if (f.size > 4 * 1024 * 1024) { flash('composer-msg', `${f.name} dépasse 4 Mo — ignoré.`, 'err'); continue; }
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
    row.innerHTML = `<span class="fx"><svg class="ic"><use href="#i-clip"/></svg>${escapeHtml(f.name)} · ${kb} Ko</span><button title="Retirer">&times;</button>`;
    row.querySelector('button').onclick = () => { attachedFiles.splice(i, 1); renderFileList(); };
    el.appendChild(row);
  });
}
async function ensureLabels() {
  const labels = [['pocket', 'c96442'], ['approved', '5c8a44'], ['via:phone', 'b8863a'], ...Object.entries(CATS).map(([k, v]) => [k, v.color.replace('#', '')])];
  for (const [name, color] of labels) { try { await gh('/labels', { method: 'POST', body: JSON.stringify({ name, color }) }); } catch {} }
}

// ── Dispatch ────────────────────────────────────────────────────────────────
function buildBody(d, w, c) {
  return ['### Demande', '', d, '', "### Autoriser l'écriture ?", '', w ? 'oui' : 'non', '',
    "### Conditions d'écriture (si OUI)", '', c || '_No response_', '',
    '### Modèle', '', selectedModel, ''].join('\n');
}
async function dispatch() {
  const demande = $('demande').value.trim(); const msg = $('composer-msg');
  if (!demande) { flash('composer-msg', 'Écris une demande.', 'err'); return; }
  const w = $('write-allowed').checked, c = $('conditions').value.trim();
  flash('composer-msg', 'Envoi…');
  try {
    await ensureLabels();
    let attachNote = '';
    if (attachedFiles.length) {
      flash('composer-msg', 'Envoi des fichiers…');
      const paths = [];
      for (const f of attachedFiles) {
        const path = `pocket-data/uploads/${Date.now()}-${f.name.replace(/[^a-zA-Z0-9._-]/g, '_')}`;
        await putRaw(path, f.b64); paths.push(path);
      }
      attachNote = '\n\n### Fichiers joints\n' + paths.map((p) => '- `' + p + '` (lis-le avec `cat ' + p + '`)').join('\n');
    }
    const title = '[Pocket] ' + demande.slice(0, 60).replace(/\n/g, ' ');
    const issue = await gh('/issues', { method: 'POST', body: JSON.stringify({ title, body: buildBody(demande, w, c) + attachNote, labels: ['pocket', 'via:phone'] }) });
    $('demande').value = ''; $('conditions').value = ''; $('write-allowed').checked = false; $('conditions-wrap').classList.add('hidden');
    attachedFiles = []; renderFileList();
    flash('composer-msg', `Conversation #${issue.number} lancée.`, 'ok');
    navigate('detail:' + issue.number);
  } catch (e) { flash('composer-msg', friendlyError(e), 'err'); }
}
function flash(id, text, cls) { const m = $(id); if (!m) return; m.className = 'msg' + (cls ? ' ' + cls : ''); m.textContent = text; }

// ── Accueil : conversations récentes ─────────────────────────────────────────
function issueCat(i) { const l = (i.labels || []).map((x) => x.name || x).find((n) => n.startsWith('cat:')); return l || null; }
async function loadHistory() {
  try { allIssues = await gh('/issues?labels=pocket&state=all&per_page=40&sort=created&direction=desc'); } catch { allIssues = []; }
  renderMiniStats(); renderHistory();
}
async function renderMiniStats() {
  const today = new Date().toDateString();
  const todayN = allIssues.filter((i) => i.created_at && new Date(i.created_at).toDateString() === today).length;
  let running = 0;
  try { const r = await gh('/actions/workflows/pocket.yml/runs?status=in_progress&per_page=20'); running = (r.workflow_runs || []).length; } catch {}
  $('mini-stats').innerHTML =
    (running ? `<span class="live"><b>${running}</b> en cours</span>` : '') +
    `<span><b>${todayN}</b> aujourd'hui</span><span><b>${allIssues.length}</b> total</span>`;
}
function histBucket(iso) {
  if (!iso) return 'Plus tôt';
  const d = new Date(iso), now = new Date();
  const days = Math.floor((now.setHours(0, 0, 0, 0) - new Date(iso).setHours(0, 0, 0, 0)) / 86400000);
  if (days <= 0) return "Aujourd'hui";
  if (days === 1) return 'Hier';
  if (days < 7) return '7 derniers jours';
  if (days < 31) return 'Ce mois-ci';
  return 'Plus tôt';
}
function renderHistory() {
  const host = $('history-list'); host.innerHTML = '';
  if (!allIssues.length) { host.innerHTML = '<div class="thread-list"><div class="empty" style="text-align:center;color:var(--faint);padding:22px;font-size:13.5px">Aucune conversation. Lance ta première tâche ci-dessus.</div></div>'; return; }
  const order = ["Aujourd'hui", 'Hier', '7 derniers jours', 'Ce mois-ci', 'Plus tôt'];
  const groups = {};
  for (const i of allIssues) { const b = histBucket(i.created_at); (groups[b] = groups[b] || []).push(i); }
  for (const label of order) {
    const items = groups[label]; if (!items || !items.length) continue;
    const lab = document.createElement('div'); lab.className = 'hgroup-label'; lab.textContent = label; host.appendChild(lab);
    const ul = document.createElement('ul'); ul.className = 'thread-list';
    for (const i of items) {
      const cat = issueCat(i) || 'cat:other'; const cm = CATS[cat] || CATS['cat:other'];
      const li = document.createElement('li'); li.style.setProperty('--cat', cm.color);
      li.innerHTML = `<span class="t-wrap"><span class="t">${escapeHtml((i.title || '').replace('[Pocket] ', ''))}</span><span class="t-time">${i.created_at ? timeago(i.created_at) : ''} · ${cm.label}</span></span>
        <span class="meta-r"><span class="st ${i.state === 'open' ? 'open' : 'done'}"></span></span>`;
      li.onclick = () => navigate('detail:' + i.number);
      ul.appendChild(li);
    }
    host.appendChild(ul);
  }
}

// ── Conversation (détail + chat) ─────────────────────────────────────────────
const STEP_LABELS = { 'Set up job': 'Préparation', 'Install MCP servers': 'Installation des outils', 'Write task to disk': 'Lecture de la demande', 'Write MCP config with secrets': 'Connexion aux systèmes', 'Build claude_args': 'Configuration', 'Run Claude Pocket': 'Claude travaille', 'Check Claude result': 'Vérification', 'Notify (push)': 'Notification' };
function fmtDur(s, e) { if (!s) return '—'; const x = Math.max(0, ((e ? new Date(e) : new Date()) - new Date(s)) / 1000); return x < 60 ? `${Math.round(x)}s` : `${Math.floor(x / 60)}m${Math.round(x % 60)}s`; }
function cell(k, icon, v) { return `<div class="kcell"><div class="k"><svg class="ic"><use href="#${icon}"/></svg>${k}</div><div class="v sm">${v}</div></div>`; }
async function findRun(title) {
  try { const d = await gh('/actions/workflows/pocket.yml/runs?per_page=30'); const runs = (d.workflow_runs || []).filter((r) => r.display_title === title); runs.sort((a, b) => new Date(b.created_at) - new Date(a.created_at)); return runs[0] || null; } catch { return null; }
}
function isProgress(text) { const t = (text || '').trim(); return t.length < 170 && !/\n\n/.test(t) && /^(compris|je\s|j'|d'accord|ok\b)/i.test(t); }
async function renderRunStatus(run) {
  const bar = $('run-status');
  if (!run) { bar.className = 'status-pill idle'; bar.textContent = 'En attente'; return null; }
  if (run.status === 'queued') { bar.className = 'status-pill queued'; bar.textContent = 'En file'; return null; }
  if (run.status === 'completed') { bar.className = 'status-pill ' + (run.conclusion === 'success' ? 'ok' : (run.conclusion === 'cancelled' ? 'idle' : 'err')); bar.textContent = run.conclusion === 'success' ? 'Terminé' : (run.conclusion === 'cancelled' ? 'Annulé' : 'Échec'); return null; }
  let step = 'Claude travaille', jobs = null;
  try { jobs = await gh(`/actions/runs/${run.id}/jobs`); const job = (jobs.jobs || []).find((j) => j.status === 'in_progress') || (jobs.jobs || [])[0]; const cur = job && (job.steps || []).find((s) => s.status === 'in_progress'); if (cur) step = STEP_LABELS[cur.name] || cur.name; } catch {}
  bar.className = 'status-pill running'; bar.textContent = step; return jobs;
}
async function renderMonitor(run, jobs, usage) {
  const el = $('monitor'); const u = usage || { tokens: 0, pct: 0 };
  let h = '<div class="kgrid">';
  h += cell('Modèle', 'i-brain', MODELS[selectedModel] || 'Opus 4.8');
  h += cell('Statut', 'i-info', run ? (run.status === 'completed' ? (run.conclusion || 'fini') : run.status) : '—');
  h += cell('Durée', 'i-clock', run ? fmtDur(run.run_started_at, run.status === 'completed' ? run.updated_at : null) : '—');
  h += cell('Contexte', 'i-brain', u.pct.toFixed(1) + '% de 200K');
  h += '</div>';
  if (!jobs && run && run.status !== 'completed') { try { jobs = await gh(`/actions/runs/${run.id}/jobs`); } catch {} }
  const job = jobs && ((jobs.jobs || []).find((j) => j.name && j.name.includes('pocket')) || (jobs.jobs || [])[0]);
  if (job && job.steps) {
    h += '<div class="steps">';
    for (const s of job.steps.filter((s) => STEP_LABELS[s.name])) {
      const cls = s.status === 'in_progress' ? 'cur' : (s.conclusion === 'success' ? 'done' : '');
      const dur = (s.started_at && s.completed_at) ? Math.max(1, Math.round((new Date(s.completed_at) - new Date(s.started_at)) / 1000)) + 's' : '';
      h += `<div class="step ${cls}"><span class="sdot"></span>${STEP_LABELS[s.name]}${dur ? '<span style="margin-left:auto">' + dur + '</span>' : ''}</div>`;
    }
    h += '</div>';
  }
  el.innerHTML = h;
}
function loadDetail(number) {
  stopPoll(); detailNum = number;
  $('detail-title').textContent = `Conversation #${number}`;
  $('run-status').className = 'status-pill idle'; $('run-status').textContent = 'Chargement';
  $('monitor').innerHTML = ''; $('comments').innerHTML = ''; $('approve').classList.add('hidden'); $('detail-msg').textContent = '';
  const load = async () => {
    if (detailNum !== number) return;
    try {
      const [issue, comments] = await Promise.all([gh(`/issues/${number}`), gh(`/issues/${number}/comments?per_page=100`)]);
      const approved = (issue.labels || []).map((l) => l.name).includes('approved');
      const threadText = (issue.body || '') + comments.map((c) => c.body).join('\n');
      const usage = { tokens: estTokens(threadText), pct: Math.min(100, estTokens(threadText) / CTX_WINDOW * 100) };
      const run = await findRun(issue.title);
      const jobs = await renderRunStatus(run);
      await renderMonitor(run, jobs, usage);
      const prog = comments.filter((cm) => cm.user.type !== 'User' && isProgress(cm.body));
      const la = $('live-activity');
      if (run && run.status !== 'completed' && prog.length) { la.classList.remove('hidden'); la.textContent = prog[prog.length - 1].body.split('\n')[0].slice(0, 130); }
      else la.classList.add('hidden');
      const rl = $('run-link'); if (run && run.html_url) { rl.href = run.html_url; rl.classList.remove('hidden'); } else rl.classList.add('hidden');
      const c = $('comments'); c.innerHTML = '';
      const body = (issue.body || '').split('### Autoriser')[0].replace('### Demande', '').trim();
      if (body) c.appendChild(bubble(connectedLogin || 'toi', body, 'user', issue.created_at));
      for (const cm of comments) {
        const isUser = cm.user.type === 'User';
        c.appendChild(bubble(cm.user.login, cm.body, isUser ? 'user' : 'assistant', cm.created_at, !isUser && isProgress(cm.body)));
      }
      const needsApproval = comments.some((cm) => /aperçu|preview|approb|approuv/i.test(cm.body)) && !approved && issue.state === 'open';
      $('approve').classList.toggle('hidden', !needsApproval); $('approve').onclick = () => approve(number);
    } catch (e) { flash('detail-msg', friendlyError(e), 'err'); stopPoll(); }
  };
  load(); pollTimer = setInterval(load, 6000);
}

// ── Markdown ────────────────────────────────────────────────────────────────
function mdLink(u, text) {
  const clean = u.replace(/&amp;/g, '&');
  if (/\.csv(\?|$)/i.test(clean)) return `<a class="dl" href="${clean}" target="_blank" rel="noopener"><svg class="ic"><use href="#i-download"/></svg>Télécharger le CSV</a>`;
  return `<a href="${clean}" target="_blank" rel="noopener">${text || (clean.length > 46 ? clean.slice(0, 43) + '…' : clean)}</a>`;
}
function mdInline(s) {
  s = s.replace(/`([^`]+)`/g, '<code>$1</code>');
  s = s.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  s = s.replace(/(^|[^*\w])\*([^*\n]+)\*/g, '$1<em>$2</em>');
  s = s.replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, (m, t, u) => mdLink(u, t));
  try { s = s.replace(/(?<!["'>=\/])(https?:\/\/[^\s<]+)/g, (m, u) => mdLink(u, null)); } catch {}
  return s;
}
function splitRow(l) { return l.replace(/^\s*\|/, '').replace(/\|\s*$/, '').split('|').map((x) => x.trim()); }
function renderMarkdown(raw) {
  try {
    const lines = escapeHtml(raw).split('\n'); let html = '', i = 0;
    const blockStart = /^(#{1,6}\s|```|\s*[-*+]\s|\s*\d+\.\s|\s*>|\|)/;
    while (i < lines.length) {
      const line = lines[i];
      if (/^```/.test(line.trim())) { let code = ''; i++; while (i < lines.length && !/^```/.test(lines[i].trim())) { code += lines[i] + '\n'; i++; } i++; html += `<pre><code>${code.replace(/\n$/, '')}</code></pre>`; continue; }
      if (line.includes('|') && i + 1 < lines.length && lines[i + 1].includes('-') && /^[\s:|\-]+$/.test(lines[i + 1])) {
        const header = splitRow(line); i += 2; const rows = [];
        while (i < lines.length && lines[i].includes('|') && lines[i].trim() !== '') { rows.push(splitRow(lines[i])); i++; }
        html += '<table><thead><tr>' + header.map((h) => `<th>${mdInline(h)}</th>`).join('') + '</tr></thead><tbody>' + rows.map((r) => '<tr>' + r.map((c) => `<td>${mdInline(c)}</td>`).join('') + '</tr>').join('') + '</tbody></table>'; continue;
      }
      const h = line.match(/^(#{1,6})\s+(.*)$/); if (h) { const lvl = Math.min(6, h[1].length); html += `<h${lvl} class="md-h">${mdInline(h[2])}</h${lvl}>`; i++; continue; }
      if (/^\s*([-*_])\1\1+\s*$/.test(line)) { html += '<hr>'; i++; continue; }
      if (/^\s*>\s?/.test(line)) { let q = ''; while (i < lines.length && /^\s*>\s?/.test(lines[i])) { q += lines[i].replace(/^\s*>\s?/, '') + '\n'; i++; } html += `<blockquote>${mdInline(q.trim()).replace(/\n/g, '<br>')}</blockquote>`; continue; }
      if (/^\s*[-*+]\s+/.test(line) || /^\s*\d+\.\s+/.test(line)) {
        const ordered = /^\s*\d+\.\s+/.test(line); const items = [];
        while (i < lines.length && (/^\s*[-*+]\s+/.test(lines[i]) || /^\s*\d+\.\s+/.test(lines[i]))) { items.push(lines[i].replace(/^\s*(?:[-*+]|\d+\.)\s+/, '')); i++; }
        html += (ordered ? '<ol>' : '<ul>') + items.map((it) => `<li>${mdInline(it)}</li>`).join('') + (ordered ? '</ol>' : '</ul>'); continue;
      }
      if (line.trim() === '') { i++; continue; }
      let para = line; i++;
      while (i < lines.length && lines[i].trim() !== '' && !blockStart.test(lines[i]) && !/^\s*([-*_])\1\1+\s*$/.test(lines[i])) { para += '\n' + lines[i]; i++; }
      html += `<p>${mdInline(para).replace(/\n/g, '<br>')}</p>`;
    }
    return html;
  } catch { return escapeHtml(raw); }
}
function bubble(who, text, kind, ts, prog) {
  const div = document.createElement('div'); div.className = 'comment ' + kind + (prog ? ' progress' : '');
  div.innerHTML = `<div class="who">${escapeHtml(who)}${ts ? ' · ' + timeago(ts) : ''}</div><div class="md">${renderMarkdown(text)}</div>`; return div;
}
async function chatSend() {
  const ta = $('chat-input'), txt = ta.value.trim(); if (!txt || detailNum == null) return;
  ta.value = ''; ta.style.height = 'auto';
  $('comments').appendChild(bubble(connectedLogin || 'toi', txt, 'user', new Date().toISOString()));
  try { await gh(`/issues/${detailNum}/comments`, { method: 'POST', body: JSON.stringify({ body: txt }) }); setTimeout(() => { if (detailNum != null) loadDetail(detailNum); }, 900); }
  catch (e) { flash('detail-msg', friendlyError(e), 'err'); }
}
async function approve(number) {
  flash('detail-msg', 'Approbation…');
  try { await gh(`/issues/${number}/labels`, { method: 'POST', body: JSON.stringify({ labels: ['approved'] }) }); flash('detail-msg', 'Approuvé — Claude exécute.', 'ok'); $('approve').classList.add('hidden'); }
  catch (e) { flash('detail-msg', friendlyError(e), 'err'); }
}
function stopPoll() { if (pollTimer) { clearInterval(pollTimer); pollTimer = null; } }

// ── Administration : santé & coût ────────────────────────────────────────────
function ago(iso) { if (!iso) return '—'; const s = Math.max(0, (Date.now() - new Date(iso)) / 1000); if (s < 90) return "à l'instant"; if (s < 3600) return `il y a ${Math.round(s / 60)} min`; if (s < 86400) return `il y a ${Math.round(s / 3600)} h`; return `il y a ${Math.round(s / 86400)} j`; }
const SECRET_LABELS = { hubspot: 'HubSpot', fullenrich: 'FullEnrich', phantombuster: 'PhantomBuster', tavily: 'Tavily', firecrawl: 'Firecrawl', vault: 'Vault', google_sa: 'Google Sheets (SA)' };
async function renderHealthAndCost() {
  const h = await ghJSON('pocket-data/health.json'); const ht = $('health-token');
  if (!h) { ht.className = 'health-token'; ht.textContent = "Aucune donnée (le canari n'a pas encore tourné)."; $('health-grid').innerHTML = ''; }
  else {
    ht.className = 'health-token ' + (h.token_ok ? 'ok' : 'err');
    ht.innerHTML = h.token_ok
      ? `<svg class="ic"><use href="#i-check"/></svg> Auth Claude OK <small>${escapeHtml(h.model || '')} · vérifié ${ago(h.checked_at)}</small>`
      : `<svg class="ic"><use href="#i-alert"/></svg> Token Claude expiré — à renouveler <small>(vérifié ${ago(h.checked_at)})</small>`;
    const sec = h.secrets || {};
    $('health-grid').innerHTML = Object.keys(SECRET_LABELS).map((k) =>
      `<div class="kcell"><div class="k">${SECRET_LABELS[k]}</div><div class="v sm">${sec[k] ? '<span class="ok-dot">●</span> OK' : '<span class="err-dot">●</span> absent'}</div></div>`).join('');
  }
  const st = await ghJSON('pocket-data/status.json'); const runs = (st && st.runs) || [];
  const now = new Date(), day = now.toISOString().slice(0, 10), month = day.slice(0, 7);
  let cToday = 0, cMonth = 0, nToday = 0;
  for (const r of runs) { const ts = (r.ts || '').slice(0, 10); if (ts === day) { cToday += r.cost_usd || 0; nToday++; } if (ts.slice(0, 7) === month) cMonth += r.cost_usd || 0; }
  const fmt = (n) => '$' + (n || 0).toFixed(2);
  $('cost-box').innerHTML = runs.length
    ? `<div class="kgrid">${cell("Aujourd'hui", 'i-clock', fmt(cToday) + ` · ${nToday} run${nToday > 1 ? 's' : ''}`)}${cell('Ce mois', 'i-clock', fmt(cMonth))}${cell('Total suivi', 'i-info', runs.length + ' runs')}</div>`
    : '<p class="hint" style="margin:0">Aucun run enregistré pour l\'instant.</p>';
}

// ── Administration : éditeur MCP ─────────────────────────────────────────────
async function loadMCP() {
  const data = await ghJSON('pocket-config/mcp.json');
  mcpServers = Array.isArray(data) ? data : (data && data.servers) || [];
  renderMCP();
}
function renderMCP() {
  const ul = $('mcp-list'); ul.innerHTML = '';
  for (const b of MCP_BASE) {
    const li = document.createElement('li'); li.className = 'mcp-row';
    li.innerHTML = `<span class="mcp-ic"><svg class="ic"><use href="#i-plug"/></svg></span><span class="mcp-meta"><span class="mcp-n">${b.name}</span><span class="mcp-d">${b.desc}</span></span><span class="mcp-badge base">intégré</span>`;
    ul.appendChild(li);
  }
  for (const s of mcpServers) {
    const li = document.createElement('li'); li.className = 'mcp-row editable';
    const d = s.transport === 'http' ? (s.url || '') : ((s.command || '') + ' ' + (s.args || []).join(' '));
    li.innerHTML = `<span class="mcp-ic"><svg class="ic"><use href="#i-plug"/></svg></span><span class="mcp-meta"><span class="mcp-n">${escapeHtml(s.name)}</span><span class="mcp-d">${escapeHtml(d.trim())}</span></span><span class="mcp-badge ${s.enabled === false ? 'base' : 'on'}">${s.enabled === false ? 'off' : 'actif'}</span>`;
    li.onclick = () => openMcpEditor(s);
    ul.appendChild(li);
  }
}
function setTransport(t) {
  for (const b of document.querySelectorAll('#mcp-transport button')) b.classList.toggle('active', b.dataset.t === t);
  $('mcp-stdio').classList.toggle('hidden', t !== 'stdio');
  $('mcp-http').classList.toggle('hidden', t !== 'http');
}
function openMcpEditor(s) {
  editingMcp = s || null;
  $('mcp-editor').classList.remove('hidden');
  $('mcp-name').value = s ? s.name : '';
  setTransport(s && s.transport === 'http' ? 'http' : 'stdio');
  $('mcp-command').value = s ? (s.command || 'npx') : 'npx';
  $('mcp-args').value = s && s.args ? s.args.join('\n') : '';
  $('mcp-url').value = s ? (s.url || '') : '';
  $('mcp-headers').value = s && s.headers ? Object.entries(s.headers).map(([k, v]) => `${k}: ${v}`).join('\n') : '';
  $('mcp-env').value = s && s.env ? Object.entries(s.env).map(([k, v]) => `${k}=${v}`).join('\n') : '';
  $('mcp-tools').value = s && s.allowedTools ? s.allowedTools.join(', ') : '*';
  $('mcp-delete').classList.toggle('hidden', !s);
  $('mcp-msg').textContent = '';
  $('mcp-editor').scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}
function parsePairs(text, sep) {
  const o = {}; for (const l of (text || '').split('\n')) { const idx = l.indexOf(sep); if (idx > 0) o[l.slice(0, idx).trim()] = l.slice(idx + 1).trim(); } return o;
}
async function saveMcp() {
  const name = $('mcp-name').value.trim().replace(/[^a-zA-Z0-9_-]/g, '');
  if (!name) { flash('mcp-msg', 'Nom requis (sans espace).', 'err'); return; }
  const transport = document.querySelector('#mcp-transport button.active').dataset.t;
  const tools = $('mcp-tools').value.split(',').map((x) => x.trim()).filter(Boolean);
  const srv = { name, enabled: true, transport, allowedTools: tools.length ? tools : ['*'] };
  if (transport === 'http') { srv.url = $('mcp-url').value.trim(); const h = parsePairs($('mcp-headers').value, ':'); if (Object.keys(h).length) srv.headers = h; }
  else { srv.command = $('mcp-command').value.trim() || 'npx'; srv.args = $('mcp-args').value.split('\n').map((x) => x.trim()).filter(Boolean); }
  const env = parsePairs($('mcp-env').value, '='); if (Object.keys(env).length) srv.env = env;
  flash('mcp-msg', 'Enregistrement…');
  try {
    const idx = mcpServers.findIndex((x) => x.name === (editingMcp ? editingMcp.name : name));
    if (idx >= 0) mcpServers[idx] = srv; else mcpServers.push(srv);
    await putJSON('pocket-config/mcp.json', mcpServers, 'pocket: MCP ' + name);
    flash('mcp-msg', 'Serveur enregistré — actif à la prochaine tâche.', 'ok');
    $('mcp-editor').classList.add('hidden'); renderMCP();
  } catch (e) { flash('mcp-msg', friendlyError(e), 'err'); }
}
async function deleteMcp() {
  if (!editingMcp) return; flash('mcp-msg', 'Suppression…');
  try {
    mcpServers = mcpServers.filter((x) => x.name !== editingMcp.name);
    await putJSON('pocket-config/mcp.json', mcpServers, 'pocket: remove MCP ' + editingMcp.name);
    $('mcp-editor').classList.add('hidden'); renderMCP(); flash('mcp-msg', '', '');
  } catch (e) { flash('mcp-msg', friendlyError(e), 'err'); }
}

// ── Connaissances ────────────────────────────────────────────────────────────
let knowSha = {};
async function loadKnowledge() {
  const d = $('know-domain').value; $('know-msg').textContent = ''; $('know-text').value = 'Chargement…';
  try { const c = await gh('/contents/pocket-knowledge/' + d + '.md'); $('know-text').value = decodeB64(c.content); knowSha[d] = c.sha; }
  catch { $('know-text').value = ''; knowSha[d] = null; }
}
async function saveKnowledge() {
  const d = $('know-domain').value; flash('know-msg', 'Enregistrement…');
  try {
    const body = { message: 'knowledge: ' + d + ' (édition manuelle)', content: b64($('know-text').value) };
    if (knowSha[d]) body.sha = knowSha[d];
    const r = await gh('/contents/pocket-knowledge/' + d + '.md', { method: 'PUT', body: JSON.stringify(body) });
    knowSha[d] = r.content.sha; flash('know-msg', 'Enregistré.', 'ok');
  } catch (e) { flash('know-msg', friendlyError(e), 'err'); }
}

// ── Savoir (savoir accumulé + recherche vault) ───────────────────────────────
const DOMAIN_LABELS = { crm: 'CRM', enrich: 'Enrichissement', content: 'Contenu', web: 'Web', vault: 'Vault', other: 'Autre' };
async function renderSavoir() {
  const host = $('know-cards'); host.innerHTML = '<p class="savoir-empty">Chargement du savoir…</p>';
  let files = [];
  try { const items = await gh('/contents/pocket-knowledge'); files = (Array.isArray(items) ? items : []).filter((f) => f.name.endsWith('.md') && f.name.toLowerCase() !== 'readme.md'); } catch { files = []; }
  host.innerHTML = '';
  for (const f of files) {
    const domain = f.name.replace('.md', '');
    let content = ''; try { const c = await gh('/contents/' + f.path); content = decodeB64(c.content); } catch {}
    if (!content.trim()) continue;
    const cm = CATS['cat:' + domain] || CATS['cat:other'];
    const card = document.createElement('div'); card.className = 'know-card';
    card.innerHTML = `<div class="kc-head"><h3><span class="kc-dot" style="background:${cm.color}"></span>${DOMAIN_LABELS[domain] || domain}</h3><button class="kc-toggle">Déplier</button></div><div class="know-body md">${renderMarkdown(content)}</div>`;
    const tg = card.querySelector('.kc-toggle');
    tg.onclick = () => { const e = card.classList.toggle('expanded'); tg.textContent = e ? 'Replier' : 'Déplier'; };
    host.appendChild(card);
  }
  if (!host.children.length) host.innerHTML = "<p class=\"savoir-empty\">Aucun savoir accumulé pour l'instant. Pocket apprend au fil des tâches — et tu peux interroger le vault ci-dessus.</p>";
}
async function vaultSearch() {
  const q = $('vault-q').value.trim(); if (!q) return;
  flash('vault-msg', 'Lancement de la recherche…');
  try {
    await ensureLabels();
    const demande = `Cherche dans le vault EMAsphere : « ${q} ». Utilise pocket_vault.py (search puis read) sur les notes pertinentes, puis résume les points clés en citant les chemins des notes.`;
    const issue = await gh('/issues', { method: 'POST', body: JSON.stringify({ title: '[Pocket] Vault : ' + q.slice(0, 50), body: buildBody(demande, false, ''), labels: ['pocket', 'via:phone'] }) });
    $('vault-q').value = ''; flash('vault-msg', `Recherche #${issue.number} lancée.`, 'ok');
    navigate('detail:' + issue.number);
  } catch (e) { flash('vault-msg', friendlyError(e), 'err'); }
}

// ── Système (device) ─────────────────────────────────────────────────────────
async function renderSystem() {
  const d = [];
  d.push(cell('CPU (cœurs)', 'i-cpu', navigator.hardwareConcurrency || '—'));
  d.push(cell('Mémoire', 'i-cpu', navigator.deviceMemory ? navigator.deviceMemory + ' Go' : 'non exposé'));
  d.push(cell('Plateforme', 'i-info', escapeHtml(navigator.platform || '—')));
  d.push(cell('Réseau', 'i-info', (navigator.connection && navigator.connection.effectiveType) || 'non exposé'));
  let bat = 'non exposé'; if (navigator.getBattery) { try { const b = await navigator.getBattery(); bat = Math.round(b.level * 100) + '%' + (b.charging ? ' (charge)' : ''); } catch {} }
  d.push(cell('Batterie', 'i-info', bat));
  d.push(cell('Version', 'i-info', APP_VERSION));
  $('system-grid').innerHTML = d.join('');
}

// ── Push ─────────────────────────────────────────────────────────────────────
function urlB64ToUint8Array(s) { const p = '='.repeat((4 - s.length % 4) % 4); const b = (s + p).replace(/-/g, '+').replace(/_/g, '/'); const r = atob(b); const a = new Uint8Array(r.length); for (let i = 0; i < r.length; i++) a[i] = r.charCodeAt(i); return a; }
async function enablePush() {
  flash('push-msg', 'Autorisation…');
  if (!('serviceWorker' in navigator) || !('PushManager' in window)) { flash('push-msg', "Push indisponible. Ouvre l'app depuis l'écran d'accueil (iOS 16.4+).", 'err'); return; }
  try {
    if (await Notification.requestPermission() !== 'granted') { flash('push-msg', 'Permission refusée.', 'err'); return; }
    const reg = await navigator.serviceWorker.ready;
    let sub = await reg.pushManager.getSubscription();
    if (!sub) sub = await reg.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: urlB64ToUint8Array(VAPID_PUBLIC) });
    await putJSON(`pocket-data/sub-${LS.device}.json`, sub.toJSON(), 'pocket: sub ' + LS.device);
    flash('push-msg', 'Notifications activées.', 'ok');
  } catch (e) { flash('push-msg', 'Échec : ' + (e.message || e), 'err'); }
}

// ── Router ────────────────────────────────────────────────────────────────────
function setTab(view) {
  const map = { home: 'tab-home', savoir: 'tab-savoir', admin: 'tab-admin' };
  const active = view.startsWith('detail:') ? 'tab-home' : (map[view] || null);
  for (const id of ['tab-home', 'tab-savoir', 'tab-admin']) $(id).classList.toggle('active', id === active);
}
function applyView(view) {
  const isDetail = view.startsWith('detail:');
  const isHome = view === 'home' || view === 'main';
  currentView = isDetail ? 'detail' : view;
  $('home').classList.toggle('hidden', !isHome);
  $('detail').classList.toggle('hidden', !isDetail);
  $('savoir').classList.toggle('hidden', view !== 'savoir');
  $('admin').classList.toggle('hidden', view !== 'admin');
  setTab(view);
  if (!isDetail) stopPoll();
  stopMainPoll();
  if (isDetail) loadDetail(parseInt(view.split(':')[1], 10));
  else if (view === 'savoir') renderSavoir();
  else if (view === 'admin') { renderHealthAndCost(); loadMCP(); renderSystem(); $('mcp-editor').classList.add('hidden'); }
  else { detailNum = null; if (LS.repo && LS.pat) { loadHistory(); startMainPoll(); } }
  window.scrollTo(0, 0);
  document.body.classList.remove('scrolled'); showNav();
}
function startMainPoll() { stopMainPoll(); mainTimer = setInterval(() => { if (LS.repo && LS.pat && !document.hidden && currentView === 'home') loadHistory(); }, 20000); }
function stopMainPoll() { if (mainTimer) { clearInterval(mainTimer); mainTimer = null; } }
function navigate(view) { history.pushState({ view }, '', '#' + view); applyView(view); }

async function testConn(silent) {
  const dot = $('conn-dot');
  try { const r = await gh(''); dot.className = 'dot ok'; try { const u = await (await fetch('https://api.github.com/user', { headers: { Authorization: `Bearer ${LS.pat}`, Accept: 'application/vnd.github+json' } })).json(); if (u && u.login) connectedLogin = u.login; } catch {} return r; }
  catch { dot.className = 'dot err'; if (!silent) throw new Error('non connecté'); return null; }
}
// Câble un bouton micro (dictée fr-FR) sur un champ texte. Réutilisable :
// composer principal ET fil de conversation (chaque message, pas que le premier).
function wireMic(micId, fieldId, msgId, onInput) {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  const mic = $(micId), field = $(fieldId);
  if (!mic || !field) return;
  // Pas de reconnaissance vocale du navigateur (cas iOS Safari / PWA installée) :
  // on GARDE le micro visible sur CHAQUE champ (accueil ET fil de discussion) et
  // on ouvre le clavier — la dictée se fait alors via le 🎙️ du clavier iOS, dispo
  // sur n'importe quel champ texte. Plus jamais de micro masqué => visible partout.
  if (!SR) {
    mic.title = 'Dicter avec le micro du clavier';
    mic.onclick = () => { field.focus(); flash(msgId, 'Touche le 🎙️ de ton clavier pour dicter.', 'ok'); };
    return;
  }
  const rec = new SR(); rec.lang = 'fr-FR'; rec.interimResults = true; rec.continuous = true; let base = '', live = false;
  rec.onresult = (e) => { let t = ''; for (let i = e.resultIndex; i < e.results.length; i++) t += e.results[i][0].transcript; field.value = (base + ' ' + t).trim(); if (onInput) onInput(); };
  rec.onerror = (e) => { live = false; mic.classList.remove('live'); if (e && e.error === 'not-allowed') flash(msgId, 'Micro refusé. Utilise le micro du clavier iOS.', 'err'); };
  rec.onend = () => { live = false; mic.classList.remove('live'); };
  mic.onclick = () => { if (live) { rec.stop(); return; } base = field.value; try { rec.start(); live = true; mic.classList.add('live'); } catch { mic.classList.remove('live'); } };
}
// Auto-masquage du footer (tab bar) au scroll : on le replie quand on descend
// (lecture) et on le révèle dès qu'on remonte, en haut, ou en bas de page.
// Objectif : moins gêner l'affichage sans jamais rendre la nav inaccessible.
function showNav() { const t = document.querySelector('.tabbar'); if (t) t.classList.remove('tucked'); }
function setupAutoHideNav() {
  const bar = document.querySelector('.tabbar');
  if (!bar) return;
  let lastY = window.scrollY, ticking = false;
  const HIDE_AFTER = 90;   // ne se replie qu'après un vrai défilement vers le bas
  const DELTA = 6;         // seuil anti-tremblement
  const onScroll = () => {
    if (ticking) return; ticking = true;
    requestAnimationFrame(() => {
      const y = Math.max(0, window.scrollY);
      const doc = document.documentElement;
      const atTop = y < 40;
      const atBottom = (window.innerHeight + y) >= (doc.scrollHeight - 6);
      document.body.classList.toggle('scrolled', y > 4);
      if (y > lastY + DELTA) {           // on descend
        if (y > HIDE_AFTER && !atBottom) bar.classList.add('tucked');
      } else if (y < lastY - DELTA) {    // on remonte
        bar.classList.remove('tucked');
      }
      if (atTop || atBottom) bar.classList.remove('tucked');
      lastY = y; ticking = false;
    });
  };
  window.addEventListener('scroll', onScroll, { passive: true });
  // Toujours révéler la nav quand on tape (le champ pousse le contenu vers le bas)
  document.addEventListener('focusin', (e) => { if (e.target && e.target.matches('input, textarea')) showNav(); });
}
function setupMic() {
  wireMic('mic', 'demande', 'composer-msg');
  // Dictée dans le fil : la valeur est posée par programme, donc on relance
  // l'auto-agrandissement du textarea manuellement (l'événement input ne part pas).
  wireMic('chat-mic', 'chat-input', 'detail-msg', () => {
    const ci = $('chat-input'); ci.style.height = 'auto'; ci.style.height = Math.min(ci.scrollHeight, 130) + 'px';
  });
}
function applyTheme(t) {
  if (t === 'auto') document.documentElement.removeAttribute('data-theme');
  else document.documentElement.setAttribute('data-theme', t);
  for (const b of document.querySelectorAll('#theme-seg button')) b.classList.toggle('active', b.dataset.theme === t);
  const dark = t === 'dark' || (t === 'auto' && window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches);
  const meta = document.querySelector('meta[name=theme-color]'); if (meta) meta.setAttribute('content', dark ? '#101317' : '#eef2ef');
}
function cycleTheme() { const order = ['auto', 'light', 'dark']; const next = order[(order.indexOf(LS.theme) + 1) % 3]; LS.theme = next; applyTheme(next); flash('composer-msg', 'Thème : ' + next, ''); setTimeout(() => flash('composer-msg', '', ''), 1200); }
function setModel(m) { selectedModel = m; LS.model = m; for (const b of document.querySelectorAll('#model-seg button')) b.classList.toggle('active', b.dataset.model === m); }

function init() {
  $('repo').value = LS.repo || 'GaspardCoche/agent-system'; $('pat').value = LS.pat;
  // greeting
  const hr = new Date().getHours();
  $('greet').textContent = hr < 6 ? 'Bonne nuit.' : hr < 18 ? 'Bonjour.' : 'Bonsoir.';
  // nav
  $('brand-home').onclick = () => navigate('home');
  $('nav-new').onclick = () => { navigate('home'); $('demande').focus(); };
  $('nav-theme').onclick = cycleTheme;
  $('tab-home').onclick = () => navigate('home');
  $('tab-savoir').onclick = () => navigate('savoir');
  $('tab-admin').onclick = () => navigate('admin');
  $('back').onclick = () => history.back();
  $('admin-back').onclick = () => history.back();
  $('vault-go').onclick = vaultSearch;
  $('vault-q').addEventListener('keydown', (e) => { if (e.key === 'Enter') vaultSearch(); });
  // model picker
  setModel(LS.model);
  for (const b of document.querySelectorAll('#model-seg button')) b.onclick = () => setModel(b.dataset.model);
  // composer
  $('dispatch').onclick = dispatch;
  $('write-allowed').onchange = (e) => $('conditions-wrap').classList.toggle('hidden', !e.target.checked);
  for (const ch of document.querySelectorAll('#quick-chips .chip')) ch.onclick = () => { $('demande').value = ch.dataset.q; $('demande').focus(); };
  // files + drag/drop
  $('attach-btn').onclick = () => $('file-input').click();
  $('file-input').onchange = (e) => { addFiles(e.target.files); e.target.value = ''; };
  const dz = $('dropzone');
  ['dragover', 'dragenter'].forEach((ev) => dz.addEventListener(ev, (e) => { e.preventDefault(); dz.classList.add('drag'); }));
  ['dragleave', 'drop'].forEach((ev) => dz.addEventListener(ev, (e) => { e.preventDefault(); dz.classList.remove('drag'); }));
  dz.addEventListener('drop', (e) => { if (e.dataTransfer && e.dataTransfer.files) addFiles(e.dataTransfer.files); });
  // detail chat
  $('chat-send').onclick = chatSend;
  $('chat-input').addEventListener('input', (e) => { e.target.style.height = 'auto'; e.target.style.height = Math.min(e.target.scrollHeight, 130) + 'px'; });
  // admin: settings
  $('save-settings').onclick = async () => {
    LS.repo = $('repo').value.trim(); LS.pat = $('pat').value.trim();
    flash('settings-msg', 'Test…');
    try { const r = await testConn(false); flash('settings-msg', `Connecté à ${r.full_name}${connectedLogin ? ' · ' + connectedLogin : ''}`, 'ok'); loadHistory(); renderHealthAndCost(); loadMCP(); }
    catch (e) { flash('settings-msg', friendlyError(e), 'err'); }
  };
  $('health-refresh').onclick = async () => {
    flash('health-msg', 'Test lancé…');
    try { await gh('/actions/workflows/pocket-health.yml/dispatches', { method: 'POST', body: JSON.stringify({ ref: 'main' }) }); flash('health-msg', 'Canari lancé — résultat dans ~40 s.', 'ok'); setTimeout(() => { renderHealthAndCost(); flash('health-msg', '', ''); }, 45000); }
    catch (e) { flash('health-msg', friendlyError(e), 'err'); }
  };
  // admin: MCP editor
  $('mcp-new').onclick = () => openMcpEditor(null);
  for (const b of document.querySelectorAll('#mcp-transport button')) b.onclick = () => setTransport(b.dataset.t);
  $('mcp-save').onclick = saveMcp;
  $('mcp-delete').onclick = deleteMcp;
  // admin: knowledge
  $('know-domain').onchange = loadKnowledge;
  $('know-save').onclick = saveKnowledge;
  // admin: theme + push
  applyTheme(LS.theme);
  for (const b of document.querySelectorAll('#theme-seg button')) b.onclick = () => { LS.theme = b.dataset.theme; applyTheme(b.dataset.theme); };
  $('enable-push').onclick = enablePush;
  // misc
  document.addEventListener('visibilitychange', () => { if (!document.hidden && currentView === 'home' && LS.repo && LS.pat) loadHistory(); });
  window.addEventListener('popstate', (e) => applyView((e.state && e.state.view) || 'home'));
  const vb = $('ver-badge'); if (vb) vb.textContent = APP_VERSION;
  setupMic();
  setupAutoHideNav();
  history.replaceState({ view: 'home' }, '', '#home');
  if (LS.repo && LS.pat) { testConn(true).then(() => { loadHistory(); startMainPoll(); }); } else { renderHistory(); navigate('admin'); }
  if ('serviceWorker' in navigator) {
    let refreshing = false;
    navigator.serviceWorker.addEventListener('controllerchange', () => { if (refreshing) return; refreshing = true; location.reload(); });
    navigator.serviceWorker.register('sw.js').catch(() => {});
  }
}
document.addEventListener('DOMContentLoaded', init);
