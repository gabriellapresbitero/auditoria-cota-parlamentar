"""Consultas de resumo e geração dos arquivos finais."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

from .banco import consultar

SQL_SUSPEITAS_DETALHADAS = """
SELECT
    s.id_documento, s.regra, s.pontos, s.detalhe,
    d.deputado, d.partido, d.uf, d.categoria, d.fornecedor, d.cnpj_cpf,
    d.numero_documento, d.data_emissao, d.valor_liquido, d.url_documento
FROM suspeitas AS s
JOIN despesas  AS d USING (id_documento)
ORDER BY s.pontos DESC, d.valor_liquido DESC
"""

# Uma despesa pode cair em várias regras: os pontos somam, mas o valor
# só é contado uma vez (por isso a subconsulta agrupa por documento).
SQL_RANKING = """
WITH por_documento AS (
    SELECT id_documento, SUM(pontos) AS pontos
    FROM suspeitas
    GROUP BY id_documento
),
totais AS (
    SELECT id_deputado, SUM(valor_liquido) AS total_gasto, COUNT(*) AS despesas
    FROM despesas
    GROUP BY id_deputado
)
SELECT
    d.deputado,
    d.partido,
    d.uf,
    SUM(p.pontos)                                  AS pontos,
    COUNT(*)                                       AS despesas_suspeitas,
    t.despesas                                     AS despesas_total,
    ROUND(SUM(d.valor_liquido), 2)                 AS valor_suspeito,
    ROUND(t.total_gasto, 2)                        AS total_gasto,
    ROUND(100.0 * SUM(d.valor_liquido) / t.total_gasto, 1) AS percentual_suspeito
FROM por_documento AS p
JOIN despesas AS d USING (id_documento)
JOIN totais   AS t ON t.id_deputado = d.id_deputado
GROUP BY d.id_deputado
ORDER BY pontos DESC, valor_suspeito DESC
"""

SQL_POR_REGRA = """
SELECT s.regra, COUNT(*) AS ocorrencias, ROUND(SUM(d.valor_liquido), 2) AS valor
FROM suspeitas AS s
JOIN despesas  AS d USING (id_documento)
GROUP BY s.regra
ORDER BY ocorrencias DESC
"""


def moeda(valor: float) -> str:
    """Formata 1234.5 como "R$ 1.234,50"."""
    return "R$ " + f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def exportar(conexao: sqlite3.Connection, pasta: Path) -> dict[str, pd.DataFrame]:
    """Gera os CSVs para o Power BI e devolve as tabelas para o relatório."""
    pasta.mkdir(parents=True, exist_ok=True)
    tabelas = {
        "suspeitas_detalhadas": consultar(conexao, SQL_SUSPEITAS_DETALHADAS),
        "ranking_deputados": consultar(conexao, SQL_RANKING),
        "resumo_por_regra": consultar(conexao, SQL_POR_REGRA),
    }
    for nome, tabela in tabelas.items():
        tabela.to_csv(pasta / f"{nome}.csv", index=False, sep=";", decimal=",", encoding="utf-8-sig")
    return tabelas


def gerar_markdown(tabelas: dict[str, pd.DataFrame], titulo: str, total_despesas: int, top: int = 10) -> str:
    ranking = tabelas["ranking_deputados"].head(top)
    suspeitas = tabelas["suspeitas_detalhadas"].head(top)
    por_regra = tabelas["resumo_por_regra"]

    linhas = [
        f"# {titulo}",
        "",
        f"Foram analisadas **{total_despesas:,}** despesas e encontrados "
        f"**{len(tabelas['suspeitas_detalhadas']):,}** indícios.".replace(",", "."),
        "",
        "> Atenção: um indício **não** é prova de irregularidade. É uma despesa que merece ser conferida,",
        "> abrindo a nota fiscal pelo link.",
        "",
        "## Indícios por regra",
        "",
        "| Regra | Ocorrências | Valor envolvido |",
        "|---|---:|---:|",
        *[f"| {r.regra} | {r.ocorrencias} | {moeda(r.valor)} |" for r in por_regra.itertuples()],
        "",
        f"## Deputados com mais pontos (top {len(ranking)})",
        "",
        "| # | Deputado | Partido/UF | Pontos | Despesas suspeitas | Valor suspeito | % do total gasto |",
        "|---:|---|---|---:|---:|---:|---:|",
    ]
    for posicao, r in enumerate(ranking.itertuples(), start=1):
        linhas.append(
            f"| {posicao} | {r.deputado.title()} | {r.partido}/{r.uf} | {r.pontos} "
            f"| {r.despesas_suspeitas} de {r.despesas_total} | {moeda(r.valor_suspeito)} "
            f"| {str(r.percentual_suspeito).replace('.', ',')}% |"
        )

    linhas += [
        "",
        f"## Indícios mais graves (top {len(suspeitas)})",
        "",
        "| Deputado | Fornecedor | Valor | Regra | Detalhe | Nota |",
        "|---|---|---:|---|---|---|",
    ]
    for s in suspeitas.itertuples():
        link = f"[abrir]({s.url_documento})" if str(s.url_documento).startswith("http") else "—"
        linhas.append(
            f"| {s.deputado.title()} | {s.fornecedor.title()} | {moeda(s.valor_liquido)} "
            f"| {s.regra} | {s.detalhe} | {link} |"
        )
    linhas.append("")
    return "\n".join(linhas)
