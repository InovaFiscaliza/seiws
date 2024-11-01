from zeep import Client, xsd


from seiws.exceptions import (
    InvalidAmbienteError,
    InvalidWSDLError,
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
    def _download_wsdl(url, file):
        import urllib3
        http = urllib3.PoolManager()
        response = http.request('GET', url)
        file.write_bytes(response.data)
        return str(file)
    if ambiente == "homologação":
        WSDL_URL = "https://{}.anatel.gov.br/sei/controlador_ws.php?servico=sei"
        WSDL_HM = Path(__file__).parent / "seihm.wsdl"
        if WSDL_HM.is_file():
            return str(WSDL_HM)
        else:
            return _download_wsdl(WSDL_URL.format("seihm"), WSDL_HM)   
    elif ambiente == "produção":
        WSDL_URL = "https://{}.anatel.gov.br/sei/controlador_ws.php?servico=sei"
        WSDL_PD = Path(__file__).parent / "sei.wsdl"
        if WSDL_PD.is_file():
            return str(WSDL_PD)
        else:
            return _download_wsdl(WSDL_URL.format("sei"), WSDL_PD)
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
