import { escapeHtml as e } from "/js/api.js";

export const roles = {
  admin: "Administrador",
  professor: "Professor",
  aluno: "Estudante",
};
export const levels = {
  permitido: ["Permitido", "allowed"],
  restricao: ["Com restrição", "restricted"],
  proibido: ["Proibido", "prohibited"],
};
export const action = (key, label, primary = false) =>
  `<button class="btn ${primary ? "primary" : ""}" type="button" data-action="${e(key)}">${e(label)}</button>`;
const heading = (section, title, description, buttons = "") =>
  `<header class="page-head"><div><span class="eyebrow">${e(section)}</span><h1>${e(title)}</h1><p>${e(description)}</p></div><div class="page-actions">${buttons}</div></header>`;
const section = (title, content) =>
  `<article class="card card-pad"><div class="section-head"><h2>${e(title)}</h2></div>${content}</article>`;
const row = (icon, title, detail) =>
  `<div class="dashboard-row"><div class="dashboard-row-main"><span class="dashboard-row-icon"><svg class="icon" aria-hidden="true"><use href="#icon-${icon}"/></svg></span><div><strong>${e(title)}</strong><small>${e(detail)}</small></div></div></div>`;
const stat = (label, value, note) =>
  `<article class="card stat"><span class="stat-label">${e(label)}</span><strong class="stat-value">${value}</strong><span class="stat-note">${e(note)}</span></article>`;
const empty = (label) => `<p class="records-empty">${e(label)}</p>`;
const badge = (status) =>
  `<span class="tag ${levels[status][1]}">${levels[status][0]}</span>`;
const writable = (u, d) =>
  u.role === "admin" || (u.role === "professor" && u.id === d.ownerId);

export function home({ user, dashboard, disciplines, turmas }) {
  const counts = dashboard.distribution;
  const staff = user.role !== "aluno";
  return (
    heading(
      roles[user.role],
      "Olá, " + user.name,
      "Acompanhe as disciplinas, políticas e comunicações do seu ambiente acadêmico.",
      action("check", "Posso usar IA?", true) +
        (staff ? action("new-policy", "Nova política") : ""),
    ) +
    `<section class="dashboard-banner ${user.role}"><span class="dashboard-banner-icon"><svg class="icon" aria-hidden="true"><use href="#icon-book"/></svg></span><div><h2>Políticas de uso de IA</h2><p>Confira as regras de uma atividade antes de começar.</p></div>${action("disciplines", "Consultar disciplinas")}</section>
    <section class="grid stats-grid">${stat("Disciplinas", dashboard.disciplines, "Visíveis ao seu perfil")}${stat("Políticas", dashboard.policies, "Regras cadastradas")}${stat("Turmas", turmas.length, staff ? "Disponíveis para gestão" : "Minhas matrículas")}${stat("Com restrição", counts.restricao, "Atividades com condições de uso")}</section>
    <section class="grid two-col dashboard-section">${section(
      "Disciplinas",
      disciplines
        .slice(0, 4)
        .map((d) => row("book", d.name, d.code || d.instructor))
        .join("") || empty("Nenhuma disciplina disponível."),
    )}${section("Comunicados", dashboard.announcements.map((a) => row("bell", a.title, a.message)).join("") || empty("Nenhum comunicado publicado."))}</section>`
  );
}
export function disciplineView({ user }) {
  return (
    heading(
      "Consultar",
      "Disciplinas e políticas",
      "Consulte as atividades, condições e fontes de cada disciplina.",
      (user.role === "admin" ? action("new", "Nova disciplina") : "") +
        (user.role !== "aluno"
          ? action("new-policy", "Nova política", true)
          : ""),
    ) +
    `<div class="toolbar"><div class="field search-field"><label for="search">Buscar disciplina ou atividade</label><input id="search" type="search"></div><div class="field"><label for="level">Uso de IA</label><select id="level"><option value="">Todos</option>${Object.entries(
      levels,
    )
      .map(([key, [label]]) => `<option value="${key}">${label}</option>`)
      .join(
        "",
      )}</select></div></div><div class="grid two-col" id="discipline-list"></div>`
  );
}
export function cards({ user, disciplines, policies }, search, level) {
  const query = search.trim().toLocaleLowerCase("pt-BR");
  return (
    disciplines
      .map((d) => {
        const matches = [d.name, d.code, d.instructor]
          .join(" ")
          .toLocaleLowerCase("pt-BR")
          .includes(query);
        const all = policies.filter((p) => p.disciplineId === d.id);
        const filtered = all.filter(
          (p) =>
            (!level || p.status === level) &&
            (matches ||
              p.activityName.toLocaleLowerCase("pt-BR").includes(query)),
        );
        if (!filtered.length && (level || !matches)) return "";
        return `<article class="card discipline-card"><div class="section-head"><div><span class="tag">${e(d.code || "Disciplina")}</span><h2>${e(d.name)}</h2></div><span class="tag">${all.length} política(s)</span></div><p>${e(d.instructor || d.ownerName || "")}</p><div class="policy-mini">${filtered.map((p) => `<div><span>${e(p.activityName)}</span>${badge(p.status)}</div>`).join("") || empty("Nenhuma política cadastrada.")}</div><div class="discipline-actions">${action("details:" + d.id, "Ver detalhes")}${writable(user, d) ? action("manage:" + d.id, "Gerenciar políticas", true) : ""}</div></article>`;
      })
      .join("") || empty("Nenhuma disciplina encontrada.")
  );
}
export function policyDetails(policies) {
  return (
    policies
      .map(
        (p) =>
          `<article class="card card-pad"><div class="section-head"><h3>${e(p.activityName)}</h3>${badge(p.status)}</div><p>${e(p.conditions)}</p><p>${e(p.details)}</p><small>Fonte · ${e(p.source || "Não informada")}</small></article>`,
      )
      .join("") || empty("Nenhuma política cadastrada.")
  );
}
export function reports({ disciplines, policies }) {
  const missing = disciplines.filter(
    (d) => !policies.some((p) => p.disciplineId === d.id),
  );
  const noSource = policies.filter((p) => !p.source?.trim());
  return (
    heading(
      "Acompanhamento",
      "Clareza das políticas",
      "Identifique orientações que precisam de revisão.",
    ) +
    `<section class="grid two-col">${section("Disciplinas sem política", missing.map((d) => row("book", d.name, d.code)).join("") || empty("Todas as disciplinas visíveis têm políticas, ou ainda não há disciplinas."))}${section("Políticas sem fonte", noSource.map((p) => row("chart", p.activityName, p.disciplineName)).join("") || empty("Nenhuma política sem fonte."))}</section>`
  );
}
export function reflection() {
  return (
    heading(
      "Apoio ao estudante",
      "Plano de uso responsável",
      "Antes de usar IA, confira os cuidados e prepare sua declaração.",
    ) +
    `<section class="grid two-col">${section("Antes de usar uma ferramenta de IA", ["Li a política da atividade", "Defini o objetivo do apoio", "Vou verificar fatos e referências", "Sei como declarar o uso"].map((label) => `<label class="check-row"><input type="checkbox" name="care"><strong>${label}</strong></label>`).join(""))}${section("Rascunho de declaração", '<div class="field"><label for="purpose">Como a ferramenta ajudou?</label><textarea id="purpose"></textarea></div><div class="field"><label for="review">O que você verificou ou modificou?</label><textarea id="review"></textarea></div><output class="declaration-preview" id="preview"></output>' + action("download", "Baixar declaração"))}</section>`
  );
}
