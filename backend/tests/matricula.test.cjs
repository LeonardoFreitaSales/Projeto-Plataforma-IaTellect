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
  const turma = await post("/api/turmas", { name: "Turma piloto" });
  await api.put("/api/turmas/" + turma.id + "/disciplines/" + disciplina.id, { failOnStatusCode: true });
  await post("/api/policies", {
    disciplineId: disciplina.id, activityName: "Avaliação final", activityType: "prova",
    status: "proibido", source: "Plano de ensino",
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
  const api = await request.newContext({ baseURL: origem });
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

  await docente.goto(origem);
  await entrar(docente, professor);
  await docente.locator('[data-view="classes"]').click();
  await docente.locator('[data-action="section"]').click();
  await docente.getByRole("button", { name: "Aprovar " + estudante, exact: true }).click();
  await docente.getByRole("button", { name: "Mover " + estudante + " para não permitidos" }).waitFor();

  const consultas = [];
  aluno.on("request", requisicao => {
    const rota = new URL(requisicao.url()).pathname;
    if (rota.startsWith("/api/")) consultas.push(rota);
  });
  await aluno.locator('[data-view="responsible"]').click();
  await aluno.locator("#purpose").waitFor();
  assert.deepEqual(consultas, [], "A reflexão deve abrir sem consultar a API");
  await aluno.locator('[data-view="disciplines"]').click();
  await aluno.getByRole("button", { name: "Ver detalhes" }).click();
  const detalhes = aluno.locator("#app-modal");
  await detalhes.getByText("Avaliação final", { exact: true }).waitFor();
  await detalhes.getByText("Proibido", { exact: true }).waitFor();
  await detalhes.getByText(/Plano de ensino/).waitFor();
  assert.deepEqual(consultas.sort(), ["/api/disciplines", "/api/policies"]);
});
