"""Download dos dados da Cota para o Exercício da Atividade Parlamentar (CEAP).

A Câmara dos Deputados publica um arquivo por ano com todas as despesas
reembolsadas: https://dadosabertos.camara.leg.br/swagger/api.html#staticfile
"""

from __future__ import annotations

import io
import time
import urllib.request
import zipfile
from pathlib import Path

URL_ARQUIVO = "https://www.camara.leg.br/cotas/Ano-{ano}.csv.zip"


def baixar_ano(ano: int, pasta: Path = Path("dados/brutos"), tentativas: int = 3) -> Path:
    """Baixa e descompacta o CSV de um ano. Retorna o caminho do CSV.

    Se o arquivo já foi baixado antes, ele é reaproveitado.
    """
    pasta = Path(pasta)
    destino = pasta / f"Ano-{ano}.csv"
    if destino.exists():
        return destino

    url = URL_ARQUIVO.format(ano=ano)
    ultimo_erro: Exception | None = None
    for tentativa in range(1, tentativas + 1):
        try:
            with urllib.request.urlopen(url, timeout=120) as resposta:
                conteudo = resposta.read()
            break
        except OSError as erro:
            ultimo_erro = erro
            if tentativa < tentativas:
                time.sleep(2 ** tentativa)
    else:
        raise ConnectionError(f"Não foi possível baixar {url}") from ultimo_erro

    pasta.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(conteudo)) as arquivo_zip:
        nome_csv = next(n for n in arquivo_zip.namelist() if n.lower().endswith(".csv"))
        destino.write_bytes(arquivo_zip.read(nome_csv))
    return destino
