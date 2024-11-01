import os

import pytest
from seiws.client import SeiClient

PROCESSOS_HM = [
    "53500.000124/2024-04",  # Demanda Externa: Ministério Público Federal",
    "53500.201128/2014-28",  # Demanda Externa: Órgãos Governamentais Federais
    "53500.059070/2019-18",  # Demanda Externa: Judiciário
    "53569.200039/2014-70",  # Procuradoria: Cumprimento de Decisão Judicial
]

UNIDADES = ["SFI", "FISF", "FIGF"]

FLAGS = ["S"]


class TestConsultarProcedimento:
    @pytest.fixture
    def sei_client(self):
        return SeiClient(
            sigla_sistema=os.getenv("SIGLA_SISTEMA"),
            chave_api=os.getenv("SEI_HM_API_KEY_BLOQUEIO"),
        )

    @pytest.mark.parametrize("sigla_unidade", UNIDADES)
    @pytest.mark.parametrize("protocolo_procedimento", PROCESSOS_HM)
    @pytest.mark.parametrize("sin_retornar_assuntos", FLAGS)
    @pytest.mark.parametrize("sin_retornar_interessados", FLAGS)
    @pytest.mark.parametrize("sin_retornar_observacoes", FLAGS)
    @pytest.mark.parametrize("sin_retornar_andamento_geracao", FLAGS)
    @pytest.mark.parametrize("sin_retornar_andamento_conclusao", FLAGS)
    @pytest.mark.parametrize("sin_retornar_ultimo_andamento", FLAGS)
    @pytest.mark.parametrize("sin_retornar_unidades_procedimento_aberto", FLAGS)
    @pytest.mark.parametrize("sin_retornar_procedimentos_relacionados", FLAGS)
    @pytest.mark.parametrize("sin_retornar_procedimentos_anexados", FLAGS)
    def test_consultar_procedimento_hm(
        self,
        sei_client,
        sigla_unidade,
        protocolo_procedimento,
        sin_retornar_assuntos,
        sin_retornar_interessados,
        sin_retornar_observacoes,
        sin_retornar_andamento_geracao,
        sin_retornar_andamento_conclusao,
        sin_retornar_ultimo_andamento,
        sin_retornar_unidades_procedimento_aberto,
        sin_retornar_procedimentos_relacionados,
        sin_retornar_procedimentos_anexados,
    ):
        chamada = sei_client.consultar_procedimento(
            sigla_unidade=sigla_unidade,
            protocolo_procedimento=protocolo_procedimento,
            sin_retornar_assuntos=sin_retornar_assuntos,
            sin_retornar_interessados=sin_retornar_interessados,
            sin_retornar_observacoes=sin_retornar_observacoes,
            sin_retornar_andamento_geracao=sin_retornar_andamento_geracao,
            sin_retornar_andamento_conclusao=sin_retornar_andamento_conclusao,
            sin_retornar_ultimo_andamento=sin_retornar_ultimo_andamento,
            sin_retornar_unidades_procedimento_aberto=sin_retornar_unidades_procedimento_aberto,
            sin_retornar_procedimentos_relacionados=sin_retornar_procedimentos_relacionados,
            sin_retornar_procedimentos_anexados=sin_retornar_procedimentos_anexados,
        )
        assert hasattr(chamada, "IdProcedimento")
