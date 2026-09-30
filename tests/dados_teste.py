"""Dados falsos no mesmo formato do CSV da Câmara, para os testes."""

from __future__ import annotations

import itertools

import pandas as pd

from auditoria_cota.documentos import _digito

CNPJ_VALIDO = "11222333000181"
CPF_VALIDO = "52998224725"
CNPJ_INVALIDO = "11222333000100"

_ids = itertools.count(1)


def gerar_cnpj(numero: int) -> str:
    """Gera um CNPJ válido diferente para cada número."""
    base = [int(c) for c in f"{numero:08d}0001"]
    pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    d1 = _digito(base, pesos1)
    d2 = _digito(base + [d1], [6] + pesos1)
    return "".join(map(str, base + [d1, d2]))


def despesa(**campos) -> dict:
    """Uma linha do CSV da Câmara. Qualquer campo pode ser trocado por parâmetro."""
    linha = {
        "ideDocumento": str(next(_ids)),
        "nuDeputadoId": "1",
        "txNomeParlamentar": "Fulana de Tal",
        "cpf": "",
        "sgUF": "PE",
        "sgPartido": "ABC",
        "txtDescricao": "COMBUSTÍVEIS E LUBRIFICANTES.",
        "txtFornecedor": "Posto Exemplo",
        "txtCNPJCPF": CNPJ_VALIDO,
        "txtNumero": str(next(_ids)),
        "datEmissao": "2025-03-10T00:00:00",
        "vlrDocumento": "200.00",
        "vlrGlosa": "0",
        "vlrLiquido": "200.00",
        "numMes": "3",
        "numAno": "2025",
        "urlDocumento": "https://www.camara.leg.br/cota-parlamentar/nota-fiscal-eletronica?ideDocumentoFiscal=1",
    }
    linha.update(campos)
    return linha


def tabela(*linhas: dict) -> pd.DataFrame:
    return pd.DataFrame(list(linhas)).astype(str)
