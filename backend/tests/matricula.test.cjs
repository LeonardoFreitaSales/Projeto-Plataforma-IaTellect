const { test } = require("node:test");
const assert = require("node:assert/strict");
const { chromium, request } = require("playwright-core");

const origem = process.env.TEST_ORIGIN;
const professor = "Professor Teste";
const estudante = "Estudante Teste";
const senha = "senha-teste-123";

async function prepararTurma(api) {
  const post = async (rota, data) => {
    const resposta = await api.post(rota, { data, failOnStatusCode: true });
    return resposta.json();
  };
  await post("/api/auth/login", { name: "admin", password: "admin-teste-123" });
  const docente = await post("/api/users", { name: professor, password: senha });
  const disciplina = await post("/api/disciplines", { name: "Estatística", ownerId: docente.id });
  const historia = await post("/api/disciplines", { name: "História", ownerId: docente.id });
  const turma = await post("/api/turmas", { name: "Turma piloto" });
  await api.put("/api/turmas/" + turma.id + "/disciplines/" + historia.id, { failOnStatusCode: true });
  await post("/api/policies", {
    disciplineId: historia.id, activityName: "Prova final", activityType: "prova",
    status: "permitido", source: "Guia de História",
  });
  await api.put("/api/turmas/" + turma.id + "/disciplines/" + disciplina.id, { failOnStatusCode: true });
  await post("/api/policies", {
    disciplineId: disciplina.id, activityName: "Avaliação <final>", activityType: "prova",
    status: "proibido", source: "Plano de ensino",
  });
  await post("/api/policies", {
    disciplineId: disciplina.id, activityName: "Avaliação parcial", activityType: "prova",
    status: "permitido", source: "Guia da avaliação parcial",
  });
}

async function entrar(pagina, nome) {
  await pagina.locator("#login-identity").fill(nome);
  await pagina.locator("#login-password").fill(senha);
  await pagina.locator("#login-form [type=submit]").click();
  await pagina.locator("#view-root h1").filter({ hasText: nome }).waitFor();
}

