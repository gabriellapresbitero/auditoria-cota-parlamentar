-- Estrutura do banco da auditoria.

CREATE TABLE IF NOT EXISTS despesas (
    id_documento      INTEGER PRIMARY KEY,
    id_deputado       INTEGER NOT NULL,
    deputado          TEXT    NOT NULL,
    uf                TEXT,
    partido           TEXT,
    categoria         TEXT    NOT NULL,
    fornecedor        TEXT,
    cnpj_cpf          TEXT,
    numero_documento  TEXT,
    data_emissao      TEXT,
    valor_documento   REAL    NOT NULL,
    valor_glosa       REAL    NOT NULL DEFAULT 0,
    valor_liquido     REAL    NOT NULL,
    mes               INTEGER,
    ano               INTEGER,
    url_documento     TEXT
);

CREATE INDEX IF NOT EXISTS idx_despesas_deputado   ON despesas (id_deputado);
CREATE INDEX IF NOT EXISTS idx_despesas_fornecedor ON despesas (cnpj_cpf);
CREATE INDEX IF NOT EXISTS idx_despesas_categoria  ON despesas (categoria);

-- Cada linha é um indício encontrado por uma regra.
-- Uma mesma despesa pode aparecer em mais de uma regra.
CREATE TABLE IF NOT EXISTS suspeitas (
    id_documento  INTEGER NOT NULL REFERENCES despesas (id_documento),
    regra         TEXT    NOT NULL,
    pontos        INTEGER NOT NULL,
    detalhe       TEXT    NOT NULL,
    PRIMARY KEY (id_documento, regra)
);
