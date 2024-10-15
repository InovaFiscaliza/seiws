import logging
from pathlib import Path

from config import (
    AMBIENTES_DE_DESENVOLVIMENTO,
    CHAVES_API,
)
from dotenv import find_dotenv, load_dotenv
from zeep import Client

load_dotenv(find_dotenv(), override=True)

WSDL_URL = "https://sei{}.anatel.gov.br/sei/controlador_ws.php?servico=sei"
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


class InvalidTipoProcessoError(Exception):
    pass


class InvalidAmbienteError(Exception):
    pass


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
            self.chave_api = CHAVES_API[self.ambiente]

    def _validar_tipo_processo(self, tipo_processo: str):
        pass

    def instanciar_cliente(
        self,
    ):
        self.logger = logging.getLogger(__name__)  # Initialize logger
        self.wsdl_file = WSDL_HM if self.homologação else WSDL_PD
        try:
            self.client = Client(self.wsdl_file)
        except Exception as e:
            raise Exception("Erro ao criar o cliente SOAP") from e

    def _call_service(self, operation_name: str, **kwargs):
        try:
            self.logger.info(
                f"Chamando operação: {operation_name} com parâmetros: {kwargs}"
            )
            operation = getattr(self.client.service, operation_name)
            response = operation(
                SiglaSistema=self.sigla_sistema,
                IdentificadorServico=self.chave_api,
                **kwargs,
            )
            self.logger.info(f"Resposta recebida: {response}")
            return response
        except Exception as e:
            self.logger.error(f"Erro ao chamar a operação {operation_name}: {e}")
            raise

    def adicionar_arquivo(
        self, id_unidade: str, nome: str, tamanho: str, hash: str, conteudo: str
    ) -> str:
        return self._call_service(
            "adicionarArquivo",
            IdUnidade=id_unidade,
            Nome=nome,
            Tamanho=tamanho,
            Hash=hash,
            Conteudo=conteudo,
        )

    def adicionar_conteudo_arquivo(
        self, id_unidade: str, id_arquivo: str, conteudo: str
    ) -> str:
        return self._call_service(
            "adicionarConteudoArquivo",
            IdUnidade=id_unidade,
            IdArquivo=id_arquivo,
            Conteudo=conteudo,
        )
