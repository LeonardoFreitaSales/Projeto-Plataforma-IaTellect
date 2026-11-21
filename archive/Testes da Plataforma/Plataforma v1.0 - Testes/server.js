const http = require('node:http');
const fs = require('node:fs');
const path = require('node:path');
const { randomUUID } = require('node:crypto');

const ROOT = __dirname;
const DATA_DIR = path.join(ROOT, 'data');
const DB_FILE = path.join(DATA_DIR, 'database.json');
const PORT = Number(process.env.PORT || 3001);
const STATUSES = new Set(['proibido', 'restricao', 'permitido']);
const TYPES = new Set(['prova', 'trabalho', 'atividade', 'pesquisa', 'outro']);

function loadDb() {
  fs.mkdirSync(DATA_DIR, { recursive: true });
  if (!fs.existsSync(DB_FILE)) {
    const initial = { disciplines: [], policies: [], announcements: [], history: [] };
    fs.writeFileSync(DB_FILE, JSON.stringify(initial, null, 2));
    return initial;
  }
  try {
    const db = JSON.parse(fs.readFileSync(DB_FILE, 'utf8'));
    return { disciplines: [], policies: [], announcements: [], history: [], ...db };
  } catch {
    throw new Error(`Não foi possível ler ${DB_FILE}. Corrija o JSON antes de iniciar o servidor.`);
  }
}
let db = loadDb();

