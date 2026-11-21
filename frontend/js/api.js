export const escapeHtml = (value) =>
  String(value ?? "").replace(
    /[&<>"']/g,
    (char) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        char
      ],
  );

export async function request(path, options = {}) {
  const response = await fetch(path, {
    credentials: "same-origin",
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (
    response.status === 401 &&
    path !== "/api/me" &&
    !path.startsWith("/api/auth/")
  ) {
    location.replace("/acesso.html?motivo=sessao");
  }
  const data = await response.json();
  if (!response.ok) {
    const error = new Error(data.error || "Falha ao consultar a plataforma.");
    error.status = response.status;
    throw error;
  }
  return data;
}
