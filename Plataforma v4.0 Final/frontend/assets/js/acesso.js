import { request } from "./api.js";

export function enableAuth(onLogin) {
  const byId = (id) => document.getElementById(id);
  const login = byId("login-form"),
    register = byId("register-form");
  async function tab(registering) {
    login.hidden = registering;
    register.hidden = !registering;
    for (const [id, selected] of [
      ["register-tab", registering],
      ["login-tab", !registering],
    ]) {
      byId(id).classList.toggle("active", selected);
      byId(id).setAttribute("aria-selected", String(selected));
    }
    byId("auth-form-title").textContent = registering
      ? "Solicite sua matrícula"
      : "Acesse sua conta";
    byId("auth-form-description").textContent = registering
      ? "Informe seu nome e escolha uma turma."
      : "Use seu nome de acesso e senha para continuar.";
    if (!registering) return;
    const select = byId("register-class");
    select.replaceChildren(new Option("Carregando turmas…", ""));
    try {
      const turmas = await request("/api/public/turmas");
      select.replaceChildren(
        new Option(
          turmas.length ? "Selecione sua turma" : "Nenhuma turma disponível",
          "",
        ),
        ...turmas.map((t) => new Option(t.name, t.id)),
      );
    } catch (error) {
      select.replaceChildren(new Option("Falha ao carregar as turmas", ""));
      byId("register-message").textContent = error.message;
    }
  }
  byId("register-tab").onclick = () => tab(true);
  byId("login-tab").onclick = () => tab(false);
  byId("forgot-access").onclick = () => {
    byId("login-message").textContent =
      "Peça a redefinição da senha ao administrador. Estudantes também podem procurar o professor da turma.";
  };
  document.querySelectorAll("[data-password-toggle]").forEach((button) => {
    button.onclick = () => {
      const input = byId(button.dataset.passwordToggle);
      input.type = input.type === "password" ? "text" : "password";
      button.textContent = input.type === "password" ? "Mostrar" : "Ocultar";
      button.setAttribute("aria-label", button.textContent + " senha");
    };
  });
  for (const form of [login, register]) {
    form.querySelector("[type=submit]").disabled = false;
    form.onsubmit = async (event) => {
      event.preventDefault();
      const registering = form === register;
      const message = byId(registering ? "register-message" : "login-message");
      const submit = form.querySelector("[type=submit]");
      submit.disabled = true;
      message.textContent = "";
      const body = registering
        ? {
            name: byId("register-name").value,
            turmaId: byId("register-class").value,
            password: byId("register-password").value,
          }
        : {
            name: byId("login-identity").value,
            password: byId("login-password").value,
          };
      try {
        const result = await request(
          "/api/auth/" + (registering ? "register" : "login"),
          { method: "POST", body: JSON.stringify(body) },
        );
        form.reset();
        if (registering) {
          await tab(false);
          byId("login-message").textContent = result.message;
        } else await onLogin(result);
      } catch (error) {
        message.textContent = error.message;
      } finally {
        submit.disabled = false;
      }
    };
  }
}
