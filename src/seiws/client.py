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
            operacao = getattr(self.client.service, nome_operacao)
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
        protocolo_processo_principal: str,
        protocolo_processo_anexado: dict,
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
            ProtocoloProcessoPrincipal=protocolo_processo_principal,
            ProtocoloProcessoAnexado=protocolo_processo_anexado,
        )

        return chamada == "1"

    def bloquear_processo(
        self,
        protocolo_processo: str,
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
            ProtocoloProcesso=protocolo_processo,
        )

        return chamada == "1"

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

    def _validar_email(self, email: str):
        if not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", email):
            raise ValueError(f"Email inválido: {email}")

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
            self.consultar_documento(sigla_unidade, d)["IdDocumento"]
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
            IdUnidade=self._validar_unidade(unidade_origem),
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

    def incluir_documento(
        self,
        documento: dict,
    ) -> dict:
        return self._chamar_servico(
            "incluirDocumento",
            IdUnidade=self.id_unidade,
            Documento=documento,
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
            IdUnidade=self.id_unidade,
            IdUsuario=id_usuario,
        )

    def reabrir_processo(self, sigla_unidade: str, protocolo_procedimento: str) -> bool:
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

    @cached_property
    def unidades(self):
        return {d["Sigla"]: d for d in self.listar_unidades()}

    @cached_property
    def usuarios(self):
        return {d["Sigla"]: d for d in self.listar_usuarios()}

    @cached_property
    def documentos(self):
        return {d["Nome"]: d for d in self.listar_series()}


if __name__ == "__main__":
    import os
    from datetime import datetime
    from pathlib import Path
    import base64

    from dotenv import find_dotenv, load_dotenv

    load_dotenv(find_dotenv(), override=True)

    sigla_sistema = "InovaFiscaliza"

    client = SeiClient(
        sigla_sistema=sigla_sistema, chave_api=os.getenv("SEI_HM_API_KEY_BLOQUEIO")
    )

    # client.enviar_email(
    #     "FISF",
    #     "53500.000124/2024-04",
    #     "rsilva@anatel.gov.br",
    #     "eric@anatel.gov.br",
    #     "mer.de.dirac@gmail.com",
    #     assunto="Teste de Email via API",
    #     mensagem="Este é um teste de email enviado via API do SEI",
    #     documentos=["0206167"],
    # )

    # client.concluir_processo("FISF", "53500.000124/2024-04")

    # client.reabrir_processo("FISF", "53500.000124/2024-04")

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

    client.incluir_documento("FISF", documento=documento)
