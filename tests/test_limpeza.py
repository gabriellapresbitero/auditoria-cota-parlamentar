import unittest

import pandas as pd

from auditoria_cota.limpeza import limpar, para_numero
from tests.dados_teste import despesa, tabela


class TestParaNumero(unittest.TestCase):
    def test_formatos(self):
        valores = pd.Series(["1234.56", "1.234,56", "0", "", "abc", "-35.10"])
        self.assertEqual(para_numero(valores).tolist(), [1234.56, 1234.56, 0.0, 0.0, 0.0, -35.10])


class TestLimpar(unittest.TestCase):
    def test_renomeia_e_converte_tipos(self):
        limpa = limpar(tabela(despesa(ideDocumento="10", vlrLiquido="150.5")))
        linha = limpa.iloc[0]
        self.assertEqual(linha["id_documento"], 10)
        self.assertEqual(linha["valor_liquido"], 150.5)
        self.assertEqual(linha["data_emissao"], "2025-03-10")
        self.assertEqual(linha["deputado"], "FULANA DE TAL")

    def test_cnpj_fica_so_com_digitos(self):
        limpa = limpar(tabela(despesa(txtCNPJCPF="11.222.333/0001-81")))
        self.assertEqual(limpa.loc[0, "cnpj_cpf"], "11222333000181")

    def test_url_mantem_maiusculas_e_minusculas(self):
        limpa = limpar(tabela(despesa(urlDocumento="https://exemplo.com/Nota")))
        self.assertEqual(limpa.loc[0, "url_documento"], "https://exemplo.com/Nota")

    def test_remove_despesas_de_lideranca_sem_deputado(self):
        limpa = limpar(tabela(despesa(), despesa(nuDeputadoId="", txNomeParlamentar="LIDERANÇA DO XYZ")))
        self.assertEqual(len(limpa), 1)

    def test_remove_documento_repetido(self):
        limpa = limpar(tabela(despesa(ideDocumento="5"), despesa(ideDocumento="5")))
        self.assertEqual(len(limpa), 1)

    def test_data_invalida_vira_vazio(self):
        limpa = limpar(tabela(despesa(datEmissao="")))
        self.assertTrue(pd.isna(limpa.loc[0, "data_emissao"]))

    def test_erro_quando_falta_coluna(self):
        with self.assertRaisesRegex(ValueError, "vlrLiquido"):
            limpar(tabela(despesa()).drop(columns="vlrLiquido"))


if __name__ == "__main__":
    unittest.main()
