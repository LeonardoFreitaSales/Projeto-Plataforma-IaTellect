import { request, escapeHtml as e } from "/js/api.js";
import { newPolicy } from "/js/nova-politica.js";
import { enableAuth } from "/js/acesso.js";
import {
  aiCheck,
  auditHistory,
  announcements,
  manageDisciplineForm,
  manageDiscipline,
  show,
} from "/js/painel.js";
import {
  configure,
  turmas,
  usuarios,
  minhaSenha,
  notify,
} from "/js/painel-disciplinas.js";
import {
  roles,
  levels,
  home,
  disciplineView,
  cards,
  reports,
  reflection,
  policyDetails,
  action,
} from "./vistas.js";

const $ = (selector) => document.querySelector(selector);
const root = $("#view-root");
const state = {
  user: null,
  disciplines: [],
  policies: [],
  turmas: [],
  dashboard: null,
};
let current = "home",
  revision = 0;
const draft = { purpose: "", review: "", checks: [] };
const available = (view) =>
  (view !== "users" || state.user.role === "admin") &&
  (!["reports", "history"].includes(view) || state.user.role !== "aluno");
const sections = {
  classes: ["Turmas e matrículas", "Consultar matrículas", turmas],
  users: [
    "Usuários e acessos",
    "Gerenciar professores e responsáveis",
    usuarios,
  ],
  announcements: ["Comunicados", "Gerenciar comunicados", announcements],
  history: ["Histórico", "Filtrar histórico", auditHistory],
};

function paintCards() {
  $("#discipline-list").innerHTML = cards(
    state,
    $("#search").value,
    $("#level").value,
  );
}
function declaration() {
  return [
    draft.purpose && "Utilizei IA para " + draft.purpose,
    draft.review && "Minha revisão: " + draft.review,
  ]
    .filter(Boolean)
    .join("\n");
}
function bindReflection() {
  $("#purpose").value = draft.purpose;
  $("#review").value = draft.review;
  $("#preview").textContent = declaration();
  for (const key of ["purpose", "review"])
    $("#" + key).oninput = (event) => {
      draft[key] = event.target.value;
      $("#preview").textContent = declaration();
    };
  root.querySelectorAll("[name=care]").forEach((box, i) => {
    box.checked = Boolean(draft.checks[i]);
    box.onchange = () => {
      draft.checks[i] = box.checked;
    };
  });
}
async function section(view) {
  const [title, label] = sections[view];
  let items;
  if (view === "classes")
    items = state.turmas.map((t) => [
      t.name,
      t.status
        ? "Matrícula · " + t.status
        : (t.pendentes || 0) + " matrícula(s) pendente(s)",
      t.disciplines.map((d) => d.name).join(" · "),
    ]);
  if (view === "users")
    items = (await request("/api/users")).map((u) => [u.name, roles[u.role]]);
  if (view === "history")
    items = (await request("/api/history")).map((h) => [
      h.summary || h.description || h.action,
      new Date(h.createdAt).toLocaleString("pt-BR"),
    ]);
  if (view === "announcements")
    items = (
      await request(
        "/api/announcements" + (state.user.role === "admin" ? "?all=true" : ""),
      )
    ).map((a) => [a.title, a.message, a.active ? "" : "Inativo"]);
  const button =
    view !== "announcements" || state.user.role === "admin"
      ? action("section", label, true)
      : "";
  return `<header class="page-head"><h1>${title}</h1><div class="page-actions">${button}</div></header><section class="grid two-col">${items.map(([title, detail, meta]) => `<article class="card card-pad"><h2>${e(title)}</h2><p>${e(detail)}</p><small>${e(meta)}</small></article>`).join("") || '<p class="records-empty">Nenhum registro disponível.</p>'}</section>`;
}

const viewResources = {
  home: ["dashboard", "disciplines", "turmas"],
  disciplines: ["disciplines", "policies"],
  reports: ["disciplines", "policies"],
  classes: ["turmas"],
};