function persist() {
  const temp = `${DB_FILE}.tmp`;
  fs.writeFileSync(temp, JSON.stringify(db, null, 2));
  fs.renameSync(temp, DB_FILE);
}
function send(res, status, body) {
  res.writeHead(status, { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store' });
  res.end(JSON.stringify(body));
}
function fail(res, status, message) { send(res, status, { error: message }); }
function bodyJson(req) {
  return new Promise((resolve, reject) => {
    let raw = '';
    req.on('data', chunk => { raw += chunk; if (raw.length > 1_000_000) reject(new Error('Corpo da requisição excede 1 MB.')); });
    req.on('end', () => {
      if (!raw) return resolve({});
      try { resolve(JSON.parse(raw)); } catch { reject(new Error('JSON inválido.')); }
    });
    req.on('error', reject);
  });
}
function text(value, name, max = 5000, required = true) {
  if (value == null && !required) return '';
  if (typeof value !== 'string') throw new Error(`${name} deve ser texto.`);
  const out = value.trim();
  if (required && !out) throw new Error(`${name} é obrigatório.`);
  if (out.length > max) throw new Error(`${name} excede ${max} caracteres.`);
  return out;
}
function addHistory(action, entity, entityId, summary) {
  db.history.unshift({ id: randomUUID(), action, entity, entityId, summary, createdAt: new Date().toISOString() });
  db.history = db.history.slice(0, 500);
}
function parsePolicy(input, existing = {}) {
  const disciplineId = input.disciplineId ?? existing.disciplineId;
  if (!db.disciplines.some(item => item.id === disciplineId)) throw new Error('Disciplina não encontrada.');
  const status = input.status ?? existing.status;
  if (!STATUSES.has(status)) throw new Error('status deve ser proibido, restricao ou permitido.');
  const activityType = input.activityType ?? existing.activityType ?? 'outro';
  if (!TYPES.has(activityType)) throw new Error('Tipo de atividade inválido.');
  return {
    disciplineId,
    activityType,
    activityName: text(input.activityName ?? existing.activityName, 'activityName', 180),
    status,
    conditions: text(input.conditions ?? existing.conditions ?? '', 'conditions', 3000, false),
    details: text(input.details ?? existing.details ?? '', 'details', 5000, false),
    source: text(input.source ?? existing.source ?? '', 'source', 500, false),
    updatedAt: new Date().toISOString()
  };
}
function policyView(policy) {
  const discipline = db.disciplines.find(item => item.id === policy.disciplineId);
  return { ...policy, disciplineName: discipline?.name ?? null };
}
function dashboard() {
  const counts = { proibido: 0, restricao: 0, permitido: 0 };
  for (const p of db.policies) counts[p.status]++;
  return {
    disciplines: db.disciplines.length,
    policies: db.policies.length,
    changedSinceLastVisit: 0,
    distribution: counts,
    announcements: db.announcements.filter(a => a.active).slice(0, 5)
  };
}
function routeId(url, base) {
  const rest = url.pathname.slice(base.length);
  if (!rest || rest === '/') return null;
  return decodeURIComponent(rest.replace(/^\//, ''));
}

async function api(req, res, url) {
  const method = req.method;
  const p = url.pathname;
  if (method === 'GET' && p === '/api/health') return send(res, 200, { status: 'ok', time: new Date().toISOString() });
  if (method === 'GET' && p === '/api/dashboard') return send(res, 200, dashboard());

  if (p === '/api/disciplines' && method === 'GET') return send(res, 200, db.disciplines);
  if (p === '/api/disciplines' && method === 'POST') {
    const input = await bodyJson(req);
    const name = text(input.name, 'name', 180);
    if (db.disciplines.some(d => d.name.toLocaleLowerCase('pt-BR') === name.toLocaleLowerCase('pt-BR'))) return fail(res, 409, 'Já existe uma disciplina com esse nome.');
    const item = { id: randomUUID(), name, code: text(input.code ?? '', 'code', 40, false), instructor: text(input.instructor ?? '', 'instructor', 180, false), createdAt: new Date().toISOString(), updatedAt: new Date().toISOString() };
    db.disciplines.push(item); addHistory('created', 'discipline', item.id, `Disciplina criada: ${item.name}`); persist(); return send(res, 201, item);
  }
  if (p.startsWith('/api/disciplines/')) {
    const id = routeId(url, '/api/disciplines'); const item = db.disciplines.find(d => d.id === id);
    if (!item) return fail(res, 404, 'Disciplina não encontrada.');
    if (method === 'GET') return send(res, 200, { ...item, policies: db.policies.filter(x => x.disciplineId === id).map(policyView) });
    if (method === 'PUT' || method === 'PATCH') {
      const input = await bodyJson(req); const name = text(input.name ?? item.name, 'name', 180);
      if (db.disciplines.some(d => d.id !== id && d.name.toLocaleLowerCase('pt-BR') === name.toLocaleLowerCase('pt-BR'))) return fail(res, 409, 'Já existe uma disciplina com esse nome.');
      Object.assign(item, { name, code: text(input.code ?? item.code, 'code', 40, false), instructor: text(input.instructor ?? item.instructor, 'instructor', 180, false), updatedAt: new Date().toISOString() });
      addHistory('updated', 'discipline', id, `Disciplina atualizada: ${item.name}`); persist(); return send(res, 200, item);
    }
    if (method === 'DELETE') {
      if (db.policies.some(x => x.disciplineId === id)) return fail(res, 409, 'Remova ou mova as políticas desta disciplina antes de excluí-la.');
      db.disciplines = db.disciplines.filter(d => d.id !== id); addHistory('deleted', 'discipline', id, `Disciplina removida: ${item.name}`); persist(); return send(res, 200, { deleted: true, id });
    }
  }

  if (p === '/api/policies' && method === 'GET') {
    let items = db.policies;
    const disciplineId = url.searchParams.get('disciplineId'); const status = url.searchParams.get('status'); const q = (url.searchParams.get('q') || '').toLocaleLowerCase('pt-BR');
    if (disciplineId) items = items.filter(x => x.disciplineId === disciplineId);
    if (status) items = items.filter(x => x.status === status);
    if (q) items = items.filter(x => `${x.activityName} ${x.details} ${x.conditions} ${policyView(x).disciplineName}`.toLocaleLowerCase('pt-BR').includes(q));
    return send(res, 200, items.map(policyView));
  }
  if (p === '/api/policies' && method === 'POST') {
    const input = await bodyJson(req); const item = { id: randomUUID(), ...parsePolicy(input), createdAt: new Date().toISOString() };
    db.policies.push(item); addHistory('created', 'policy', item.id, `Política criada: ${item.activityName}`); persist(); return send(res, 201, policyView(item));
  }
  if (p.startsWith('/api/policies/')) {
    const id = routeId(url, '/api/policies'); const item = db.policies.find(x => x.id === id);
    if (!item) return fail(res, 404, 'Política não encontrada.');
    if (method === 'GET') return send(res, 200, policyView(item));
    if (method === 'PUT' || method === 'PATCH') {
      const input = await bodyJson(req); Object.assign(item, parsePolicy(input, item)); addHistory('updated', 'policy', id, `Política atualizada: ${item.activityName}`); persist(); return send(res, 200, policyView(item));
    }
    if (method === 'DELETE') {
      db.policies = db.policies.filter(x => x.id !== id); addHistory('deleted', 'policy', id, `Política removida: ${item.activityName}`); persist(); return send(res, 200, { deleted: true, id });
    }
  }

  if (p === '/api/announcements' && method === 'GET') return send(res, 200, db.announcements.filter(a => a.active || url.searchParams.get('all') === 'true'));
  if (p === '/api/announcements' && method === 'POST') {
    const input = await bodyJson(req); const item = { id: randomUUID(), title: text(input.title, 'title', 180), message: text(input.message, 'message', 3000), active: input.active !== false, createdAt: new Date().toISOString(), updatedAt: new Date().toISOString() };
    db.announcements.unshift(item); addHistory('created', 'announcement', item.id, `Comunicado criado: ${item.title}`); persist(); return send(res, 201, item);
  }
  if (p.startsWith('/api/announcements/')) {
    const id = routeId(url, '/api/announcements'); const item = db.announcements.find(x => x.id === id);
    if (!item) return fail(res, 404, 'Comunicado não encontrado.');
    if (method === 'PUT' || method === 'PATCH') {
      const input = await bodyJson(req); Object.assign(item, { title: text(input.title ?? item.title, 'title', 180), message: text(input.message ?? item.message, 'message', 3000), active: input.active ?? item.active, updatedAt: new Date().toISOString() });
      addHistory('updated', 'announcement', id, `Comunicado atualizado: ${item.title}`); persist(); return send(res, 200, item);
    }
    if (method === 'DELETE') { db.announcements = db.announcements.filter(x => x.id !== id); addHistory('deleted', 'announcement', id, `Comunicado removido: ${item.title}`); persist(); return send(res, 200, { deleted: true, id }); }
  }

  if (p === '/api/history' && method === 'GET') {
    const limit = Math.min(100, Math.max(1, Number(url.searchParams.get('limit') || 50)));
    return send(res, 200, db.history.slice(0, limit));
  }
  if (p === '/api/ai-check' && method === 'POST') {
    const input = await bodyJson(req); const disciplineId = text(input.disciplineId, 'disciplineId', 100);
    if (!db.disciplines.some(d => d.id === disciplineId)) return fail(res, 404, 'Disciplina não encontrada.');
    const activityType = text(input.activityType, 'activityType', 40);
    if (!TYPES.has(activityType)) return fail(res, 400, 'Tipo de atividade inválido.');
    const matches = db.policies.filter(x => x.disciplineId === disciplineId && (x.activityType === activityType || x.activityType === 'outro')).map(policyView);
    return send(res, 200, { disciplineId, activityType, policies: matches, decision: matches.length ? (matches.some(x => x.status === 'proibido') ? 'proibido' : matches.some(x => x.status === 'restricao') ? 'restricao' : 'permitido') : 'sem_politica', message: matches.length ? null : 'Nenhuma política cadastrada para esta atividade.' });
  }

  if (p.startsWith('/api/')) return fail(res, 404, 'Rota de API não encontrada.');
  return false;
}

const mime = { '.html': 'text/html; charset=utf-8', '.css': 'text/css; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.json': 'application/json; charset=utf-8', '.svg': 'image/svg+xml' };
const server = http.createServer(async (req, res) => {
  try {
    const url = new URL(req.url, `http://${req.headers.host || 'localhost'}`);
    if (url.pathname.startsWith('/api/')) {
      const handled = await api(req, res, url);
      if (handled === false) return fail(res, 404, 'Rota de API não encontrada.');
      return;
    }
    if (req.method !== 'GET' && req.method !== 'HEAD') return fail(res, 405, 'Método não permitido.');
    const requested = decodeURIComponent(url.pathname === '/' ? '/index.html' : url.pathname);
    const file = path.resolve(ROOT, `.${requested}`);
    if (!file.startsWith(ROOT + path.sep) && file !== path.join(ROOT, 'index.html')) return fail(res, 403, 'Acesso negado.');
    if (!fs.existsSync(file) || !fs.statSync(file).isFile()) return fail(res, 404, 'Arquivo não encontrado.');
    res.writeHead(200, { 'Content-Type': mime[path.extname(file)] || 'application/octet-stream', 'Cache-Control': 'no-cache' });
    if (req.method === 'HEAD') return res.end();
    fs.createReadStream(file).pipe(res);
  } catch (error) {
    const status = /inválido|obrigatório|excede|deve ser|Tipo de atividade/i.test(error.message) ? 400 : 500;
    if (status === 500) console.error(error);
    if (!res.headersSent) fail(res, status, status === 500 ? 'Erro interno do servidor.' : error.message);
  }
});
server.listen(PORT, () => console.log(`Painel disponível em http://localhost:${PORT}`));
