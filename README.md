# 🏛️ Auditoria da Cota Parlamentar

[![Testes](https://github.com/gabriellapresbitero/auditoria-cota-parlamentar/actions/workflows/testes.yml/badge.svg)](https://github.com/gabriellapresbitero/auditoria-cota-parlamentar/actions/workflows/testes.yml)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![SQL](https://img.shields.io/badge/SQL-SQLite-003B57?logo=sqlite&logoColor=white)

Ferramenta que lê **todas as despesas reembolsadas aos deputados federais** e aponta as que
merecem ser conferidas: notas duplicadas, CNPJ inválido, valores fora do padrão e outros sinais
de alerta.

## O problema

Cada deputado federal tem direito à **Cota para o Exercício da Atividade Parlamentar (CEAP)**,
um reembolso mensal de gastos como combustível, passagens, alimentação e divulgação do mandato.
São **centenas de milhares de notas fiscais por ano**, pagas com dinheiro público.

Os dados são abertos, mas ninguém consegue conferir nota por nota. Este projeto faz uma
**triagem automática**: separa, no meio de todas as despesas, as poucas que têm mais chance de
estarem erradas. Assim, um jornalista, um órgão de controle ou um cidadão sabe por onde começar.

Projeto inspirado na [Operação Serenata de Amor](https://serenata.ai).

## Regras de auditoria

Cada regra dá **pontos** conforme a força do indício. As regras em SQL ficam em
[`sql/regras/`](sql/regras). Para criar uma nova, basta adicionar um arquivo `.sql`.

| Regra | Pontos | O que procura | Onde |
|---|:---:|---|---|
| `nota_duplicada` | 3 | Mesma nota (fornecedor, número e valor) reembolsada mais de uma vez | SQL com `ROW_NUMBER()` |
| `documento_fornecedor_invalido` | 2 | CPF/CNPJ do fornecedor com dígito verificador errado | SQL + função Python registrada no SQLite |
| `valor_atipico` | 2 | Valor muito acima do normal da categoria (Q3 + 3×IQR, o critério do boxplot) | Python/pandas |
| `fornecedor_exclusivo` | 1 | Fornecedor que recebeu R$ 50 mil ou mais de **um único** deputado | SQL com CTE |
| `valor_redondo` | 1 | Divulgação ou consultoria com valor "cheio" (múltiplo de R$ 1.000) | SQL |

Com isso, o projeto monta um **ranking de deputados** por pontos, com o valor suspeito e o
percentual que ele representa do total gasto.

> ⚠️ **Indício não é prova.** Um CNPJ inválido pode ser erro de digitação. Uma nota
> "duplicada" pode ser uma correção. O objetivo é priorizar o que conferir, e cada indício traz
> o link da nota fiscal original.

### Decisões e cuidados com os dados

- **Despesas de liderança** (ex.: "LIDERANÇA DO PARTIDO X") não têm deputado associado e ficam de fora.
- **Valores negativos** são estornos de passagens aéreas. A regra de valor atípico os ignora.
- **Aluguel de escritório e locação de veículos** costumam ter valores redondos legítimos,
  então ficam fora da regra `valor_redondo`.
- **Categorias com menos de 30 despesas** não entram na regra de valor atípico, porque com
  poucos dados os quartis não são confiáveis.
- **Uma despesa pode cair em várias regras.** Os pontos somam, mas o valor só é contado uma vez no ranking.

## Como rodar

Pré-requisito: Python 3.11 ou mais novo.

```bash
git clone https://github.com/gabriellapresbitero/auditoria-cota-parlamentar.git
cd auditoria-cota-parlamentar
python -m venv .venv
source .venv/bin/activate        # no Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Todas as despesas do ano passado (o download tem algumas dezenas de MB)
python -m auditoria_cota

# Só os deputados de Pernambuco em 2025
python -m auditoria_cota --ano 2025 --uf PE

# Usando um CSV que você já baixou
python -m auditoria_cota --arquivo Ano-2025.csv --ano 2025
```

Os dados vêm de `https://www.camara.leg.br/cotas/Ano-<ano>.csv.zip`, do
[portal de dados abertos da Câmara](https://dadosabertos.camara.leg.br).

### Saídas (`saida/<ano>/`)

| Arquivo | Para quê |
|---|---|
| `auditoria.db` | Banco **SQLite** com as tabelas `despesas` e `suspeitas` |
| `suspeitas_detalhadas.csv` | Cada indício com deputado, fornecedor, valor e link da nota |
| `ranking_deputados.csv` | Pontos, valor suspeito e % do gasto por deputado |
| `resumo_por_regra.csv` | Quantos indícios cada regra encontrou |
| `relatorio.md` | Resumo pronto para ler ou publicar |

Os CSVs usam `;` e vírgula decimal, então abrem direto no Excel e no **Power BI**.
Para explorar os dados com SQL, veja as consultas em [`sql/analises.sql`](sql/analises.sql)
(gasto por categoria, maiores fornecedores, média por estado, evolução mensal).

## Testes

```bash
python -m unittest discover -s tests -t . -v
```

Os testes cobrem a validação de CPF/CNPJ, a limpeza dos dados, cada regra (casos que devem e
que **não** devem ser marcados) e o pipeline completo, com um CSV no formato da Câmara. Eles
rodam no GitHub Actions a cada push.

## Estrutura

```
auditoria_cota/
├── __main__.py     # linha de comando e orquestração
├── coleta.py       # download e descompactação do arquivo da Câmara
├── limpeza.py      # colunas, tipos, valores e CPF/CNPJ
├── documentos.py   # validação de CPF e CNPJ (dígitos verificadores)
├── banco.py        # SQLite: criação, carga e função Python dentro do SQL
├── regras.py       # executa as regras .sql e a regra de valor atípico
└── relatorio.py    # ranking, CSVs e relatório em Markdown
sql/
├── schema.sql      # tabelas e índices
├── regras/         # uma regra de auditoria por arquivo
└── analises.sql    # consultas exploratórias
tests/
```

## Próximos passos

- [ ] Regra de refeições caras demais para uma pessoa (valor por nota de alimentação)
- [ ] Consultar a Receita Federal para saber se o CNPJ estava ativo na data da nota
- [ ] Comparar vários anos para achar fornecedores que surgem e somem
- [ ] Painel no Power BI a partir dos CSVs

---
Feito por **Gabriella Presbítero** · Licença MIT
