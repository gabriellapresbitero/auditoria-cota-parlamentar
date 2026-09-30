import unittest

from auditoria_cota import banco
from auditoria_cota.limpeza import limpar
from auditoria_cota.regras import auditar, carregar_regras, executar_regras_sql, regra_valor_atipico
from tests.dados_teste import CNPJ_INVALIDO, despesa, gerar_cnpj, tabela

DIVULGACAO = "DIVULGAÇÃO DA ATIVIDADE PARLAMENTAR."
ALUGUEL = "MANUTENÇÃO DE ESCRITÓRIO DE APOIO À ATIVIDADE PARLAMENTAR"


def preparar(*linhas):
    despesas = limpar(tabela(*linhas))
    conexao = banco.conectar(":memory:")
    banco.carregar_despesas(conexao, despesas)
    return conexao, despesas


def rodar(nome_regra, *linhas, valor_minimo=50_000):
    conexao, _ = preparar(*linhas)
    regra = next(r for r in carregar_regras() if r.nome == nome_regra)
    return executar_regras_sql(conexao, [regra], {"valor_minimo": valor_minimo})


class TestCarregarRegras(unittest.TestCase):
    def test_le_cabecalho_de_todas_as_regras(self):
        regras = {r.nome: r.pontos for r in carregar_regras()}
        self.assertEqual(regras, {
            "nota_duplicada": 3,
            "documento_fornecedor_invalido": 2,
            "fornecedor_exclusivo": 1,
            "valor_redondo": 1,
        })

    def test_toda_regra_tem_descricao(self):
        for regra in carregar_regras():
            self.assertTrue(regra.descricao, regra.nome)


class TestNotaDuplicada(unittest.TestCase):
    def test_marca_so_a_repeticao(self):
        primeira = despesa(ideDocumento="100", txtNumero="555", datEmissao="2025-03-01")
        repetida = despesa(ideDocumento="101", txtNumero="555", datEmissao="2025-03-20")
        resultado = rodar("nota_duplicada", primeira, repetida)
        self.assertEqual(resultado["id_documento"].tolist(), [101])
        self.assertIn("100", resultado.loc[0, "detalhe"])

    def test_mesma_nota_de_deputados_diferentes_nao_e_duplicada(self):
        resultado = rodar("nota_duplicada",
                          despesa(txtNumero="555"), despesa(txtNumero="555", nuDeputadoId="2"))
        self.assertTrue(resultado.empty)

    def test_nota_sem_numero_e_ignorada(self):
        resultado = rodar("nota_duplicada", despesa(txtNumero="S/N"), despesa(txtNumero="S/N"))
        self.assertTrue(resultado.empty)

    def test_mesmo_numero_com_valor_diferente_nao_e_duplicada(self):
        resultado = rodar("nota_duplicada",
                          despesa(txtNumero="7", vlrDocumento="10"), despesa(txtNumero="7", vlrDocumento="20"))
        self.assertTrue(resultado.empty)


class TestDocumentoInvalido(unittest.TestCase):
    def test_marca_cnpj_invalido_e_ignora_vazio(self):
        resultado = rodar("documento_fornecedor_invalido",
                          despesa(ideDocumento="1", txtCNPJCPF=CNPJ_INVALIDO),
                          despesa(ideDocumento="2", txtCNPJCPF=""),
                          despesa(ideDocumento="3"))
        self.assertEqual(resultado["id_documento"].tolist(), [1])


