"""Ponto de entrada da auditoria.

Uso:
    python -m auditoria_cota --ano 2025
    python -m auditoria_cota --ano 2025 --uf PE
    python -m auditoria_cota --arquivo meu_arquivo.csv

Etapas:
    1. Coleta   -> baixa o CSV anual da Câmara (ou usa um arquivo local)
    2. Limpeza  -> padroniza colunas, valores e CPF/CNPJ
    3. Banco    -> carrega tudo em um SQLite
    4. Regras   -> roda as regras de auditoria (SQL + Python)
    5. Saídas   -> CSVs para o Power BI e relatório em Markdown
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

from . import banco, coleta, limpeza, regras, relatorio


def ler_argumentos(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="auditoria_cota",
        description="Procura despesas suspeitas na Cota Parlamentar (CEAP) da Câmara dos Deputados.",
    )
    parser.add_argument("--ano", type=int, default=date.today().year - 1,
                        help="Ano das despesas. Padrão: ano passado (já completo).")
    parser.add_argument("--arquivo", type=Path, help="Usa um CSV já baixado em vez de baixar.")
    parser.add_argument("--uf", help="Analisa só os deputados de um estado (ex.: PE).")
    parser.add_argument("--valor-minimo-exclusivo", type=float, default=50_000,
                        help="Valor mínimo para a regra de fornecedor exclusivo. Padrão: 50000")
    parser.add_argument("--saida", type=Path, default=Path("saida"), help="Pasta dos resultados.")
    return parser.parse_args(argv)


def executar(args: argparse.Namespace) -> Path:
    if args.arquivo:
        caminho_csv = args.arquivo
        print(f"[1/5] Usando o arquivo {caminho_csv}")
    else:
        print(f"[1/5] Baixando as despesas de {args.ano} (o arquivo tem algumas dezenas de MB)...")
        caminho_csv = coleta.baixar_ano(args.ano)

    print("[2/5] Limpando os dados...")
    despesas = limpeza.limpar(limpeza.ler_csv(caminho_csv))
    if args.uf:
        despesas = despesas[despesas["uf"] == args.uf.upper()]
        if despesas.empty:
            raise ValueError(f"Nenhuma despesa encontrada para a UF {args.uf.upper()}.")

    escopo = f"{args.ano}" + (f"_{args.uf.upper()}" if args.uf else "")
    pasta = args.saida / escopo

    print(f"[3/5] Carregando {len(despesas):,} despesas no banco...".replace(",", "."))
    conexao = banco.conectar(pasta / "auditoria.db")
    try:
        banco.carregar_despesas(conexao, despesas)

        print("[4/5] Rodando as regras de auditoria...")
        suspeitas = regras.auditar(conexao, despesas, args.valor_minimo_exclusivo)

        print("[5/5] Gerando relatório e CSVs...")
        tabelas = relatorio.exportar(conexao, pasta)
    finally:
        conexao.close()

    titulo = f"Auditoria da Cota Parlamentar: {args.ano}" + (f" ({args.uf.upper()})" if args.uf else "")
    texto = relatorio.gerar_markdown(tabelas, titulo, len(despesas))
    (pasta / "relatorio.md").write_text(texto, encoding="utf-8")

    print(f"\n{len(suspeitas)} indícios encontrados. Resultados em: {pasta}")
    return pasta


def main(argv: list[str] | None = None) -> int:
    try:
        executar(ler_argumentos(argv))
    except (ValueError, ConnectionError, FileNotFoundError) as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
