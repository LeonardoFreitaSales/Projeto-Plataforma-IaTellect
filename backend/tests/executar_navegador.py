"""Inicia a plataforma com banco temporário e executa o fluxo de matrícula no navegador."""
import os
from pathlib import Path
import subprocess
import tempfile

from test_permissoes import servidor_de_teste


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as tmp, servidor_de_teste(tmp) as origem:
        subprocess.run(
            ["node", "--test", "matricula.test.cjs"],
            cwd=Path(__file__).resolve().parent,
            env=dict(os.environ, TEST_ORIGIN=origem),
            check=True,
        )
