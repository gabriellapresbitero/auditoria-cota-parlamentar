"""Validação de CPF e CNPJ pelos dígitos verificadores.

Os dois últimos dígitos de um CPF ou CNPJ são calculados a partir dos
anteriores. Se a conta não bate, o número foi digitado errado ou foi
inventado. Numa nota fiscal de despesa pública, os dois casos merecem
atenção.
"""

from __future__ import annotations


def somente_digitos(texto: str | None) -> str:
    return "".join(c for c in (texto or "") if c.isdigit())


def _digito(numeros: list[int], pesos: list[int]) -> int:
    resto = sum(n * p for n, p in zip(numeros, pesos)) % 11
    return 0 if resto < 2 else 11 - resto


def cpf_valido(cpf: str) -> bool:
    numeros = [int(c) for c in somente_digitos(cpf)]
    if len(numeros) != 11 or len(set(numeros)) == 1:  # 111.111.111-11 passa na conta, mas é inválido
        return False
    d1 = _digito(numeros[:9], list(range(10, 1, -1)))
    d2 = _digito(numeros[:9] + [d1], list(range(11, 1, -1)))
    return numeros[9:] == [d1, d2]


def cnpj_valido(cnpj: str) -> bool:
    numeros = [int(c) for c in somente_digitos(cnpj)]
    if len(numeros) != 14 or len(set(numeros)) == 1:
        return False
    pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    pesos2 = [6] + pesos1
    d1 = _digito(numeros[:12], pesos1)
    d2 = _digito(numeros[:12] + [d1], pesos2)
    return numeros[12:] == [d1, d2]


def documento_valido(documento: str | None) -> bool:
    """Valida CPF (11 dígitos) ou CNPJ (14 dígitos). Qualquer outro tamanho é inválido."""
    digitos = somente_digitos(documento)
    if len(digitos) == 11:
        return cpf_valido(digitos)
    if len(digitos) == 14:
        return cnpj_valido(digitos)
    return False
