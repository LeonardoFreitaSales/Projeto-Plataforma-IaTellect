import { request, escapeHtml as e } from "./api.js";
import { show } from "./painel.js";
import { notify } from "./painel-disciplinas.js";

const steps = ["Contexto", "Decisão", "Condições", "Fonte", "Revisão"];
const types = {
  trabalho: "Trabalho",
  prova: "Prova",
  atividade: "Atividade",
  pesquisa: "Pesquisa",
  outro: "Outro",
};
const levels = {
  permitido: "Permitido",
  restricao: "Com restrições",
  proibido: "Proibido",
};
let draft = null;

export function newPolicy(user, disciplines) {
  const allowed = disciplines.filter(
    (d) => user.role === "admin" || d.ownerId === user.id,
  );
  if (!allowed.length)
    return notify(
      "É preciso ter uma disciplina sob sua responsabilidade para publicar uma política.",
    );
  let step = 0;
  const data = {
    ...{
      disciplineId: allowed[0].id,
      activityType: "trabalho",
      activityName: "",
      status: "restricao",
      conditions: "",
      details: "",
      source: "",
    },
    ...draft,
  };
  if (!allowed.some((d) => d.id === data.disciplineId))
    data.disciplineId = allowed[0].id;
  const select = (key, options) =>
    Object.entries(options)
      .map(
        ([value, label]) =>
          `<option value="${e(value)}" ${data[key] === value ? "selected" : ""}>${e(label)}</option>`,
      )
      .join("");
  const field = (label, control) =>
    `<label class="field"><span>${label}</span>${control}</label>`;
  function panel() {
    if (step === 0)
      return (
        field(
          "Disciplina",
          `<select name="disciplineId">${select("disciplineId", Object.fromEntries(allowed.map((d) => [d.id, d.name])))}</select>`,
        ) +
        field(
          "Tipo de atividade",
          `<select name="activityType">${select("activityType", types)}</select>`,
        ) +
        field(
          "Nome da atividade",
          `<input name="activityName" maxlength="180" required value="${e(data.activityName)}">`,
        )
      );
    if (step === 1)
      return `<fieldset class="choice-grid"><legend>Uso de IA na atividade</legend>${Object.entries(
        levels,
      )
        .map(
          ([key, label]) =>
            `<label class="policy-choice"><input type="radio" name="status" value="${key}" ${key === data.status ? "checked" : ""}><span class="policy-choice-body">${label}</span></label>`,
        )
        .join("")}</fieldset>`;
    if (step === 2)
      return (
        field(
          "Condições de uso",
          `<textarea name="conditions" maxlength="3000">${e(data.conditions)}</textarea>`,
        ) +
        field(
          "Explicação complementar",
          `<textarea name="details" maxlength="5000">${e(data.details)}</textarea>`,
        )
      );
    if (step === 3)
      return field(
        "Fonte da política",
        `<input name="source" maxlength="500" value="${e(data.source)}" placeholder="Plano de ensino ou orientação docente">`,
      );
    const discipline = allowed.find((d) => d.id === data.disciplineId);
    return `<article class="policy-preview"><div class="policy-preview-head"><div><h3>${e(data.activityName)}</h3><small>${e(discipline.name)} · ${types[data.activityType]}</small></div><strong>${levels[data.status]}</strong></div><dl>${[
      ["Condições", data.conditions],
      ["Detalhes", data.details],
      ["Fonte", data.source],
    ]
      .map(
        ([label, value]) =>
          `<dt>${label}</dt><dd>${e(value || "Não informado")}</dd>`,
      )
      .join("")}</dl></article>`;
  }
  function render() {
    const last = step === steps.length - 1;
    const indicators = steps
      .map(
        (label, i) =>
          `<li class="wizard-step ${i === step ? "active" : i < step ? "complete" : ""}">${label}</li>`,
      )
      .join("");
    show(
      "Nova política · etapa " + (step + 1) + " de 5",
      `<ol class="wizard-steps">${indicators}</ol><form id="policy-wizard"><div class="wizard-panel">${panel()}</div><p role="alert" id="wizard-error"></p><div class="wizard-actions"><button class="btn" type="button" data-draft>Guardar rascunho nesta sessão</button><div class="wizard-actions-group">${step ? '<button class="btn" type="button" data-back>Voltar</button>' : ""}<button class="btn primary" type="submit">${last ? "Publicar política" : "Continuar"}</button></div></div></form>`,
    );
    const form = document.querySelector("#policy-wizard");
    const capture = () =>
      Object.assign(data, Object.fromEntries(new FormData(form)));
    form.querySelector("[data-draft]").onclick = () => {
      capture();
      draft = { ...data };
      form.closest("dialog").close();
    };
    if (step)
      form.querySelector("[data-back]").onclick = () => {
        capture();
        step--;
        render();
      };
    form.onsubmit = async (event) => {
      event.preventDefault();
      capture();
      if (!last) {
        step++;
        render();
        return;
      }
      const submit = form.querySelector("[type=submit]");
      submit.disabled = true;
      try {
        await request("/api/policies", {
          method: "POST",
          body: JSON.stringify(data),
        });
        draft = null;
        form.closest("dialog").close();
      } catch (error) {
        form.querySelector("#wizard-error").textContent = error.message;
        submit.disabled = false;
      }
    };
    form.querySelector("select,input,textarea,button").focus();
  }
  render();
}
