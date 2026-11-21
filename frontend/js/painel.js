import { mostrarAviso } from "./mensagens.js";
import { request as api, escapeHtml as esc } from "./api.js";
const modal = document.querySelector("#app-modal");
const title = document.querySelector("#modal-title");
const body = document.querySelector("#modal-body");
document.querySelector("#app-modal .close").onclick = () => modal.close();
modal.addEventListener("click", event => { if (event.target === modal) modal.close(); });
export const show = (t, h) => {
  title.textContent = t;
  body.innerHTML = h;
  if (!modal.open) modal.showModal();
};
const notice = (t, kind = "") =>
  `<div class="notice ${kind}" role="status">${esc(t)}</div>`;
const button = (t, primary = false, type = "submit") =>
  `<button class="btn ${primary ? "primary" : ""}" type="${type}">${esc(t)}</button>`;
const empty = (t) => `<div class="records-empty">${esc(t)}</div>`;
async function aiCheck() {
  const ds = await api("/api/disciplines");
  if (!ds.length) {
    show(
      "Posso usar IA?",
      `${notice("Cadastre uma disciplina e suas políticas para consultar as regras.")}<div class="form-actions">${button("Adicionar disciplina", true, "button")}</div>`,
    );
    body.querySelector("button").onclick = () => manageDisciplineForm();
    return;
  }
  show(
    "Posso usar IA?",
    `<form class="form"><div class="field"><label>Disciplina</label><select name="disciplineId">${ds.map((d) => `<option value="${esc(d.id)}">${esc(d.name)}</option>`)}</select></div><div class="field"><label>Tipo de atividade</label><select name="activityType"><option value="prova">Prova</option><option value="trabalho">Trabalho</option><option value="atividade">Atividade</option><option value="pesquisa">Pesquisa</option><option value="outro">Outro</option></select></div><div id="check-result"></div><div class="form-actions">${button("Verificar regras", true)}</div></form>`,
  );
  body.querySelector("form").onsubmit = async (e) => {
    e.preventDefault();
    try {
      const r = await api("/api/ai-check", {
          method: "POST",
          body: JSON.stringify(
            Object.fromEntries(new FormData(e.currentTarget)),
          ),
        }),
        labels = {
          proibido: "Proibido",
          restricao: "Permitido com restrição",
          permitido: "Permitido",
          sem_politica: "Sem política cadastrada",
        };
      body.querySelector("#check-result").innerHTML =
        `<div class="result ${esc(r.decision)}"><b>${esc(labels[r.decision])}</b><p>${r.policies.length ? `${r.policies.length} regra(s) encontrada(s).` : esc(r.message)}</p>${r.policies.map((p) => `<p><b>${esc(p.activityName)}</b> — ${esc(p.conditions || p.details || labels[p.status])}</p>`).join("")}</div>`;
    } catch (err) {
      mostrarAviso(body.querySelector("#check-result"), err.message, "error");
    }
  };
}
async function announcements() {
  const as = await api("/api/announcements?all=true");
  show(
    "Comunicados",
    `${button("＋ Novo comunicado", true, "button")}<div id="list-message"></div>${as.length ? as.map((a) => `<article class="result"><b>${esc(a.title)}</b><p>${esc(a.message)}</p><button class="mini" data-toggle="${esc(a.id)}" type="button">${a.active ? "Inativar" : "Reativar"}</button> <button class="mini danger" data-del="${esc(a.id)}">Remover</button></article>`).join("") : empty("Nenhum comunicado publicado.")}`,
  );
  body.querySelector(".modal-body > button").onclick = announcementForm;
  body.querySelectorAll("[data-toggle]").forEach(button => {
    button.onclick = async () => {
      const item = as.find(a => a.id === button.dataset.toggle);
      try {
        await api("/api/announcements/" + item.id, {method:"PATCH", body:JSON.stringify({active:!item.active})});
        await announcements();
      } catch (error) {
        mostrarAviso(body.querySelector("#list-message"), error.message, "error");
      }
    };
  });
  body.querySelectorAll("[data-del]").forEach(
    (b) =>
      (b.onclick = async () => {
        try {
          await api(`/api/announcements/${b.dataset.del}`, {
            method: "DELETE",
          });

          await announcements();
        } catch (e) {
          mostrarAviso(body.querySelector("#list-message"), e.message, "error");
        }
      }),
  );
}
function announcementForm() {
  show(
    "Novo comunicado",
    `<form class="form"><div class="field"><label>Título *</label><input name="title" required maxlength="180"></div><div class="field"><label>Mensagem *</label><textarea name="message" required maxlength="3000"></textarea></div><div class="form-message"></div><div class="form-actions">${button("Cancelar", false, "button")}${button("Publicar", true)}</div></form>`,
  );
  body.querySelector("[type=button]").onclick = () => modal.close();
  body.querySelector("form").onsubmit = async (e) => {
    e.preventDefault();
    try {
      await api("/api/announcements", {
        method: "POST",
        body: JSON.stringify(
          Object.fromEntries(new FormData(e.currentTarget)),
        ),
      });

      await announcements();
    } catch (err) {
      mostrarAviso(body.querySelector(".form-message"), err.message, "error");
    }
  };
}
async function history() {
  const hs = await api("/api/history?limit=500");
  const EL = {
      discipline: "Disciplina",
      policy: "Política",
      announcement: "Comunicado",
      turma: "Turma",
      user: "Usuário",
      matricula: "Matrícula",
    },
    AL = { created: "Criação", updated: "Alteração", deleted: "Exclusão" },
    RL = { admin: "Administrador", professor: "Professor", aluno: "Aluno" },
    FL = {
      name: "Nome",
      code: "Código",
      instructor: "Docente",
      ownerId: "Responsável",
      activityName: "Atividade",
      activityType: "Tipo",
      status: "Status",
      conditions: "Condições",
      details: "Detalhes",
      source: "Fonte",
      disciplineId: "Disciplina",
      title: "Título",
      message: "Mensagem",
      active: "Ativo",
      role: "Perfil",
    };
  const who = (h) => {
      if (h.authorName)
        return {
          n: h.authorName,
          i: h.authorId || "",
          r: RL[h.authorRole] || "",
        };
      const m = / \(por (.+)\)$/.exec(h.summary || "");
      return { n: m ? m[1] : "Não registrado", i: "", r: "" };
    },
    sum = (h) => String(h.summary || "").replace(/ \(por .+\)$/, ""),
    key = (h) => {
      const w = who(h);
      return w.i || w.n;
    };
  const au = [...new Map(hs.map((h) => [key(h), who(h).n])).entries()];
  const q = (v) => `“${esc(v)}”`,
    fl = (c) => `<b>${esc(FL[c.field] || c.field)}</b>`;
  const ch = (c) =>
    c.from == null
      ? `${fl(c)}: ${q(c.to)}`
      : c.to == null
        ? `${fl(c)}: ${q(c.from)} <i>(removido)</i>`
        : `${fl(c)} alterado de ${q(c.from)} para ${q(c.to)}`;
  show(
    "Histórico (trilha de auditoria)",
    hs.length
      ? `<div class="toolbar"><input class="search" id="h-q" type="search" placeholder="Buscar descrição ou registro" aria-label="Buscar no histórico"><select class="filter-author search" id="h-au" aria-label="Filtrar por autor"><option value="">Todos os autores</option>${au.map(([k, n]) => `<option value="${esc(k)}">${esc(n)}</option>`).join("")}</select><select class="filter-action search" id="h-ac" aria-label="Filtrar por ação"><option value="">Todas as ações</option><option value="created">Criação</option><option value="updated">Alteração</option><option value="deleted">Exclusão</option></select></div><div id="h-count" class="notice" role="status"></div><div id="h-rows"></div>`
      : empty("O histórico aparecerá após as primeiras alterações."),
  );
  if (!hs.length) return;
  const draw = () => {
    const t = body.querySelector("#h-q").value.toLocaleLowerCase("pt-BR"),
      a = body.querySelector("#h-au").value,
      k = body.querySelector("#h-ac").value,
      rows = hs.filter(
        (h) =>
          (!a || key(h) === a) &&
          (!k || h.action === k) &&
          `${sum(h)} ${h.entityId} ${EL[h.entity] || h.entity}`
            .toLocaleLowerCase("pt-BR")
            .includes(t),
      );
    body.querySelector("#h-count").textContent =
      `${rows.length} de ${hs.length} registros`;
    body.querySelector("#h-rows").innerHTML = rows.length
      ? `<div class="table-wrap"><table class="records"><thead><tr><th>Quando</th><th>Autor</th><th>Ação</th><th>Registro</th><th>O que mudou</th></tr></thead><tbody>${rows
          .map((h) => {
            const w = who(h);
            return `<tr><td>${new Date(h.createdAt).toLocaleString("pt-BR")}</td><td><b>${esc(w.n)}</b><br><small>${esc([w.r, w.i && String(w.i).slice(0, 8)].filter(Boolean).join(" · ") || "—")}</small></td><td>${esc(AL[h.action] || h.action)}</td><td>${esc(EL[h.entity] || h.entity)}<br><small>${esc(String(h.entityId).slice(0, 8))}</small></td><td>${esc(sum(h))}${(h.changes || []).length ? "<br>" + h.changes.map(ch).join("<br>") : ""}</td></tr>`;
          })
          .join("")}</tbody></table></div>`
      : empty("Nenhum registro com esses filtros.");
  };
  ["#h-q", "#h-au", "#h-ac"].forEach(
    (i) =>
      (body.querySelector(i)[i === "#h-q" ? "oninput" : "onchange"] = draw),
  );
  draw();
}
const SL = {
  proibido: ["Proibido", "red"],
  restricao: ["Com restrição", "yellow"],
  permitido: ["Permitido", "green"],
};
const TY =
  '<option value="prova">Prova</option><option value="trabalho">Trabalho</option><option value="atividade">Atividade</option><option value="pesquisa">Pesquisa</option><option value="outro">Outro</option>';
