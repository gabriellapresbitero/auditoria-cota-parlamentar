import unittest

from auditoria_cota.documentos import cnpj_valido, cpf_valido, documento_valido, somente_digitos
from tests.dados_teste import CNPJ_VALIDO, CPF_VALIDO, gerar_cnpj


class TestDocumentos(unittest.TestCase):
    def test_cpf_valido(self):
        self.assertTrue(cpf_valido("529.982.247-25"))
        self.assertTrue(cpf_valido(CPF_VALIDO))

    def test_cpf_com_digito_errado(self):
        self.assertFalse(cpf_valido("529.982.247-24"))

    def test_cpf_com_todos_digitos_iguais_e_invalido(self):
        self.assertFalse(cpf_valido("111.111.111-11"))

    def test_cnpj_valido(self):
        self.assertTrue(cnpj_valido("11.222.333/0001-81"))
        self.assertTrue(cnpj_valido(CNPJ_VALIDO))

    def test_cnpj_com_digito_errado(self):
        self.assertFalse(cnpj_valido("11.222.333/0001-80"))

    def test_cnpj_zerado_e_invalido(self):
        self.assertFalse(cnpj_valido("00000000000000"))

    def test_documento_escolhe_cpf_ou_cnpj_pelo_tamanho(self):
        self.assertTrue(documento_valido(CPF_VALIDO))
        self.assertTrue(documento_valido(CNPJ_VALIDO))
        self.assertFalse(documento_valido("12345"))
        self.assertFalse(documento_valido(""))
        self.assertFalse(documento_valido(None))

    def test_somente_digitos(self):
        self.assertEqual(somente_digitos("11.222.333/0001-81"), "11222333000181")

    def test_gerador_dos_testes_cria_cnpjs_validos(self):
        for numero in range(1, 50):
            self.assertTrue(cnpj_valido(gerar_cnpj(numero)), gerar_cnpj(numero))


if __name__ == "__main__":
    unittest.main()
