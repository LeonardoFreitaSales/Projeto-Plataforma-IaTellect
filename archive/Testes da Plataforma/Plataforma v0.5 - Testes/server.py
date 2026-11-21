"""Plataforma v0.6 - servidor em Python puro (sem instalar nada).

Uso:  python server.py [porta]      ->  http://127.0.0.1:8000
Os dados ficam em data/database.json.
"""
import json
import mimetypes
import sys
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

BASE = Path(__file__).parent
DB = BASE / "data" / "database.json"
PUBLICO = BASE
ESTATICOS = {"index.html", "style.css", "app.js"}
lock = threading.Lock()

CAMPOS = {
    "disciplinas": ("nome", "docente"),
    "politicas": ("disc", "tipo", "nome", "status", "cond"),
    "comunicados": ("titulo", "mensagem", "prioridade", "fixado"),
}
OBRIG = {"disciplinas": ("nome",), "politicas": ("disc", "nome"), "comunicados": ("titulo", "mensagem")}


def ler():
    """Carrega o banco de dados do disco, criando as coleções que faltarem."""
    try:
        dados = json.loads(DB.read_text("utf-8"))
    except FileNotFoundError:
        dados = {}
    except json.JSONDecodeError:
        print(f"Aviso: {DB} está corrompido, iniciando vazio")
        dados = {}
    return {c: dados.get(c, []) for c in CAMPOS}


def gravar(dados):
    """Grava de forma atômica (escreve em .tmp e renomeia) para não corromper o arquivo."""
    DB.parent.mkdir(exist_ok=True)
    tmp = DB.with_suffix(".tmp")
    tmp.write_text(json.dumps(dados, ensure_ascii=False, indent=2), "utf-8")
    tmp.replace(DB)


def limpar(colecao, corpo):
    """Mantém só os campos permitidos pela coleção e limita o tamanho dos textos."""
    saida = {}
    for campo in CAMPOS[colecao]:
        if campo in corpo:
            valor = corpo[campo]
            saida[campo] = bool(valor) if campo == "fixado" else str(valor).strip()[:1000]
    return saida


def campos_obrigatorios_ok(colecao, item):
    return all(item.get(campo) for campo in OBRIG[colecao])


def caminho_estatico_seguro(nome_pedido):
    """Só libera os arquivos da lista ESTATICOS, nunca o resto da pasta (ex: server.py)."""
    nome = nome_pedido or "index.html"
    if nome not in ESTATICOS:
        return None
    alvo = PUBLICO / nome
    return alvo if alvo.is_file() else None


class Handler(BaseHTTPRequestHandler):
    server_version = "Plataforma/0.6"

    def responder_json(self, codigo, corpo):
        dados = json.dumps(corpo, ensure_ascii=False).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(dados)))
        self.end_headers()
        self.wfile.write(dados)

    def responder_arquivo(self, caminho):
        tipo, _ = mimetypes.guess_type(caminho.name)
        dados = caminho.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", tipo or "application/octet-stream")
        self.send_header("Content-Length", str(len(dados)))
        self.end_headers()
        self.wfile.write(dados)

    def corpo_json(self):
        """Lê e decodifica o corpo da requisição. Retorna None se o JSON for inválido."""
        tamanho = int(self.headers.get("Content-Length") or 0)
        bruto = self.rfile.read(tamanho) if tamanho else b"{}"
        try:
            return json.loads(bruto or b"{}")
        except json.JSONDecodeError:
            return None

    def rota(self):
        partes = self.path.split("?")[0].strip("/").split("/")
        return [p for p in partes if p] or [""]

    def do_GET(self):
        self.tratando(self._get)

    def do_POST(self):
        self.tratando(lambda: self._escrever("POST"))

    def do_PATCH(self):
        self.tratando(lambda: self._escrever("PATCH"))

    def do_DELETE(self):
        self.tratando(lambda: self._escrever("DELETE"))

    def tratando(self, funcao):
        try:
            funcao()
        except Exception as erro:
            print(f"Erro ao atender {self.command} {self.path}: {erro}")
            self.responder_json(500, {"erro": "Erro interno no servidor"})

    def _get(self):
        rota = self.rota()
        if rota == ["api", "dados"]:
            with lock:
                return self.responder_json(200, ler())
        if len(rota) == 1:
            arquivo = caminho_estatico_seguro(rota[0])
            if arquivo:
                return self.responder_arquivo(arquivo)
        self.responder_json(404, {"erro": "Não encontrado"})

    def _escrever(self, metodo):
        rota = self.rota()
        if len(rota) < 2 or rota[0] != "api" or rota[1] not in CAMPOS:
            return self.responder_json(404, {"erro": "Rota inválida"})
        colecao, item_id = rota[1], rota[2] if len(rota) > 2 else None

        corpo = {} if metodo == "DELETE" else self.corpo_json()
        if corpo is None:
            return self.responder_json(400, {"erro": "JSON inválido"})

        with lock:
            dados = ler()
            lista = dados[colecao]

            if metodo == "POST":
                resposta, codigo = self._criar(dados, colecao, corpo)
            else:
                alvo = next((x for x in lista if x["id"] == item_id), None)
                if not alvo:
                    return self.responder_json(404, {"erro": "Item não encontrado"})
                if metodo == "PATCH":
                    alvo.update(limpar(colecao, corpo))
                    resposta, codigo = alvo, 200
                else:
                    lista.remove(alvo)
                    if colecao == "disciplinas":
                        dados["politicas"] = [p for p in dados["politicas"] if p["disc"] != item_id]
                    resposta, codigo = {"ok": True}, 200

            if codigo < 400:
                gravar(dados)
        self.responder_json(codigo, resposta)

    def _criar(self, dados, colecao, corpo):
        item = limpar(colecao, corpo)
        if not campos_obrigatorios_ok(colecao, item):
            return {"erro": "Preencha os campos obrigatórios"}, 400
        if colecao == "politicas" and not any(d["id"] == item["disc"] for d in dados["disciplinas"]):
            return {"erro": "Disciplina inexistente"}, 400
        item.update(id=uuid.uuid4().hex[:8], criado=int(time.time() * 1000))
        dados[colecao].append(item)
        return item, 201

    def log_message(self, fmt, *args):
        print(f"{self.command} {self.path} -> {args[1]}")


def main():
    porta = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    servidor = ThreadingHTTPServer(("127.0.0.1", porta), Handler)
    servidor.daemon_threads = True
    print(f"Plataforma v0.6 em http://127.0.0.1:{porta}  (Ctrl+C para parar)")
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nEncerrando servidor...")
        servidor.shutdown()


if __name__ == "__main__":
    main()