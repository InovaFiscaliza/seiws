import os
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(), override=True)

TIPOS_DE_PROCESSO = {
    "processos_bloqueio_sites": [
        "Demanda Externa: Ministério Público Federal",
        "Demanda Externa: Órgãos Governamentais Federais",
        "Demanda Externa: Judiciário",
        "Procuradoria: Cumprimento de Decisão Judicial",
    ],
    "Instrucao_processos_fiscalizacao": [
        "Fiscalização Regulatória: Fiscalização e Controle",
        "Fiscalização: Certificação",
        "Fiscalização: Tributário",
        "Fiscalização: Uso do Espectro",
        "Gestão da Fiscalização: Lacração, Apreensão e Interrupção",
        "Gestão da Fiscalização: Processo de Guarda",
    ],
}

PARAMETROS = {
    "SiglaSistema": "Fiscaliza",  # TODO: Mudar isso quando for testar para o InovaFiscaliza
}

CHAVES_API = {
    "homologação": {
        "processos_bloqueio_sites": {
            "chave_api": os.getenv("SEI_HM_API_KEY"),
        },
        "Instrucao_processos_fiscalizacao": {
            "chave_api": os.getenv(
                "SEI_HM_API_KEY"
            ),  # TODO: Mudar isso quando for testar para o InovaFiscaliza
        },
    },
    "produção": {
        "processos_bloqueio_sites": {
            "chave_api": os.getenv("SEI_PD_API_KEY_BLOQUEIO"),
        },
        "Instrucao_processos_fiscalizacao": {
            "chave_api": os.getenv("SEI_PD_API_KEY_INSTRUCAO"),
        },
    },
}
