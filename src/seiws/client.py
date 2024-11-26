import re
import logging
from functools import cached_property
from pathlib import Path
from typing import Dict, List

from dotenv import find_dotenv, load_dotenv
from zeep import xsd

from seiws.estrutura_de_dados import EXTENSOES
from seiws.helpers import download_wsdl, instanciar_cliente_soap


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


class SeiClient:
    def __init__(
        self,
        cliente_soap,  # Cliente SOAP instanciado com o WSDL do SEI
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

    def _validar_pais(self, sigla_pais: str) -> str:
        """
        Valida e retorna o ID do pais correspondente à sigla fornecida.

        Args:
            sigla_pais (str): A sigla do pais a ser validada.

        Returns:
            str: O ID do pais correspondente à sigla fornecida.

        Raises:
            ValueError: Se a sigla do pais não for encontrada no dicionário de paises.

        Esta função verifica se a sigla do pais fornecida existe no dicionário de paises.
        Se existir, retorna o ID correspondente. Caso contrário, lança uma exceção ValueError.
        """
        if sigla_pais not in self.paises:
            raise ValueError(f"Pais inválido: {sigla_pais}")
        return self.paises[sigla_pais]["IdPais"]

    def atribuir_processo(
        self,
        protocolo_procedimento: str,
        sigla_usuario: str,
        sin_reabrir: str = "S",
    ) -> bool:
        """Atribui um processo a um usuário.

        Args:
            protocolo_procedimento (str): Protocolo do processo.
            sigla_usuario (str): Sigla (login) do usuário.
            sin_reabrir (str, opcional): Sinal de reabertura. Valores possíveis: S - Sim, N - Não. Valor padrão: S.

        Returns:
            bool: True se o processo foi atribuído com sucesso, False caso contrário.
        """
        id_usuario = self._validar_usuario(sigla_usuario)
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

    def bloquear_documento(
        self,
        protocolo_documento: str,
    ) -> bool:
        """Bloqueia um documento no sistema SEI.

        Args:
            protocolo_documento (str): O número do documento a ser bloqueado.

        Returns:
            bool: True se o documento foi bloqueado com sucesso, False caso contrário.
        """
        return (
            self._chamar_servico(
                "bloquearDocumento",
                IdUnidade=self.id_unidade,
                ProtocoloDocumento=protocolo_documento,
            )
            == "1"
        )

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
        protocolo_documento: str,  # Número do documento visível para o usuário, ex: 0003934
        sin_retornar_andamento_geracao: str = "N",  # S/N - sinalizador para retorno do andamento de geração
        sin_retornar_assinaturas: str = "N",  # S/N - sinalizador para retorno das assinaturas do documento
        sin_retornar_publicacao: str = "N",  # S/N - sinalizador para retorno dos dados de publicação
        sin_retornar_campos: str = "N",  # S/N - sinalizador para retorno dos campos do formulário
        sin_retornar_blocos: str = "N",  #  S/N - sinalizador para retorno dos blocos na unidade que contém o documento
    ) -> "Documento":
        """Retorna estrutura de dados com informações sobre o documento.
        Args:
            protocolo_documento (str): Número do documento visível para o usuário, ex: 0003934.
            sin_retornar_andamento_geracao (str, opcional): S/N - sinalizador para retorno do andamento de geração. Valores possíveis: S - Sim, N - Não. Valor padrão: N.
            sin_retornar_assinaturas (str, opcional): S/N - sinalizador para retorno das assinaturas do documento. Valores possíveis: S - Sim, N - Não. Valor padrão: N.
            sin_retornar_publicacao (str, opcional): S/N - sinalizador para retorno dos dados de publicação. Valores possíveis: S - Sim, N - Não. Valor padrão: N.
            sin_retornar_campos (str, opcional): S/N - sinalizador para retorno dos campos do formulário. Valores possíveis: S - Sim, N - Não. Valor padrão: N.
            sin_retornar_blocos (str, opcional): S/N - sinalizador para retorno dos blocos na unidade que contém o documento. Valores possíveis: S - Sim, N - Não. Valor padrão: N.
        Returns:
            Documento: Estrutura Documento.

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

    def consultar_procedimento(
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
            sin_disponibilizar (str, opcional): Sinal de disponibilização. Valores possíveis: S - Sim, N - Não. Valor padrão: N.

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

    def gerar_procedimento(
        self,
        procedimento: dict,
        documentos: list = xsd.SkipValue,
        procedimentos_relacionados: list = xsd.SkipValue,
        unidades_envio: list = xsd.SkipValue,
        sin_manter_aberto_unidade: str = "N",
        sin_enviar_email_notificacao: str = "N",
        data_retorno_programado: str = xsd.SkipValue,
        dias_retorno_programado: str = xsd.SkipValue,
        sin_dias_uteis_retorno_programado: str = "N",
        id_marcador: str = xsd.SkipValue,
        texto_marcador: str = "",
        data_controle_prazo: str = xsd.SkipValue,
        dias_controle_prazo: str = xsd.SkipValue,
        sin_dias_uteis_controle_prazo: str = "N",
    ) -> dict:
        """Gera um processo no sistema SEI.

        Args:
            procedimento (dict): Dicionário com os atributos do procedimento.
            documentos (List[str], opcional): Lista de documentos a serem incluídos no bloco. Valor padrão: Nulo.
            procedimentos_relacionados (List[str], opcional): Lista de procedimentos relacionados. Valor padrão: Nulo.
            unidades_envio (List[str], opcional): Lista de unidades de destino. Valor padrão: Nulo.
            sin_manter_aberto_unidade (str, opcional): Sinal de manter aberto unidade. Valores possíveis: S - Sim, N - Não. Valor padrão: N.
            sin_enviar_email_notificacao (str, opcional): Sinal de enviar email notificação. Valores possíveis: S - Sim, N - Não. Valor padrão: N.
            data_retorno_programado (str, opcional): Data de retorno programado. Valores possíveis: Data ISO 8601. Valor padrão: N.
            dias_retorno_programado (str, opcional): Dias de retorno programado. Valores possíveis: Valores de 1 a 1000. Valor padrão: N.
            sin_dias_uteis_retorno_programado (str, opcional): Sinal de dias uteis de retorno programado. Valores possíveis: S - Sim, N - Não. Valor padrão: N.
            id_marcador (str, opcional): Identificador do marcador. Valor padrão: Nulo.
            texto_marcador (str, opcional): Texto do marcador. Valor padrão: N.
            data_controle_prazo (str, opcional): Data de controle de prazo. Valores possíveis: Data ISO 8601. Valor padrão: Nulo.
            dias_controle_prazo (str, opcional): Dias de controle de prazo. Valores possíveis: Valores de 1 a 1000. Valor padrão: Nulo.
            sin_dias_uteis_controle_prazo (str, opcional): Sinal de dias uteis de controle de prazo. Valores possíveis: S - Sim, N - Não. Valor padrão: N.

        Returns:
            dict: Dicionário com os atributos do procedimento.
        """
        return self._chamar_servico(
            "gerarProcedimento",
            IdUnidade=self.id_unidade,
            Procedimento=procedimento,
            Documentos=documentos,
            ProcedimentosRelacionados=procedimentos_relacionados,
            UnidadesEnvio=unidades_envio,
            SinManterAbertoUnidade=sin_manter_aberto_unidade,
            SinEnviarEmailNotificacao=sin_enviar_email_notificacao,
            DataRetornoProgramado=data_retorno_programado,
            DiasRetornoProgramado=dias_retorno_programado,
            SinDiasUteisRetornoProgramado=sin_dias_uteis_retorno_programado,
            IdMarcador=id_marcador,
            TextoMarcador=texto_marcador,
            DataControlePrazo=data_controle_prazo,
            DiasControlePrazo=dias_controle_prazo,
            SinDiasUteisControlePrazo=sin_dias_uteis_controle_prazo,
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
            sin_retornar_atributos (str, opcional): Sinal de retorno de atributos. Valores possíveis: S - Sim, N - Não. Valor padrão: N.
            andamentos (str, opcional): Filtra os andamentos. Valores possíveis: Qualquer id válido de andamento. A string vazia ("") indica que nenhum filtro é aplicado.
            tarefas (str, opcional): Filtra as tarefas. Valores possíveis: Qualquer id válido de tarefa. A string vazia ("") indica que nenhum filtro é aplicado.
            tarefas_modulos (str, opcional): Filtra os módulos de tarefas. Valores possíveis: Qualquer id válido de módulo de tarefa. A string vazia ("") indica que nenhum filtro é aplicado.

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
            marcadores (str, opcional): Filtra os andamentos com marcadores. Valores possíveis: Qualquer id válido de marcador. A string vazia ("") indica que nenhum filtro é aplicado.

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
            id_cargo (str, opcional): Filtra o cargo. Valores possíveis: Qualquer id válido de cargo. A string vazia ("") indica que nenhum filtro é aplicado.

        Returns:
            Um conjunto de ocorrências da estrutura Cargo.
        """
        return self._chamar_servico(
            "listarCargos",
            IdUnidade=self.id_unidade,
            IdCargo=id_cargo,
        )

    def listar_hipoteses_legais(self, nivel_acesso: str = "") -> list:
        """Lista os hipoteses legais com acesso configurado para a chave de acesso informada.

        Args:
            nivel_acesso (str): O nível de acesso a ser consultado. 1 - restrito, 2 - sigiloso, 3 - total.

        Returns:
            Uma lista de strings com os hipoteses legais.
        """
        if nivel_acesso:
            assert (
                nivel_acesso in ["1", "2"]
            ), "Valor inválido para nivel_acesso. Valores possíveis: 1 - restrito, 2 - sigiloso"
        return self._chamar_servico(
            "listarHipotesesLegais", IdUnidade=self.id_unidade, NivelAcesso=nivel_acesso
        )

    def listar_contatos(
        self,
        id_tipo_contato: str = "",
        pagina_registros: int = 1,
        pagina_atual: int = 1,
        sigla: str = "",
        nome: str = "",
        cpf: str = "",
        cnpj: str = "",
        matricula: str = "",
        id_contatos: str = "",
    ) -> List[Dict[str, str]]:
        """Lista os contatos na unidade informada.
        Args:
            id_tipo_contato (str, opcional): Filtra o tipo de contato. Valores possíveis: Qualquer id válido de tipo de contato. A string vazia ("") indica que nenhum filtro é aplicado.
            pagina_registros (int, opcional): Filtra a página de registros. Valores possíveis: Valores de 1 a 1000.
            pagina_atual (int, opcional): Filtra a página atual. Valores possíveis: Valores de 1 a 1000.
            sigla (str, opcional): Filtra o nome do contato. Valores possíveis: Qualquer nome de contato. A string vazia ("") indica que nenhum filtro é aplicado.
            nome (str, opcional): Filtra o nome do contato. Valores possíveis: Qualquer nome de contato. A string vazia ("") indica que nenhum filtro é aplicado.
            cpf (str, opcional): Filtra o CPF do contato. Valores possíveis: Qualquer CPF válido. A string vazia ("") indica que nenhum filtro é aplicado.
            cnpj (str, opcional): Filtra o CNPJ do contato. Valores possíveis: Qualquer CNPJ válido. A string vazia ("") indica que nenhum filtro é aplicado.
            matricula (str, opcional): Filtra a matrícula do contato. Valores possíveis: Qualquer matrícula válida. A string vazia ("") indica que nenhum filtro é aplicado.
            id_contatos (str, opcional): Filtra o ID do contato. Valores possíveis: Qualquer ID válido de contato. A string vazia ("") indica que nenhum filtro é aplicado.
        Returns:
            Uma lista de dicionários com os contatos com acesso configurado para a chave de acesso informada.
        """
        self._chamar_servico(
            "listarContatos",
            IdUnidade=self.id_unidade,
            IdTipoContato=id_tipo_contato,
            PaginaRegistros=pagina_registros,
            PaginaAtual=pagina_atual,
            Sigla=sigla,
            Nome=nome,
            Cpf=cpf,
            Cnpj=cnpj,
            Matricula=matricula,
            IdContatos=id_contatos,
        )

    def listar_estados(self, sigla_pais: str = "") -> List[Dict[str, str]]:
        """Lista os estados com acesso configurado para a chave de acesso informada.
        Args:
            sigla_pais (str, opcional): Filtra o estado. Valores possíveis: Qualquer sigla de pais válida. A string vazia ("") indica que nenhum filtro é aplicado.
        Returns:
            Uma lista de dicionários com os estados com acesso configurado para a chave de acesso informada.
        """
        if sigla_pais:
            id_pais = self._validar_pais(sigla_pais)
        else:
            id_pais = ""
        return self._chamar_servico(
            "listarEstados", IdUnidade=self.id_unidade, IdPais=id_pais
        )

    def listar_extensoes_permitidas(self, id_arquivo_extensao: str = "") -> list:
        """Lista as extensões de arquivo permitidas para o documento.
        Args:
            id_arquivo_extensao (str, opcional): Filtra a extensão do arquivo. Valores possíveis: Qualquer extensão válida de arquivo. A string vazia ("") indica que nenhum filtro é aplicado.
        Returns:
            Uma lista de strings com as extensões de arquivo permitidas para o documento.
        """
        if id_arquivo_extensao:
            assert (
                id_arquivo_extensao in EXTENSOES
            ), f"Extensão inválida: {id_arquivo_extensao}"
        return self._chamar_servico(
            "listarExtensoesPermitidas",
            IdUnidade=self.id_unidade,
            IdArquivoExtensao=id_arquivo_extensao,
        )

    def listar_marcadores_unidade(self) -> List[str]:
        """Lista os marcadores de unidades com acesso configurado para a chave de acesso informada.

        Returns:
            Uma lista de strings com os marcadores de unidades.
        """
        return self._chamar_servico(
            "listarMarcadoresUnidade", IdUnidade=self.id_unidade
        )

    def listar_paises(self) -> List[str]:
        """Lista os paises com acesso configurado para a chave de acesso informada.

        Returns:
            Uma lista de strings com os códigos dos paises.
        """
        return self._chamar_servico("listarPaises", IdUnidade=self.id_unidade)

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

    def listar_tipos_conferencia(self) -> List[Dict[str, str]]:
        """Lista os tipos de conferencia disponíveis na unidade.

        Returns:
            List[Dict[str, str]]: Lista de tipos de conferencia disponíveis na unidade.
        """
        return self._chamar_servico(
            "listarTiposConferencia",
            IdUnidade=self.id_unidade,
        )

    def listar_tipos_procedimento(
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

    def listar_tipos_prioridade(self) -> List[Dict[str, str]]:
        """Lista os tipos de prioridade disponíveis na unidade.

        Returns:
            List[Dict[str, str]]: Lista de tipos de prioridade disponíveis na unidade.
        """
        return self._chamar_servico(
            "listarTiposPrioridade",
            IdUnidade=self.id_unidade,
        )

    def listar_unidades(
        self,
        id_tipo_procedimento: str = "",  # Opcional. Filtra o tipo do processo
        tipo_de_documento: str = "",  # Opcional. Filtra a tipo de documento
    ) -> List[Dict[str, str]]:
        """Lista as unidades com acesso configurado para a chave de acesso informada.

        Args:
            id_tipo_procedimento (str, opcional): Filtra o tipo do processo. Valores possíveis: Qualquer id válido de processo. A string vazia ("") indica que nenhum filtro é aplicado.
            tipo_de_documento (str, opcional): Filtra o tipo de documento. Valores possíveis: Qualquer tipo válido de documento. A string vazia ("") indica que nenhum filtro é aplicado.

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

    def listar_usuarios(self, id_usuario: str = "") -> List[Dict[str, str]]:
        """Retorna o conjunto de usuários que possuem o perfil "Básico" do SEI na unidade.

        Args:
            sigla_unidade (str): Sigla da unidade.
            id_usuario (str, opcional): Filtra determinado usuário. Valores possíveis: Qualquer id válido de usuário. A string vazia ("") indica que nenhum filtro é aplicado.

        Returns:
            List[Dict[str, str]]: Lista de usuários que possuem o perfil "Básico" do SEI na unidade..
        """
        return self._chamar_servico(
            "listarUsuarios",
            IdUnidade=self.id_unidade,
            IdUsuario=id_usuario,
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

    def registrar_anotacao(self, anotacoes: dict) -> bool:
        """Registra uma anotação no sistema SEI.
        Args:
            anotacao (dict): conjunto de anotações a serem registradas.
        Returns:
            bool: True se o processo foi registrado com sucesso, False caso contrário.
        """
        return (
            self._chamar_servico(
                "registrarAnotacao",
                IdUnidade=self.id_unidade,
                Anotacoes=anotacoes,
            )
            == "1"
        )

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

    def remover_relacionamento_processo(
        self,
        protocolo_procedimento1: str,
        protocolo_procedimento2: str,
    ) -> bool:
        """Remove o relacionamento entre dois processos no sistema SEI.

        Args:
            protocolo_processo1 (str): O número do processo a ser removido.
            protocolo_processo2 (str): O número do processo a ser removido.

        Returns:
            bool: True se os processos foram removidos do relacionamento com sucesso, False caso contrário.
        """
        return (
            self._chamar_servico(
                "removerRelacionamentoProcesso",
                IdUnidade=self.id_unidade,
                ProtocoloProcedimento1=protocolo_procedimento1,
                ProtocoloProcedimento2=protocolo_procedimento2,
            )
            == "1"
        )

    def remover_sobrestamento_processo(
        self,
        protocolo_procedimento: str,
    ) -> bool:
        """Remove o sobrestamento de um processo no sistema SEI.

        Args:
            protocolo_procedimento (str): O número de protocolo do processo a ser removido do sobrestamento.

        Returns:
            bool: True se o processo foi removido do sobrestamento com sucesso, False caso contrário.
        """
        return (
            self._chamar_servico(
                "removerSobrestamentoProcesso",
                IdUnidade=self.id_unidade,
                ProtocoloProcedimento=protocolo_procedimento,
            )
            == "1"
        )

    def sobrestar_processo(
        self,
        protocolo_procedimento: str,
        protocolo_procedimento_vinculado: str,
        motivo: str,
    ) -> bool:
        """Sobrestar um processo no sistema SEI.

        Args:
            protocolo_procedimento (str): O número de protocolo do processo a ser sobrestado.
            protocolo_procedimento_vinculado (str): O número de protocolo do processo vinculado.
            motivo (str): Motivo do sobrestamento.

        Returns:
            bool: True se o processo foi sobrestado com sucesso, False caso contrário.
        """
        return (
            self._chamar_servico(
                "sobrestarProcesso",
                IdUnidade=self.id_unidade,
                ProtocoloProcedimento=protocolo_procedimento,
                ProtocoloProcedimentoVinculado=protocolo_procedimento_vinculado,
                Motivo=motivo,
            )
            == "1"
        )

    @cached_property
    def documentos(self):
        return {d["Nome"]: d for d in self.listar_series()}

    @cached_property
    def extensoes(self):
        return {d["Extensao"]: d for d in self.listar_extensoes_permitidas()}

    @cached_property
    def paises(self):
        return {d["Nome"]: d for d in self.listar_paises()}

    @cached_property
    def processos(self):
        return {d["Nome"]: d for d in self.listar_tipos_procedimento()}

    @cached_property
    def unidades(self):
        return {d["Sigla"]: d for d in self.listar_unidades()}

    @cached_property
    def usuarios(self):
        return {d["Sigla"]: d for d in self.listar_usuarios()}


def instanciar_cliente_sei(
    ambiente: str, sigla_sistema: str, chave_api: str, sigla_unidade: str
):
    assert ambiente in ["homologacao", "producao"], f"Ambiente inválido: {ambiente}"
    return SeiClient(
        cliente_soap=instanciar_cliente_soap(download_wsdl(ambiente)),
        sigla_sistema=sigla_sistema,
        chave_api=chave_api,
        sigla_unidade=sigla_unidade,
    )


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
        chave_api = os.environ["SEI_HM_API_KEY_BLOQUEIO"]
    elif sigla_sistema == "Fiscaliza":
        chave_api = os.environ["SEI_HM_API_KEY_FISCALIZA"]

    cliente_sei = instanciar_cliente_sei(
        ambiente="homologacao",
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
        Nome="DESCRICAO",
        Valor="Teste InovaFiscaliza",
        IdOrigem="3130803",
    )

    DefinicaoMarcador = cliente_sei.cliente.get_type("ns0:DefinicaoMarcador")

    definicao_marcador = xsd.AnyObject(
        DefinicaoMarcador,
        DefinicaoMarcador(
            ProtocoloProcedimento="53500.000124/2024-04",
            IdMarcador=90,
            Texto="Marcador de teste",
        ),
    )

    definicao_marcador = DefinicaoMarcador(
        ProtocoloProcedimento="53500.000124/2024-04",
        IdMarcador="90",
        Texto="Marcador de teste",
    )

    ArrayOfDefinicaoMarcador = cliente_sei.cliente.get_element("ns1:Array")

    array_definicao_marcador = ArrayOfDefinicaoMarcador(_value_1=[definicao_marcador])

    Procedimento = {
        "IdTipoProcedimento": "100000623",
        "NumeroProtocolo": xsd.SkipValue,
        "DataAutuacao": xsd.SkipValue,
        "Especificacao": "Teste de Geração de Procedimento - InovaFiscaliza",
        "IdTipoPrioridade": xsd.SkipValue,
        "Assuntos": xsd.SkipValue,
        "Interessados": xsd.SkipValue,
        "Observacao": xsd.SkipValue,
        "NivelAcesso": "0",
        "IdHipoteseLegal": xsd.SkipValue,
    }

    Anotacoes = [
        {
            "ProtocoloProcedimento": "53500.000612/2024-11",
            "Descricao": "Teste de Anotação",
            "SinPrioridade": "N",
        }
    ]

    # cliente_sei.anexar_processo("53500.000124/2024-04", "53500.201128/2014-28")

    # cliente_sei.bloquear_documento("0208319")

    # cliente_sei.bloquear_processo("53500.201128/2014-28")

    # cliente_sei.concluir_bloco("3723")

    # cliente_sei.reabrir_bloco("3723")

    # cliente_sei.disponibilizar_bloco("3723")

    # cliente_sei.cancelar_disponibilizacao_bloco("3723")

    # cliente_sei.cancelar_documento("0208314", "Cancelamento por falta de informações")

    # cliente_sei.concluir_controle_prazo(["53500.000124/2024-04"])

    # cliente_sei.consultar_procedimento(
    #     "53500.201128/2014-28",
    #     sin_retornar_assuntos="S",
    #     sin_retornar_interessados="S",
    #     sin_retornar_observacoes="S",
    #     sin_retornar_andamento_geracao="S",
    #     sin_retornar_andamento_conclusao="S",
    #     sin_retornar_ultimo_andamento="S",
    #     sin_retornar_unidades_procedimento_aberto="S",
    #     sin_retornar_procedimentos_relacionados="S",
    #     sin_retornar_procedimentos_anexados="S",
    # )

    # cliente_sei.definir_marcador(definicao_marcador)

    # cliente_sei.gerar_bloco(
    #     "A", "Bloco de assinatura", unidades, ["0208314", "0208319"], "S"
    # )

    # cliente_sei.gerar_procedimento(Procedimento)

    # cliente_sei.incluir_documento(documento)

    # cliente_sei.lancar_andamento(
    #     "53500.000124/2024-04",
    #     id_tarefa=65,
    #     id_tarefa_modulo=xsd.SkipValue,
    #     atributos=atributos_andamento,
    #     Nome="DESCRICAO",
    # )

    Andamento = [
        {
            "IdAndamento": None,
            "IdTarefa": None,
            "IdTarefaModulo": None,
            "Descricao": "Processo recebido na unidade",
            # 'DataHora': '17/10/2024 01:39:06',
            # 'Unidade': {
            #     'IdUnidade': '110000966',
            #     'Sigla': 'FIGF',
            #     'Descricao': 'Gerência de Fiscalização',
            #     'SinProtocolo': None,
            #     'SinArquivamento': None,
            #     'SinOuvidoria': None
            # },
            # 'Usuario': {
            #     'IdUsuario': '100001310',
            #     'Sigla': 'rsilva',
            #     'Nome': 'Ronaldo da Silva Alves Batista'
            # },
        }
    ]

    cliente_sei.listar_andamentos(
        "53500.000124/2024-04", "S", ["1"], xsd.SkipValue, xsd.SkipValue
    )

    # cliente_sei.listar_andamentos_marcadores("53500.000124/2024-04", xsd.SkipValue)

    # cliente_sei.listar_cargos()

    # cliente_sei.consultar_bloco("3754", "S")

    # cliente_sei.incluir_documento_bloco("3755", "0208319", "Autografe por obséquio")

    # cliente_sei.retirar_documento_bloco("3755", "0208319")

    # cliente_sei.registrar_anotacao(Anotacao)

    # cliente_sei.incluir_processo_bloco("3755", "53500.201128/2014-28", "Assine tudo!")

    # cliente_sei.listar_contatos(
    #     "1", 1, 1, xsd.SkipValue, xsd.SkipValue, xsd.SkipValue, "1"
    # )

    # cliente_sei.listar_estados()

    # cliente_sei.listar_extensoes_permitidas()

    # cliente_sei.listar_tipos_prioridade()

    # cliente_sei.listar_tipos_conferencia()

    # cliente_sei.listar_tipos_procedimento()

    # cliente_sei.listar_paises()

    # cliente_sei.listar_hipoteses_legais()

    # cliente_sei.listar_marcadores_unidade()

    # cliente_sei.listar_unidades()

    # cliente_sei.sobrestar_processo(
    #     protocolo_procedimento="53500.000124/2024-04",
    #     protocolo_procedimento_vinculado="53500.201128/2014-28",
    #     motivo="Teste",
    # )

    # cliente_sei.remover_relacionamento_processo(
    #     protocolo_procedimento1="53500.000124/2024-04",
    #     protocolo_procedimento2="53500.201128/2014-28",
    # )

    # cliente_sei.remover_sobrestamento_processo(
    #     protocolo_procedimento="53500.000124/2024-04"
    # )
