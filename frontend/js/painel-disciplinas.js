import { mostrarAviso } from "./mensagens.js";
import { request as j, escapeHtml as esc } from "./api.js";
const $ = selector => document.querySelector(selector);
const app = $("#app-modal"), mb = $("#modal-body");
let me, owners = {};
export function configure(user, disciplines) {
  me = user;
  owners = Object.fromEntries(disciplines.map(d => [d.id, d.ownerId]));
}
// diálogos acessíveis (substituem alert/prompt/confirm): foco preso e Esc pelo <dialog> nativo
const mdl = $("#msg-modal");
// Mantem Tab e Shift+Tab dentro do dialogo, inclusive nos limites do navegador.
[app, mdl].forEach((d) =>
  d.addEventListener("keydown", (e) => {
    if (e.key !== "Tab") return;
    const items = [
      ...d.querySelectorAll(
        "button,input,select,textarea,a[href],[tabindex]",
      ),
    ].filter(
      (x) => !x.disabled && x.tabIndex >= 0 && x.getClientRects().length,
    );
    if (!items.length) {
      e.preventDefault();
      return;
    }
    const first = items[0],
      last = items[items.length - 1],
      active = document.activeElement;
    if (e.shiftKey && (active === first || !items.includes(active))) {
      e.preventDefault();
      last.focus();
    } else if (!e.shiftKey && (active === last || !items.includes(active))) {
      e.preventDefault();
      first.focus();
    }
  }),
);
function dialog(o) {
  return new Promise((res) => {
    const t = $("#msg-title"),
      x = $("#msg-text"),
      f = $("#msg-field"),
      i = $("#msg-input"),
      ok = $("#msg-ok"),
      c = $("#msg-cancel"),
      m = $("#msg-err");
    t.textContent = o.title || "Aviso";
    x.textContent = o.text || "";
    f.hidden = !o.field;
    m.hidden = true;
    m.textContent = "";
    i.value = "";
    if (o.field) $("#msg-label").textContent = o.field;
    ok.textContent = o.ok || "OK";
    ok.className = "btn " + (o.danger ? "danger" : "primary");
    c.hidden = !o.cancel;
    let done = false;
    const end = (v) => {
      if (done) return;
      done = true;
      mdl.removeEventListener("cancel", esc2);
      mdl.close();
      ok.onclick = c.onclick = null;
      res(v);
    };
    const esc2 = (ev) => {
      ev.preventDefault();
      end(o.field ? null : !o.cancel);
    };
    mdl.addEventListener("cancel", esc2);
    ok.onclick = () => {
      if (o.field) {
        if (!i.value) {
          m.textContent = "Preencha o campo.";
          m.hidden = false;
          i.focus();
          return;
        }
        end(i.value);
      } else end(true);
    };
    c.onclick = () => end(o.field ? null : false);
    mdl.showModal();
    (o.field ? i : o.cancel ? c : ok).focus();
  });
}
const notify = (text, title) => dialog({ title: title || "Aviso", text });
const askText = (title, field) =>
  dialog({ title, field, ok: "Salvar", cancel: true });
const askConfirm = (title, text, ok) =>
  dialog({ title, text, ok: ok || "Confirmar", cancel: true, danger: true });
const can = (id) =>
  !!me &&
  (me.role === "admin" || (me.role === "professor" && owners[id] === me.id));
