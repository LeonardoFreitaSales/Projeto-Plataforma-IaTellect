(() => {
  const accessibilityButton = document.querySelector("#accessibility-toggle"),
    accessibilityMenu = document.querySelector("#accessibility-menu"),
    accessibilityStatus = document.querySelector("#accessibility-status");
  const accessibilityStorageKey = "painel-acessibilidade";
  const colorScheme = window.matchMedia("(prefers-color-scheme: dark)"),
    motionQuery = window.matchMedia("(prefers-reduced-motion: reduce)"),
    aModes = ["normal", "medio", "grande"];
  const systemTheme = () => (colorScheme.matches ? "escuro" : "claro");
  const defaultAccessibility = () => ({
    theme: null,
    font: "normal",
    contrast: false,
    lines: "normal",
    letters: "normal",
    underline: false,
    motion: null,
  });
  const readAccessibilityPreferences = () => {
    try {
      const p =
        JSON.parse(localStorage.getItem(accessibilityStorageKey) || "{}") || {};
      return {
        theme: ["claro", "escuro"].includes(p.theme) ? p.theme : null,
        font: ["normal", "grande", "maior"].includes(p.font)
          ? p.font
          : "normal",
        contrast: p.contrast === true,
        lines: aModes.includes(p.lines) ? p.lines : "normal",
        letters: aModes.includes(p.letters) ? p.letters : "normal",
        underline: p.underline === true,
        motion: typeof p.motion === "boolean" ? p.motion : null,
      };
    } catch {
      return defaultAccessibility();
    }
  };
  let accessibilityPreferences = readAccessibilityPreferences();
  const effectiveMotion = () =>
    accessibilityPreferences.motion === null
      ? motionQuery.matches
      : accessibilityPreferences.motion;
  function syncAccessibilityControls() {
    const root = document.documentElement,
      p = accessibilityPreferences,
      theme = p.theme || systemTheme(),
      motion = effectiveMotion();
    root.dataset.theme = theme;
    root.dataset.font = p.font;
    root.dataset.contrast = p.contrast ? "alto" : "normal";
    root.dataset.lines = p.lines;
    root.dataset.letters = p.letters;
    root.dataset.underline = p.underline ? "sim" : "nao";
    root.dataset.motion = motion ? "reduzido" : "normal";
    [
      ["theme-choice", theme],
      ["font-choice", p.font],
      ["lines-choice", p.lines],
      ["letters-choice", p.letters],
    ].forEach(([k, v]) =>
      document
        .querySelectorAll("[data-" + k + "]")
        .forEach((b) =>
          b.setAttribute(
            "aria-pressed",
            String(b.getAttribute("data-" + k) === v),
          ),
        ),
    );
    const sw = { contrast: p.contrast, underline: p.underline, motion };
    accessibilityMenu.querySelectorAll("[data-switch]").forEach((s) => {
      const on = sw[s.dataset.switch];
      s.setAttribute("aria-checked", String(on));
      const st = s.parentNode.querySelector(".a11y-state");
      if (st) st.textContent = on ? "Ligado" : "Desligado";
    });
  }
  function saveAccessibilityPreferences(next) {
    accessibilityPreferences = next;
    syncAccessibilityControls();
    accessibilityStatus.textContent = "";
    try {
      localStorage.setItem(accessibilityStorageKey, JSON.stringify(next));
    } catch {}
  }
  function setAccessibilityMenu(open, returnFocus = false) {
    accessibilityMenu.hidden = !open;
    accessibilityButton.setAttribute("aria-expanded", String(open));
    accessibilityButton.setAttribute(
      "aria-label",
      open ? "Fechar menu de acessibilidade" : "Abrir menu de acessibilidade",
    );
    if (!open && returnFocus) accessibilityButton.focus();
  }
  accessibilityButton.addEventListener("click", () =>
    setAccessibilityMenu(accessibilityMenu.hidden),
  );
  [
    ["theme-choice", "theme"],
    ["font-choice", "font"],
    ["lines-choice", "lines"],
    ["letters-choice", "letters"],
  ].forEach(([a, k]) =>
    document
      .querySelectorAll("[data-" + a + "]")
      .forEach((b) =>
        b.addEventListener("click", () =>
          saveAccessibilityPreferences({
            ...accessibilityPreferences,
            [k]: b.getAttribute("data-" + a),
          }),
        ),
      ),
  );
  accessibilityMenu.querySelectorAll("[data-switch]").forEach((s) =>
    s.addEventListener("click", () => {
      const k = s.dataset.switch,
        cur = k === "motion" ? effectiveMotion() : accessibilityPreferences[k];
      saveAccessibilityPreferences({ ...accessibilityPreferences, [k]: !cur });
    }),
  );
  accessibilityMenu
    .querySelector("[data-accessibility-reset]")
    .addEventListener("click", () => {
      try {
        localStorage.removeItem(accessibilityStorageKey);
      } catch {}
      accessibilityPreferences = defaultAccessibility();
      syncAccessibilityControls();
      accessibilityStatus.textContent =
        "Preferências restauradas ao padrão. Tema e movimento seguem as configurações do sistema.";
    });
  document.addEventListener("click", (e) => {
    if (
      !accessibilityMenu.hidden &&
      !accessibilityMenu.contains(e.target) &&
      !accessibilityButton.contains(e.target)
    )
      setAccessibilityMenu(false);
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && !accessibilityMenu.hidden) {
      e.preventDefault();
      e.stopPropagation();
      setAccessibilityMenu(false, true);
    }
  });
  const onSystemChange = () => {
    if (
      !accessibilityPreferences.theme ||
      accessibilityPreferences.motion === null
    )
      syncAccessibilityControls();
  };
  [colorScheme, motionQuery].forEach((q) =>
    q.addEventListener
      ? q.addEventListener("change", onSystemChange)
      : q.addListener && q.addListener(onSystemChange),
  );
  syncAccessibilityControls();
})();
