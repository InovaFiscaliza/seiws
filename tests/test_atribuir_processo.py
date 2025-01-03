import os

import pytest
from seiws.client import SeiClient

PROCESSOS_HM = [
    "53500.000124/2024-04"  # Demanda Externa: Ministério Público Federal",
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

sei_client = SeiClient(
    sigla_sistema=os.getenv("SIGLA_SISTEMA"),
    chave_api=os.getenv("SEI_HM_API_KEY_BLOQUEIO"),
)

USUARIOS_FISF = [
    u["IdUsuario"] for u in sei_client.listar_usuarios(sigla_unidade="FISF")
]

USUARIOS_FIGF = [
    u["IdUsuario"] for u in sei_client.listar_usuarios(sigla_unidade="FIGF")
]


class TestAtribuirProcesso:
    """
    Test the process assignment functionality for the SFI, FISF and FIGF unit.

    This test case checks that the `atribuir_processo` method of the `SeiClient` class
    correctly assigns a process to a user in the unit.

    The test is parameterized with a list of process protocols (`PROCESSOS_HM`) and a list
    of user IDs (`USUARIOS_*`). For each combination of process protocol and user ID,
    the test calls the `atribuir_processo` method and asserts that the call returns `True`,
    indicating that the process was successfully assigned.
    """

    # @pytest.fixture
    # def sei_client(self):
    #     return SeiClient(
    #         sigla_sistema=os.getenv("SIGLA_SISTEMA"),
    #         chave_api=os.getenv("SEI_HM_API_KEY_BLOQUEIO"),
    #     )

    @pytest.mark.parametrize("protocolo_procedimento", PROCESSOS_HM)
    @pytest.mark.parametrize("id_usuario", USUARIOS_SFI)
    def test_atribuir_processo_hm_sfi(self, protocolo_procedimento, id_usuario):
        assert sei_client.atribuir_processo(
            sigla_unidade="SFI",
            protocolo_procedimento=protocolo_procedimento,
            id_usuario=id_usuario,
            sin_reabrir="S",
        )

    @pytest.mark.parametrize("protocolo_procedimento", PROCESSOS_HM)
    @pytest.mark.parametrize("id_usuario", USUARIOS_FISF)
    def test_atribuir_processo_hm_fisf(
        self,
        id_usuario,
        protocolo_procedimento,
    ):
        assert sei_client.atribuir_processo(
            sigla_unidade="FISF",  # FISF
            protocolo_procedimento=protocolo_procedimento,
            id_usuario=id_usuario,
            sin_reabrir="S",
        )

    @pytest.mark.parametrize("protocolo_procedimento", PROCESSOS_HM)
    @pytest.mark.parametrize("id_usuario", USUARIOS_FIGF)
    def test_atribuir_processo_hm_figf(
        self,
        id_usuario,
        protocolo_procedimento,
    ):
        assert sei_client.atribuir_processo(
            sigla_unidade="FIGF",  # FIGF
            protocolo_procedimento=protocolo_procedimento,
            id_usuario=id_usuario,
            sin_reabrir="S",
        )
