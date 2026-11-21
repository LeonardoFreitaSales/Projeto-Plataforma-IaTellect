export function mostrarAviso(destino, texto, tipo) {
  const aviso = document.createElement("div");
  aviso.className = "notice " + tipo;
  aviso.setAttribute("role", "status");
  aviso.textContent = texto;
  destino.replaceChildren(aviso);
}
