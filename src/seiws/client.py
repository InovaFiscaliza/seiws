import logging
from pathlib import Path
from typing import List, Dict

from dotenv import find_dotenv, load_dotenv
from fastcore.basics import snake2camel
from zeep import Client

from seiws.exceptions import InvalidAmbienteError, InvalidChaveApiError
from seiws.config import (
    AMBIENTES_DE_DESENVOLVIMENTO,
)

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

    def listar_usuarios(self, id_unidade: str) -> List[Dict[str, str]]:
        return self._chamar_servico(
            "listarUsuarios",
            id_unidade=id_unidade,
        )


if __name__ == "__main__":
    from pprint import pprint
    import os
    from dotenv import find_dotenv, load_dotenv

    load_dotenv(find_dotenv(), override=True)

    client = SeiClient(chave_api=os.getenv("SEI_HM_API_KEY_BLOQUEIO"))

    pprint(client.listar_unidades())

    client.chave_api = os.getenv("SEI_HM_API_KEY_INSTRUCAO")

    pprint(client.listar_unidades())

    client = SeiClient(
        sigla_sistema="Fiscaliza", chave_api=os.getenv("SEI_HM_API_KEY_FISCALIZA")
    )

    pprint(client.listar_unidades())
