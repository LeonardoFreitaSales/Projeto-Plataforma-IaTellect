const KEY = 'plataforma-simples', J = { 'Content-Type': 'application/json' };
const TIPOS = ['prova', 'trabalho', 'atividade', 'pesquisa', 'outro'];
const NOME = { proibido: 'Proibido', restricao: 'Com restrição', permitido: 'Permitido' };
const vazio = () => ({ disciplinas: [], politicas: [] });
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
  const { disciplinas: D, politicas: P } = db;
  $('#n-disc').textContent = D.length;
  $('#n-pol').textContent = P.length;
  Object.keys(NOME).forEach(k => {
    const n = P.filter(p => p.status === k).length;
    $('#n-' + k).textContent = n;
    $('#b-' + k).style.width = P.length ? (n / P.length * 100) + '%' : '0';
  });

  const opcoes = D.map(d => `<option value="${d.id}">${esc(d.nome)}</option>`).join('') || '<option value="">Cadastre uma disciplina</option>';
  const tipos = TIPOS.map(t => `<option value="${t}">${t[0].toUpperCase() + t.slice(1)}</option>`).join('');
  ['#c-disc', '#p-disc'].forEach(s => preencher($(s), opcoes));
  ['#c-tipo', '#p-tipo'].forEach(s => preencher($(s), tipos));

  $('#chips').innerHTML = D.length
    ? D.map(d => `<span class="chip">${esc(d.nome)}<button class="x" data-del-disc="${d.id}" aria-label="Remover ${esc(d.nome)}">×</button></span>`).join('')
    : '<p class="empty">Nenhuma disciplina ainda.</p>';

  const f = $('#filtro').value;
  const lista = P.filter(p => !f || p.status === f);
  $('#lista').innerHTML = lista.length ? lista.map(p => `
    <div class="item"><div><b>${esc(nomeDisc(p.disc))}</b> · ${esc(p.nome)}
      <small>${esc(p.tipo)}${p.cond ? ' · ' + esc(p.cond) : ''}</small>
      <span class="tag ${p.status}">${NOME[p.status]}</span></div>
      <button class="x" data-del-pol="${p.id}" aria-label="Remover política">×</button></div>`).join('')
    : '<p class="empty">Nenhuma política encontrada.</p>';

  $('#modo').textContent = remoto ? 'Dados salvos no servidor Python' : 'Dados salvos neste navegador';
}

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

document.addEventListener('click', e => {
  const d = e.target.dataset;
  if (d.delDisc) enviar('DELETE', 'disciplinas', d.delDisc);
  else if (d.delPol) enviar('DELETE', 'politicas', d.delPol);
});

carregar();
