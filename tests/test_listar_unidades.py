import os
from seiws.client import SeiClient
from tests.constants import UNIDADES_BLOQUEIO, UNIDADES_INSTRUCAO, UNIDADES_FISCALIZA


class TestListarUnidades:
    def test_listar_unidades_hm_bloqueio(self):
        client = SeiClient(
            sigla_sistema=os.getenv("SIGLA_SISTEMA"),
            chave_api=os.getenv("SEI_HM_API_KEY_BLOQUEIO"),
        )
        unidades = client.listar_unidades()
        assert isinstance(unidades, list)
        assert set(unidade["IdUnidade"] for unidade in unidades) == set(
            unidade["IdUnidade"] for unidade in UNIDADES_BLOQUEIO
        )

    def test_listar_unidades_hm_instrucao(self):
        client = SeiClient(
            sigla_sistema=os.getenv("SIGLA_SISTEMA"),
            chave_api=os.getenv("SEI_HM_API_KEY_INSTRUCAO"),
        )
        unidades = client.listar_unidades()
        assert isinstance(unidades, list)
        assert set(unidade["IdUnidade"] for unidade in unidades) == set(
            unidade["IdUnidade"] for unidade in UNIDADES_INSTRUCAO
        )

    def test_listar_unidades_hm_fiscaliza(self):
        client = SeiClient(
            sigla_sistema="Fiscaliza",
            chave_api=os.getenv("SEI_HM_API_KEY_FISCALIZA"),
        )
        unidades = client.listar_unidades()
        assert isinstance(unidades, list)
        assert set(unidade["IdUnidade"] for unidade in unidades) == set(
            unidade["IdUnidade"] for unidade in UNIDADES_FISCALIZA
        )
