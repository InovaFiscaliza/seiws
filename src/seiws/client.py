import re
import logging
from functools import cached_property
from pathlib import Path
from typing import Dict, List

from dotenv import find_dotenv, load_dotenv
from zeep import Client

from seiws.exceptions import (
    InvalidAmbienteError,
    InvalidWSDLError,
)

load_dotenv(find_dotenv(), override=True)

logging.basicConfig(
    level=logging.INFO,  # Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Log format
    handlers=[
        logging.StreamHandler(),  # Output to console
        # Uncomment the next line to log to a file
        logging.FileHandler("servico_sei.log"),
    ],
)


def download_wsdl(ambiente: str):
    """Download the appropriate WSDL file based on the provided environment.

    Args:
        ambiente (str): The environment, either "homologação" or "produção".

    Returns:
        str: The path to the WSDL file, either a local file or a URL.

    Raises:
        InvalidAmbienteError: If the provided environment is not "homologação" or "produção".
    """
    if ambiente == "homologação":
        WSDL_URL = "https://{}.anatel.gov.br/sei/controlador_ws.php?servico=sei"
        WSDL_HM = Path(__file__).parent / "seihm.wsdl"
        return str(WSDL_HM) if WSDL_HM.is_file() else WSDL_URL.format("seihm")
    elif ambiente == "produção":
        WSDL_URL = "https://{}.anatel.gov.br/sei/controlador_ws.php?servico=sei"
        WSDL_PD = Path(__file__).parent / "sei.wsdl"
        return str(WSDL_PD) if WSDL_PD.is_file() else WSDL_URL.format("sei")
    else:
        raise InvalidAmbienteError(f"Ambiente inválido: {ambiente}")


def instanciar_cliente_soap(wsdl_file: str) -> Client:
    """Instantiates a SOAP client using the provided WSDL file.

    Args:
        wsdl_file (str): The path or URL to the WSDL file.

    Returns:
        Client: The SOAP client instance.

    Raises:
        InvalidWSDLError: If there is an error creating the SOAP client.
    """
    try:
        return Client(wsdl_file)
    except Exception as e:
        raise InvalidWSDLError(f"Erro ao criar o cliente SOAP: {e}")


