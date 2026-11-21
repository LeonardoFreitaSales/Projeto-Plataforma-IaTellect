"""Plataforma simples - servidor em Python puro (sem instalar nada).

Uso:  python server.py [porta]      ->  http://127.0.0.1:8000
Os dados ficam em data/database.json.
"""
import json
import sys
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

BASE = Path(__file__).parent
DB = BASE / "data" / "database.json"
lock = threading.Lock()

# arquivos estáticos entregues pelo servidor
ESTATICOS = {
    "": ("index.html", "text/html; charset=utf-8"),
    "index.html": ("index.html", "text/html; charset=utf-8"),
    "style.css": ("style.css", "text/css; charset=utf-8"),
    "app.js": ("app.js", "text/javascript; charset=utf-8"),
}

# campos aceitos e obrigatórios de cada coleção
CAMPOS = {
    "disciplinas": ("nome", "docente"),
    "politicas": ("disc", "tipo", "nome", "status", "cond"),
}
OBRIG = {"disciplinas": ("nome",), "politicas": ("disc", "nome")}


def ler():
    try:
        dados = json.loads(DB.read_text("utf-8"))
    except (FileNotFoundError, ValueError):
        dados = {}
    return {c: dados.get(c, []) for c in CAMPOS}


def gravar(dados):
    DB.parent.mkdir(exist_ok=True)
    tmp = DB.with_suffix(".tmp")
    tmp.write_text(json.dumps(dados, ensure_ascii=False, indent=2), "utf-8")
    tmp.replace(DB)


def limpar(col, corpo):
    """Mantém só os campos permitidos e limita o tamanho dos textos."""
    out = {}
    for k in CAMPOS[col]:
        if k in corpo:
            v = corpo[k]
            out[k] = bool(v) if k == "fixado" else str(v).strip()[:1000]
    return out


class Handler(BaseHTTPRequestHandler):
    def responder(self, codigo, corpo, tipo="application/json; charset=utf-8"):
        dados = corpo if isinstance(corpo, bytes) else json.dumps(corpo, ensure_ascii=False).encode()
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(dados)))
        self.end_headers()
        self.wfile.write(dados)

    def corpo(self):
        try:
            return json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
        except ValueError:
            return None

    def rota(self):
        return self.path.split("?")[0].strip("/").split("/")

    def do_GET(self):
        rota = self.rota()
        if rota == ["api", "dados"]:
            with lock:
                return self.responder(200, ler())
        if len(rota) == 1 and rota[0] in ESTATICOS:
            arquivo, tipo = ESTATICOS[rota[0]]
            return self.responder(200, (BASE / arquivo).read_bytes(), tipo)
        self.responder(404, {"erro": "Não encontrado"})

    def escrever(self, metodo):
        rota = self.rota()
        if len(rota) < 2 or rota[0] != "api" or rota[1] not in CAMPOS:
            return self.responder(404, {"erro": "Rota inválida"})
        col, item_id = rota[1], rota[2] if len(rota) > 2 else None
        corpo = self.corpo() if metodo != "DELETE" else {}
        if not isinstance(corpo, dict):
            return self.responder(400, {"erro": "JSON inválido"})
        with lock:
            dados = ler()
            lista = dados[col]
            if metodo == "POST":
                item = limpar(col, corpo)
                if any(not item.get(k) for k in OBRIG[col]):
                    return self.responder(400, {"erro": "Preencha os campos obrigatórios"})
                if col == "politicas" and not any(d["id"] == item["disc"] for d in dados["disciplinas"]):
                    return self.responder(400, {"erro": "Disciplina inexistente"})
                item.update(id=uuid.uuid4().hex[:8], criado=int(time.time() * 1000))
                lista.append(item)
                resposta, codigo = item, 201
            else:
                alvo = next((x for x in lista if x["id"] == item_id), None)
                if not alvo:
                    return self.responder(404, {"erro": "Item não encontrado"})
                if metodo == "PATCH":
                    alvo.update(limpar(col, corpo))
                else:
                    lista.remove(alvo)
                    if col == "disciplinas":  # apaga também as políticas da disciplina
                        dados["politicas"] = [p for p in dados["politicas"] if p["disc"] != item_id]
                resposta, codigo = {"ok": True}, 200
            gravar(dados)
        self.responder(codigo, resposta)

    def do_POST(self):
        self.escrever("POST")

    def do_PATCH(self):
        self.escrever("PATCH")

    def do_DELETE(self):
        self.escrever("DELETE")

    def log_message(self, fmt, *args):
        print(f"{self.command} {self.path} -> {args[1]}")


if __name__ == "__main__":
    porta = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    print(f"Plataforma simples em http://127.0.0.1:{porta}  (Ctrl+C para parar)")
    ThreadingHTTPServer(("127.0.0.1", porta), Handler).serve_forever()
