"""Criação do banco SQLite e carga das despesas."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

from .documentos import documento_valido

PASTA_SQL = Path(__file__).resolve().parent.parent / "sql"


def conectar(caminho: Path | str) -> sqlite3.Connection:
    """Abre (ou cria) o banco, cria as tabelas e registra as funções em Python.

    `create_function` permite chamar uma função Python dentro do SQL.
    Aqui ela expõe a validação de CPF/CNPJ como `documento_valido(texto)`.
    """
    if caminho != ":memory:":
        Path(caminho).parent.mkdir(parents=True, exist_ok=True)
    conexao = sqlite3.connect(caminho)
    conexao.create_function(
        "documento_valido", 1, lambda texto: int(documento_valido(texto)), deterministic=True
    )
    conexao.executescript((PASTA_SQL / "schema.sql").read_text(encoding="utf-8"))
    return conexao


def carregar_despesas(conexao: sqlite3.Connection, despesas: pd.DataFrame) -> int:
    """Substitui o conteúdo das tabelas pelas despesas informadas."""
    with conexao:
        conexao.execute("DELETE FROM suspeitas")
        conexao.execute("DELETE FROM despesas")
        despesas.to_sql("despesas", conexao, if_exists="append", index=False)
    return len(despesas)


def consultar(conexao: sqlite3.Connection, sql: str, parametros: dict | tuple = ()) -> pd.DataFrame:
    return pd.read_sql_query(sql, conexao, params=parametros)
