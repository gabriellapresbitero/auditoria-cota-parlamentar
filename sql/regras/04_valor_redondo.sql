-- regra: valor_redondo
-- pontos: 1
-- descricao: Serviço de divulgação ou consultoria com valor redondo alto (múltiplo de R$ 1.000).
--
-- Nessas categorias o preço é livre e difícil de conferir. Valores
-- "cheios" como R$ 15.000,00 são um sinal clássico de nota montada.
-- Aluguel e locação de veículos ficam de fora: neles, valor redondo é normal.

SELECT
    id_documento,
    'valor redondo de R$ ' || CAST(valor_documento AS INTEGER) || ' em ' || categoria AS detalhe
FROM despesas
WHERE (categoria LIKE 'DIVULGA%' OR categoria LIKE 'CONSULTORIA%')
  AND valor_documento >= 1000
  AND valor_documento = CAST(valor_documento AS INTEGER)
  AND CAST(valor_documento AS INTEGER) % 1000 = 0;
