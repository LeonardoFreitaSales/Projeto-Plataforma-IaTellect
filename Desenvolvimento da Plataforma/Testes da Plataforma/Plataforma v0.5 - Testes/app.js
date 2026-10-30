const KEY = 'plataforma-v05', J = { 'Content-Type': 'application/json' };
const TIPOS = ['prova', 'trabalho', 'atividade', 'pesquisa', 'outro'];
const NOME = { proibido: 'Proibido', restricao: 'Com restrição', permitido: 'Permitido' };
const PRIO = { info: 'Informação', aviso: 'Aviso', urgente: 'Urgente' };
const vazio = () => ({ disciplinas: [], politicas: [], comunicados: [] });
let db = vazio(), remoto = false;

const $ = s => document.querySelector(s);
const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const nomeDisc = i => (db.disciplinas.find(d => d.id === i) || {}).nome || '—';

// Usa a API Python se ela existir; caso contrário, guarda no navegador.
async function carregar() {
  try {
    const r = await fetch('/api/dados'), d = await r.json();
    if (!r.ok || !d.politicas) throw 0;
    db = d; remoto = true;
  } catch (e) {
    remoto = false;
    try { db = { ...vazio(), ...JSON.parse(localStorage.getItem(KEY)) }; } catch (e2) { db = vazio(); }
  }
  render();
}

async function enviar(metodo, col, id, corpo) {
  if (remoto) {
    await fetch(`/api/${col}${id ? '/' + id : ''}`, { method: metodo, headers: J, body: corpo && JSON.stringify(corpo) });
    return carregar();
  }
  const lista = db[col];
  if (metodo === 'POST') lista.push({ id: Date.now().toString(36) + Math.random().toString(36).slice(2, 5), criado: Date.now(), ...corpo });
  if (metodo === 'PATCH') Object.assign(lista.find(x => x.id === id) || {}, corpo);
  if (metodo === 'DELETE') {
    db[col] = lista.filter(x => x.id !== id);
    if (col === 'disciplinas') db.politicas = db.politicas.filter(p => p.disc !== id);
  }
  try { localStorage.setItem(KEY, JSON.stringify(db)); } catch (e) {}
  render();
}

function preencher(el, html) {
  const atual = el.value;
  el.innerHTML = html;
  if ([...el.options].some(o => o.value === atual)) el.value = atual;
}

function render() {
  const { disciplinas: D, politicas: P, comunicados: C } = db;
  $('#n-disc').textContent = D.length;
  $('#n-pol').textContent = P.length;
  $('#n-com').textContent = C.length;
  Object.keys(NOME).forEach(k => {
    const n = P.filter(p => p.status === k).length;
    $('#n-' + k).textContent = n;
    $('#b-' + k).style.width = P.length ? (n / P.length * 100) + '%' : '0';
  });

  const opcoes = D.map(d => `<option value="${d.id}">${esc(d.nome)}</option>`).join('') || '<option value="">Cadastre uma disciplina</option>';
  const tipos = TIPOS.map(t => `<option value="${t}">${t[0].toUpperCase() + t.slice(1)}</option>`).join('');
  ['#c-disc', '#p-disc'].forEach(s => preencher($(s), opcoes));
  ['#c-tipo', '#p-tipo'].forEach(s => preencher($(s), tipos));

  const ordem = [...C].sort((a, b) => (!!b.fixado - !!a.fixado) || b.criado - a.criado);
  $('#lista-comunicados').innerHTML = ordem.length ? ordem.map(c => `
    <article class="com ${esc(c.prioridade)}">
      <b>${c.fixado ? '📌 ' : ''}${esc(c.titulo)}</b>
      <small class="${esc(c.prioridade)}"> · ${PRIO[c.prioridade] || 'Informação'} · ${new Date(c.criado).toLocaleDateString('pt-BR')}</small>
      <p>${esc(c.mensagem)}</p>
      <div class="acoes"><button data-fixar="${c.id}">${c.fixado ? 'Desafixar' : 'Fixar'}</button><button data-del-com="${c.id}">Remover</button></div>
    </article>`).join('') : '<p class="empty">Nenhum comunicado no momento.</p>';

  $('#chips').innerHTML = D.length
    ? D.map(d => `<span class="chip">${esc(d.nome)}<button class="x" data-del-disc="${d.id}" aria-label="Remover ${esc(d.nome)}">×</button></span>`).join('')
    : '<p class="empty">Nenhuma disciplina ainda.</p>';

  const f = $('#filtro').value, q = $('#busca').value.toLocaleLowerCase('pt-BR');
  const lista = P.filter(p => (!f || p.status === f) && `${p.nome} ${nomeDisc(p.disc)}`.toLocaleLowerCase('pt-BR').includes(q));
  $('#lista').innerHTML = lista.length ? lista.map(p => `
    <div class="item"><div><b>${esc(nomeDisc(p.disc))}</b> · ${esc(p.nome)}
      <small>${esc(p.tipo)}${p.cond ? ' · ' + esc(p.cond) : ''}</small>
      <span class="tag ${p.status}">${NOME[p.status]}</span></div>
      <button class="x" data-del-pol="${p.id}" aria-label="Remover política">×</button></div>`).join('')
    : '<p class="empty">Nenhuma política encontrada.</p>';

  $('#modo').textContent = remoto ? 'Dados salvos no servidor Python' : 'Dados salvos neste navegador';
}

