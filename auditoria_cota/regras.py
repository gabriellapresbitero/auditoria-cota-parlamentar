"""Regras de auditoria.

Existem dois tipos de regra:

* Regras em SQL, na pasta `sql/regras/`. Cada arquivo tem um cabeçalho com
  nome, pontos e descrição, e uma consulta que devolve `id_documento` e
  `detalhe`. Para criar uma regra nova, basta adicionar um arquivo `.sql`.
* A regra de valor atípico, em Python, porque calcular quartis por grupo
  é bem mais simples com pandas do que com SQLite.

Os pontos indicam a gravidade: 3 = forte, 2 = médio, 1 = fraco.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from .banco import PASTA_SQL, consultar

COLUNAS_SUSPEITA = ["id_documento", "regra", "pontos", "detalhe"]


@dataclass(frozen=True)
class Regra:
    nome: str
    pontos: int
    descricao: str
    sql: str


def carregar_regras(pasta: Path = PASTA_SQL / "regras") -> list[Regra]:
    regras = []
    for arquivo in sorted(Path(pasta).glob("*.sql")):
        texto = arquivo.read_text(encoding="utf-8")
        cabecalho = {}
        for linha in texto.splitlines():
            if linha.startswith("-- ") and ":" in linha:
                chave, _, valor = linha[3:].partition(":")
                cabecalho.setdefault(chave.strip(), valor.strip())
        try:
            regras.append(Regra(cabecalho["regra"], int(cabecalho["pontos"]), cabecalho["descricao"], texto))
        except KeyError as erro:
            raise ValueError(f"{arquivo.name}: cabeçalho sem o campo {erro}") from None
    return regras


def executar_regras_sql(conexao: sqlite3.Connection, regras: list[Regra], parametros: dict) -> pd.DataFrame:
    resultados = []
    for regra in regras:
        # Cada regra recebe só os parâmetros que ela usa (ex.: :valor_minimo).
        usados = {nome: valor for nome, valor in parametros.items() if f":{nome}" in regra.sql}
        encontrados = consultar(conexao, regra.sql, usados)
        encontrados["regra"] = regra.nome
        encontrados["pontos"] = regra.pontos
        resultados.append(encontrados)
    if not resultados:
        return pd.DataFrame(columns=COLUNAS_SUSPEITA)
    return pd.concat(resultados, ignore_index=True)[COLUNAS_SUSPEITA]


def regra_valor_atipico(despesas: pd.DataFrame, fator: float = 3.0, minimo_despesas: int = 30) -> pd.DataFrame:
    """Marca despesas muito acima do normal para a sua categoria.

    Usa o critério do intervalo interquartil (IQR), o mesmo do boxplot:
        limite = Q3 + fator × (Q3 − Q1)
    Com fator 3, só valores extremos são marcados. Categorias com poucas
    despesas ficam de fora, porque os quartis não seriam confiáveis.
    """
    positivas = despesas[despesas["valor_liquido"] > 0]
    grupos = positivas.groupby("categoria")["valor_liquido"]

    estatisticas = pd.DataFrame(
        {
            "quantidade": grupos.size(),
            "q1": grupos.quantile(0.25),
            "mediana": grupos.median(),
            "q3": grupos.quantile(0.75),
        }
    )
    estatisticas["limite"] = estatisticas["q3"] + fator * (estatisticas["q3"] - estatisticas["q1"])
    estatisticas = estatisticas[estatisticas["quantidade"] >= minimo_despesas]

    marcadas = positivas.join(estatisticas, on="categoria", how="inner")
    marcadas = marcadas[marcadas["valor_liquido"] > marcadas["limite"]]

    detalhe = marcadas.apply(
        lambda d: f"R$ {d.valor_liquido:.2f} é {d.valor_liquido / d.mediana:.0f}x a mediana da categoria "
                  f"(limite R$ {d.limite:.2f})",
        axis=1,
    )
    return pd.DataFrame(
        {
            "id_documento": marcadas["id_documento"],
            "regra": "valor_atipico",
            "pontos": 2,
            "detalhe": detalhe if len(marcadas) else pd.Series(dtype=str),
        }
    )[COLUNAS_SUSPEITA]


def auditar(conexao: sqlite3.Connection, despesas: pd.DataFrame, valor_minimo_exclusivo: float = 50_000) -> pd.DataFrame:
    """Roda todas as regras e grava o resultado na tabela `suspeitas`."""
    suspeitas = pd.concat(
        [
            executar_regras_sql(conexao, carregar_regras(), {"valor_minimo": valor_minimo_exclusivo}),
            regra_valor_atipico(despesas),
        ],
        ignore_index=True,
    )
    suspeitas = suspeitas.drop_duplicates(subset=["id_documento", "regra"])
    with conexao:
        conexao.execute("DELETE FROM suspeitas")
        suspeitas.to_sql("suspeitas", conexao, if_exists="append", index=False)
    return suspeitas
