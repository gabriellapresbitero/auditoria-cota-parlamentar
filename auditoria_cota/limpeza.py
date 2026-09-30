"""Leitura e limpeza do CSV da cota parlamentar.

O arquivo original tem mais de 30 colunas com nomes abreviados
(ex.: `txNomeParlamentar`, `vlrLiquido`). Ficamos só com o que a
auditoria usa, com nomes claros e tipos corretos.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .documentos import somente_digitos

# nome no arquivo da Câmara -> nome usado no projeto
COLUNAS = {
    "ideDocumento": "id_documento",
    "nuDeputadoId": "id_deputado",
    "txNomeParlamentar": "deputado",
    "sgUF": "uf",
    "sgPartido": "partido",
    "txtDescricao": "categoria",
    "txtFornecedor": "fornecedor",
    "txtCNPJCPF": "cnpj_cpf",
    "txtNumero": "numero_documento",
    "datEmissao": "data_emissao",
    "vlrDocumento": "valor_documento",
    "vlrGlosa": "valor_glosa",
    "vlrLiquido": "valor_liquido",
    "numMes": "mes",
    "numAno": "ano",
    "urlDocumento": "url_documento",
}

COLUNAS_TEXTO = ["deputado", "uf", "partido", "categoria", "fornecedor", "numero_documento", "url_documento"]
COLUNAS_VALOR = ["valor_documento", "valor_glosa", "valor_liquido"]


def ler_csv(caminho: Path) -> pd.DataFrame:
    """Lê o CSV da Câmara (separado por `;`) mantendo tudo como texto."""
    return pd.read_csv(caminho, sep=";", dtype=str, encoding="utf-8-sig", keep_default_na=False)


def para_numero(serie: pd.Series) -> pd.Series:
    """Converte valores como "1234.56" ou "1.234,56" em número."""
    texto = serie.astype(str).str.strip()
    formato_brasileiro = texto.str.contains(",", regex=False)
    texto = texto.where(~formato_brasileiro, texto.str.replace(".", "", regex=False).str.replace(",", ".", regex=False))
    return pd.to_numeric(texto, errors="coerce").fillna(0.0)


def limpar(bruto: pd.DataFrame) -> pd.DataFrame:
    faltando = set(COLUNAS) - set(bruto.columns)
    if faltando:
        raise ValueError(f"Colunas ausentes no arquivo: {sorted(faltando)}")

    tabela = bruto[list(COLUNAS)].rename(columns=COLUNAS).copy()

    for coluna in COLUNAS_TEXTO:
        tabela[coluna] = tabela[coluna].astype(str).str.strip().str.upper()
    tabela["url_documento"] = bruto["urlDocumento"].astype(str).str.strip()  # URL não vai para maiúsculas

    for coluna in COLUNAS_VALOR:
        tabela[coluna] = para_numero(tabela[coluna]).round(2)

    tabela["cnpj_cpf"] = tabela["cnpj_cpf"].map(somente_digitos)
    tabela["id_documento"] = pd.to_numeric(tabela["id_documento"], errors="coerce")
    tabela["id_deputado"] = pd.to_numeric(tabela["id_deputado"], errors="coerce")
    tabela["mes"] = pd.to_numeric(tabela["mes"], errors="coerce")
    tabela["ano"] = pd.to_numeric(tabela["ano"], errors="coerce")
    tabela["data_emissao"] = (
        pd.to_datetime(tabela["data_emissao"].str[:10], errors="coerce").dt.strftime("%Y-%m-%d")
    )

    # Despesas das lideranças partidárias não têm deputado associado. Ficam de fora.
    tabela = tabela[tabela["id_deputado"].notna() & tabela["id_documento"].notna()]
    tabela = tabela.drop_duplicates(subset="id_documento")

    for coluna in ["id_documento", "id_deputado", "mes", "ano"]:
        tabela[coluna] = tabela[coluna].astype(int)
    return tabela.reset_index(drop=True)