function apply() {
  if (!me) return;
  const adm = me.role === "admin";
  const sw = mb.querySelector("#md-switch");
  if (sw && !can(sw.value))
    mb.querySelectorAll(
      "[data-dedit],[data-ddel],[data-add],[data-pe],[data-pd]",
    ).forEach((e) => (e.hidden = true));
  if (!adm)
    mb.querySelectorAll("[data-ddel]").forEach((e) => (e.hidden = true));
  mb.querySelectorAll(".disc-item [data-edit],.disc-item [data-del]").forEach(
    (b) => {
      if (!can(b.dataset.edit || b.dataset.del) || (!adm && b.dataset.del))
        b.hidden = true;
    },
  );
  if (!adm) {
    document
      .querySelectorAll("[data-new]")
      .forEach((e) => (e.hidden = true));
    mb.querySelectorAll(".form-actions button").forEach((b) => {
      if (/Adicionar disciplina/.test(b.textContent)) b.hidden = true;
    });
  }
  if (!adm && /Comunicados/.test($("#modal-title").textContent))
    mb.querySelectorAll("[data-del],:scope > button").forEach(
      (b) => (b.hidden = true),
    );
}
new MutationObserver(apply).observe(document.body, {
  childList: true,
  subtree: true,
});
const open = (t, h) => {
  $("#modal-title").textContent = t;
  mb.innerHTML = h;
  if (!app.open) app.showModal();
};
const PL = {
  pendente: ["Pendente", "yellow"],
  aprovada: ["Aprovada", "green"],
  recusada: ["Recusada", "red"],
};
const CAT = [
  [
    "pendente",
    "A serem aprovados",
    "Não há alunos aguardando aprovação nesta turma.",
  ],
  ["recusada", "Não permitidos", "Não há alunos não permitidos nesta turma."],
  [
    "aprovada",
    "Aceitos/Permitidos",
    "Ainda não há alunos aceitos nesta turma.",
  ],
];
const loadingBox =
  '<div class="records-empty" role="status" aria-busy="true">Carregando…</div>';
