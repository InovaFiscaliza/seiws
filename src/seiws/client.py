import logging
from pathlib import Path

from dotenv import find_dotenv, load_dotenv
from zeep import Client
from zeep.exceptions import Fault

load_dotenv(find_dotenv(), override=True)

WSDL_URL = "https://sei{}.anatel.gov.br/sei/controlador_ws.php?servico=sei"

logging.basicConfig(
    level=logging.INFO,  # Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Log format
    handlers=[
        logging.StreamHandler(),  # Output to console
        # Uncomment the next line to log to a file
        logging.FileHandler("soap_service.log"),
    ],
)


class SeiClient:
    def __init__(self, identificador: str, chave_api: str, homologação: bool = False):
        self.identificador = identificador
        self.chave_api = chave_api
        self.homologação = homologação
        self.instanciar_cliente()

    def instanciar_cliente(
        self,
    ):
        self.logger = logging.getLogger(__name__)  # Initialize logger
        self.wsdl_url = WSDL_URL.format("hm" if self.homologação else "")
        try:
            self.client = Client(self.wsdl_url)
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
                IdentificadorServico=self.identificador_servico,
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