-- regra: fornecedor_exclusivo
-- pontos: 1
-- descricao: Fornecedor que recebeu muito dinheiro da cota, mas de um único deputado.
--
-- Empresas de verdade costumam atender vários clientes. Um fornecedor que
-- só aparece nas notas de um deputado, com valores altos, merece verificação:
-- pode ser uma empresa de fachada ou de alguém ligado ao gabinete.
-- :valor_minimo é definido no código (padrão: R$ 50.000 no período analisado).

WITH fornecedores AS (
    SELECT
        cnpj_cpf,
        COUNT(DISTINCT id_deputado) AS deputados_atendidos,
        SUM(valor_liquido)          AS total_recebido
    FROM despesas
    WHERE cnpj_cpf <> ''
    GROUP BY cnpj_cpf
)
SELECT
    d.id_documento,
    'fornecedor recebeu R$ ' || printf('%.2f', f.total_recebido) || ' apenas deste deputado' AS detalhe
FROM despesas AS d
JOIN fornecedores AS f ON f.cnpj_cpf = d.cnpj_cpf
WHERE f.deputados_atendidos = 1
  AND f.total_recebido >= :valor_minimo;