async function loadTurma(t) {
  const box = mb.querySelector(`[data-body="${t.id}"]`);
  if (!box) return;
  box.innerHTML =
    '<p class="records-empty" role="status" aria-busy="true">Carregando alunos…</p>';
  let en,
    notes = null;
  try {
    en = await j(`/api/turmas/${t.id}/enrollments`);
  } catch (x) {
    box.innerHTML = `<div class="notice error" role="alert">Não foi possível carregar os alunos da turma ${esc(t.name)}: ${esc(x.message)} <button class="mini" type="button" data-retry>Tentar novamente</button></div>`;
    box.querySelector("[data-retry]").onclick = () => loadTurma(t);
    return;
  }
  const useNotes = me.role === "professor";
  if (useNotes)
    notes = await j(`/api/turmas/${t.id}/notes`).catch(() => null);
  const acts = (e, st) =>
    (st !== "aprovada"
      ? `<button class="mini" type="button" data-en="${esc(e.id)}" data-s="aprovada" aria-label="Aprovar ${esc(e.studentName)}">Aprovar</button>`
      : "") +
    (st === "pendente"
      ? `<button class="mini danger" type="button" data-en="${esc(e.id)}" data-s="recusada" aria-label="Recusar ${esc(e.studentName)}">Recusar</button>`
      : "") +
    (st === "aprovada"
      ? `<button class="mini danger" type="button" data-en="${esc(e.id)}" data-s="recusada" aria-label="Mover ${esc(e.studentName)} para não permitidos">Mover para não permitidos</button>`
      : "");
  const stu = (e, st) => {
    const sid = esc(e.studentId),
      has = notes && notes[e.studentId];
    return `<li class="srow"><div class="sname"><b>${esc(e.studentName)}</b>${has ? ' <span class="pill yellow">Com anotação privada</span>' : ""}</div><div class="row-actions">${acts(e, st)}<button class="mini" type="button" data-spw="${sid}" aria-label="Definir senha de ${esc(e.studentName)}">Definir senha</button>${notes ? `<button class="mini" type="button" data-note="${sid}" aria-expanded="false" aria-label="Anotação privada sobre ${esc(e.studentName)}">Anotação privada</button>` : ""}</div>${notes ? `<div class="note" hidden><label for="n-${sid}">Anotação privada sobre ${esc(e.studentName)}. Só você vê: não aparece para o aluno nem para outros professores.</label><textarea id="n-${sid}" maxlength="2000" rows="3">${esc(notes[e.studentId] || "")}</textarea><div class="form-actions"><span class="nmsg" role="status"></span><button class="mini" type="button" data-nsave="${sid}">Salvar anotação</button></div></div>` : ""}</li>`;
  };
  box.innerHTML =
    CAT.map(([st, label, msg]) => {
      const l = en.filter((e) => e.status === st);
      return `<section class="cat" aria-labelledby="c-${t.id}-${st}"><h4 id="c-${t.id}-${st}">${label} <span class="cnt">(${l.length})</span></h4>${l.length ? `<ul class="slist">${l.map((e) => stu(e, st)).join("")}</ul>` : `<p class="records-empty" role="status"><b>Turma ${esc(t.name)} · ${label}:</b> ${msg}</p>`}</section>`;
    }).join("") +
    (useNotes && notes === null
      ? '<p class="notice" role="status">As anotações privadas não puderam ser carregadas agora.</p>'
      : "");
  box.querySelectorAll("[data-en]").forEach(
    (b) =>
      (b.onclick = async () => {
        b.disabled = true;
        try {
          await j("/api/matriculas/" + b.dataset.en, {
            method: "PUT",
            body: JSON.stringify({ status: b.dataset.s }),
          });
          loadTurma(t);
        } catch (x) {
          b.disabled = false;
          notify(x.message);
        }
      }),
  );
  box.querySelectorAll("[data-note]").forEach(
    (b) =>
      (b.onclick = () => {
        const n = b.closest("li").querySelector(".note");
        n.hidden = !n.hidden;
        b.setAttribute("aria-expanded", String(!n.hidden));
        if (!n.hidden) n.querySelector("textarea").focus();
      }),
  );
  box.querySelectorAll("[data-spw]").forEach(
    (b) =>
      (b.onclick = async () => {
        const p = await askText(
          "Definir senha do aluno",
          "Nova senha (mín. 8 caracteres)",
        );
        if (!p) return;
        try {
          await j("/api/alunos/" + b.dataset.spw + "/password", {
            method: "PUT",
            body: JSON.stringify({ password: p }),
          });
          notify("Senha definida. Informe-a ao aluno por um canal seguro.");
        } catch (x) {
          notify(x.message);
        }
      }),
  );
  box.querySelectorAll("[data-nsave]").forEach(
    (b) =>
      (b.onclick = async () => {
        const n = b.closest(".note"),
          v = n.querySelector("textarea").value,
          m = n.querySelector(".nmsg");
        try {
          await j("/api/notas/" + b.dataset.nsave, {
            method: "PUT",
            body: JSON.stringify({ text: v }),
          });
          m.textContent = v.trim() ? "Anotação salva." : "Anotação removida.";
        } catch (x) {
          m.textContent = "Erro ao salvar: " + x.message;
        }
      }),
  );
}
function minhaSenha() {
  open(
    "Alterar minha senha",
    `<form class="form" id="pw"><div class="field"><label for="pw-a">Senha atual</label><input id="pw-a" name="currentPassword" type="password" autocomplete="current-password" required></div><div class="field"><label for="pw-n">Nova senha (mínimo 8 caracteres)</label><input id="pw-n" name="newPassword" type="password" autocomplete="new-password" minlength="8" required></div><div class="field"><label for="pw-r">Repita a nova senha</label><input id="pw-r" type="password" autocomplete="new-password" required></div><div id="pw-m"></div><div class="form-actions"><button class="btn primary" type="submit">Salvar nova senha</button></div></form>`,
  );
  $("#pw").onsubmit = async (e) => {
    e.preventDefault();
    const f = Object.fromEntries(new FormData(e.target)),
      m = $("#pw-m");
    if (f.newPassword !== $("#pw-r").value) {
      mostrarAviso(m, "As senhas novas não são iguais.", "error");
      return;
    }
    try {
      await j("/api/me/password", { method: "PUT", body: JSON.stringify(f) });
      mostrarAviso(m, "Senha alterada. Suas outras sessões foram encerradas.", "success");
      e.target.reset();
    } catch (x) {
      mostrarAviso(m, x.message, "error");
    }
  };
}
async function turmas() {
  const aluno = me.role === "aluno";
  open(aluno ? "Minha turma" : "Turmas e alunos", loadingBox);
  let ts,
    ds = [];
  try {
    [ts, ds] = await Promise.all([
      j("/api/turmas"),
      aluno ? [] : j("/api/disciplines"),
    ]);
  } catch (x) {
    mb.innerHTML = `<div class="notice error" role="alert">Não foi possível carregar as turmas: ${esc(x.message)} <button class="mini" type="button" id="rt">Tentar novamente</button></div>`;
    $("#rt").onclick = turmas;
    return;
  }
  if (aluno) {
    mb.innerHTML = ts.length
      ? ts
          .map(
            (t) =>
              `<section class="tgroup" aria-labelledby="mt-${esc(t.id)}"><div class="tg-head"><h3 id="mt-${esc(t.id)}">Turma ${esc(t.name)}</h3><span class="pill ${PL[t.status][1]}">Matrícula: ${PL[t.status][0].toLowerCase()}</span></div>${t.status === "pendente" ? '<p class="notice" role="status">Aguardando a aprovação de um professor da turma. As matérias aparecem aqui depois da aprovação.</p>' : t.status === "recusada" ? '<p class="notice error" role="status">Sua matrícula nesta turma não foi permitida.</p>' : t.disciplines.length ? `<h4 class="tg-sub">Matérias da turma</h4><ul class="slist">${t.disciplines.map((d) => `<li class="srow"><b>${esc(d.name)}</b></li>`).join("")}</ul>` : '<p class="records-empty" role="status">Ainda não há matérias vinculadas a esta turma.</p>'}</section>`,
          )
          .join("")
      : '<div class="records-empty" role="status">Você ainda não está em nenhuma turma.</div>';
    return;
  }
  ds.forEach((d) => (owners[d.id] = d.ownerId));
  const mine = ds.filter((d) => can(d.id));
  mb.innerHTML = `<form class="form" id="nt"><div class="field"><label for="nt-n">Nova turma</label><input id="nt-n" name="name" required maxlength="120" placeholder="Ex.: 9º ano"></div><div id="nt-m"></div><div class="form-actions"><button class="btn primary" type="submit">Criar turma</button></div></form>${
    ts
      .map((t) => {
        const lk = new Set(t.disciplines.map((d) => d.id)),
          free = mine.filter((d) => !lk.has(d.id));
        return `<section class="tgroup" aria-labelledby="th-${esc(t.id)}"><div class="tg-head"><h3 id="th-${esc(t.id)}">Turma ${esc(t.name)}</h3><button class="mini danger" type="button" data-dt="${esc(t.id)}" aria-label="Excluir a turma ${esc(t.name)}">Excluir turma</button></div><h4 class="tg-sub">Matérias nesta turma</h4><div class="legend">${t.disciplines.map((d) => `<span class="pill green">${esc(d.name)}${can(d.id) ? ` <button class="mini" type="button" data-un="${esc(t.id)}|${esc(d.id)}" aria-label="Desvincular ${esc(d.name)} da turma ${esc(t.name)}">×</button>` : ""}</span>`).join("") || '<span class="notice">Nenhuma matéria sua vinculada a esta turma.</span>'}</div>${free.length ? `<div class="toolbar"><select class="search" data-sel="${esc(t.id)}" aria-label="Matéria para vincular à turma ${esc(t.name)}">${free.map((d) => `<option value="${esc(d.id)}">${esc(d.name)}</option>`).join("")}</select><button class="mini" type="button" data-ln="${esc(t.id)}">Vincular matéria</button></div>` : ""}<div data-body="${esc(t.id)}" aria-live="polite"></div></section>`;
      })
      .join("") ||
    '<div class="records-empty" role="status">Nenhuma turma vinculada a você até o momento.</div>'
  }`;
  const go = async (u, m, b) => {
    try {
      await j(u, { method: m, body: b && JSON.stringify(b) });
      turmas();
    } catch (x) {
      notify(x.message);
    }
  };
  $("#nt").onsubmit = (e) => {
    e.preventDefault();
    go("/api/turmas", "POST", Object.fromEntries(new FormData(e.target)));
  };
  mb.querySelectorAll("[data-ln]").forEach(
    (b) =>
      (b.onclick = () =>
        go(
          `/api/turmas/${b.dataset.ln}/disciplines/${mb.querySelector(`[data-sel="${b.dataset.ln}"]`).value}`,
          "PUT",
        )),
  );
  mb.querySelectorAll("[data-un]").forEach(
    (b) =>
      (b.onclick = () => {
        const [t, d] = b.dataset.un.split("|");
        go(`/api/turmas/${t}/disciplines/${d}`, "DELETE");
      }),
  );
  mb.querySelectorAll("[data-dt]").forEach(
    (b) =>
      (b.onclick = () => {
        askConfirm(
          "Excluir turma",
          "Excluir esta turma e suas matrículas? Esta ação não pode ser desfeita.",
          "Excluir turma",
        ).then((ok) => {
          if (ok) go("/api/turmas/" + b.dataset.dt, "DELETE");
        });
      }),
  );
  ts.forEach(loadTurma);
}
async function usuarios() {
  const [us, ds] = await Promise.all([
      j("/api/users"),
      j("/api/disciplines"),
    ]),
    pr = us.filter((x) => x.role !== "aluno");
  open(
    "Usuários e donos das matérias",
    `<form class="form" id="nu"><div class="form-grid"><div class="field"><label for="nu-n">Nome do professor</label><input id="nu-n" name="name" required></div><div class="field"><label for="nu-p">Senha inicial (mín. 8)</label><input id="nu-p" name="password" type="password" minlength="8" required></div></div><div id="nu-m"></div><div class="form-actions"><button class="btn primary" type="submit">Cadastrar professor</button></div></form><h3 class="section-heading">Professores</h3>${pr.map((x) => `<article class="result disc-item"><div class="meta"><b>${esc(x.name)}</b><br><small>${esc(x.role)}</small></div><button class="mini" data-pw="${esc(x.id)}">Redefinir senha</button></article>`).join("")}<h3 class="section-heading">Dono de cada matéria</h3>${ds.map((d) => `<article class="result disc-item"><div class="meta"><b>${esc(d.name)}</b></div><select class="filter-owner search" data-own="${esc(d.id)}" aria-label="Dono de ${esc(d.name)}"><option value="">Sem dono (só admin)</option>${pr.map((x) => `<option value="${esc(x.id)}" ${x.id === d.ownerId ? "selected" : ""}>${esc(x.name)}</option>`).join("")}</select></article>`).join("")}`,
  );
  $("#nu").onsubmit = async (e) => {
    e.preventDefault();
    try {
      await j("/api/users", {
        method: "POST",
        body: JSON.stringify(Object.fromEntries(new FormData(e.target))),
      });
      usuarios();
    } catch (x) {
      mostrarAviso($("#nu-m"), x.message, "error");
    }
  };
  mb.querySelectorAll("[data-pw]").forEach(
    (b) =>
      (b.onclick = async () => {
        const p = await askText(
          "Redefinir senha",
          "Nova senha temporária (mín. 8 caracteres)",
        );
        if (!p) return;
        try {
          await j(`/api/users/${b.dataset.pw}/password`, {
            method: "PUT",
            body: JSON.stringify({ password: p }),
          });
          notify("Senha redefinida.");
        } catch (x) {
          notify(x.message);
        }
      }),
  );
  mb.querySelectorAll("[data-own]").forEach(
    (s) =>
      (s.onchange = async () => {
        try {
          await j("/api/disciplines/" + s.dataset.own, {
            method: "PUT",
            body: JSON.stringify({ ownerId: s.value }),
          });
        } catch (x) {
          notify(x.message);
        }
      }),
  );
}

export { turmas, usuarios, minhaSenha, notify };