class SeiClient:
    def __init__(
        self,
        cliente_soap: Client,  # Cliente SOAP instanciado com o WSDL do SEI
        sigla_sistema: str,  # SiglaSistema - Valor informado no cadastro do sistema realizado no SEI
        chave_api: str,  # IdentificacaoServico - Chave de acesso ao Web Service do SEI.
        sigla_unidade: str,  # Sigla da unidade no SEI
    ):
        """
        Cria uma instância do cliente SEI.

        Args:
            cliente (Client): Cliente SOAP instanciado com o WSDL do SEI.
            sigla_sistema (str): SiglaSistema - Valor informado no cadastro do sistema realizado no SEI.
            chave_api (str): IdentificacaoServico - Chave de acesso ao Web Service do SEI.
            sigla_unidade (str): Sigla da unidade no SEI.
        """
        self.logger = logging.getLogger(__name__)
        self.cliente = cliente_soap
        self.sigla_sistema = sigla_sistema
        self.chave_api = chave_api
        self.sigla_unidade = sigla_unidade
        self.id_unidade = self._validar_unidade(sigla_unidade)

    def _chamar_servico(self, nome_operacao: str, **kwargs):
        try:
            parametros = {
                "SiglaSistema": self.sigla_sistema,
                "SiglaUnidade": self.sigla_unidade,
                **kwargs,
            }
            self.logger.info(
                f"Chamando operação: {nome_operacao} com parâmetros: {parametros}"
            )
            operacao = getattr(self.cliente.service, nome_operacao)
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

    def _validar_unidade(self, sigla_unidade: str) -> str:
        """
        Valida e retorna o ID da unidade correspondente à sigla fornecida.

        Args:
            sigla_unidade (str): A sigla da unidade a ser validada.

        Returns:
            str: O ID da unidade correspondente à sigla fornecida.

        Raises:
            ValueError: Se a sigla da unidade não for encontrada no dicionário de unidades.

        Esta função verifica se a sigla da unidade fornecida existe no dicionário de unidades.
        Se existir, retorna o ID correspondente. Caso contrário, lança uma exceção ValueError.
        """
        if sigla_unidade not in self.unidades:
            raise ValueError(f"Unidade inválida: {sigla_unidade}")
        return self.unidades[sigla_unidade]["IdUnidade"]

    def _validar_usuario(self, sigla_usuario: str) -> str:
        """
        Valida e retorna o ID do usuário correspondente à sigla fornecida.

        Args:
            sigla_usuario (str): A sigla do usuário a ser validada.

        Returns:
            str: O ID do usuário correspondente à sigla fornecida.

        Raises:
            ValueError: Se a sigla do usuário não for encontrada no dicionário de usuários.

        Esta função verifica se a sigla do usuário fornecida existe no dicionário de usuários.
        Se existir, retorna o ID correspondente. Caso contrário, lança uma exceção ValueError.
        """
        if sigla_usuario not in self.usuarios:
            raise ValueError(f"Usuário inválido: {sigla_usuario}")
        return self.usuarios[sigla_usuario]["IdUsuario"]

    def _validar_documento(self, tipo_de_documento: str) -> str:
        """
        Valida e retorna o ID do documento correspondente à sigla fornecida.

        Args:
            serie (str): A sigla do documento a ser validada.

        Returns:
            str: O ID do documento correspondente à sigla fornecida.

        Raises:
            ValueError: Se a sigla do documento não for encontrada no dicionário de series.

        Esta função verifica se a sigla do documento fornecida existe no dicionário de series.
        Se existir, retorna o ID correspondente. Caso contrário, lança uma exceção ValueError.
        """
        if tipo_de_documento not in self.documentos:
            raise ValueError(f"Tipo de documento inválido: {tipo_de_documento}")
        return self.documentos[tipo_de_documento]["IdSerie"]

    def _validar_booleano(self, atributo: str, valor: str):
        if valor not in ["S", "N"]:
            raise ValueError(
                f"Valor inválido para {atributo}. Valores possíveis: S - Sim, N - Não"
            )

    def _validar_email(self, email: str):
        if not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", email):
            raise ValueError(f"Email inválido: {email}")

    def atribuir_processo(
        self,
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
        self._validar_booleano("sin_reabrir", sin_reabrir)
        chamada = self._chamar_servico(
            "atribuirProcesso",
            IdUnidade=self.id_unidade,
            ProtocoloProcedimento=protocolo_procedimento,
            IdUsuario=id_usuario,
            SinReabrir=sin_reabrir,
        )

        return chamada == "1"

    def anexar_processo(
        self,
        protocolo_procedimento_principal: str,
        protocolo_procedimento_anexado: dict,
    ) -> bool:
        """Anexa um processo ao outro.

        Args:
            sigla_unidade (str): A sigla da unidade onde o processo está localizado.
            protocolo_processo_principal (str): O número de protocolo do processo principal.
            protocolo_processo_anexado (dict): O número de protocolo do processo anexado.

        Returns:
            bool: True se o processo foi anexado com sucesso, False caso contrário.
        """
        chamada = self._chamar_servico(
            "anexarProcesso",
            IdUnidade=self.id_unidade,
            ProtocoloProcedimentoPrincipal=protocolo_procedimento_principal,
            ProtocoloProcedimentoAnexado=protocolo_procedimento_anexado,
        )

        return chamada == "1"

    def bloquear_processo(
        self,
        protocolo_procedimento: str,
    ) -> bool:
        """Bloqueia um processo no sistema SEI.
        Somente com o processo aberto. Não é possível bloquear processos sigilosos.

        Args:
            sigla_unidade (str): A sigla da unidade onde o processo está localizado.
            protocolo_processo (str): O número de protocolo do processo a ser bloqueado.

        Returns:
            bool: True se o processo foi bloqueado com sucesso, False caso contrário.
        """
        chamada = self._chamar_servico(
            "bloquearProcesso",
            IdUnidade=self.id_unidade,
            ProtocoloProcedimento=protocolo_procedimento,
        )

        return chamada == "1"

    def cancelar_disponibilizacao_bloco(self, id_bloco: str) -> bool:
        """Cancela a disponibilização de um bloco no sistema SEI."""
        return (
            self._chamar_servico(
                "cancelarDisponibilizacaoBloco",
                IdUnidade=self.id_unidade,
                IdBloco=id_bloco,
            )
            == "1"
        )

    def cancelar_documento(self, protocolo_documento: str, motivo: str) -> bool:
        """Cancela um documento no sistema SEI.

        Args:
            protocolo_documento (str): O número do documento a ser cancelado.
            motivo (str): Motivo do cancelamento.

        Returns:
            bool: True se o documento foi cancelado com sucesso, False caso contrário.
        """
        return (
            self._chamar_servico(
                "cancelarDocumento",
                IdUnidade=self.id_unidade,
                ProtocoloDocumento=protocolo_documento,
                Motivo=motivo,
            )
            == "1"
        )

    def concluir_bloco(self, id_bloco: str) -> bool:
        """Conclui um bloco no sistema SEI."""
        return (
            self._chamar_servico(
                "concluirBloco",
                IdUnidade=self.id_unidade,
                IdBloco=id_bloco,
            )
            == "1"
        )

    def concluir_controle_prazo(
        self,
        protocolos_procedimentos: List[str],
    ):
        """Conclui um controle de prazo para um ou mais processos no sistema SEI.

        Args:
            protocolos_procedimentos (List[str]): Lista de protocolos de processos a serem concluídos o controle de prazo.
        """
        return self._chamar_servico(
            "concluirControlePrazo",
            IdUnidade=self.id_unidade,
            ProtocolosProcedimentos=protocolos_procedimentos,
        )

    def concluir_processo(self, protocolo_procedimento: str) -> bool:
        """Conclui um processo no sistema SEI.

        Args:
            sigla_unidade (str): A sigla da unidade onde o processo está localizado.
            protocolo_procedimento (str): O número de protocolo do processo a ser concluído.

        Returns:
            bool: True se o processo foi concluído com sucesso, False caso contrário.

        Raises:
            ValueError: Se a sigla da unidade fornecida for inválida.
        """
        chamada = self._chamar_servico(
            "concluirProcesso",
            IdUnidade=self.id_unidade,
            ProtocoloProcedimento=protocolo_procedimento,
        )
        return chamada == "1"

    def consultar_bloco(
        self, id_bloco: str, sin_retornar_protocolos: str = "N"
    ) -> dict:
        """
        Consulta os dados de um bloco.

        Args:
            id_bloco (str): Identificador do bloco a ser consultado.
            sin_retornar_protocolos (str): S/N - sinalizador para retorno dos protocolos do bloco.

        Returns:
            dict: Dados do bloco.

        Observações:
            O bloco deve ser da unidade ou estar disponibilizado para ela. O sinalizador de retorno dos protocolos implica em processamento adicional realizado pelo sistema, sendo assim, recomenda-se que seja solicitado o retorno
            apenas se as informações forem estritamente necessárias.
        """
        self._chamar_servico(
            "consultarBloco",
            IdUnidade=self.id_unidade,
            IdBloco=id_bloco,
            SinRetornarProtocolos=sin_retornar_protocolos,
        )

    def consultar_documento(
        self,
        # Sigla da unidade no SEI
        protocolo_documento: str,  # Número do documento visível para o usuário, ex: 0003934
        sin_retornar_andamento_geracao: str = "N",  # S/N - sinalizador para retorno do andamento de geração
        sin_retornar_assinaturas: str = "N",  # S/N - sinalizador para retorno das assinaturas do documento
        sin_retornar_publicacao: str = "N",  # S/N - sinalizador para retorno dos dados de publicação
        sin_retornar_campos: str = "N",  # S/N - sinalizador para retorno dos campos do formulário
        sin_retornar_blocos: str = "N",  #  S/N - sinalizador para retorno dos blocos na unidade que contém o documento
    ):
        """
        Retorna estrutura de dados com informações sobre o documento.

        Observações: Documento de processos sigilosos não são retornados. Cada um dos sinalizadores implica em processamento
        adicional realizado pelo sistema, sendo assim, recomenda-se que seja solicitado o retorno somente para infor-
        mações estritamente necessárias.
        """
        for key, value in locals().items():
            if key.startswith("sin_retornar_"):
                assert value in ["S", "N"], f"Valor inválido para {key}: {value}"

        return self._chamar_servico(
            "consultarDocumento",
            IdUnidade=self.id_unidade,
            ProtocoloDocumento=protocolo_documento,
            SinRetornarAndamentoGeracao=sin_retornar_andamento_geracao,
            SinRetornarAssinaturas=sin_retornar_assinaturas,
            SinRetornarPublicacao=sin_retornar_publicacao,
            SinRetornarCampos=sin_retornar_campos,
            SinRetornarBlocos=sin_retornar_blocos,
        )

    def consultar_processo(
        self,
        # Sigla da unidade no SEI
        protocolo_processo: str,  # Número do processo visível para o usuário, ex: 12.1.000000077-4
        sin_retornar_assuntos: str = "N",  # S/N - sinalizador para retorno dos assuntos do processo
        sin_retornar_interessados: str = "N",  # S/N - sinalizador para retorno dos interessados do processo
        sin_retornar_observacoes: str = "N",  # S/N - sinalizador para retorno das observações das unidades
        sin_retornar_andamento_geracao: str = "N",  # S/N - sinalizador para retorno do andamento de geração
        sin_retornar_andamento_conclusao: str = "N",  # S/N - sinalizador para retorno do andamento de conclusão
        sin_retornar_ultimo_andamento: str = "S",  #  S/N - sinalizador para retorno do último andamento
        sin_retornar_unidades_procedimento_aberto: str = "N",  # S/N - sinalizador para retorno das unidades onde o processo está aberto
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
            IdUnidade=self.id_unidade,
            ProtocoloProcedimento=protocolo_processo,
            SinRetornarAssuntos=sin_retornar_assuntos,
            SinRetornarInteressados=sin_retornar_interessados,
            SinRetornarObservacoes=sin_retornar_observacoes,
            SinRetornarAndamentoGeracao=sin_retornar_andamento_geracao,
            SinRetornarAndamentoConclusao=sin_retornar_andamento_conclusao,
            SinRetornarUltimoAndamento=sin_retornar_ultimo_andamento,
            SinRetornarUnidadesProcedimentoAberto=sin_retornar_unidades_procedimento_aberto,
            SinRetornarProcedimentosRelacionados=sin_retornar_procedimentos_relacionados,
            SinRetornarProcedimentosAnexados=sin_retornar_procedimentos_anexados,
        )

    def definir_marcador(self, definicoes: dict) -> bool:
        """Define um marcador no sistema SEI.

        Args:
            definicoes (Dict[str, str]): Dicionário com as definições do marcador.

        Returns:
            bool: True se o marcador foi definido com sucesso, False caso contrário.
        """
        return (
            self._chamar_servico(
                "definirMarcador",
                IdUnidade=self.id_unidade,
                Definicoes=definicoes,
            )
            == "1"
        )

    def desanexar_processo(
        self,
        protocolo_procedimento_principal: str,
        protocolo_procedimento_anexado: dict,
        motivo: str,
    ) -> bool:
        """Desanexa um processo no sistema SEI.

        Args:
            protocolo_processo_principal (str): O número de protocolo do processo principal.
            protocolo_processo_anexado (dict): O número de protocolo do processo anexado.
            motivo (str): Motivo da desanexação.

        Returns:
            bool: True se o processo foi desanexado com sucesso, False caso contrário.
        """
        return (
            self._chamar_servico(
                "desanexarProcesso",
                IdUnidade=self.id_unidade,
                ProtocoloProcedimentoPrincipal=protocolo_procedimento_principal,
                ProtocoloProcedimentoAnexado=protocolo_procedimento_anexado,
                Motivo=motivo,
            )
            == "1"
        )

    def desbloquear_processo(self, protocolo_procedimento: str) -> bool:
        """Desbloqueia um processo no sistema SEI.

        Args:
            protocolo_procedimento (str): O número de protocolo do processo a ser desbloqueado.

        Returns:
            bool: True se o processo foi desbloqueado com sucesso, False caso contrário.
        """
        return (
            self._chamar_servico(
                "desbloquearProcesso",
                IdUnidade=self.id_unidade,
                ProtocoloProcedimento=protocolo_procedimento,
            )
            == "1"
        )

    def devolver_bloco(self, id_bloco: str) -> bool:
        """Devolve um bloco no sistema SEI."""
        return (
            self._chamar_servico(
                "devolverBloco",
                IdUnidade=self.id_unidade,
                IdBloco=id_bloco,
            )
            == "1"
        )

    def disponibilizar_bloco(self, id_bloco: str) -> bool:
        """Disponibiliza um bloco no sistema SEI."""
        return (
            self._chamar_servico(
                "disponibilizarBloco",
                IdUnidade=self.id_unidade,
                IdBloco=id_bloco,
            )
            == "1"
        )

    def enviar_email(
        self,
        protocolo_procedimento: str,
        de: str,
        para: str,
        cco: str,
        assunto: str,
        mensagem: str,
        documentos: str,
    ):
        """Envia um email para um usuário.

        Args:
            id_unidade (str): ID da unidade.
            protocolo_procedimento (str): Protocolo do processo.
            de (str): Endereço de email do remetente.
            para (str): Endereço de email do destinatário.
            cco (str): Endereço de email para cópia.
            assunto (str): Assunto do email.
            mensagem (str): Mensagem do email.
            documentos (list): Número SEI dos documentos do processo que devem ser anexados no email.
        """
        for email in [de, para, cco]:
            self._validar_email(email)

        id_documentos = [
            self.consultar_documento(self.sigla_unidade, d)["IdDocumento"]
            for d in documentos
        ]
        return self._chamar_servico(
            "enviarEmail",
            IdUnidade=self.id_unidade,
            ProtocoloProcedimento=protocolo_procedimento,
            De=de,
            Para=para,
            CCO=cco,
            Assunto=assunto,
            Mensagem=mensagem,
            IdDocumentos=id_documentos,
        )

    def enviar_processo(
        self,
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
        # Estas unidades não são limitadas pelo acesso da chave, então não é possível checar dinamicamente
        # assert all(
        #     u in self.unidades for u in unidades_destino
        # ), f"Uma ou mais unidades inválidas presentes: {unidades_destino}"
        for key, value in locals().items():
            if key.startswith("sin_"):
                assert value in ["S", "N"], f"Valor inválido para {key}: {value}"
        unidades_destino = [self.unidades[u]["IdUnidade"] for u in unidades_destino]
        chamada = self._chamar_servico(
            "enviarProcesso",
            IdUnidade=self.id_unidade,
            ProtocoloProcedimento=protocolo_procedimento,
            UnidadesDestino=unidades_destino,
            SinManterAbertoUnidade=sin_manter_aberto_unidade,
            SinRemoverAnotacao=sin_remover_anotacao,
            SinEnviarEmailNotificacao=sin_enviar_email_notificacao,
            DataRetornoProgramado=data_retorno_programado,
            DiasRetornoProgramado=dias_retorno_programado,
            SinDiasUteisRetornoProgramado=sin_dias_uteis_retorno_programado,
            SinReabrir=sin_reabrir,
        )
        return chamada == "1"

    def excluir_bloco(self, id_bloco: str) -> bool:
        """Exclui um bloco no sistema SEI."""
        return (
            self._chamar_servico(
                "excluirBloco",
                IdUnidade=self.id_unidade,
                IdBloco=id_bloco,
            )
            == "1"
        )

    def excluir_documento(
        self,
        protocolo_documento: str,
    ) -> bool:
        """Exclui um documento do sistema SEI.

        Args:
            sigla_unidade (str): A sigla da unidade onde o processo está localizado.
            protocolo_documento (str): O número do documento a ser excluído.

        Returns:
            bool: True se o documento foi excluído com sucesso, False caso contrário.
        """
        return (
            self._chamar_servico(
                "excluirDocumento",
                IdUnidade=self.id_unidade,
                ProtocoloDocumento=protocolo_documento,
            )
            == "1"
        )

    def excluir_processo(
        self,
        protocolo_processo: str,
    ) -> bool:
        """Exclui um processo do sistema SEI.

        Args:
            sigla_unidade (str): A sigla da unidade onde o processo está localizado.
            protocolo_processo (str): O número do processo a ser excluído.

        Returns:
            bool: True se o processo foi excluído com sucesso, False caso contrário.
        """
        return (
            self._chamar_servico(
                "excluirProcesso",
                IdUnidade=self.id_unidade,
                ProtocoloProcesso=protocolo_processo,
            )
            == "1"
        )

    def gerar_bloco(
        self,
        tipo: str,
        descricao: str,
        unidades_disponibilizacao: dict,
        documentos: list,
        sin_disponibilizar: str = "N",
    ) -> str:
        """Gera um bloco no sistema SEI.

        Args:
            tipo (str): Tipo do bloco a ser gerado.
            descricao (str): Descrição do bloco a ser gerado.
            unidades_disponibilizacao (Dict[str, str]): Dicionário com as unidades a serem disponibilizadas no bloco.
            documentos (List[str]): Lista de documentos a serem incluídos no bloco.
            sin_disponibilizar (str, optional): Sinal de disponibilização. Valores possíveis: S - Sim, N - Não. Valor padrão: N.

        Returns:
            str: Número do bloco gerado.

        Tipos de Bloco:
            A - Assinatura
            R - Reunião
            I - Interno
        """
        self._validar_booleano("sin_disponibilizar", sin_disponibilizar)
        assert tipo in ["A", "R", "I"], f"Tipo de bloco inválido: {tipo}"
        self._chamar_servico(
            "gerarBloco",
            IdUnidade=self.id_unidade,
            Tipo=tipo,
            Descricao=descricao,
            UnidadesDisponibilizacao=unidades_disponibilizacao,
            Documentos=documentos,
            SinDisponibilizar=sin_disponibilizar,
        )

    def incluir_documento(
        self,
        documento: dict,
    ) -> dict:
        return self._chamar_servico(
            "incluirDocumento",
            IdUnidade=self.id_unidade,
            Documento=documento,
        )

    def incluir_documento_bloco(
        self, id_bloco: str, protocolo_documento: str, anotacao: str = ""
    ) -> bool:
        """
        Inclui um novo documento no bloco.

        Args:
            id_bloco (str): Identificador do bloco no qual o documento será incluído.
            protocolo_documento (str): Protocolo do documento a ser incluído.
            anotacao (str): Opcional. Texto de anotação associado com o documento no bloco.

        Returns:
            bool: True se o documento foi incluído com sucesso, False caso contrário.
        """
        return (
            self._chamar_servico(
                "incluirDocumentoBloco",
                IdUnidade=self.id_unidade,
                IdBloco=id_bloco,
                ProtocoloDocumento=protocolo_documento,
                Anotacao=anotacao,
            )
            == "1"
        )

    def incluir_processo_bloco(
        self, id_bloco: str, protocolo_processo: str, anotacao: str = ""
    ) -> bool:
        """
        Inclui um novo processo no bloco.

        Args:
            id_bloco (str): Identificador do bloco no qual o processo será incluído.
            protocolo_processo (str): Protocolo do processo a ser incluído.
            anotacao (str): Opcional. Texto de anotação associado com o processo no bloco.

        Returns:
            bool: True se o processo foi incluído com sucesso, False caso contrário.
        """
        return (
            self._chamar_servico(
                "incluirProcessoBloco",
                IdUnidade=self.id_unidade,
                IdBloco=id_bloco,
                ProtocoloProcedimento=protocolo_processo,
                Anotacao=anotacao,
            )
            == "1"
        )

    def lancar_andamento(
        self,
        protocolo_procedimento: str,
        id_tarefa: int = 65,
        id_tarefa_modulo: int = None,
        atributos: dict = None,
    ) -> dict:
        """
        Lança um andamento no sistema SEI.

        Args:
            protocolo_procedimento (str): Protocolo do processo a ser lançado.
            id_tarefa (int): Identificador da tarefa associada.
            id_tarefa_modulo (int): Identificador do módulo de tarefas associado.
            atributos (dict): Dicionário com os atributos do andamento.

        Returns:
            dict: Dicionário com os atributos do andamento.
        """
        if atributos is None:
            atributos = {}
        kwargs = dict(
            IdUnidade=self.id_unidade,
            ProtocoloProcedimento=protocolo_procedimento,
            IdTarefa=id_tarefa,
            IdTarefaModulo="",
            Atributos=atributos,
        )
        if id_tarefa_modulo is not None:
            kwargs.update(IdTarefaModulo=id_tarefa_modulo)
        return self._chamar_servico(
            "lancarAndamento",
            **kwargs,
        )

    def listar_andamentos(
        self,
        protocolo_procedimento: str,
        sin_retornar_atributos: str = "S",
        andamentos: str = "",
        tarefas: str = "",
        tarefas_modulos: str = "",
    ) -> List[Dict[str, str]]:
        """Lista os andamentos de um processo.

        Args:
            protocolo_procedimento (str): O número de protocolo do processo a ser relacionado.
            sin_retornar_atributos (str, optional): Sinal de retorno de atributos. Valores possíveis: S - Sim, N - Não. Valor padrão: N.
            andamentos (str, optional): Filtra os andamentos. Valores possíveis: Qualquer id válido de andamento. A string vazia ("") indica que nenhum filtro é aplicado.
            tarefas (str, optional): Filtra as tarefas. Valores possíveis: Qualquer id válido de tarefa. A string vazia ("") indica que nenhum filtro é aplicado.
            tarefas_modulos (str, optional): Filtra os módulos de tarefas. Valores possíveis: Qualquer id válido de módulo de tarefa. A string vazia ("") indica que nenhum filtro é aplicado.

        Returns:
            List[Dict[str, str]]: Lista de andamentos de um processo.
        """
        self._validar_booleano("sin_retornar_atributos", sin_retornar_atributos)

        return self._chamar_servico(
            "listarAndamentos",
            IdUnidade=self.id_unidade,
            ProtocoloProcedimento=protocolo_procedimento,
            SinRetornarAtributos=sin_retornar_atributos,
            Andamentos=andamentos,
            Tarefas=tarefas,
            TarefasModulos=tarefas_modulos,
        )

    def listar_andamentos_marcadores(
        self, protocolo_procedimento: str, marcadores: str = ""
    ) -> dict:
        """Lista os andamentos de um processo com marcadores.

        Args:
            protocolo_procedimento (str): O número de protocolo do processo a ser relacionado.
            marcadores (str, optional): Filtra os andamentos com marcadores. Valores possíveis: Qualquer id válido de marcador. A string vazia ("") indica que nenhum filtro é aplicado.

        Returns:
            List[Dict[str, str]]: Lista de andamentos de um processo com marcador.
        """
        return self._chamar_servico(
            "listarAndamentosMarcadores",
            IdUnidade=self.id_unidade,
            ProtocoloProcedimento=protocolo_procedimento,
            Marcadores=marcadores,
        )

    def listar_cargos(self, id_cargo: str = "") -> dict:
        """Lista os cargos disponíveis na unidade.

        Args:
            id_cargo (str, optional): Filtra o cargo. Valores possíveis: Qualquer id válido de cargo. A string vazia ("") indica que nenhum filtro é aplicado.

        Returns:
            Um conjunto de ocorrências da estrutura Cargo.
        """
        return self._chamar_servico(
            "listarCargos",
            IdUnidade=self.id_unidade,
            IdCargo=id_cargo,
        )

    def listar_series(
        self,
        sigla_unidade: str = "",  # Opcional. Filtra a unidade
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
        if sigla_unidade:
            id_unidade = self._validar_unidade(sigla_unidade)
        else:
            id_unidade = ""
        return self._chamar_servico(
            "listarSeries",
            IdUnidade=id_unidade,
            IdTipoProcedimento=id_tipo_procedimento,
        )

    def listar_tipos_processo(
        self,
        sigla_unidade: str = None,
        tipo_de_documento: str = None,
        sin_individual: str = "N",
    ) -> dict:
        """
        Lista os tipos de processos disponíveis na unidade.

        Args:
            sigla_unidade (str): Sigla da unidade no SEI.
            tipo_de_documento (str): Tipo de documento a ser consultado.
            sin_individual (str): S/N - sinalizador para retorno individual.

        Returns:
            dict: Dicionário com os tipos de processos disponíveis na unidade.
        """
        if sigla_unidade is not None:
            id_unidade = self._validar_unidade(sigla_unidade)
        else:
            id_unidade = ""
        if tipo_de_documento is not None:
            id_serie = self._validar_series(tipo_de_documento)
        else:
            id_serie = ""
        return self._chamar_servico(
            "listarTiposProcedimento",
            IdUnidade=id_unidade,
            IdSerie=id_serie,
            SinIndividual=sin_individual,
        )

    def listar_unidades(
        self,
        id_tipo_procedimento: str = "",  # Opcional. Filtra o tipo do processo
        tipo_de_documento: str = "",  # Opcional. Filtra a tipo de documento
    ) -> List[Dict[str, str]]:
        """Lista as unidades com acesso configurado para a chave de acesso informada.

        Args:
            id_tipo_procedimento (str, optional): Filtra o tipo do processo. Valores possíveis: Qualquer id válido de processo. A string vazia ("") indica que nenhum filtro é aplicado.
            tipo_de_documento (str, optional): Filtra o tipo de documento. Valores possíveis: Qualquer tipo válido de documento. A string vazia ("") indica que nenhum filtro é aplicado.

        Returns:
            List[Dict[str, str]]: Lista de unidades com acesso configurado para a chave de acesso informada.
        """
        if tipo_de_documento:
            id_serie = self._validar_documento(tipo_de_documento)
        else:
            id_serie = ""
        return self._chamar_servico(
            "listarUnidades",
            IdTipoProcedimento=id_tipo_procedimento,
            IdSerie=id_serie,
        )

    def listar_usuarios(
        self, sigla_unidade: str, id_usuario: str = ""
    ) -> List[Dict[str, str]]:
        """Retorna o conjunto de usuários que possuem o perfil "Básico" do SEI na unidade.

        Args:
            sigla_unidade (str): Sigla da unidade.
            id_usuario (str, optional): Filtra o usuário. Valores possíveis: Qualquer id válido de usuário. A string vazia ("") indica que nenhum filtro é aplicado.

        Returns:
            List[Dict[str, str]]: Lista de usuários que possuem o perfil "Básico" do SEI na unidade..
        """
        return self._chamar_servico(
            "listarUsuarios",
            IdUnidade=self._validar_unidade(sigla_unidade),
            IdUsuario=self.id_usuario,
        )

    def reabrir_bloco(self, id_bloco: str) -> bool:
        """Reabre um bloco no sistema SEI."""
        return (
            self._chamar_servico(
                "reabrirBloco",
                IdUnidade=self.id_unidade,
                IdBloco=id_bloco,
            )
            == "1"
        )

    def reabrir_processo(self, protocolo_procedimento: str) -> bool:
        """
        Reabre um processo no sistema SEI.

        Args:
            sigla_unidade (str): A sigla da unidade onde o processo está localizado.
            protocolo_procedimento (str): O número de protocolo do processo a ser reaberto.

        Returns:
            bool: True se o processo foi reaberto com sucesso, False caso contrário.

        Raises:
            ValueError: Se a sigla da unidade fornecida for inválida.
        """

        chamada = self._chamar_servico(
            "reabrirProcesso",
            IdUnidade=self.id_unidade,
            ProtocoloProcedimento=protocolo_procedimento,
        )
        return chamada == "1"

    def relacionar_processo(
        self, protocolo_processo1: str, protocolo_processo2: str
    ) -> bool:
        """Relaciona dois processos no sistema SEI.
        Args:
            protocolo_processo1 (str): O número do processo a ser relacionado.
            protocolo_processo2 (str): O número do processo a ser relacionado.

        Returns:
            bool: True se os processos foram relacionados com sucesso, False caso contrário.

        Observações:
            O relacionamento entre processos é bilateral sendo assim relacionar nos dois tipos de processos envolvidos.
        """
        return (
            self._chamar_servico(
                "relacionarProcesso",
                IdUnidade=self.id_unidade,
                ProtocoloProcedimento1=protocolo_processo1,
                ProtocoloProcedimento2=protocolo_processo2,
            )
            == "1"
        )

    def retirar_documento_bloco(
        self,
        id_bloco: str,
        protocolo_documento: str,
    ) -> bool:
        """Retira documento do bloco.
        Args:
            id_bloco (str): Identificador do bloco no qual o documento será retirado.
            protocolo_documento (str): Protocolo do documento a ser retirado.

        Returns:
            bool: True se o documento foi retirado com sucesso, False caso contrário.

        """
        return (
            self._chamar_servico(
                "retirarDocumentoBloco",
                IdUnidade=self.id_unidade,
                IdBloco=id_bloco,
                ProtocoloDocumento=protocolo_documento,
            )
            == "1"
        )

    def retirar_processo_bloco(
        self,
        id_bloco: str,
        protocolo_processo: str,
    ) -> bool:
        """Retira processo do bloco.
        Args:
            id_bloco (str): Identificador do bloco no qual o processo será retirado.
            protocolo_processo (str): Protocolo do processo a ser retirado.

        Returns:
            bool: True se o processo foi retirado com sucesso, False caso contrário.

        """
        return (
            self._chamar_servico(
                "retirarProcessoBloco",
                IdUnidade=self.id_unidade,
                IdBloco=id_bloco,
                ProtocoloProcedimento=protocolo_processo,
            )
            == "1"
        )

    @cached_property
    def unidades(self):
        return {d["Sigla"]: d for d in self.listar_unidades()}

    @cached_property
    def usuarios(self):
        return {d["Sigla"]: d for d in self.listar_usuarios()}

    @cached_property
    def documentos(self):
        return {d["Nome"]: d for d in self.listar_series()}

    @cached_property
    def processos(self):
        return {d["Nome"]: d for d in self.listar_tipos_processo()}


if __name__ == "__main__":
    import os
    from datetime import datetime
    from pathlib import Path
    import base64
    from zeep import xsd

    from dotenv import find_dotenv, load_dotenv

    load_dotenv(find_dotenv(), override=True)

    sigla_sistema = "InovaFiscaliza"

    if sigla_sistema == "InovaFiscaliza":
        chave_api = os.getenv("SEI_HM_API_KEY_BLOQUEIO")
    elif sigla_sistema == "Fiscaliza":
        chave_api = os.getenv("SEI_HM_API_KEY_FISCALIZA")

    wsdl_file = download_wsdl("homologação")

    cliente_soap = instanciar_cliente_soap(wsdl_file)

    cliente_sei = SeiClient(
        cliente_soap=cliente_soap,
        sigla_sistema=sigla_sistema,
        chave_api=chave_api,
        sigla_unidade="FISF",
    )

    html_bytes = Path("C:/Users/rsilva/Code/Oficio.html").read_bytes()
    html_base64 = base64.b64encode(html_bytes).decode("utf-8")

    documento = {
        "Tipo": "R",
        "ProtocoloProcedimento": "53500.000124/2024-04",
        "IdSerie": "11",  # Ofício
        # "Descricao": "Documento de Teste - InovaFiscaliza",
        "Conteudo": html_base64,
        "Data": datetime.now().strftime("%d/%m/%Y"),
        "NomeArquivo": "Ofício_Resposta.html",
    }

    andamento = "Processo recebido na unidade"

    definicao_marcador = {
        "ProtocoloProcedimento": "53500.000124/2024-04",
        "IdMarcador": "1",
        "Texto": "Marcador de teste",
    }

    unidades = {
        "IdUnidade": "110000965",
        "Sigla": "SFI",
        "Descricao": "Superintendência de Fiscalização",
        "SinProtocolo": "N",
        "SinArquivamento": "N",
        "SinOuvidoria": "N",
    }

    unidades = {"110000965", "110001021"}

    element = cliente_sei.cliente.get_type("ns0:AtributoAndamento")
    atributos_andamento = element(
        Nome="Atualização de Andamento",
        Valor="Teste InovaFiscaliza",
        IdOrigem="3130803",
    )

    # cliente_sei.anexar_processo("53500.000124/2024-04", "53500.201128/2014-28")

    # cliente_sei.bloquear_processo("53500.201128/2014-28")

    # cliente_sei.concluir_bloco("3723")

    # cliente_sei.reabrir_bloco("3723")

    # cliente_sei.disponibilizar_bloco("3723")

    # cliente_sei.cancelar_disponibilizacao_bloco("3723")

    # cliente_sei.cancelar_documento("0208314", "Cancelamento por falta de informações")

    # cliente_sei.concluir_controle_prazo(["53500.000124/2024-04"])

    # cliente_sei.definir_marcador(definicao_marcador)

    # cliente_sei.gerar_bloco(
    #     "A", "Bloco de assinatura", unidades, ["0208314", "0208319"], "S"
    # )

    # cliente_sei.incluir_documento(documento)

    # cliente_sei.lancar_andamento(
    #     "53500.000124/2024-04",
    #     id_tarefa=65,
    #     id_tarefa_modulo=xsd.SkipValue,
    #     atributos=atributos_andamento,
    # )

    # cliente_sei.listar_andamentos(
    #     "53500.000124/2024-04", "S", xsd.SkipValue, ["65"], xsd.SkipValue
    # )

    cliente_sei.listar_andamentos_marcadores("53500.000124/2024-04", xsd.SkipValue)

    # cliente_sei.listar_cargos()

    # cliente_sei.consultar_bloco("3754", "S")

    # cliente_sei.incluir_documento_bloco("3755", "0208319", "Autografe por obséquio")

    # cliente_sei.retirar_documento_bloco("3755", "0208319")

    # cliente_sei.incluir_processo_bloco("3755", "53500.201128/2014-28", "Assine tudo!")

    # cliente_sei.listar_tipos_processo()
