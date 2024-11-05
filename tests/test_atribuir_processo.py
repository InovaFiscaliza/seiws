import os

import pytest
from seiws.client import SeiClient
from seiws.helpers import download_wsdl, instanciar_cliente_soap


PROCESSOS_HM = [
    "53500.000124/2024-04",  # Demanda Externa: Ministério Público Federal",
    "53500.201128/2014-28",  # Demanda Externa: Órgãos Governamentais Federais
    "53500.059070/2019-18",  # Demanda Externa: Judiciário
    "53569.200039/2014-70",  # Procuradoria: Cumprimento de Decisão Judicial
]

CLIENTE_SOAP = instanciar_cliente_soap(download_wsdl("homologação"))


class TestAtribuirProcessoBloqueio:
    """
    Test the process assignment functionality for the SFI, FISF and FIGF unit.

    This test case checks that the `atribuir_processo` method of the `SeiClient` class
    correctly assigns a process to a user in the unit.

    The test is parameterized with a list of process protocols (`PROCESSOS_HM`) and a list
    of user IDs (client.usuarios). For each combination of process protocol and user ID,
    the test calls the `atribuir_processo` method and asserts that the call returns `True`,
    indicating that the process was successfully assigned.
    """

    @pytest.fixture
    def sei_client_sfi(self):
        return SeiClient(
            cliente_soap=CLIENTE_SOAP,
            sigla_sistema="InovaFiscaliza",
            chave_api=os.environ["SEI_HM_API_KEY_BLOQUEIO"],
            sigla_unidade="SFI",
        )

    @pytest.fixture
    def sei_client_fisf(self):
        return SeiClient(
            cliente_soap=CLIENTE_SOAP,
            sigla_sistema="InovaFiscaliza",
            chave_api=os.environ["SEI_HM_API_KEY_BLOQUEIO"],
            sigla_unidade="FISF",
        )

    @pytest.fixture
    def sei_client_figf(self):
        return SeiClient(
            cliente_soap=CLIENTE_SOAP,
            sigla_sistema="InovaFiscaliza",
            chave_api=os.environ["SEI_HM_API_KEY_BLOQUEIO"],
            sigla_unidade="FIGF",
        )

    @pytest.mark.parametrize("protocolo_procedimento", PROCESSOS_HM)
    def test_atribuir_processo_hm_sfi(self, sei_client_sfi, protocolo_procedimento):
        for sigla_usuario in sei_client_sfi.usuarios:
            assert sei_client_sfi.atribuir_processo(
                protocolo_procedimento=protocolo_procedimento,
                sigla_usuario=sigla_usuario,
                sin_reabrir="S",
            )

    @pytest.mark.parametrize("protocolo_procedimento", PROCESSOS_HM)
    def test_atribuir_processo_hm_fisf(self, sei_client_fisf, protocolo_procedimento):
        for sigla_usuario in sei_client_fisf.usuarios:
            assert sei_client_fisf.atribuir_processo(
                protocolo_procedimento=protocolo_procedimento,
                sigla_usuario=sigla_usuario,
                sin_reabrir="S",
            )

    @pytest.mark.parametrize("protocolo_procedimento", PROCESSOS_HM)
    def test_atribuir_processo_hm_figf(self, sei_client_figf, protocolo_procedimento):
        for sigla_usuario in sei_client_figf.usuarios:
            assert sei_client_figf.atribuir_processo(
                protocolo_procedimento=protocolo_procedimento,
                sigla_usuario=sigla_usuario,
                sin_reabrir="S",
            )
