(() => {
  const $ = (s) => document.querySelector(s),
    esc = (v) =>
      String(v ?? "").replace(
        /[&<>"']/g,
        (c) =>
          ({
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#39;",
          })[c],
      );
  const real = window.fetch.bind(window),
    app = $("#app-modal"),
    mb = $("#modal-body");
  let me = null,
    owners = {};
  const j = async (u, o = {}) => {
    const r = await fetch(u, {
      headers: { "Content-Type": "application/json" },
      ...o,
    });
    const d = await r.json().catch(() => ({}));
    if (!r.ok) throw Error(d.error || "Erro " + r.status);
    return d;
  };
  const note = (t, k = "") =>
    `<div class="notice ${k}" role="status">${esc(t)}</div>`;
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
  // fetch com cookie de sessão; 401 abre a tela de login; guarda o dono de cada matéria
  const NOAPI =
    "Não foi possível se conectar ao servidor da plataforma. Para usar a plataforma localmente, execute iniciar.bat e abra http://127.0.0.1:3002/acesso.html.";
  const noapi = () =>
    new Response(JSON.stringify({ error: NOAPI }), {
      status: 503,
      headers: { "Content-Type": "application/json" },
    });
  window.fetch = async (u, o = {}) => {
    const s = String(u);
    let r;
    try {
      r = await real(u, { credentials: "same-origin", ...o });
    } catch (e) {
      if (s.startsWith("/api/")) return noapi();
      throw e;
    }
    if (
      s.startsWith("/api/") &&
      r.status === 404 &&
      !(r.headers.get("content-type") || "").includes("json")
    )
      return noapi();
    if (
      s.startsWith("/api/") &&
      !s.startsWith("/api/auth") &&
      !s.startsWith("/api/public")
    ) {
      if (r.status === 401) showLogin();
      if (s === "/api/disciplines" && r.ok)
        r.clone()
          .json()
          .then((l) => {
            owners = {};
            l.forEach((d) => (owners[d.id] = d.ownerId));
            apply();
          })
          .catch(() => {});
    }
    return r;
  };
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
        .querySelectorAll("#lv-new,[data-new]")
        .forEach((e) => (e.hidden = true));
      mb.querySelectorAll(".form-actions button").forEach((b) => {
        if (/Adicionar disciplina/.test(b.textContent)) b.hidden = true;
      });
    }
    document.querySelectorAll("#lv-cards [data-manage]").forEach((b) => {
      if (!can(b.dataset.manage)) b.hidden = true;
    });
    if (!adm && /Comunicados/.test($("#modal-title").textContent))
      mb.querySelectorAll("[data-del],:scope > button").forEach(
        (b) => (b.hidden = true),
      );
  }
  new MutationObserver(apply).observe(document.body, {
    childList: true,
    subtree: true,
  });
  function showLogin() {
    location.replace("/acesso.html?motivo=sessao");
  }
  const open = (t, h) => {
    $("#modal-title").textContent = t;
    mb.innerHTML = h;
    if (!app.open) app.showModal();
  };
  // ---- Fluxo: Matéria > Atividades > Política (com descrições) ----
  const LB = {
      proibido: ["Proibido", "red"],
      restricao: ["Com restrição", "yellow"],
      permitido: ["Permitido", "green"],
    },
    TL = {
      prova: "Prova",
      trabalho: "Trabalho",
      atividade: "Atividade",
      pesquisa: "Pesquisa",
      outro: "Outro",
    };
  const vl = $("#view-list"),
    lvSec = vl.querySelector('[aria-labelledby="lv-h"]'),
    lvHead = vl.querySelector("header.hero");
  vl.insertAdjacentHTML(
    "beforeend",
    '<section id="flow" hidden aria-label="Consulta da matéria"></section>',
  );
  const flow = $("#flow");
  let F = null,
    ftok = 0;
  const fdate = (s) => {
    const d = new Date(s);
    return isNaN(d) ? "" : d.toLocaleDateString("pt-BR");
  };
  const pill = (s) => `<span class="pill ${LB[s][1]}">${LB[s][0]}</span>`;
  function closeFlow() {
    F = null;
    ftok++;
    flow.hidden = true;
    flow.innerHTML = "";
    lvSec.hidden = false;
    lvHead.hidden = false;
  }
  async function loadFlow(id, quiet) {
    const tok = ++ftok;
    if (!quiet)
      flow.innerHTML =
        '<div class="records-empty" role="status" aria-busy="true">Carregando matéria…</div>';
    try {
      const [d, all] = await Promise.all([
        j("/api/disciplines/" + encodeURIComponent(id)),
        j("/api/disciplines").catch(() => []),
      ]);
      if (tok !== ftok) return;
      owners[id] = d.ownerId;
      F.data = d;
      F.all = all;
      renderFlow(!quiet);
    } catch (x) {
      if (tok !== ftok) return;
      if (quiet) {
        closeFlow();
        return;
      }
      flow.innerHTML = `<div class="notice error" role="alert">Não foi possível carregar a matéria: ${esc(x.message)} <button class="mini" type="button" id="f-retry">Tentar novamente</button> <button class="mini" type="button" id="f-back">Voltar à lista</button></div>`;
      $("#f-retry").onclick = () => loadFlow(id);
      $("#f-back").onclick = closeFlow;
    }
  }
  function openDisc(id) {
    lvSec.hidden = true;
    lvHead.hidden = true;
    flow.hidden = false;
    F = { id, mode: "atividades", pid: null, data: null, all: [] };
    scrollTo({ top: 0 });
    loadFlow(id);
  }
  function renderFlow(focus) {
    const d = F.data,
      ps = d.policies || [],
      pol = F.pid && ps.find((p) => p.id === F.pid);
    if (F.pid && !pol) F.pid = null;
    const meta = [
      d.code && "Código: " + d.code,
      d.instructor && "Docente: " + d.instructor,
    ]
      .filter(Boolean)
      .map(esc)
      .join(" · ");
    const crumbs = `<nav aria-label="Você está em"><ol class="crumbs"><li><button class="linkbtn" type="button" data-f="list">Lista de matérias</button></li><li>${pol ? `<button class="linkbtn" type="button" data-f="disc">${esc(d.name)}</button>` : `<span aria-current="page">${esc(d.name)}</span>`}</li>${pol ? `<li><span aria-current="page">${esc(pol.activityName)}</span></li>` : ""}</ol></nav>`;
    const sw =
      F.all.length > 1
        ? `<label class="sr-only" for="f-sw">Trocar de matéria</label><select class="filter-discipline search" id="f-sw">${F.all.map((x) => `<option value="${esc(x.id)}" ${x.id === d.id ? "selected" : ""}>${esc(x.name)}</option>`).join("")}</select>`
        : "";
    let html = crumbs;
    if (!pol) {
      const list =
        F.mode === "atividades"
          ? ps.length
            ? ps
                .map((p) => {
                  const ex = p.conditions || p.details || "";
                  return `<button class="act aitem" type="button" data-p="${esc(p.id)}" aria-label="Abrir a política da atividade ${esc(p.activityName)}, ${LB[p.status][0]}"><div><b>${esc(p.activityName)}</b><small>${esc(TL[p.activityType] || p.activityType)}</small>${ex ? `<small>${esc(ex.length > 110 ? ex.slice(0, 110) + "…" : ex)}</small>` : ""}</div>${pill(p.status)}</button>`;
                })
                .join("")
            : '<p class="records-empty" role="status">Esta matéria ainda não tem atividades cadastradas.</p>'
          : ps.length
            ? ps
                .map(
                  (p) =>
                    `<details class="pol"><summary><span><b>${esc(p.activityName)}</b> · ${esc(TL[p.activityType] || p.activityType)}</span>${pill(p.status)}</summary><dl class="pdl">${polBody(p)}</dl></details>`,
                )
                .join("")
            : '<p class="records-empty" role="status">Esta matéria ainda não tem políticas cadastradas.</p>';
      html += `<section class="tgroup" aria-labelledby="f-h"><div class="tg-head"><h2 id="f-h" tabindex="-1" class="discipline-title">${esc(d.name)}</h2>${can(d.id) ? `<button class="mini" type="button" data-fmanage>Gerenciar políticas</button>` : ""}</div>${meta ? `<div class="ctxbar">${meta}</div>` : ""}<div class="manage-head"><div class="no-margin chips" role="group" aria-label="Modo de consulta"><button class="chip" type="button" data-mode="atividades" aria-pressed="${F.mode === "atividades"}">Atividades (${ps.length})</button><button class="chip" type="button" data-mode="politicas" aria-pressed="${F.mode === "politicas"}">Todas as políticas</button></div>${sw}</div><div aria-live="polite">${list}</div></section>`;
    } else {
      const i = ps.indexOf(pol);
      html += `<article class="tgroup" aria-labelledby="f-h"><div class="ctxbar"><span>Matéria: <b>${esc(d.name)}</b></span><span>Atividade: <b>${esc(pol.activityName)}</b> (${esc(TL[pol.activityType] || pol.activityType)})</span></div><h2 id="f-h" tabindex="-1" class="discipline-title">Política · ${esc(pol.activityName)}</h2><div>${pill(pol.status).replace('">', '">Uso de IA: ')}</div><dl class="pdl">${polBody(pol)}</dl><div class="fnav"><button class="btn" type="button" data-f="disc">← Atividades de ${esc(d.name)}</button><span class="row-actions"><button class="btn" type="button" data-nav="-1" ${i <= 0 ? "disabled" : ""}>‹ Anterior</button><button class="btn" type="button" data-nav="1" ${i >= ps.length - 1 ? "disabled" : ""}>Próxima ›</button></span></div></article>`;
    }
    flow.innerHTML = html;
    flow
      .querySelectorAll("[data-f]")
      .forEach(
        (b) =>
          (b.onclick = () =>
            b.dataset.f === "list"
              ? closeFlow()
              : ((F.pid = null), renderFlow(true))),
      );
    flow.querySelectorAll("[data-p]").forEach(
      (b) =>
        (b.onclick = () => {
          F.pid = b.dataset.p;
          renderFlow(true);
          scrollTo({ top: 0 });
        }),
    );
    flow.querySelectorAll("[data-mode]").forEach(
      (b) =>
        (b.onclick = () => {
          F.mode = b.dataset.mode;
          renderFlow(false);
          flow.querySelector(`[data-mode="${F.mode}"]`).focus();
        }),
    );
    flow.querySelectorAll("[data-nav]").forEach(
      (b) =>
        (b.onclick = () => {
          F.pid = ps[ps.indexOf(pol) + Number(b.dataset.nav)].id;
          renderFlow(true);
        }),
    );
    const s = flow.querySelector("#f-sw");
    if (s)
      s.onchange = () => {
        F = {
          id: s.value,
          mode: "atividades",
          pid: null,
          data: null,
          all: F.all,
        };
        loadFlow(s.value);
      };
    const mg = flow.querySelector("[data-fmanage]");
    if (mg)
      mg.onclick = () => {
        const o = document.querySelector(`#lv-cards [data-manage="${d.id}"]`);
        if (o) o.click();
      };
    if (focus) {
      const hd = $("#f-h");
      if (hd) hd.focus({ preventScroll: false });
    }
  }
  function polBody(p) {
    const t = (k, l) =>
      `<dt>${l}</dt><dd>${p[k] ? esc(p[k]) : '<span class="none">Sem descrição cadastrada.</span>'}</dd>`;
    return (
      t("conditions", "Condições") +
      t("details", "Detalhes") +
      (p.source ? `<dt>Fonte</dt><dd>${esc(p.source)}</dd>` : "") +
      (fdate(p.updatedAt)
        ? `<dt>Atualizada em</dt><dd>${fdate(p.updatedAt)}</dd>`
        : "")
    );
  }
  $("#lv-cards").addEventListener("click", (e) => {
    const b = e.target.closest("[data-consult]");
    if (b) openDisc(b.dataset.consult);
  });
  document.addEventListener(
    "click",
    (e) => {
      const a = e.target.closest(".nav a,.back-link");
      if (
        F &&
        a &&
        /Lista de matérias|Início|Voltar ao início/.test(a.textContent)
      )
        closeFlow();
    },
    true,
  );
  app.addEventListener("close", () => {
    if (F && !flow.hidden) loadFlow(F.id, true);
  });
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
        m.innerHTML = note("As senhas novas não são iguais.", "error");
        return;
      }
      try {
        await j("/api/me/password", { method: "PUT", body: JSON.stringify(f) });
        m.innerHTML = note(
          "Senha alterada. Suas outras sessões foram encerradas.",
          "success",
        );
        e.target.reset();
      } catch (x) {
        m.innerHTML = note(x.message, "error");
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
  // painel de matérias agrupado por turma (aluno e professor)
  let gtok = 0,
    tcache = null;
  const expanded = new Set();
  window.__afterList = async () => {
    const box = $("#lv-cards");
    box.classList.remove("grouped");
    if (!me || me.role === "admin") return;
    const my = ++gtok;
    let ts;
    try {
      ts =
        tcache && Date.now() - tcache.at < 15000
          ? tcache.v
          : await j("/api/turmas");
      tcache = { at: Date.now(), v: ts };
    } catch {
      return;
    }
    if (my !== gtok) return;
    const byId = {};
    box.querySelectorAll(".mcard").forEach((c) => {
      const b = c.querySelector("[data-manage]");
      if (b) byId[b.dataset.manage] = c;
    });
    if (!Object.keys(byId).length) return;
    const used = new Set(),
      frag = document.createDocumentFragment();
    const block = (title, ids, key) => {
      const sec = document.createElement("section");
      sec.className = "tgroup";
      sec.setAttribute("aria-label", title);
      sec.innerHTML = `<div class="tg-head"><h3>${esc(title)}</h3><span class="tg-sub">${ids.length} matéria${ids.length === 1 ? "" : "s"}</span></div><div class="cards"></div>`;
      const grid = sec.querySelector(".cards"),
        cs = ids.map((id) => {
          const o = byId[id];
          used.add(id);
          const c = o.cloneNode(true),
            ob = o.querySelector("[data-manage]"),
            cb = c.querySelector("[data-manage]");
          if (cb) cb.onclick = () => ob.click();
          return c;
        });
      if (cs.length <= 2) {
        grid.replaceChildren(...cs);
        return sec;
      }
      grid.id = "tg-" + key;
      const foot = document.createElement("div"),
        tg = document.createElement("button");
      foot.className = "mcard-foot";
      tg.type = "button";
      tg.className = "mini";
      tg.setAttribute("aria-controls", grid.id);
      foot.appendChild(tg);
      sec.appendChild(foot);
      const draw = () => {
        const open = expanded.has(key);
        grid.replaceChildren(...(open ? cs : cs.slice(0, 2)));
        tg.textContent = open ? "Mostrar menos" : "Ver todas as matérias";
        tg.setAttribute("aria-expanded", String(open));
      };
      tg.onclick = () => {
        expanded.has(key) ? expanded.delete(key) : expanded.add(key);
        draw();
      };
      draw();
      return sec;
    };
    ts.filter((t) => me.role !== "aluno" || t.status === "aprovada").forEach(
      (t) => {
        const ids = t.disciplines.map((d) => d.id).filter((id) => byId[id]);
        if (ids.length) frag.appendChild(block("Turma " + t.name, ids, t.id));
      },
    );
    const rest = Object.keys(byId).filter((id) => !used.has(id));
    if (rest.length)
      frag.appendChild(block("Sem turma vinculada", rest, "sem-turma"));
    box.replaceChildren(frag);
    box.classList.add("grouped");
    apply();
  };
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
        $("#nu-m").innerHTML = note(x.message, "error");
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
  real("/api/me", { credentials: "same-origin" })
    .then((r) => {
      if (r.status === 401) {
        showLogin();
        return null;
      }
      return r.ok ? r.json() : null;
    })
    .then((u) => {
      if (!u) return;
      me = u;
      if (u.role !== "admin") {
        window.__noDisc = "Não há matérias disponíveis para o seu perfil.";
        window.__emptyList =
          u.role === "aluno"
            ? "Nenhuma matéria liberada para a sua turma até o momento."
            : "Nenhuma matéria atribuída a você até o momento.";
      }
      const ini = u.name
          .split(/\s+/)
          .map((w) => w[0])
          .slice(0, 2)
          .join("")
          .toUpperCase(),
        av = $(".avatar");
      if (av) av.textContent = ini;
      $(".sidebar-bottom").insertAdjacentHTML(
        "beforeend",
        `<div class="who"><span><b>${esc(u.name)}</b> · ${esc(u.role)}</span><button class="mini" type="button" id="logout">Sair</button></div>`,
      );
      const doLogout = async () => {
        await real("/api/auth/logout", {
          method: "POST",
          credentials: "same-origin",
        });
        location.reload();
      };
      $("#logout").onclick = doLogout;
      const ub = $("#userbar");
      ub.innerHTML = `<span class="ub-name"><b>${esc(u.name)}</b> · ${esc(u.role)}</span><button class="mini" type="button" id="pwd-btn">Alterar senha</button><button class="mini pri" type="button" id="logout-top">Sair</button>`;
      ub.hidden = false;
      $("#pwd-btn").onclick = minhaSenha;
      $("#logout-top").onclick = doLogout;
      // menu por perfil
      const links = [...document.querySelectorAll(".sidebar .nav a")],
        hide = (t) =>
          links
            .filter((a) => a.textContent.includes(t))
            .forEach((a) => (a.hidden = true)),
        grp = document.querySelectorAll(".sidebar .nav")[2].parentElement;
      if (u.role !== "admin") {
        hide("Todas as políticas");
        hide("Ferramentas");
        document.querySelectorAll(".quick-card").forEach((c) => {
          if (/Nova política/.test(c.textContent)) c.hidden = true;
        });
        document
          .querySelectorAll('.section-head .text-link[href="#atalhos"]')
          .forEach((c) => (c.hidden = true));
      }
      if (u.role === "aluno") {
        hide("Histórico");
        document.querySelectorAll(".quick-card").forEach((c) => {
          if (/histórico/i.test(c.textContent)) c.hidden = true;
        });
      }
      const items =
        u.role === "aluno"
          ? [["turmas", "Minha turma"]]
          : [["turmas", "Turmas e alunos"]].concat(
              u.role === "admin" ? [["usuarios", "Usuários e donos"]] : [],
            );
      grp.insertAdjacentHTML(
        "beforebegin",
        `<div><p class="nav-group-label">${u.role === "aluno" ? "Minha área" : "Gestão"}</p><nav class="nav">${items.map((x) => `<a href="#${x[0]}" data-x="${x[0]}"><span class="ico">${x[0] === "usuarios" ? "☺" : "☷"}</span>${x[1]}</a>`).join("")}</nav></div>`,
      );
      document.querySelectorAll("[data-x]").forEach((a) =>
        a.addEventListener("click", (e) => {
          e.preventDefault();
          document.body.classList.remove("mobile-menu-open");
          (a.dataset.x === "turmas" ? turmas : usuarios)().catch((x) =>
            notify(x.message),
          );
        }),
      );
      apply();
    });
})();