const ST =
  '<option value="proibido">Proibido</option><option value="restricao">Permitido com restrição</option><option value="permitido">Permitido</option>';
const sub = (d) =>
  esc(
    [d.code, d.instructor].filter(Boolean).join(" · ") ||
      "Sem código ou docente",
  );
function confirmView(t, msg, label, ok, back) {
  show(
    t,
    `<p>${msg}</p><div id="confirm-message"></div><div class="form-actions"><button class="btn" type="button" data-no>Cancelar</button><button class="btn danger" type="button" data-ok>${esc(label)}</button></div>`,
  );
  const no = body.querySelector("[data-no]");
  no.onclick = back;
  no.focus();
  body.querySelector("[data-ok]").onclick = async () => {
    try {
      await ok();
    } catch (e) {
      mostrarAviso(body.querySelector("#confirm-message"), e.message, "error");
    }
  };
}
const delDiscipline = (d, back) =>
  confirmView(
    "Remover disciplina",
    `Remover a disciplina <b>${esc(d.name)}</b>? Ela só pode ser removida se não tiver políticas. Esta ação não pode ser desfeita.`,
    "Remover disciplina",
    async () => {
      await api(`/api/disciplines/${d.id}`, { method: "DELETE" });

      await manageDisciplines();
    },
    back,
  );
