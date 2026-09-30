-- regra: documento_fornecedor_invalido
-- pontos: 2
-- descricao: O CPF ou CNPJ do fornecedor não passa na conta dos dígitos verificadores.
--
-- documento_valido() não é uma função padrão do SQLite: ela é escrita em
-- Python (auditoria_cota/documentos.py) e registrada na conexão pelo projeto.
-- Fornecedores sem documento (ex.: companhias aéreas estrangeiras) ficam de fora.

SELECT
    id_documento,
    'CPF/CNPJ ' || cnpj_cpf || ' é inválido' AS detalhe
FROM despesas
WHERE cnpj_cpf <> ''
  AND documento_valido(cnpj_cpf) = 0;
