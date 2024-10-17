import os

import pytest
from seiws.client import SeiClient

PROCESSOS_HM = [
    "53500.200727/2014-24",
    "53500.201008/2014-21",
    "53500.201144/2015-00",
    "53500.000567/2016-87",
]
USUARIOS_HM = [
    "100000141",
    "100003387",
    "100000205",
    "100000474",
    "100000641",
    "100003137",
    "100000737",
    "100001719",
    "100003260",
    "100001292",
    "100003429",
    "100001426",
]


class TestAtribuirProcesso:
    @pytest.mark.parametrize("protocolo_procedimento", PROCESSOS_HM)
    @pytest.mark.parametrize("id_usuario", USUARIOS_HM)
    def test_atribuir_processo_hm_bloqueio(self, protocolo_procedimento, id_usuario):
        client = SeiClient(
            sigla_sistema="InovaFiscaliza",
            chave_api=os.getenv("SEI_HM_API_KEY_BLOQUEIO"),
        )
        assert client.atribuir_processo(
            id_unidade="110000965",  # SFI
            protocolo_procedimento=protocolo_procedimento,
            id_usuario=id_usuario,
            sin_reabrir="S",
        )

    # @pytest.mark.parametrize("id_unidade", [d["IdUnidade"] for d in UNIDADES_INSTRUCAO])
    # def test_atribuir_processo_hm_instrucao(self, id_unidade):
    #     client = SeiClient(
    #         sigla_sistema="InovaFiscaliza",
    #         chave_api=os.getenv("SEI_HM_API_KEY_INSTRUCAO"),
    #     )
    #     assert client.atribuir_processo(
    #         id_unidade=id_unidade,
    #         protocolo_procedimento="53554.000005/2024-18",
    #         id_usuario="100001310",
    #         sin_reabrir="S",
    #     )