class TestFornecedorExclusivo(unittest.TestCase):
    def test_marca_fornecedor_alto_de_um_so_deputado(self):
        exclusivo, compartilhado, pequeno = gerar_cnpj(1), gerar_cnpj(2), gerar_cnpj(3)
        resultado = rodar(
            "fornecedor_exclusivo",
            despesa(ideDocumento="1", txtCNPJCPF=exclusivo, vlrLiquido="30000"),
            despesa(ideDocumento="2", txtCNPJCPF=exclusivo, vlrLiquido="30000"),
            despesa(ideDocumento="3", txtCNPJCPF=compartilhado, vlrLiquido="30000"),
            despesa(ideDocumento="4", txtCNPJCPF=compartilhado, vlrLiquido="30000", nuDeputadoId="2"),
            despesa(ideDocumento="5", txtCNPJCPF=pequeno, vlrLiquido="10000"),
        )
        self.assertEqual(sorted(resultado["id_documento"]), [1, 2])

    def test_valor_minimo_e_configuravel(self):
        resultado = rodar("fornecedor_exclusivo",
                          despesa(txtCNPJCPF=gerar_cnpj(9), vlrLiquido="10000"), valor_minimo=5_000)
        self.assertEqual(len(resultado), 1)


class TestValorRedondo(unittest.TestCase):
    def test_casos(self):
        resultado = rodar(
            "valor_redondo",
            despesa(ideDocumento="1", txtDescricao=DIVULGACAO, vlrDocumento="15000.00"),
            despesa(ideDocumento="2", txtDescricao=DIVULGACAO, vlrDocumento="15000.50"),
            despesa(ideDocumento="3", txtDescricao=DIVULGACAO, vlrDocumento="500"),
            despesa(ideDocumento="4", txtDescricao=ALUGUEL, vlrDocumento="5000"),
            despesa(ideDocumento="5", txtDescricao="CONSULTORIAS, PESQUISAS E TRABALHOS TÉCNICOS.",
                    vlrDocumento="8000"),
        )
        self.assertEqual(sorted(resultado["id_documento"]), [1, 5])


class TestValorAtipico(unittest.TestCase):
    def test_marca_valor_extremo_da_categoria(self):
        normais = [despesa(vlrLiquido=str(200 + i)) for i in range(40)]
        extremo = despesa(ideDocumento="999", vlrLiquido="5000")
        despesas = limpar(tabela(*normais, extremo))
        resultado = regra_valor_atipico(despesas)
        self.assertEqual(resultado["id_documento"].tolist(), [999])
        self.assertIn("mediana", resultado.iloc[0]["detalhe"])

    def test_categoria_com_poucas_despesas_e_ignorada(self):
        poucas = [despesa(vlrLiquido="200") for _ in range(5)] + [despesa(vlrLiquido="5000")]
        self.assertTrue(regra_valor_atipico(limpar(tabela(*poucas))).empty)

    def test_valores_negativos_sao_ignorados(self):
        # Valores negativos são estornos de passagens aéreas, não gastos.
        linhas = [despesa(vlrLiquido="200") for _ in range(40)] + [despesa(vlrLiquido="-9000")]
        self.assertTrue(regra_valor_atipico(limpar(tabela(*linhas))).empty)


class TestAuditar(unittest.TestCase):
    def test_despesa_pode_cair_em_mais_de_uma_regra(self):
        cnpj = gerar_cnpj(4)
        conexao, despesas = preparar(
            despesa(ideDocumento="1", txtNumero="1", txtCNPJCPF=cnpj, txtDescricao=DIVULGACAO, vlrDocumento="20000"),
            despesa(ideDocumento="2", txtNumero="1", txtCNPJCPF=cnpj, txtDescricao=DIVULGACAO, vlrDocumento="20000"),
        )
        auditar(conexao, despesas)
        regras_do_2 = banco.consultar(conexao, "SELECT regra FROM suspeitas WHERE id_documento = 2")
        self.assertEqual(set(regras_do_2["regra"]), {"nota_duplicada", "valor_redondo"})

    def test_rodar_duas_vezes_nao_duplica(self):
        conexao, despesas = preparar(despesa(txtCNPJCPF=CNPJ_INVALIDO))
        auditar(conexao, despesas)
        auditar(conexao, despesas)
        total = banco.consultar(conexao, "SELECT COUNT(*) AS n FROM suspeitas")
        self.assertEqual(total["n"].iloc[0], 1)


if __name__ == "__main__":
    unittest.main()
