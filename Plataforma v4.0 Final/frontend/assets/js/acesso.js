(() => {
  const $ = (s) => document.querySelector(s);
  const icone =
    '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><use href="#i-alert"/></svg>';
  const MSG = {
    credenciais: "Nome ou senha incorretos.",
    limite: "Muitas tentativas. Aguarde alguns minutos e tente de novo.",
    rede: "Não foi possível conectar ao servidor da plataforma. Verifique se ele está em execução e tente de novo.",
    generico: "Não foi possível concluir agora. Tente de novo em instantes.",
  };
  const form = $("#form"),
    nome = $("#nome"),
    senha = $("#senha"),
    entrar = $("#entrar");
  const formC = $("#form-cadastro"),
    cNome = $("#c-nome"),
    cTurma = $("#c-turma"),
    cSenha = $("#c-senha"),
    cSenha2 = $("#c-senha2"),
    cadastrar = $("#cadastrar");
  const perfil = () => $('input[name="perfil"]:checked').value;

  function mostraErro(el, msg) {
    el.className = "err";
    el.setAttribute("role", "alert");
    el.innerHTML = icone + "<span></span>";
    el.lastChild.textContent = msg;
    el.hidden = false;
  }
  function erro(input, msg) {
    mostraErro($("#" + input.id + "-erro"), msg);
    input.setAttribute("aria-invalid", "true");
    input.setAttribute("aria-describedby", input.id + "-erro");
  }
  function limpa(input) {
    const e = $("#" + input.id + "-erro");
    e.hidden = true;
    e.innerHTML = "";
    input.removeAttribute("aria-invalid");
    input.removeAttribute("aria-describedby");
  }
  function ocupado(botao, sim, texto) {
    botao.disabled = sim;
    botao.textContent = texto;
    if (sim) botao.setAttribute("aria-busy", "true");
    else botao.removeAttribute("aria-busy");
  }
  // O servidor é a única autoridade: a tela só mostra o resultado.
  async function enviar(url, corpo) {
    let r;
    try {
      r = await fetch(url, {
        method: "POST",
        credentials: "same-origin",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(corpo),
      });
    } catch (_) {
      return { rede: true };
    }
    const dados = await r.json().catch(() => null);
    return { status: r.status, dados };
  }
  function mensagem(res) {
    if (res.rede || res.status === 404 || res.status >= 500) return MSG.rede;
    if (res.status === 401) return MSG.credenciais;
    if (res.status === 429) return MSG.limite;
    if (
      (res.status === 400 || res.status === 409) &&
      res.dados &&
      res.dados.error
    )
      return res.dados.error;
    return MSG.generico;
  }

  // Avisos vindos do painel (ex.: sessão ausente ou terminada)
  const params = new URLSearchParams(location.search);
  if (params.get("motivo") === "sessao") {
    const aviso = $("#aviso");
    aviso.textContent =
      "Faça login para continuar. Sua sessão pode ter terminado.";
    aviso.hidden = false;
    history.replaceState(null, "", location.pathname);
  }
  // Quem já tem sessão válida vai direto ao painel
  fetch("/api/me", { credentials: "same-origin" })
    .then((r) => {
      if (r.ok) location.replace("/");
    })
    .catch(() => {});

  document.querySelectorAll('input[name="perfil"]').forEach((r) =>
    r.addEventListener("change", () => {
      $("#dica-senha").hidden = perfil() === "equipe";
      $("#form-erro").hidden = true;
      limpa(senha);
    }),
  );
  [nome, senha, cNome, cTurma, cSenha, cSenha2].forEach((i) =>
    i.addEventListener(
      "input",
      () => i.hasAttribute("aria-invalid") && limpa(i),
    ),
  );
  cTurma.addEventListener(
    "change",
    () => cTurma.hasAttribute("aria-invalid") && limpa(cTurma),
  );

  $("#reveal").addEventListener("click", (e) => {
    const mostrar = senha.type === "password";
    senha.type = mostrar ? "text" : "password";
    e.currentTarget.textContent = mostrar ? "Ocultar" : "Mostrar";
    e.currentTarget.setAttribute(
      "aria-label",
      mostrar ? "Ocultar senha" : "Mostrar senha",
    );
  });

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const n = nome.value.trim();
    let primeiro = null;
    $("#form-erro").hidden = true;
    if (!n) {
      erro(nome, "Informe seu nome.");
      primeiro = nome;
    } else limpa(nome);
    {
      if (!senha.value) {
        erro(senha, "Informe a senha.");
        primeiro = primeiro || senha;
      } else limpa(senha);
    }
    if (primeiro) {
      primeiro.focus();
      return;
    }
    ocupado(entrar, true, "Entrando…");
    const res = await enviar(
      "/api/auth/login",
      senha.value ? { name: n, password: senha.value } : { name: n },
    );
    if (res.status === 200) {
      location.replace("/");
      return;
    }
    ocupado(entrar, false, "Entrar");
    mostraErro($("#form-erro"), mensagem(res));
  });

  // ---- Cadastro do aluno ----
  let turmasCarregadas = false;
  async function carregarTurmas() {
    if (turmasCarregadas) return;
    cTurma.replaceChildren(new Option("Carregando turmas…", ""));
    let lista = null;
    try {
      const r = await fetch("/api/public/turmas", {
        credentials: "same-origin",
      });
      if (r.ok) lista = await r.json();
    } catch (_) {
      /* tratado abaixo */
    }
    if (!Array.isArray(lista)) {
      cTurma.replaceChildren(
        new Option("Não foi possível carregar as turmas", ""),
      );
      mostraErro($("#c-form-erro"), MSG.rede);
      return;
    }
    if (!lista.length) {
      cTurma.replaceChildren(new Option("Nenhuma turma cadastrada ainda", ""));
      cadastrar.disabled = true;
      mostraErro(
        $("#c-form-erro"),
        "Ainda não há turmas. Peça a um professor para criar a sua turma.",
      );
      return;
    }
    cTurma.replaceChildren(
      new Option("Escolha a turma", ""),
      ...lista.map(
        (t) =>
          new Option(
            t.name + (t.disciplines ? " — " + t.disciplines : ""),
            t.id,
          ),
      ),
    );
    turmasCarregadas = true;
  }
  function vista(qual) {
    const cad = qual === "cadastro";
    $("#vista-login").hidden = cad;
    $("#vista-cadastro").hidden = !cad;
    $(cad ? "#titulo-cadastro" : "#titulo-login").focus();
    if (cad) carregarTurmas();
  }
  $("#ir-cadastro").addEventListener("click", () => vista("cadastro"));
  $("#voltar-login").addEventListener("click", () => vista("login"));

  formC.addEventListener("submit", async (e) => {
    e.preventDefault();
    const n = cNome.value.trim().replace(/\s+/g, " ");
    let primeiro = null;
    $("#c-form-erro").hidden = true;
    if (n.split(" ").length < 2) {
      erro(cNome, "Informe o nome completo.");
      primeiro = cNome;
    } else limpa(cNome);
    if (!cTurma.value) {
      erro(cTurma, "Escolha a turma.");
      primeiro = primeiro || cTurma;
    } else limpa(cTurma);
    if (cSenha.value.length < 8) {
      erro(cSenha, "A senha deve ter pelo menos 8 caracteres.");
      primeiro = primeiro || cSenha;
    } else limpa(cSenha);
    if (cSenha2.value !== cSenha.value) {
      erro(cSenha2, "As senhas não são iguais.");
      primeiro = primeiro || cSenha2;
    } else limpa(cSenha2);
    if (primeiro) {
      primeiro.focus();
      return;
    }
    ocupado(cadastrar, true, "Cadastrando…");
    const res = await enviar("/api/auth/register", {
      name: n,
      turmaId: cTurma.value,
      password: cSenha.value,
    });
    if (res.status === 202) {
      cSenha.value = "";
      cSenha2.value = "";
      ocupado(cadastrar, false, "Cadastrar");
      const status = $("#c-form-erro");
      status.className = "dica";
      status.setAttribute("role", "status");
      status.textContent =
        res.dados?.message || "Confira as informações ou fale com o professor.";
      status.hidden = false;
      return;
    }
    cSenha.value = "";
    cSenha2.value = "";
    ocupado(cadastrar, false, "Cadastrar");
    mostraErro($("#c-form-erro"), mensagem(res));
  });
})();
