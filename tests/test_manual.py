import os
from datetime import datetime
from pathlib import Path
import base64
from zeep import xsd

from dotenv import find_dotenv, load_dotenv

from seiws.client import instanciar_cliente_sei

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