async function navigate(view) {
  if (!available(view)) return;
  current = view;
  const ticket = ++revision;
  document.body.classList.remove("menu-open");
  $("#mobile-menu").setAttribute("aria-expanded", "false");
  document.querySelectorAll("[data-view]").forEach((b) => {
    const active = b.dataset.view === view;
    b.classList.toggle("active", active);
    if (active) b.setAttribute("aria-current", "page");
    else b.removeAttribute("aria-current");
    if (active)
      $("#assistant-context").textContent =
        "Nesta tela · " + b.textContent.trim();
  });
  root.textContent = "Carregando…";
  try {
    const resources = viewResources[view] || [];
    const entries = await Promise.all(resources.map(async key => [key, await request("/api/" + key)]));
    if (revision !== ticket) return;
    Object.assign(state, Object.fromEntries(entries));
    if (resources.includes("disciplines")) configure(state.user, state.disciplines);
    if (resources.includes("turmas")) {
      const pending = state.turmas.reduce((n, t) => n + (t.pendentes || 0), 0);
      $("[data-pending-count]").textContent = pending;
      $("[data-pending-count]").hidden = !pending;
    }
    const markup = sections[view]
      ? await section(view)
      : { home, disciplines: disciplineView, reports, responsible: reflection }[
          view
        ](state);
    if (revision !== ticket) return;
    root.innerHTML = markup;
    if (view === "disciplines") {
      paintCards();
      $("#search").oninput = paintCards;
      $("#level").onchange = paintCards;
    }
    if (view === "responsible") bindReflection();
  } catch (error) {
    if (revision === ticket)
      root.innerHTML = `<p role="alert">${e(error.message)}</p>${action("retry", "Tentar novamente")}`;
  }
}
async function enter(user) {
  state.user = user;
  configure(user, []);
  document.body.classList.add("authenticated");
  $("#auth-screen").hidden = true;
  $("#app-shell").hidden = false;
  $("#assistant-toggle").hidden = false;
  $("#skip-link").href = "#main-content";
  $(".topbar-title span").textContent = user.name + " · " + roles[user.role];
  $(".avatar").textContent = user.name
    .split(/\s+/)
    .slice(0, 2)
    .map((s) => s[0])
    .join("")
    .toUpperCase();
  document.querySelectorAll("[data-view]").forEach((b) => {
    b.parentNode.hidden = !available(b.dataset.view);
  });
  await navigate("home");
  $("#main-content").focus();
}
document.querySelectorAll("[data-view]").forEach((b) => {
  b.onclick = () => navigate(b.dataset.view);
});
$("#app-modal").addEventListener("close", () => {
  if (state.user) navigate(current);
});
root.onclick = async (event) => {
  const key = event.target.closest("[data-action]")?.dataset.action;
  if (!key) return;
  const [op, id] = key.split(":");
  try {
    if (op === "details")
      show(
        state.disciplines.find((d) => d.id === id).name,
        policyDetails(state.policies.filter((p) => p.disciplineId === id)),
      );
    if (op === "manage") await manageDiscipline(id);
    if (op === "new-policy") newPolicy(state.user, state.disciplines);
    if (op === "new") manageDisciplineForm();
    if (op === "check") await aiCheck();
    if (op === "section") await sections[current][2]();
    if (op === "retry") await navigate(current);
    if (op === "disciplines") await navigate(op);
    if (op === "download") {
      if (!declaration())
        return notify("Preencha a finalidade ou a revisão antes de baixar.");
      const url = URL.createObjectURL(
        new Blob([declaration()], { type: "text/plain;charset=utf-8" }),
      );
      const link = document.createElement("a");
      link.href = url;
      link.download = "declaracao-de-uso.txt";
      link.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    }
  } catch (error) {
    notify(error.message);
  }
};
$("#logout-button").onclick = async () => {
  try {
    await request("/api/auth/logout", { method: "POST" });
    location.replace("/acesso.html");
  } catch (error) {
    notify(error.message);
  }
};
$("#change-password").onclick = minhaSenha;
$(".notification-button").onclick = () => navigate("announcements");
$("#mobile-menu").onclick = () =>
  $("#mobile-menu").setAttribute(
    "aria-expanded",
    String(document.body.classList.toggle("menu-open")),
  );
function chat(open) {
  $("#assistant-panel").hidden = !open;
  $("#assistant-toggle").setAttribute("aria-expanded", String(open));
  (open ? $("#chat-input") : $("#assistant-toggle")).focus();
}
$("#assistant-toggle").onclick = () => chat($("#assistant-panel").hidden);
$("#assistant-close").onclick = () => chat(false);
$("#assistant-clear").onclick = () => $("#chat-log").replaceChildren();
$("#chat-form").onsubmit = async (event) => {
  event.preventDefault();
  const input = $("#chat-input"),
    query = input.value.trim();
  if (!query) return;
  function message(value, user = false) {
    const el = document.createElement("div");
    el.className = user ? "message user" : "message";
    el.textContent = value;
    $("#chat-log").append(el);
    el.scrollIntoView({ block: "nearest" });
  }
  message(query, true);
  input.value = "";
  try {
    const policies = await request("/api/policies");
    const words = query.toLocaleLowerCase("pt-BR").match(/[\p{L}\d]+/gu) || [];
    const matches = policies.filter((p) =>
      words.some(
        (w) =>
          w.length > 2 &&
          ![
            "posso",
            "usar",
            "para",
            "uma",
            "com",
            "qual",
            "sobre",
            "disciplina",
            "atividade",
          ].includes(w) &&
          [p.disciplineName, p.activityName].some((s) =>
            s?.toLocaleLowerCase("pt-BR").includes(w),
          ),
      ),
    );
    if (!matches.length)
      message(
        "Nenhuma política correspondente. Digite o nome da disciplina ou da atividade.",
      );
    matches
      .slice(0, 8)
      .forEach((p) =>
        message(
          [
            p.disciplineName + " · " + p.activityName,
            levels[p.status][0],
            p.conditions,
            p.source && "Fonte: " + p.source,
          ]
            .filter(Boolean)
            .join("\n"),
        ),
      );
  } catch (error) {
    message(error.message);
  }
};
document.addEventListener("keydown", (event) => {
  if (event.key !== "Escape") return;
  if (!$("#assistant-panel").hidden) chat(false);
  document.body.classList.remove("menu-open");
  $("#mobile-menu").setAttribute("aria-expanded", "false");
});
enableAuth(enter);
$("#login-message").textContent = new URLSearchParams(location.search).has(
  "motivo",
)
  ? "Faça login para continuar."
  : "";
try {
  await enter(await request("/api/me"));
} catch (error) {
  if (error.status !== 401) $("#login-message").textContent = error.message;
}
