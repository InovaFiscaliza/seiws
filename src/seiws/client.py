def reabrir_processo(self, sigla_unidade: str, protocolo_procedimento: str) -> bool:
    """Reabre um processo.

    Args:
        sigla_unidade (str): Sigla da unidade no SEI.
        protocolo_procedimento (str): Número do processo visível para o usuário, ex: 12.1.000000077-4

    Returns:
        bool: True se o processo foi reaberto com sucesso, False caso contrário.
    """
