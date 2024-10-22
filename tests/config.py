import os
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(), override=True)

AMBIENTES_DE_DESENVOLVIMENTO = ["desenvolvimento", "homologação", "produção"]

# Esse parâmetro é específico para o cadastro de serviços no SEI para o InovaFiscaliza
# Talvez faça sentido ficar parametrizado somente num módulo de teste.
IDENTIFICADOR_POR_PROCESSO = {
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

CHAVES_API = {
    "homologação": os.getenv("SEI_HM_API_KEY_BLOQUEIO"),
    "produção": os.getenv("SEI_PD_API_KEY_BLOQUEIO"),
}

# CHAVES_API = {
#     "homologação": {
#         "processos_bloqueio_sites": {
#             "chave_api": os.getenv("SEI_HM_API_KEY_BLOQUEIO"),
#         },
#         "Instrucao_processos_fiscalizacao": {
#             "chave_api": os.getenv("SEI_HM_API_KEY_INSTRUCAO"),
#         },
#     },
#     "produção": {
#         "processos_bloqueio_sites": {
#             "chave_api": os.getenv("SEI_PD_API_KEY_BLOQUEIO"),
#         },
#         "Instrucao_processos_fiscalizacao": {
#             "chave_api": os.getenv("SEI_PD_API_KEY_INSTRUCAO"),
#         },
#     },
# }
