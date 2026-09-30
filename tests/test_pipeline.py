import contextlib
import io
import sqlite3
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from auditoria_cota.__main__ import main
from tests.dados_teste import CNPJ_INVALIDO, despesa, gerar_cnpj, tabela

DIVULGACAO = "DIVULGAÇÃO DA ATIVIDADE PARLAMENTAR."


def arquivo_de_exemplo(pasta: Path) -> Path:
    linhas = []
    # Deputada 1 (PE): uma nota duplicada e uma divulgação com valor redondo
    linhas += [
        despesa(ideDocumento="1", nuDeputadoId="1", txNomeParlamentar="Ana Souza", txtNumero="10",
                vlrDocumento="300", vlrLiquido="300"),
        despesa(ideDocumento="2", nuDeputadoId="1", txNomeParlamentar="Ana Souza", txtNumero="10",
                vlrDocumento="300", vlrLiquido="300"),
        despesa(ideDocumento="3", nuDeputadoId="1", txNomeParlamentar="Ana Souza", txtDescricao=DIVULGACAO,
                txtCNPJCPF=gerar_cnpj(7), vlrDocumento="12000", vlrLiquido="12000"),
    ]
    # Deputado 2 (SP): fornecedor com CNPJ inválido
    linhas += [
        despesa(ideDocumento="4", nuDeputadoId="2", txNomeParlamentar="Bruno Lima", sgUF="SP",
                txtCNPJCPF=CNPJ_INVALIDO, vlrLiquido="800"),
    ]
    # Deputada 3 (PE): só despesas normais
    linhas += [
        despesa(ideDocumento=str(100 + i), nuDeputadoId="3", txNomeParlamentar="Carla Dias",
                txtCNPJCPF=gerar_cnpj(20 + i), vlrLiquido="250")
        for i in range(5)
    ]
    caminho = pasta / "Ano-2025.csv"
    tabela(*linhas).to_csv(caminho, sep=";", index=False)
    return caminho


class TestPipelineCompleto(unittest.TestCase):
    def setUp(self):
        self.pasta = Path(tempfile.mkdtemp())
        self.csv = arquivo_de_exemplo(self.pasta)

    def rodar(self, *extras):
        args = ["--arquivo", str(self.csv), "--ano", "2025", "--saida", str(self.pasta / "saida"), *extras]
        with contextlib.redirect_stdout(io.StringIO()):
            return main(args)

    def ler(self, nome, escopo="2025"):
        return pd.read_csv(self.pasta / "saida" / escopo / nome, sep=";", decimal=",")

    def test_gera_arquivos(self):
        self.assertEqual(self.rodar(), 0)
        for nome in ["auditoria.db", "relatorio.md", "suspeitas_detalhadas.csv",
                     "ranking_deputados.csv", "resumo_por_regra.csv"]:
            with self.subTest(arquivo=nome):
                self.assertTrue((self.pasta / "saida" / "2025" / nome).exists())

    def test_ranking(self):
        self.rodar()
        ranking = self.ler("ranking_deputados.csv")
        self.assertEqual(ranking["deputado"].tolist(), ["ANA SOUZA", "BRUNO LIMA"])
        ana = ranking.iloc[0]
        self.assertEqual(ana["pontos"], 4)  # nota duplicada (3) + valor redondo (1)
        self.assertEqual(ana["despesas_suspeitas"], 2)
        self.assertEqual(ana["valor_suspeito"], 12300)
        self.assertAlmostEqual(ana["percentual_suspeito"], 97.6)

    def test_filtro_por_uf(self):
        self.rodar("--uf", "pe")
        ranking = self.ler("ranking_deputados.csv", escopo="2025_PE")
        self.assertEqual(ranking["deputado"].tolist(), ["ANA SOUZA"])

    def test_relatorio_tem_aviso_e_ranking(self):
        self.rodar()
        texto = (self.pasta / "saida" / "2025" / "relatorio.md").read_text(encoding="utf-8")
        self.assertIn("não", texto)
        self.assertIn("Ana Souza", texto)
        self.assertIn("R$ 12.300,00", texto)

    def test_consultas_exploratorias_rodam(self):
        self.rodar()
        sql = (Path(__file__).parent.parent / "sql" / "analises.sql").read_text(encoding="utf-8")
        with sqlite3.connect(self.pasta / "saida" / "2025" / "auditoria.db") as conexao:
            for consulta in [c for c in sql.split(";") if "SELECT" in c]:
                with self.subTest(consulta=consulta.strip()[:50]):
                    conexao.execute(consulta).fetchall()

    def test_uf_sem_despesas_retorna_erro(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(self.rodar("--uf", "AC"), 1)

    def test_arquivo_inexistente_retorna_erro(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main(["--arquivo", "nao_existe.csv"]), 1)


if __name__ == "__main__":
    unittest.main()
