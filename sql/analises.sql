-- Consultas exploratórias para o banco saida/<ano>/auditoria.db
-- Rode no DB Browser for SQLite, no DBeaver ou com:
--     sqlite3 saida/2025/auditoria.db < sql/analises.sql

-- 1) Quanto cada categoria consumiu da cota
SELECT categoria,
       COUNT(*)                     AS despesas,
       ROUND(SUM(valor_liquido), 2) AS total,
       ROUND(AVG(valor_liquido), 2) AS media
FROM despesas
GROUP BY categoria
ORDER BY total DESC;

-- 2) Os 20 fornecedores que mais receberam, e de quantos deputados
SELECT fornecedor, cnpj_cpf,
       COUNT(DISTINCT id_deputado)  AS deputados,
       ROUND(SUM(valor_liquido), 2) AS total
FROM despesas
WHERE cnpj_cpf <> ''
GROUP BY cnpj_cpf
ORDER BY total DESC
LIMIT 20;

-- 3) Gasto total por estado, com média por deputado
SELECT uf,
       COUNT(DISTINCT id_deputado)                          AS deputados,
       ROUND(SUM(valor_liquido), 2)                         AS total,
       ROUND(SUM(valor_liquido) / COUNT(DISTINCT id_deputado), 2) AS media_por_deputado
FROM despesas
GROUP BY uf
ORDER BY media_por_deputado DESC;

-- 4) Evolução mensal dos gastos
SELECT ano, mes, ROUND(SUM(valor_liquido), 2) AS total
FROM despesas
GROUP BY ano, mes
ORDER BY ano, mes;

-- 5) Deputados com indícios em mais de uma regra diferente
SELECT d.deputado, d.partido, d.uf,
       COUNT(DISTINCT s.regra) AS regras_diferentes,
       GROUP_CONCAT(DISTINCT s.regra) AS regras
FROM suspeitas AS s
JOIN despesas  AS d USING (id_documento)
GROUP BY d.id_deputado
HAVING COUNT(DISTINCT s.regra) > 1
ORDER BY regras_diferentes DESC;