test("matrícula pendente, aprovação pelo professor e consulta à política", async (t) => {
  assert.ok(origem, "Execute o teste por executar_navegador.py");
  const api = await request.newContext({ baseURL: origem, extraHTTPHeaders: { Origin: origem } });
  try {
    await prepararTurma(api);
  } finally {
    await api.dispose();
  }
  const browser = await chromium.launch({ channel: process.env.BROWSER_CHANNEL || undefined });
  t.after(() => browser.close());
  const aluno = await browser.newPage();
  const docente = await browser.newPage();
  await aluno.goto(origem);
  await aluno.locator("#register-tab").click();
  await aluno.locator("#register-name").fill(estudante);
  await aluno.locator("#register-class").selectOption({ label: "Turma piloto" });
  await aluno.locator("#register-password").fill(senha);
  await aluno.locator("#register-form [type=submit]").click();
  await aluno.locator("#login-message").filter({ hasText: "solicitação" }).waitFor();
  await entrar(aluno, estudante);
  await aluno.locator('[data-view="disciplines"]').click();
  await aluno.getByText("Nenhuma disciplina encontrada.", { exact: true }).waitFor();


  await aluno.locator("#assistant-toggle").click();
  await aluno.locator("#chat-input").fill("Posso usar IA na avaliação final?");
  await aluno.locator("#chat-form [type=submit]").click();
  await aluno.locator("#chat-log .message").filter({ hasText: "Não encontrei uma política" }).waitFor();
  await aluno.locator("#assistant-close").click();

  await docente.goto(origem);
  await entrar(docente, professor);
  await docente.locator('[data-view="classes"]').click();
  await docente.locator('[data-action="section"]').click();
  await docente.getByRole("button", { name: "Aprovar " + estudante, exact: true }).click();
  await docente.getByRole("button", { name: "Mover " + estudante + " para não permitidos" }).waitFor();


  await aluno.locator("#assistant-toggle").click();
  await aluno.locator("#chat-input").fill("Posso usar IA na avaliação final?");
  await aluno.locator("#chat-form [type=submit]").click();
  await aluno.locator("#chat-log .message").filter({ hasText: /Avaliação <final>[\s\S]*Proibido[\s\S]*Plano de ensino/ }).waitFor();
  const perguntar = async (texto) => {
    await aluno.locator("#chat-input").fill(texto);
    await aluno.locator("#chat-input").press("Enter");
  };
  await perguntar("avaliação");
  await aluno.getByRole("button", { name: "2. Estatística · Avaliação parcial" }).waitFor();
  await perguntar("3");
  await aluno.getByText(/Digite um número de 1 a 2/).waitFor();
  await perguntar("2");
  await aluno.locator("#chat-log .message").filter({ hasText: /Permitido[\s\S]*Guia da avaliação parcial/ }).waitFor();
  await aluno.locator("#assistant-clear").click();
  await perguntar("2");
  await aluno.locator("#chat-log .message").filter({ hasText: "Não encontrei uma política" }).waitFor();
  await aluno.locator("#assistant-close").click();

  await aluno.locator("#assistant-toggle").click();
  for (const [pergunta, esperada] of [
    ["Avaliação parcial", "Guia da avaliação parcial"],
    ["Posso usar IA na avaliação parcial de Estatística?", "Guia da avaliação parcial"],
    ["Nessa mesma matéria, posso usar IA na prova final?", "Plano de ensino"],
    ["E na prova final?", "Plano de ensino"],
    ["Prova final de Estatística", "Plano de ensino"],
    ["O professor deixa usar inteligência artificial na avaliação parcial de Estatística?", "Guia da avaliação parcial"],
    ["E na prova final de História?", "Guia de História"],
  ]) {
    const respostas = aluno.locator("#chat-log .message:not(.user)");
    const anteriores = await respostas.count();
    await perguntar(pergunta);
    assert.ok((await respostas.nth(anteriores).innerText()).includes(esperada), pergunta);
  }
  await aluno.locator("#assistant-clear").click();
  await perguntar("E na prova final?");
  await aluno.getByRole("button", { name: /História · Prova final/ }).waitFor();
  await aluno.getByRole("button", { name: /Estatística · Avaliação <final>/ }).waitFor();
  await aluno.locator("#assistant-close").click();

  await aluno.locator("#assistant-toggle").click();
  await perguntar("Qual a previsão do tempo amanhã?");
  await aluno.getByText(/O assunto não corresponde à plataforma/).waitFor();
  await perguntar("Como aprovo uma matrícula?");
  await aluno.getByText(/A aprovação de matrículas exige/).waitFor();
  await perguntar("Onde vejo minhas disciplinas?");
  await aluno.getByRole("button", { name: "Abrir Disciplinas e políticas" }).click();
  await aluno.locator("#discipline-list").waitFor();
  const consultas = [];
  aluno.on("request", requisicao => {
    const rota = new URL(requisicao.url()).pathname;
    if (rota.startsWith("/api/")) consultas.push(rota);
  });
  await aluno.locator('[data-view="responsible"]').click();
  await aluno.locator("#purpose").waitFor();
  assert.deepEqual(consultas, [], "A reflexão deve abrir sem consultar a API");
  await aluno.locator('[data-view="disciplines"]').click();
  await aluno.locator(".discipline-card").filter({ hasText: "Estatística" }).getByRole("button", { name: "Ver detalhes" }).click();
  const detalhes = aluno.locator("#app-modal");
  await detalhes.getByText("Avaliação <final>", { exact: true }).waitFor();
  await detalhes.getByText("Proibido", { exact: true }).waitFor();
  await detalhes.getByText(/Plano de ensino/).waitFor();
  assert.deepEqual(consultas.sort(), ["/api/disciplines", "/api/policies"]);
});
