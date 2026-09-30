-- regra: nota_duplicada
-- pontos: 3
-- descricao: A mesma nota fiscal (mesmo fornecedor, número e valor) foi apresentada mais de uma vez pelo mesmo deputado.
--
-- A primeira apresentação é considerada normal. As repetições são marcadas.
-- Notas sem número ("S/N", "0" ou vazio) ficam de fora, porque não dá para comparar.

WITH numeradas AS (
    SELECT
        id_documento,
        numero_documento,
        ROW_NUMBER() OVER (
            PARTITION BY id_deputado, cnpj_cpf, numero_documento, valor_documento
            ORDER BY data_emissao, id_documento
        ) AS ordem,
        FIRST_VALUE(id_documento) OVER (
            PARTITION BY id_deputado, cnpj_cpf, numero_documento, valor_documento
            ORDER BY data_emissao, id_documento
        ) AS primeira
    FROM despesas
    WHERE numero_documento NOT IN ('', 'S/N', 'SN', '0')
      AND cnpj_cpf <> ''
      AND valor_documento > 0
)
SELECT
    id_documento,
    'nota nº ' || numero_documento || ' já apresentada no documento ' || primeira AS detalhe
FROM numeradas
WHERE ordem > 1;