$('#f-com').addEventListener('submit', e => {
  e.preventDefault();
  enviar('POST', 'comunicados', null, { titulo: $('#m-titulo').value.trim(), mensagem: $('#m-msg').value.trim(), prioridade: $('#m-prio').value, fixado: $('#m-fixar').checked });
  e.target.reset();
});
$('#f-disc').addEventListener('submit', e => {
  e.preventDefault();
  enviar('POST', 'disciplinas', null, { nome: $('#d-nome').value.trim(), docente: $('#d-doc').value.trim() });
  e.target.reset();
});
$('#f-pol').addEventListener('submit', e => {
  e.preventDefault();
  if (!$('#p-disc').value) return;
  enviar('POST', 'politicas', null, { disc: $('#p-disc').value, tipo: $('#p-tipo').value, nome: $('#p-nome').value.trim(), status: $('#p-status').value, cond: $('#p-cond').value.trim() });
  $('#p-nome').value = ''; $('#p-cond').value = '';
});
$('#f-check').addEventListener('submit', e => {
  e.preventDefault();
  const box = $('#resultado');
  const achadas = db.politicas.filter(p => p.disc === $('#c-disc').value && p.tipo === $('#c-tipo').value);
  const decisao = ['proibido', 'restricao', 'permitido'].find(k => achadas.some(p => p.status === k));
  box.hidden = false;
  box.className = decisao || '';
  box.innerHTML = decisao
    ? `<b>${NOME[decisao]}</b>` + achadas.map(p => `<div>${esc(p.nome)}: ${NOME[p.status]}${p.cond ? ' — ' + esc(p.cond) : ''}</div>`).join('')
    : '<b>Sem política cadastrada</b><div>Nenhuma regra registrada para essa combinação.</div>';
});
$('#filtro').addEventListener('change', render);
$('#busca').addEventListener('input', render);

document.addEventListener('click', e => {
  const d = e.target.dataset;
  if (d.delDisc) enviar('DELETE', 'disciplinas', d.delDisc);
  else if (d.delPol) enviar('DELETE', 'politicas', d.delPol);
  else if (d.delCom) enviar('DELETE', 'comunicados', d.delCom);
  else if (d.fixar) enviar('PATCH', 'comunicados', d.fixar, { fixado: !db.comunicados.find(c => c.id === d.fixar).fixado });
});

carregar();

// ===== Menu (protótipo) =====
const linksMenu = [...document.querySelectorAll('.menu a')];
const marcar = id => linksMenu.forEach(a => {
  const ativo = a.dataset.alvo === id;
  a.classList.toggle('ativo', ativo);
  if (ativo) a.setAttribute('aria-current', 'true'); else a.removeAttribute('aria-current');
});
const fecharMenu = () => { document.body.classList.remove('menu-aberto'); $('#hamb').setAttribute('aria-expanded', 'false'); };
linksMenu.forEach(a => a.addEventListener('click', e => {
  e.preventDefault();
  document.getElementById(a.dataset.alvo).scrollIntoView();
  marcar(a.dataset.alvo);
  fecharMenu();
}));
$('#hamb').addEventListener('click', () => {
  const aberto = document.body.classList.toggle('menu-aberto');
  $('#hamb').setAttribute('aria-expanded', String(aberto));
});
document.addEventListener('click', e => { if (!e.target.closest('.menu, #hamb')) fecharMenu(); });
document.addEventListener('keydown', e => { if (e.key === 'Escape') fecharMenu(); });
if ('IntersectionObserver' in window) {
  const obs = new IntersectionObserver(es => es.forEach(x => x.isIntersecting && marcar(x.target.id)), { rootMargin: '-35% 0px -60% 0px' });
  document.querySelectorAll('[data-menu]').forEach(s => obs.observe(s));
}
marcar('inicio');
