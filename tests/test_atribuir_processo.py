import os

import pytest
from seiws.client import SeiClient
from tests.constants import UNIDADES_BLOQUEIO, UNIDADES_INSTRUCAO

PROCESSOS_HM = [
    "53500.201128/2014-28",  # Demanda Externa: Órgãos Governamentais Federais
]
USUARIOS_SFI = [
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

USUARIOS_FISF = ["100003241", "100000214", "100000217"]


class TestAtribuirProcesso:
    @pytest.fixture
    def sei_client():
        return SeiClient(
            sigla_sistema="InovaFiscaliza",
            chave_api=os.getenv("SEI_HM_API_KEY_BLOQUEIO"),
        )

    @pytest.mark.parametrize("protocolo_procedimento", PROCESSOS_HM)
    @pytest.mark.parametrize("id_usuario", USUARIOS_SFI)
    def test_atribuir_processo_hm_sfi(
        self, sei_client, protocolo_procedimento, id_usuario
    ):
        assert sei_client.atribuir_processo(
            id_unidade="110000965",  # SFI
            protocolo_procedimento=protocolo_procedimento,
            id_usuario=id_usuario,
            sin_reabrir="S",
        )

    @pytest.mark.parametrize("protocolo_procedimento", PROCESSOS_HM)
    @pytest.mark.parametrize("id_usuario", USUARIOS_FISF)
    def test_atribuir_processo_hm_fisf(
        self, sei_client, protocolo_procedimento, id_usuario
    ):
        assert sei_client.atribuir_processo(
            id_unidade="110000973",  # FISF
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
