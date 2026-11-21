(() => {
  const r = document.documentElement;
  let p = {};
  try {
    p = JSON.parse(localStorage.getItem("painel-acessibilidade") || "{}") || {};
  } catch {}
  let s = "escuro";
  try {
    s = matchMedia("(prefers-color-scheme: dark)").matches ? "escuro" : "claro";
  } catch {}
  let m = false;
  try {
    m = matchMedia("(prefers-reduced-motion: reduce)").matches;
  } catch {}
  const o = (v, l, d) => (l.includes(v) ? v : d),
    M = ["normal", "medio", "grande"];
  r.dataset.theme = o(p.theme, ["claro", "escuro"], s);
  r.dataset.font = o(p.font, ["normal", "grande", "maior"], "normal");
  r.dataset.contrast = p.contrast === true ? "alto" : "normal";
  r.dataset.lines = o(p.lines, M, "normal");
  r.dataset.letters = o(p.letters, M, "normal");
  r.dataset.underline = p.underline === true ? "sim" : "nao";
  r.dataset.motion = (typeof p.motion === "boolean" ? p.motion : m)
    ? "reduzido"
    : "normal";
})();
