import logging
from functools import cached_property
from pathlib import Path
from typing import Dict, List

from dotenv import find_dotenv, load_dotenv
from fastcore.basics import snake2camel
from zeep import Client

from seiws.config import (
    AMBIENTES_DE_DESENVOLVIMENTO,
)
from seiws.exceptions import InvalidAmbienteError, InvalidChaveApiError

load_dotenv(find_dotenv(), override=True)

WSDL_URL = "https://{}.anatel.gov.br/sei/controlador_ws.php?servico=sei"
WSDL_HM = Path(__file__).parent / "seihm.wsdl"
WSDL_PD = Path(__file__).parent / "sei.wsdl"

logging.basicConfig(
    level=logging.INFO,  # Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Log format
    handlers=[
        logging.StreamHandler(),  # Output to console
        # Uncomment the next line to log to a file
        logging.FileHandler("servico_sei.log"),
    ],
)


class SeiClient:
    def __init__(
        self,
        ambiente: str = "homologação",  # Ambiente de desenvolvimento: desenvolvimento, homologação ou produção
        sigla_sistema: str = "InovaFiscaliza",  # SiglaSistema - Valor informador no cadastro do sistema realizado no SEI
        chave_api: str = None,  # IdentificacaoServico - Chave de acesso ao Web Service do SEI.
    ):
        """
        Caso não seja informada uma chave api, esta será obtida a partir da chave API padrão do ambiente definida em config.py
        """
        self.ambiente = ambiente
        self.sigla_sistema = sigla_sistema
        self.chave_api = chave_api
        self._validar_ambiente()
        self.instanciar_cliente()

    def _validar_ambiente(self):
        if self.ambiente not in AMBIENTES_DE_DESENVOLVIMENTO:
            raise InvalidAmbienteError(f"Ambiente inválido: {self.ambiente}")
        if self.chave_api is None:
            raise InvalidChaveApiError(f"Chave API inválida: {self.chave_api}")

    def _chamar_servico(self, nome_operacao: str, **kwargs):
        try:
            parametros = {
                "SiglaSistema": self.sigla_sistema,
                "Ambiente": self.ambiente,
                **kwargs,
            }
            self.logger.info(
                f"Chamando operação: {nome_operacao} com parâmetros: {parametros}"
            )
            operacao = getattr(self.client.service, nome_operacao)
            kwargs = {snake2camel(k): v for k, v in kwargs.items()}
            resposta = operacao(
                SiglaSistema=self.sigla_sistema,
                IdentificacaoServico=self.chave_api,
                **kwargs,
            )
            self.logger.info(f"Resposta recebida: {resposta}")
            return resposta
        except Exception as e:
            self.logger.error(f"Erro ao chamar a operação {nome_operacao}: {e}")
            raise

    def instanciar_cliente(
        self,
    ):
        self.logger = logging.getLogger(__name__)  # Initialize logger
        if self.ambiente == "homologação":
            self.wsdl_file = (
                str(WSDL_HM) if WSDL_HM.is_file() else WSDL_URL.format("seihm")
            )
        elif self.ambiente == "produção":
            self.wsdl_file = (
                str(WSDL_PD) if WSDL_PD.is_file() else WSDL_URL.format("sei")
            )
        else:
            raise InvalidAmbienteError(f"Ambiente inválido: {self.ambiente}")
        try:
            self.client = Client(self.wsdl_file)
        except Exception as e:
            self.logger.error(f"Erro ao criar o cliente SOAP: {e}")
            raise

    def atribuir_processo(
        self,
        id_unidade: str,
        protocolo_procedimento: str,
        id_usuario: str,
        sin_reabrir: str = "S",
    ) -> bool:
        """Atribui um processo a um usuário.

        Args:
            id_unidade (str): ID da unidade.
            protocolo_procedimento (str): Protocolo do processo.
            id_usuario (str): ID do usuário.
            sin_reabrir (str, optional): Sinal de reabertura. Valores possíveis: S - Sim, N - Não. Valor padrão: S.

        Returns:
            bool: True se o processo foi atribuído com sucesso, False caso contrário.
        """
        assert (
            sin_reabrir in ["S", "N"]
        ), f"Valor inválido para sin_reabrir: {sin_reabrir}. Valores possíveis: S - Sim, N - Não"
        chamada = self._chamar_servico(
            "atribuirProcesso",
            id_unidade=id_unidade,
            protocolo_procedimento=protocolo_procedimento,
            id_usuario=id_usuario,
            sin_reabrir=sin_reabrir,
        )

        return chamada == "1"

    def consultar_procedimento(
        self,
        id_unidade: str,  # Identificador da unidade no SEI
        protocolo_procedimento: str,  # Número do processo visível para o usuário, ex: 12.1.000000077-4
        sin_retornar_assuntos: str = "N",  # S/N - sinalizador para retorno dos assuntos do processo
        sin_retornar_interessados: str = "N",  # S/N - sinalizador para retorno dos interessados do processo
        sin_retornar_observacoes: str = "N",  # S/N - sinalizador para retorno das observações das unidades
        sin_retornar_andamento_geracao: str = "N",  # S/N - sinalizador para retorno do andamento de geração
        sin_retornar_andamento_conclusao: str = "N",  # S/N - sinalizador para retorno do andamento de conclusão
        sin_retornar_ultimo_andamento: str = "S",  #  S/N - sinalizador para retorno do último andamento
        sin_retornar_unidades_procedimento_aberto: str = "S",  # S/N - sinalizador para retorno das unidades onde o processo está aberto
        sin_retornar_procedimentos_relacionados: str = "N",  # S/N - sinalizador para retorno dos processos relacionados
        sin_retornar_procedimentos_anexados: str = "N",  # S/N - sinalizador para retorno dos processos anexados
    ):
        """Retorna estrutura de dados com informações sobre o processo.

            Observações: Processos sigilosos não são retornados. Cada um dos sinalizadores implica em processamento adicional reali-
        zado pelo sistema, sendo assim, recomenda-se que seja solicitado o retorno somente para informações estri-
        tamente necessárias.
        """
        for key, value in locals().items():
            if key.startswith("sin_retornar_"):
                assert value in ["S", "N"], f"Valor inválido para {key}: {value}"
        return self._chamar_servico(
            "consultarProcedimento",
            id_unidade=id_unidade,
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

    def enviar_processo(
        self,
        unidade_origem: str,
        protocolo_procedimento: str,
        unidades_destino: list,
        sin_manter_aberto_unidade: str = "N",
        sin_remover_anotacao: str = "N",
        sin_enviar_email_notificacao: str = "N",
        data_retorno_programado: str = "",
        dias_retorno_programado: str = "",
        sin_dias_uteis_retorno_programado: str = "N",
        sin_reabrir: str = "S",
    ) -> bool:
        """Envia um processo para uma unidade ou mais unidades."""
        assert unidade_origem in self.unidades, f"Unidade inválida: {unidade_origem}"
        assert all(
            u in self.unidades for u in unidades_destino
        ), f"Uma ou mais unidades inválidas presentes: {unidades_destino}"
        for key, value in locals().items():
            if key.startswith("sin_"):
                assert value in ["S", "N"], f"Valor inválido para {key}: {value}"
        id_unidade = self.unidades[unidade_origem]["IdUnidade"]
        unidades_destino = [self.unidades[u]["IdUnidade"] for u in unidades_destino]
        chamada = self._chamar_servico(
            "enviarProcesso",
            id_unidade=id_unidade,
            protocolo_procedimento=protocolo_procedimento,
            unidades_destino=unidades_destino,
            sin_manter_aberto_unidade=sin_manter_aberto_unidade,
            sin_remover_anotacao=sin_remover_anotacao,
            sin_enviar_email_notificacao=sin_enviar_email_notificacao,
            data_retorno_programado=data_retorno_programado,
            dias_retorno_programado=dias_retorno_programado,
            sin_dias_uteis_retorno_programado=sin_dias_uteis_retorno_programado,
            sin_reabrir=sin_reabrir,
        )
        return chamada == "1"

    def listar_series(
        self,
        id_unidade: str = "",  # Opcional. Filtra a unidade
        id_tipo_procedimento: str = "",  # Opcional. Filtra o tipo do processo
    ) -> List[
        Dict[str, str]
    ]:  # Retorna uma lista de dicionários com as informações do documento
        """Lista os documentos de uma unidade com acesso configurado para a chave de acesso informada.

        Returns:
                List[Dict[str, str]]:

            IdSerie: Identificador do tipo de documento
            Nome: Nome do tipo de documento
            Aplicabilidade :
                    T = Documentos internos e externos
                    I = documentos internos
                    E = documentos externos
                    F = formulários

        """
        return self._chamar_servico(
            "listarSeries",
            id_unidade=id_unidade,
            id_tipo_procedimento=id_tipo_procedimento,
        )

    def listar_unidades(
        self,
        id_tipo_procedimento: str = "",  # Opcional. Filtra o tipo do processo
        id_serie: str = "",  # Opcional. Filtra a tipo de documento
    ) -> List[Dict[str, str]]:
        """Lista as unidades com acesso configurado para a chave de acesso informada.

        Args:
            id_tipo_procedimento (str, optional): Filtra o tipo do processo. Valores possíveis: Qualquer id válido de processo. A string vazia ("") indica que nenhum filtro é aplicado.
            id_serie (str, optional): Filtra a tipo de documento. Valores possíveis: Qualquer id válido de documento. A string vazia ("") indica que nenhum filtro é aplicado.

        Returns:
            List[Dict[str, str]]: Lista de unidades com acesso configurado para a chave de acesso informada.
        """
        return self._chamar_servico(
            "listarUnidades",
            id_tipo_procedimento=id_tipo_procedimento,
            id_serie=id_serie,
        )

    def listar_usuarios(
        self, id_unidade: str, id_usuario: str = ""
    ) -> List[Dict[str, str]]:
        """Retorna o conjunto de usuários que possuem o perfil "Básico" do SEI na unidade.

        Args:
            id_unidade (str): ID da unidade.
            id_usuario (str, optional): Filtra o usuário. Valores possíveis: Qualquer id válido de usuário. A string vazia ("") indica que nenhum filtro é aplicado.

        Returns:
            List[Dict[str, str]]: Lista de usuários que possuem o perfil "Básico" do SEI na unidade..
        """
        return self._chamar_servico(
            "listarUsuarios",
            id_unidade=id_unidade,
            id_usuario=id_usuario,
        )

    @cached_property
    def unidades(self):
        return {d["Sigla"]: d for d in self.listar_unidades()}


if __name__ == "__main__":
    import os
    from pprint import pprint

    from dotenv import find_dotenv, load_dotenv

    load_dotenv(find_dotenv(), override=True)

    sigla_sistema = "InovaFiscaliza"

    method = "consultar_procedimento"

    # client = SeiClient(
    #     sigla_sistema=sigla_sistema, chave_api=os.getenv("SEI_HM_API_KEY_BLOQUEIO")
    # )

    # pprint(
    #     getattr(client, method)(
    #         id_unidade="110001068",
    #         protocolo_procedimento="53554.000005/2024-18",
    #         id_usuario="100003445",
    #         sin_reabrir="S",
    #     )
    # )

    client = SeiClient(
        sigla_sistema=sigla_sistema, chave_api=os.getenv("SEI_HM_API_KEY_INSTRUCAO")
    )

    pprint(
        getattr(client, method)(
            id_unidade="110001068",
            protocolo_procedimento="53554.000005/2024-18",
            # id_usuario="100001310",
            # sin_reabrir="S",
        )
    )