async function manageDisciplines() {
  const [ds, ps] = await Promise.all([
    api("/api/disciplines"),
    api("/api/policies"),
  ]);
  show(
    "Gerenciar Disciplina",
    `<div class="manage-head"><p class="no-margin notice">Escolha uma disciplina para gerenciar as políticas dela.</p><button class="btn primary" type="button" data-new>＋ Nova disciplina</button></div><div id="list-message"></div>${ds.length ? ds.map((d) => `<article class="result disc-item"><div class="meta"><b>${esc(d.name)}</b><br><small>${sub(d)} · ${ps.filter((p) => p.disciplineId === d.id).length} política(s)</small></div><div class="row-actions"><button class="mini" type="button" data-open="${esc(d.id)}" aria-label="Gerenciar políticas de ${esc(d.name)}">Gerenciar políticas</button><button class="mini" type="button" data-edit="${esc(d.id)}" aria-label="Editar disciplina ${esc(d.name)}">Editar</button><button class="mini danger" type="button" data-del="${esc(d.id)}" aria-label="Remover disciplina ${esc(d.name)}">Remover</button></div></article>`).join("") : empty("Nenhuma disciplina cadastrada. Use “Nova disciplina” para começar.")}`,
  );
  body.querySelector("[data-new]").onclick = () => manageDisciplineForm();
  body
    .querySelectorAll("[data-open]")
    .forEach((b) => (b.onclick = () => manageDiscipline(b.dataset.open)));
  body
    .querySelectorAll("[data-edit]")
    .forEach(
      (b) =>
        (b.onclick = () =>
          manageDisciplineForm(ds.find((d) => d.id === b.dataset.edit))),
    );
  body.querySelectorAll("[data-del]").forEach(
    (b) =>
      (b.onclick = () =>
        delDiscipline(
          ds.find((d) => d.id === b.dataset.del),
          manageDisciplines,
        )),
  );
}
function manageDisciplineForm(item = {}) {
  const back = () =>
    item.id ? manageDiscipline(item.id) : manageDisciplines();
  show(
    item.id ? "Editar disciplina" : "Nova disciplina",
    `<form class="form"><div class="field"><label for="md-name">Nome da disciplina *</label><input id="md-name" name="name" required maxlength="180" value="${esc(item.name)}"></div><div class="form-grid"><div class="field"><label for="md-code">Código</label><input id="md-code" name="code" maxlength="40" value="${esc(item.code)}"></div><div class="field"><label for="md-inst">Docente</label><input id="md-inst" name="instructor" maxlength="180" value="${esc(item.instructor)}"></div></div><div class="form-message"></div><div class="form-actions"><button class="btn" type="button" data-no>Cancelar</button>${button("Salvar disciplina", true)}</div></form>`,
  );
  body.querySelector("[data-no]").onclick = back;
  body.querySelector("form").onsubmit = async (e) => {
    e.preventDefault();
    try {
      await api(
        item.id ? `/api/disciplines/${item.id}` : "/api/disciplines",
        {
          method: item.id ? "PUT" : "POST",
          body: JSON.stringify(
            Object.fromEntries(new FormData(e.currentTarget)),
          ),
        },
      );

      await (item.id
        ? manageDiscipline(item.id, "Disciplina atualizada.")
        : manageDisciplines());
    } catch (err) {
      mostrarAviso(body.querySelector(".form-message"), err.message, "error");
    }
  };
}
async function manageDiscipline(id, msg) {
  const ds = await api("/api/disciplines"),
    d = ds.find((x) => x.id === id);
  if (!d) return manageDisciplines();
  const ps = await api(
    "/api/policies?disciplineId=" + encodeURIComponent(id),
  );
  show(
    "Gerenciar Disciplina",
    `<div class="ctx"><small>Disciplina selecionada</small><strong>${esc(d.name)}</strong><small>${sub(d)}</small></div><div class="manage-head"><button class="mini" type="button" data-back>← Todas as disciplinas</button><label class="sr-only" for="md-switch">Trocar de disciplina</label><select class="search" id="md-switch">${ds.map((x) => `<option value="${esc(x.id)}" ${x.id === id ? "selected" : ""}>${esc(x.name)}</option>`).join("")}</select></div><div class="manage-head"><h3>Políticas (${ps.length})</h3><div class="row-actions"><button class="mini" type="button" data-dedit>Editar disciplina</button><button class="mini danger" type="button" data-ddel>Remover disciplina</button><button class="btn primary" type="button" data-add>＋ Adicionar política</button></div></div><div id="list-message">${msg ? notice(msg, "success") : ""}</div>${ps.length ? `<div class="table-wrap"><table class="records"><thead><tr><th>Atividade</th><th>Uso de IA</th><th>Condições</th><th>Ações</th></tr></thead><tbody>${ps.map((p) => `<tr><td><b>${esc(p.activityName)}</b><br>${esc(p.activityType)}</td><td><span class="pill ${SL[p.status][1]}">${SL[p.status][0]}</span></td><td>${esc(p.conditions || p.details || "—")}</td><td><div class="row-actions"><button class="mini" type="button" data-pe="${esc(p.id)}" aria-label="Editar política ${esc(p.activityName)}">Editar</button><button class="mini danger" type="button" data-pd="${esc(p.id)}" aria-label="Remover política ${esc(p.activityName)}">Remover</button></div></td></tr>`).join("")}</tbody></table></div>` : empty("Esta disciplina ainda não tem políticas. Use “Adicionar política”.")}`,
  );
  body.querySelector("[data-back]").onclick = manageDisciplines;
  body.querySelector("#md-switch").onchange = (e) =>
    manageDiscipline(e.target.value);
  body.querySelector("[data-add]").onclick = () => managePolicyForm({}, id);
  body.querySelector("[data-dedit]").onclick = () => manageDisciplineForm(d);
  body.querySelector("[data-ddel]").onclick = () =>
    delDiscipline(d, () => manageDiscipline(id));
  body.querySelectorAll("[data-pe]").forEach(
    (b) =>
      (b.onclick = () =>
        managePolicyForm(
          ps.find((p) => p.id === b.dataset.pe),
          id,
        )),
  );
  body.querySelectorAll("[data-pd]").forEach(
    (b) =>
      (b.onclick = () => {
        const p = ps.find((x) => x.id === b.dataset.pd);
        confirmView(
          "Remover política",
          `Remover a política <b>${esc(p.activityName)}</b> da disciplina <b>${esc(d.name)}</b>? Esta ação não pode ser desfeita.`,
          "Remover política",
          async () => {
            await api(`/api/policies/${p.id}`, { method: "DELETE" });

            await manageDiscipline(id, "Política removida.");
          },
          () => manageDiscipline(id),
        );
      }),
  );
}
async function managePolicyForm(item, did) {
  const ds = await api("/api/disciplines"),
    d = ds.find((x) => x.id === did);
  if (!d) return manageDisciplines();
  show(
    item.id ? "Editar política" : "Adicionar política",
    `<div class="ctx"><small>Disciplina</small><strong>${esc(d.name)}</strong></div><form class="form"><div class="form-grid"><div class="field"><label for="mp-type">Tipo de atividade</label><select id="mp-type" name="activityType">${TY}</select></div><div class="field"><label for="mp-status">Uso de IA</label><select id="mp-status" name="status">${ST}</select></div></div><div class="field"><label for="mp-name">Atividade *</label><input id="mp-name" name="activityName" required maxlength="180" value="${esc(item.activityName)}" placeholder="Ex.: Relatório final"></div><div class="field"><label for="mp-source">Fonte</label><input id="mp-source" name="source" maxlength="500" value="${esc(item.source)}"></div><div class="field"><label for="mp-cond">Condições</label><textarea id="mp-cond" name="conditions" maxlength="3000">${esc(item.conditions)}</textarea></div><div class="field"><label for="mp-det">Detalhes</label><textarea id="mp-det" name="details" maxlength="5000">${esc(item.details)}</textarea></div><div class="form-message"></div><div class="form-actions"><button class="btn" type="button" data-no>Cancelar</button>${button("Salvar política", true)}</div></form>`,
  );
  const f = body.querySelector("form");
  f.status.value = item.status || "proibido";
  f.activityType.value = item.activityType || "prova";
  body.querySelector("[data-no]").onclick = () => manageDiscipline(did);
  f.onsubmit = async (e) => {
    e.preventDefault();
    try {
      await api(item.id ? `/api/policies/${item.id}` : "/api/policies", {
        method: item.id ? "PUT" : "POST",
        body: JSON.stringify({
          ...Object.fromEntries(new FormData(f)),
          disciplineId: did,
        }),
      });

      await manageDiscipline(
        did,
        item.id ? "Política atualizada." : "Política adicionada.",
      );
    } catch (err) {
      mostrarAviso(body.querySelector(".form-message"), err.message, "error");
    }
  };
}

export { aiCheck, history as auditHistory, announcements, manageDisciplineForm, manageDiscipline, manageDisciplines };
